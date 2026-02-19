"use client";

import { useMemo, useState } from "react";

export type SurahMarker = {
  time: number;
  surah: string;
  ayah: number;
  juz?: number;
  quality?: "high" | "ambiguous" | "inferred";
  reciter?: string;
};

type SurahIndexProps = {
  markers: SurahMarker[];
  onSeek?: (seconds: number) => void;
};

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function markerClasses(quality: SurahMarker["quality"]) {
  if (quality === "high") {
    return "border-green/40 text-green hover:border-green";
  }
  if (quality === "ambiguous") {
    return "border-sand/50 text-sand hover:border-sand";
  }
  return "border-line text-muted hover:border-line";
}

function isExcludedSurah(surah: string) {
  const normalized = surah.toLowerCase().replace(/[\s-]/g, "");
  return normalized.includes("fatiha") || normalized.includes("faatiha") || surah.includes("فاتحة");
}

function reciterLabel(reciter: string) {
  if (reciter === "Hasan" || reciter === "Samir") {
    return `Sheikh ${reciter}`;
  }
  if (reciter === "Talk") {
    return "Talk Segment";
  }
  return reciter;
}

export default function SurahIndex({ markers, onSeek }: SurahIndexProps) {
  const [openSurah, setOpenSurah] = useState<string | null>(null);

  const groupedSurahs = useMemo(() => {
    const dedupedMap = new Map<string, SurahMarker>();
    markers.forEach((marker) => {
      if (isExcludedSurah(marker.surah)) {
        return;
      }

      const reciter = marker.reciter?.trim() || "Unknown";
      const key = `${marker.surah}:${reciter}:${marker.ayah}`;
      const existing = dedupedMap.get(key);
      if (!existing || marker.time < existing.time) {
        dedupedMap.set(key, marker);
      }
    });

    const surahMap = new Map<string, Map<string, SurahMarker[]>>();
    Array.from(dedupedMap.values()).forEach((marker) => {
      const reciter = marker.reciter?.trim() || "Unknown";
      const reciterMap = surahMap.get(marker.surah) ?? new Map<string, SurahMarker[]>();
      const ayahs = reciterMap.get(reciter) ?? [];
      ayahs.push(marker);
      reciterMap.set(reciter, ayahs);
      surahMap.set(marker.surah, reciterMap);
    });

    const preferredOrder = ["Hasan", "Samir", "Talk", "Unknown"];

    return Array.from(surahMap.entries())
      .map(([surah, reciterMap]) => {
        const reciters = Array.from(reciterMap.entries())
          .map(([reciter, ayahs]) => ({
            reciter,
            ayahs: ayahs.sort((a, b) => a.ayah - b.ayah)
          }))
          .sort((a, b) => {
            const ia = preferredOrder.indexOf(a.reciter);
            const ib = preferredOrder.indexOf(b.reciter);
            if (ia === -1 && ib === -1) return a.reciter.localeCompare(b.reciter);
            if (ia === -1) return 1;
            if (ib === -1) return -1;
            return ia - ib;
          });

        const firstTime = Math.min(...reciters.flatMap((group) => group.ayahs.map((ayah) => ayah.time)));
        return { surah, reciters, firstTime };
      })
      .sort((a, b) => a.firstTime - b.firstTime);
  }, [markers]);

  if (!groupedSurahs.length) {
    return null;
  }

  return (
    <section className="w-full">
      <p className="label-caps">Indexed Surahs</p>
      <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
        <span className="rounded-full border border-green/40 px-2.5 py-1 text-green">High Confidence</span>
        <span className="rounded-full border border-sand/50 px-2.5 py-1 text-sand">Ambiguous</span>
        <span className="rounded-full border border-line px-2.5 py-1 text-muted">Inferred</span>
      </div>

      <ul className="mt-4 divide-y divide-line">
        {groupedSurahs.map((surahGroup) => {
          const isOpen = openSurah === surahGroup.surah;
          return (
            <li key={surahGroup.surah} className="py-4">
              <button
                type="button"
                onClick={() => setOpenSurah(isOpen ? null : surahGroup.surah)}
                className="flex w-full items-center justify-between gap-4 text-left"
              >
                <span className="text-sm text-ivory sm:text-base">{surahGroup.surah}</span>
                <span className="text-xs text-sand">{isOpen ? "Hide" : "Show"}</span>
              </button>

              {isOpen ? (
                <div className="mt-3 space-y-4">
                  {surahGroup.reciters.map((reciterGroup) => (
                    <div key={`${surahGroup.surah}-${reciterGroup.reciter}`}>
                      <p className="text-xs uppercase tracking-[0.15em] text-muted">{reciterLabel(reciterGroup.reciter)}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {reciterGroup.ayahs.map((marker) => (
                          <button
                            key={`${surahGroup.surah}-${reciterGroup.reciter}-${marker.ayah}`}
                            type="button"
                            onClick={() => onSeek?.(marker.time)}
                            className={`rounded-full border px-3 py-1.5 text-xs ${markerClasses(marker.quality)}`}
                          >
                            Ayah {marker.ayah} - {formatTime(marker.time)}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
