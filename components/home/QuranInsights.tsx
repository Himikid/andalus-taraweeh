"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { surahAyahCounts } from "@/data/surahAyahCounts";
import { availableTaraweehDays, getVideoPartsForDay, hasMultiplePartsForDay } from "@/data/taraweehVideos";

type Marker = {
  time: number;
  surah: string;
  ayah: number;
  surah_number?: number;
  juz?: number;
  quality?: "high" | "ambiguous" | "inferred" | "manual";
  __partId?: string | null;
  __seekTime?: number;
};

type QuranInsightsProps = {
  className?: string;
};

type DayPayload = {
  markers?: Marker[];
  meta?: {
    latest_position?: Marker;
  };
};

type DayData = {
  markers: Marker[];
  latestPosition: Marker | null;
};

async function fetchDayData(day: number): Promise<DayData> {
  const parts = getVideoPartsForDay(day);
  const hasParts = parts.length > 1;

  if (!hasParts) {
    const response = await fetch(`/data/day-${day}.json`, { cache: "no-store" });
    if (!response.ok) {
      return { markers: [], latestPosition: null };
    }
    const payload = (await response.json()) as DayPayload;
    const singlePartId = parts[0]?.id ?? null;
    const markers = Array.isArray(payload.markers)
      ? payload.markers.map((marker) => ({ ...marker, __partId: singlePartId, __seekTime: marker.time }))
      : [];
    const latestPosition = payload?.meta?.latest_position ? { ...payload.meta.latest_position } : null;
    return { markers, latestPosition };
  }

  const partMarkers: Marker[] = [];
  let runningOffset = 0;

  for (const part of parts) {
    const partPath = part.dataFile?.trim()
      ? part.dataFile.startsWith("/")
        ? part.dataFile
        : `/data/${part.dataFile}`
      : `/data/day-${day}-part-${part.id}.json`;

    const response = await fetch(partPath, { cache: "no-store" });
    if (!response.ok) {
      continue;
    }

    const payload = (await response.json()) as DayPayload;
    const markers = Array.isArray(payload.markers) ? payload.markers : [];
    const adjusted = markers
      .slice()
      .sort((a, b) => a.time - b.time)
      .map((marker) => ({
        ...marker,
        __partId: part.id,
        __seekTime: marker.time,
        time: marker.time + runningOffset,
      }));

    partMarkers.push(...adjusted);
    const partMaxTime = adjusted.length ? Math.max(...adjusted.map((marker) => marker.time)) : runningOffset;
    runningOffset = partMaxTime + 30;
  }

  return { markers: partMarkers, latestPosition: null };
}

type SurahEntry = {
  day: number;
  time: number;
  partId?: string | null;
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
      let latestCandidate: LatestPosition | null = null;

      for (const day of days) {
        try {
          const { markers, latestPosition } = await fetchDayData(day);
          if (!latestCandidate) {
            const marker = markers.length ? markers[markers.length - 1] : latestPosition;
            if (marker) {
              latestCandidate = { day, marker };
            }
          }
          if (markers.length) {
            records.push({ day, markers });
          }
        } catch {
          // ignore malformed/missing day JSON
        }
      }

      if (!active) return;
      if (!records.length && !latestCandidate) {
        setLatest(null);
        setSurahStarts({});
        setDayProgress([]);
        setTotalMarkers(0);
        setIndexedDays(0);
        return;
      }

      setLatest(latestCandidate);

      const startsByQuality: Record<
        string,
        { high: SurahEntry[]; manual: SurahEntry[]; ambiguous: SurahEntry[]; inferred: SurahEntry[] }
      > = {};
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
            const seekTime = marker.__seekTime ?? marker.time;
            const entry: SurahEntry = {
              day,
              time: seekTime,
              partId: marker.__partId ?? null,
              ayah: marker.ayah,
              juz: marker.juz,
            };
            const quality = marker.quality ?? "high";
            if (!startsByQuality[key]) {
              startsByQuality[key] = { high: [], manual: [], ambiguous: [], inferred: [] };
            }
            const bucket = startsByQuality[key][quality] ? quality : "ambiguous";
            startsByQuality[key][bucket].push(entry);
          });
        });

      const starts: Record<string, SurahEntry> = {};
      for (const [surah, buckets] of Object.entries(startsByQuality)) {
        const chosenBucket = buckets.high.length
          ? buckets.high
          : buckets.manual.length
            ? buckets.manual
            : buckets.ambiguous.length
              ? buckets.ambiguous
              : buckets.inferred;
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
    return Object.entries(surahStarts)
      .filter(([surah, entry]) => Boolean(surah?.trim()) && Number.isFinite(entry?.day) && Number.isFinite(entry?.time))
      .sort((a, b) => {
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
                  href={{
                    pathname: `/day/${entry.day}`,
                    query: {
                      ...(entry.partId && hasMultiplePartsForDay(entry.day) ? { part: entry.partId } : {}),
                      t: String(Math.max(0, Math.floor(entry.time))),
                    },
                  }}
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
