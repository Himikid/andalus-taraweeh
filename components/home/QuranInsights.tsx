"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { juzStarts } from "@/data/juzBoundaries";
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

type JuzHit = {
  juz: number;
  day: number;
  time: number;
};

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function buildPolyline(values: number[], maxTotal: number) {
  if (!values.length) return "";
  const width = 100;
  const height = 30;
  const denominator = values.length > 1 ? values.length - 1 : 1;
  return values
    .map((value, index) => {
      const x = (index / denominator) * width;
      const y = height - (Math.min(value, maxTotal) / maxTotal) * height;
      return `${x},${y}`;
    })
    .join(" ");
}

type AyahPos = {
  surah: number;
  ayah: number;
};

function compareAyahPos(a: AyahPos, b: AyahPos) {
  if (a.surah !== b.surah) return a.surah - b.surah;
  return a.ayah - b.ayah;
}

function countAyahsBetween(start: AyahPos, endExclusive: AyahPos) {
  if (compareAyahPos(start, endExclusive) >= 0) return 0;

  let count = 0;
  for (let surah = start.surah; surah <= endExclusive.surah; surah += 1) {
    const total = surahAyahCounts[surah] ?? 0;
    if (!total) continue;

    const startAyah = surah === start.surah ? start.ayah : 1;
    const endAyah = surah === endExclusive.surah ? endExclusive.ayah - 1 : total;

    if (endAyah >= startAyah) {
      count += endAyah - startAyah + 1;
    }
  }
  return count;
}

function nextAyah(pos: AyahPos): AyahPos {
  const total = surahAyahCounts[pos.surah] ?? 0;
  if (pos.ayah < total) {
    return { surah: pos.surah, ayah: pos.ayah + 1 };
  }
  return { surah: pos.surah + 1, ayah: 1 };
}

export default function QuranInsights({ className = "" }: QuranInsightsProps) {
  const [latest, setLatest] = useState<LatestPosition | null>(null);
  const [surahStarts, setSurahStarts] = useState<Record<string, SurahEntry>>({});
  const [dayProgress, setDayProgress] = useState<DayProgressPoint[]>([]);
  const [juzHits, setJuzHits] = useState<JuzHit[]>([]);
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
        setJuzHits([]);
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
      const firstJuzHits: JuzHit[] = [];

      records
        .slice()
        .sort((a, b) => a.day - b.day)
        .forEach(({ day, markers }) => {
          const timeline = markers.slice().sort((a, b) => a.time - b.time);
          const detectionMarkers = timeline.some((marker) => marker.quality !== "inferred")
            ? timeline.filter((marker) => marker.quality !== "inferred")
            : timeline;

          detectionMarkers.forEach((marker) => {
            if (marker.juz && !seenJuz.has(marker.juz)) {
              seenJuz.add(marker.juz);
              firstJuzHits.push({ juz: marker.juz, day, time: marker.time });
            }
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
      setJuzHits(firstJuzHits.sort((a, b) => a.juz - b.juz));
      setIndexedDays(records.length);
      setTotalMarkers(records.reduce((sum, record) => sum + record.markers.length, 0));
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

  const currentJuz = latest?.marker?.juz ?? 0;
  const currentSurahNumber = latest?.marker?.surah_number ?? 0;
  const currentSurahTotalAyahs = currentSurahNumber ? surahAyahCounts[currentSurahNumber] ?? 0 : 0;
  const surahCoverage = dayProgress[dayProgress.length - 1]?.surahCount ?? 0;
  const currentJuzProgress = useMemo(() => {
    if (!latest?.marker?.juz || !latest.marker.surah_number) return null;
    const juz = latest.marker.juz;
    const start = juzStarts.find((item) => item.juz === juz);
    if (!start) return null;

    const startPos: AyahPos = { surah: start.surah, ayah: start.ayah };
    const markerPos: AyahPos = { surah: latest.marker.surah_number, ayah: latest.marker.ayah };
    const nextBoundary = juzStarts.find((item) => item.juz === juz + 1);
    const endExclusive: AyahPos = nextBoundary ? { surah: nextBoundary.surah, ayah: nextBoundary.ayah } : { surah: 115, ayah: 1 };

    const total = countAyahsBetween(startPos, endExclusive);
    const completed = countAyahsBetween(startPos, nextAyah(markerPos));
    const percent = total ? Math.min(100, Math.max(0, (completed / total) * 100)) : 0;

    return { completed, total, percent };
  }, [latest]);

  const surahStartEntries = useMemo(() => {
    return Object.entries(surahStarts).sort((a, b) => {
      const entryA = a[1];
      const entryB = b[1];
      if (entryA.day !== entryB.day) return entryA.day - entryB.day;
      return entryA.time - entryB.time;
    });
  }, [surahStarts]);

  const juzPolyline = useMemo(() => buildPolyline(dayProgress.map((point) => point.juzCount), 30), [dayProgress]);
  const surahPolyline = useMemo(() => buildPolyline(dayProgress.map((point) => point.surahCount), 114), [dayProgress]);

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
            {currentJuzProgress ? (
              <p className="text-xs text-muted">
                Juz {currentJuz}: {currentJuzProgress.completed}/{currentJuzProgress.total} ayahs ({currentJuzProgress.percent.toFixed(1)}%)
              </p>
            ) : null}
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
        <p className="label-caps">Progress Charts</p>
        {dayProgress.length ? (
          <div className="mt-3 space-y-5">
            <div>
              <p className="text-xs text-muted">Juz progression (cumulative by day)</p>
              <svg viewBox="0 0 100 34" className="mt-2 h-14 w-full">
                <polyline fill="none" stroke="#9f7a48" strokeOpacity="0.25" strokeWidth="1.2" points="0,30 100,30" />
                <polyline fill="none" stroke="#3f8a67" strokeWidth="1.8" points={juzPolyline} />
              </svg>
              <p className="mt-1 text-xs text-muted">{dayProgress[dayProgress.length - 1]?.juzCount ?? 0} / 30 juz reached</p>
            </div>

            <div>
              <p className="text-xs text-muted">Surah progression (cumulative by day)</p>
              <svg viewBox="0 0 100 34" className="mt-2 h-14 w-full">
                <polyline fill="none" stroke="#3f8a67" strokeOpacity="0.25" strokeWidth="1.2" points="0,30 100,30" />
                <polyline fill="none" stroke="#9f7a48" strokeWidth="1.8" points={surahPolyline} />
              </svg>
              <p className="mt-1 text-xs text-muted">{dayProgress[dayProgress.length - 1]?.surahCount ?? 0} / 114 surahs reached</p>
            </div>

            {juzHits.length ? (
              <div>
                <p className="text-xs text-muted">Juz first-hit timeline</p>
                <div className="mt-2 flex max-h-28 flex-wrap gap-2 overflow-y-auto pr-1">
                  {juzHits.map((hit) => (
                    <span key={`juz-${hit.juz}`} className="rounded-full border border-line px-2.5 py-1 text-[11px] text-ivory">
                      J{hit.juz} · D{hit.day} · {formatTime(hit.time)}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : (
          <p className="mt-3 text-sm text-muted">Progress charts will appear after indexed markers are available.</p>
        )}
      </div>

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
