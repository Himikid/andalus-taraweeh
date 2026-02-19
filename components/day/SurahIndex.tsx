"use client";

import { useMemo, useState } from "react";

export type SurahMarker = {
  time: number;
  surah: string;
  ayah: number;
  juz?: number;
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

function isExcludedSurah(surah: string) {
  const normalized = surah.toLowerCase().replace(/[\s-]/g, "");
  return normalized.includes("fatiha") || normalized.includes("faatiha") || surah.includes("فاتحة");
}

export default function SurahIndex({ markers, onSeek }: SurahIndexProps) {
  const [openSurah, setOpenSurah] = useState<string | null>(null);
  const groupedMarkers = useMemo(() => {
    const dedupedMap = new Map<string, SurahMarker>();
    markers.forEach((marker) => {
      if (isExcludedSurah(marker.surah)) {
        return;
      }

      const key = `${marker.surah}:${marker.ayah}`;
      const existing = dedupedMap.get(key);
      if (!existing || marker.time < existing.time) {
        dedupedMap.set(key, marker);
      }
    });

    const map = new Map<string, SurahMarker[]>();
    Array.from(dedupedMap.values()).forEach((marker) => {
      const existing = map.get(marker.surah);
      if (existing) {
        existing.push(marker);
      } else {
        map.set(marker.surah, [marker]);
      }
    });

    return Array.from(map.entries()).map(([surah, ayahs]) => ({
      surah,
      ayahs: ayahs.sort((a, b) => a.ayah - b.ayah)
    }));
  }, [markers]);

  if (!groupedMarkers.length) {
    return null;
  }

  return (
    <section className="w-full">
      <p className="label-caps">Indexed Surahs</p>

      <ul className="mt-4 divide-y divide-line">
        {groupedMarkers.map((group) => {
          const isOpen = openSurah === group.surah;
          return (
            <li key={group.surah} className="py-4">
              <button
                type="button"
                onClick={() => setOpenSurah(isOpen ? null : group.surah)}
                className="flex w-full items-center justify-between gap-4 text-left"
              >
                <span className="text-sm text-ivory sm:text-base">{group.surah}</span>
                <span className="text-xs text-sand">{isOpen ? "Hide" : "Show"}</span>
              </button>

              {isOpen ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {group.ayahs.map((marker) => (
                    <button
                      key={`${group.surah}-${marker.ayah}`}
                      type="button"
                      onClick={() => onSeek?.(marker.time)}
                      className="rounded-full border border-line px-3 py-1.5 text-xs text-ivory hover:border-sand hover:text-sand"
                    >
                      Ayah {marker.ayah} - {formatTime(marker.time)}
                    </button>
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
