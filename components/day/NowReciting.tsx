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
  const [isPaused, setIsPaused] = useState(false);
  const [pausedIndex, setPausedIndex] = useState<number | null>(null);

  const timeline = useMemo(() => {
    return markers.slice().sort((a, b) => a.time - b.time);
  }, [markers]);

  const liveIndex = useMemo(() => {
    if (!timeline.length) return null;
    let index = -1;
    for (let i = 0; i < timeline.length; i += 1) {
      if (timeline[i].time <= currentTime) {
        index = i;
      } else {
        break;
      }
    }
    return index >= 0 ? index : 0;
  }, [timeline, currentTime]);

  const effectiveIndex = isPaused ? pausedIndex : liveIndex;
  const active = effectiveIndex !== null ? timeline[effectiveIndex] : null;
  const activeKey = active?.surah_number ? `${active.surah_number}:${active.ayah}` : null;

  function handlePause() {
    if (liveIndex === null) return;
    setPausedIndex(liveIndex);
    setIsPaused(true);
  }

  function handleResume() {
    setIsPaused(false);
    setPausedIndex(null);
  }

  function handleStep(direction: -1 | 1) {
    if (!timeline.length) return;
    const baseIndex = isPaused ? (pausedIndex ?? liveIndex ?? 0) : (liveIndex ?? 0);
    const nextIndex = Math.max(0, Math.min(timeline.length - 1, baseIndex + direction));
    setPausedIndex(nextIndex);
    setIsPaused(true);
  }

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
      <div className="mt-4 rounded-2xl border border-line/80 bg-panel/55 p-4 sm:p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-muted">
            {active.surah} · Ayah {active.ayah} · {formatTime(active.time)} · {reciterLabel(active.reciter)}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleStep(-1)}
              disabled={!timeline.length}
              className="rounded-full border border-line px-3 py-1 text-xs text-ivory disabled:cursor-not-allowed disabled:opacity-50"
            >
              ←
            </button>
            {isPaused ? (
              <button
                type="button"
                onClick={handleResume}
                className="rounded-full border border-green/40 px-3 py-1 text-xs text-green"
              >
                Play
              </button>
            ) : (
              <button type="button" onClick={handlePause} className="rounded-full border border-line px-3 py-1 text-xs text-ivory">
                Pause
              </button>
            )}
            <button
              type="button"
              onClick={() => handleStep(1)}
              disabled={!timeline.length}
              className="rounded-full border border-line px-3 py-1 text-xs text-ivory disabled:cursor-not-allowed disabled:opacity-50"
            >
              →
            </button>
          </div>
        </div>
        <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-sand">{isPaused ? "Manual preview paused" : "Synced to video"}</p>
        <div className="mb-3 flex justify-end">
          <div className="inline-flex items-center rounded-full border border-sand/45 bg-sand/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-sand">
            AI Beta
          </div>
        </div>
        {resolvedArabic ? (
          <p className="text-right font-[var(--font-arabic)] text-2xl leading-loose text-ivory sm:text-[1.8rem]">
            {resolvedArabic}
          </p>
        ) : null}

        {resolvedEnglish ? (
          <p className="mt-4 text-sm leading-7 text-muted sm:text-base">{resolvedEnglish}</p>
        ) : (
          <p className="mt-4 text-sm text-muted">Translation unavailable for this ayah.</p>
        )}
      </div>
    </section>
  );
}
