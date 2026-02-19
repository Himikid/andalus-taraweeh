"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { availableTaraweehDays } from "@/data/taraweehVideos";

type Marker = {
  time: number;
  surah: string;
  ayah: number;
  juz?: number;
};

type QuranInsightsProps = {
  className?: string;
};

type DayPayload = {
  markers?: Marker[];
};

type SurahEntry = {
  day: number;
  time: number;
  ayah: number;
  juz?: number;
};

type LatestPosition = {
  day: number;
  marker: Marker;
};

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export default function QuranInsights({ className = "" }: QuranInsightsProps) {
  const [latest, setLatest] = useState<LatestPosition | null>(null);
  const [surahStarts, setSurahStarts] = useState<Record<string, SurahEntry>>({});

  useEffect(() => {
    let active = true;

    async function load() {
      const days = [...availableTaraweehDays].sort((a, b) => b - a);
      const records: { day: number; markers: Marker[] }[] = [];

      for (const day of days) {
        try {
          const response = await fetch(`/data/day-${day}.json`, { cache: "no-store" });
          if (!response.ok) continue;
          const payload = (await response.json()) as DayPayload;
          const markers = Array.isArray(payload.markers) ? payload.markers : [];
          if (markers.length) {
            records.push({ day, markers });
          }
        } catch {
          // ignore malformed/missing day JSON
        }
      }

      if (!active) return;
      if (!records.length) {
        setLatest(null);
        setSurahStarts({});
        return;
      }

      const latestRecord = records[0];
      const latestMarker = latestRecord.markers[latestRecord.markers.length - 1];
      setLatest({ day: latestRecord.day, marker: latestMarker });

      const starts: Record<string, SurahEntry> = {};
      records
        .slice()
        .reverse()
        .forEach(({ day, markers }) => {
          markers.forEach((marker) => {
            const key = marker.surah;
            const entry: SurahEntry = { day, time: marker.time, ayah: marker.ayah, juz: marker.juz };
            const existing = starts[key];
            if (!existing) {
              starts[key] = entry;
              return;
            }
            if (day < existing.day || (day === existing.day && entry.time < existing.time)) {
              starts[key] = entry;
            }
          });
        });

      setSurahStarts(starts);
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  const progress = useMemo(() => {
    if (!latest?.marker?.juz) return 0;
    return Math.min(100, Math.max(0, (latest.marker.juz / 30) * 100));
  }, [latest]);

  return (
    <section className={`tile-shell px-6 py-7 sm:px-7 sm:py-8 ${className}`}>
      <p className="label-caps">Quran Progress</p>

      {latest ? (
        <div className="mt-4 space-y-4">
          <div>
            <p className="text-sm text-muted">Latest populated day</p>
            <p className="mt-1 text-base text-ivory">Day {latest.day}</p>
          </div>

          <div>
            <p className="text-sm text-muted">Current detected position</p>
            <p className="mt-1 text-base text-ivory">
              {latest.marker.surah} · Ayah {latest.marker.ayah}
              {latest.marker.juz ? ` · Juz ${latest.marker.juz}` : ""}
            </p>
            <p className="mt-1 text-sm text-muted">Timestamp {formatTime(latest.marker.time)}</p>
          </div>

          <div className="space-y-2">
            <div className="h-2 w-full overflow-hidden rounded-full bg-[#c8d8cd]">
              <div className="h-full rounded-full bg-green" style={{ width: `${progress}%` }} />
            </div>
            <p className="text-xs text-muted">Estimated Quran progress: {progress.toFixed(1)}%</p>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted">No indexed ayah data found yet.</p>
      )}

      <div className="mt-7 border-t border-line pt-5">
        <p className="label-caps">Navigate By Surah</p>
        {Object.keys(surahStarts).length ? (
          <div className="mt-3 max-h-[26rem] overflow-y-auto pr-1">
            <div className="flex flex-wrap gap-2">
              {Object.entries(surahStarts).map(([surah, entry]) => (
                <Link
                  key={`${surah}-${entry.day}-${entry.time}`}
                  href={`/day/${entry.day}?t=${entry.time}`}
                  className="rounded-full border border-line px-3 py-1.5 text-xs text-ivory hover:border-sand hover:text-sand"
                >
                  {surah}
                </Link>
              ))}
            </div>
          </div>
        ) : (
          <p className="mt-3 text-sm text-muted">Surah navigation will appear after indexing.</p>
        )}
      </div>

      <p className="mt-5 text-xs leading-5 text-muted">
        AI-powered indexing. Timestamps and ayah matches are best effort and may contain minor inaccuracies.
      </p>
    </section>
  );
}
