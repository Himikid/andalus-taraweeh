"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getDateForRamadanDay } from "@/data/ramadan";
import { fetchDayArchiveMeta, type DayArchiveMeta } from "@/data/archiveMeta";

type PublishedDaysProps = {
  days: number[];
};

export default function PublishedDays({ days }: PublishedDaysProps) {
  const [metaByDay, setMetaByDay] = useState<Record<number, DayArchiveMeta>>({});

  useEffect(() => {
    let mounted = true;

    async function load() {
      const pairs = await Promise.all(
        days.map(async (day) => {
          const meta = await fetchDayArchiveMeta(day);
          return [day, meta] as const;
        }),
      );

      if (!mounted) return;
      const next: Record<number, DayArchiveMeta> = {};
      for (const [day, meta] of pairs) {
        next[day] = meta;
      }
      setMetaByDay(next);
    }

    void load();
    return () => {
      mounted = false;
    };
  }, [days]);

  if (!days.length) {
    return (
      <p className="mt-7 text-sm text-muted">
        No livestream days are published yet. Add YouTube IDs in <span className="text-ivory">data/taraweehVideos.ts</span>.
      </p>
    );
  }

  return (
    <>
      <ul className="mt-7 divide-y divide-line border-y border-line">
        {days.map((day) => {
          const meta = metaByDay[day];
          return (
            <li key={day}>
              <Link href={`/day/${day}`} className="flex items-center justify-between gap-4 py-4">
                <div>
                  <p className="text-sm font-medium text-ivory sm:text-base">Ramadan Day {day}</p>
                  <p className="mt-1 text-sm text-muted">{getDateForRamadanDay(day)}</p>
                  <p className="mt-1 text-xs text-sand">{meta?.juzLabel ?? "Loading Juz..."}</p>
                  {meta && meta.streamParts > 1 ? <p className="mt-1 text-xs text-muted">{meta.streamParts} stream parts</p> : null}
                </div>
                <span className="text-sm text-sand">Open</span>
              </Link>
            </li>
          );
        })}
      </ul>

      <div className="mt-6">
        <Link
          href="/archive"
          className="inline-flex items-center rounded-full border border-sand/35 px-5 py-2 text-sm text-sand hover:border-sand hover:text-ivory"
        >
          View Full Archive
        </Link>
      </div>
    </>
  );
}
