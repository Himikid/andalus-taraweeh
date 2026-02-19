"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { surahAyahCounts } from "@/data/surahAyahCounts";
import { availableTaraweehDays } from "@/data/taraweehVideos";

type Marker = {
  time: number;
  surah: string;
  ayah: number;
  surah_number?: number;
  juz?: number;
  quality?: "high" | "ambiguous" | "inferred";
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

type DayProgressPoint = {
  day: number;
  juzCount: number;
  surahCount: number;
};

export default function QuranInsights({ className = "" }: QuranInsightsProps) {
  const [latest, setLatest] = useState<LatestPosition | null>(null);
  const [surahStarts, setSurahStarts] = useState<Record<string, SurahEntry>>({});
  const [dayProgress, setDayProgress] = useState<DayProgressPoint[]>([]);
  const [totalMarkers, setTotalMarkers] = useState(0);
  const [indexedDays, setIndexedDays] = useState(0);

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
        setDayProgress([]);
        setTotalMarkers(0);
        setIndexedDays(0);
        return;
      }

      const latestRecord = records[0];
      const latestMarker = latestRecord.markers[latestRecord.markers.length - 1];
      setLatest({ day: latestRecord.day, marker: latestMarker });

      const startsByQuality: Record<string, Record<string, SurahEntry[]>> = {};
      const seenJuz = new Set<number>();
      const seenSurah = new Set<string>();
      const progressPoints: DayProgressPoint[] = [];

      records
        .slice()
        .sort((a, b) => a.day - b.day)
        .forEach(({ day, markers }) => {
          const timeline = markers.slice().sort((a, b) => a.time - b.time);
          const detectionMarkers = timeline.some((marker) => marker.quality !== "inferred")
            ? timeline.filter((marker) => marker.quality !== "inferred")
            : timeline;

          detectionMarkers.forEach((marker) => {
            if (marker.juz) seenJuz.add(marker.juz);
            if (marker.surah) {
              seenSurah.add(marker.surah);
            }
          });

          progressPoints.push({
            day,
            juzCount: seenJuz.size,
            surahCount: seenSurah.size,
          });
        });

      records
        .slice()
        .reverse()
        .forEach(({ day, markers }) => {
          markers.forEach((marker) => {
            const key = marker.surah;
            const entry: SurahEntry = { day, time: marker.time, ayah: marker.ayah, juz: marker.juz };
            const quality = marker.quality ?? "high";
            if (!startsByQuality[key]) {
              startsByQuality[key] = { high: [], ambiguous: [], inferred: [] };
            }
            startsByQuality[key][quality].push(entry);
          });
        });

      const starts: Record<string, SurahEntry> = {};
      for (const [surah, buckets] of Object.entries(startsByQuality)) {
        const chosenBucket = buckets.high.length ? buckets.high : buckets.ambiguous.length ? buckets.ambiguous : buckets.inferred;
        chosenBucket.sort((a, b) => (a.day !== b.day ? a.day - b.day : a.time - b.time));
        if (chosenBucket[0]) {
          starts[surah] = chosenBucket[0];
        }
      }

      setSurahStarts(starts);
      setDayProgress(progressPoints);
      setIndexedDays(records.length);
      setTotalMarkers(records.reduce((sum, record) => sum + record.markers.length, 0));
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  const currentJuz = latest?.marker?.juz ?? 0;
  const currentSurahNumber = latest?.marker?.surah_number ?? 0;
  const currentSurahTotalAyahs = currentSurahNumber ? surahAyahCounts[currentSurahNumber] ?? 0 : 0;
  const surahCoverage = dayProgress[dayProgress.length - 1]?.surahCount ?? 0;

  const surahStartEntries = useMemo(() => {
    return Object.entries(surahStarts).sort((a, b) => {
      const entryA = a[1];
      const entryB = b[1];
      if (entryA.day !== entryB.day) return entryA.day - entryB.day;
      return entryA.time - entryB.time;
    });
  }, [surahStarts]);

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
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-2xl border border-line bg-charcoalSoft px-3 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-muted">Juz Progress</p>
              <p className="mt-1 text-xl text-ivory">{currentJuz} / 30</p>
            </div>
            <div className="rounded-2xl border border-line bg-charcoalSoft px-3 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-muted">Surah Coverage</p>
              <p className="mt-1 text-xl text-ivory">{surahCoverage} / 114</p>
            </div>
            <div className="rounded-2xl border border-line bg-charcoalSoft px-3 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-muted">Current Surah</p>
              <p className="mt-1 text-xl text-ivory">{currentSurahNumber || "-"} / 114</p>
            </div>
            <div className="rounded-2xl border border-line bg-charcoalSoft px-3 py-3">
              <p className="text-[11px] uppercase tracking-[0.14em] text-muted">Current Ayah</p>
              <p className="mt-1 text-xl text-ivory">
                {latest.marker.ayah}
                {currentSurahTotalAyahs ? ` / ${currentSurahTotalAyahs}` : ""}
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-sand/30 bg-charcoalSoft px-3 py-3">
            <p className="text-[11px] uppercase tracking-[0.14em] text-sand">AI Timeline Active</p>
            <p className="mt-1 text-sm text-ivory">
              Auto-indexed {totalMarkers} moments across {indexedDays} published day{indexedDays === 1 ? "" : "s"}.
            </p>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted">No indexed ayah data found yet.</p>
      )}

      <div className="mt-7 border-t border-line pt-5">
        <p className="label-caps">Navigate By Surah</p>
        {surahStartEntries.length ? (
          <div className="mt-3 max-h-[26rem] overflow-y-auto pr-1">
            <div className="flex flex-wrap gap-2">
              {surahStartEntries.map(([surah, entry]) => (
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
