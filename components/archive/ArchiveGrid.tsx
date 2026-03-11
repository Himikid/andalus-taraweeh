"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchDayArchiveMeta, type DayArchiveMeta } from "@/data/archiveMeta";
import { getDateForRamadanDay } from "@/data/ramadan";

type ArchiveGridProps = {
  days: number[];
};

function formatAyahRange(startAyah: number, endAyah: number) {
  if (startAyah === endAyah) return `${startAyah}`;
  return `${startAyah}-${endAyah}`;
}

export default function ArchiveGrid({ days }: ArchiveGridProps) {
  const [items, setItems] = useState<DayArchiveMeta[]>([]);

  useEffect(() => {
    let mounted = true;

    async function load() {
      const results = await Promise.allSettled(days.map((day) => fetchDayArchiveMeta(day)));
      const metas = results
        .filter((result): result is PromiseFulfilledResult<DayArchiveMeta> => result.status === "fulfilled")
        .map((result) => result.value);
      if (!mounted) return;
      setItems(metas.sort((a, b) => b.day - a.day));
    }

    void load();
    return () => {
      mounted = false;
    };
  }, [days]);

  if (!days.length) {
    return <p className="text-sm text-muted">No published days available yet.</p>;
  }

  const source = items.length ? items : days.map((day) => ({ day } as DayArchiveMeta));

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {source.map((item) => {
        const surahs = item.surahs ?? [];
        return (
          <Link key={item.day} href={`/day/${item.day}`} className="tile-shell block px-5 py-5 sm:px-6 sm:py-6">
            <p className="label-caps">Day {item.day}</p>
            <p className="mt-2 text-lg font-semibold text-ivory">Ramadan Day {item.day}</p>
            <p className="mt-1 text-sm text-muted">{getDateForRamadanDay(item.day)}</p>

            <div className="mt-4 space-y-1.5">
              <p className="text-xs uppercase tracking-[0.14em] text-sand">{item.juzLabel ?? "Loading Juz..."}</p>
              <p className="text-sm text-muted">{item.surahLabel ?? "Loading Surahs..."}</p>
            </div>

            {surahs.length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {surahs.slice(0, 4).map((surah) => (
                  <span key={`${item.day}-${surah.surahNumber}`} className="rounded-full border border-line px-2.5 py-1 text-xs text-ivory">
                    {surah.surahName} {formatAyahRange(surah.startAyah, surah.endAyah)}
                  </span>
                ))}
                {surahs.length > 4 ? (
                  <span className="rounded-full border border-line px-2.5 py-1 text-xs text-muted">+{surahs.length - 4} more</span>
                ) : null}
              </div>
            ) : (
              <p className="mt-4 text-xs text-muted">Indexing in progress</p>
            )}
          </Link>
        );
      })}
    </div>
  );
}
