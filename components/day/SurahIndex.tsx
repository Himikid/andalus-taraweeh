"use client";

import { useMemo, useState } from "react";

export type SurahMarker = {
  time: number;
  surah: string;
  ayah: number;
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

export default function SurahIndex({ markers, onSeek }: SurahIndexProps) {
  const [openSurah, setOpenSurah] = useState<string | null>(null);
  const groupedMarkers = useMemo(() => {
    const map = new Map<string, SurahMarker[]>();
    markers.forEach((marker) => {
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

  if (!markers.length) {
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
                <span className="text-xs text-green">{isOpen ? "Hide" : "Show"}</span>
              </button>

              {isOpen ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {group.ayahs.map((marker) => (
                    <button
                      key={`${group.surah}-${marker.ayah}`}
                      type="button"
                      onClick={() => onSeek?.(marker.time)}
                      className="rounded-full border border-line px-3 py-1.5 text-xs text-ivory hover:border-green hover:text-green"
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
