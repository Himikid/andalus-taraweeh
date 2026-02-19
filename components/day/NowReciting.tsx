"use client";

import { useEffect, useMemo, useState } from "react";
import type { SurahMarker } from "@/components/day/SurahIndex";

type NowRecitingProps = {
  markers: SurahMarker[];
  currentTime: number;
};

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function reciterLabel(reciter?: string) {
  if (reciter === "Hasan" || reciter === "Samir") {
    return `Sheikh ${reciter}`;
  }
  if (reciter === "Talk") {
    return "Talk Segment";
  }
  return reciter || "Unknown";
}

export default function NowReciting({ markers, currentTime }: NowRecitingProps) {
  const [textCache, setTextCache] = useState<Record<string, { arabic?: string; english?: string }>>({});

  const timeline = useMemo(() => {
    return markers.slice().sort((a, b) => a.time - b.time);
  }, [markers]);

  const active = useMemo(() => {
    if (!timeline.length) return null;
    let index = -1;
    for (let i = 0; i < timeline.length; i += 1) {
      if (timeline[i].time <= currentTime) {
        index = i;
      } else {
        break;
      }
    }
    return index >= 0 ? timeline[index] : timeline[0];
  }, [timeline, currentTime]);

  const activeKey = active?.surah_number ? `${active.surah_number}:${active.ayah}` : null;

  useEffect(() => {
    if (!active || !active.surah_number || !activeKey) return;
    if (active.arabic_text && active.english_text) return;
    if (textCache[activeKey]?.arabic || textCache[activeKey]?.english) return;

    const key = activeKey;
    const surahNumber = active.surah_number;
    const ayahNumber = active.ayah;
    let mounted = true;

    async function fetchMissingText() {
      try {
        const [arabicRes, englishRes] = await Promise.all([
          fetch(`https://api.alquran.cloud/v1/ayah/${surahNumber}:${ayahNumber}/quran-uthmani`, { cache: "force-cache" }),
          fetch(`https://api.alquran.cloud/v1/ayah/${surahNumber}:${ayahNumber}/en.asad`, { cache: "force-cache" }),
        ]);

        const [arabicPayload, englishPayload] = await Promise.all([arabicRes.json(), englishRes.json()]);

        if (!mounted) return;

        const arabic = String(arabicPayload?.data?.text ?? "").trim();
        const english = String(englishPayload?.data?.text ?? "").trim();

        setTextCache((previous) => ({
          ...previous,
          [key]: {
            arabic: arabic || undefined,
            english: english || undefined,
          },
        }));
      } catch {
        // Ignore fetch errors and continue with available text.
      }
    }

    fetchMissingText();

    return () => {
      mounted = false;
    };
  }, [active, activeKey, textCache]);

  if (!active) {
    return (
      <section className="w-full">
        <p className="label-caps">Now Reciting</p>
        <p className="mt-3 text-sm text-muted">No Arabic/English ayah text available for this day yet.</p>
      </section>
    );
  }

  const resolvedArabic = active.arabic_text || (activeKey ? textCache[activeKey]?.arabic : undefined);
  const resolvedEnglish = active.english_text || (activeKey ? textCache[activeKey]?.english : undefined);

  return (
    <section className="w-full">
      <p className="label-caps">Now Reciting</p>
      <p className="mt-2 text-xs text-muted">
        {active.surah} · Ayah {active.ayah} · {formatTime(active.time)} · {reciterLabel(active.reciter)}
      </p>

      {resolvedArabic ? (
        <p className="mt-4 text-right font-[var(--font-arabic)] text-2xl leading-loose text-ivory sm:text-[1.8rem]">
          {resolvedArabic}
        </p>
      ) : null}

      {resolvedEnglish ? (
        <p className="mt-4 text-sm leading-7 text-muted sm:text-base">{resolvedEnglish}</p>
      ) : (
        <p className="mt-4 text-sm text-muted">Translation unavailable for this ayah.</p>
      )}
    </section>
  );
}
