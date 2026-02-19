"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import DaySelector from "@/components/day/DaySelector";
import RecitersInfo from "@/components/shared/RecitersInfo";
import SurahIndex, { type SurahMarker } from "@/components/day/SurahIndex";
import VideoPlayer from "@/components/day/VideoPlayer";
import { getDateForRamadanDay } from "@/data/ramadan";
import { availableTaraweehDays, getVideoIdForDay } from "@/data/taraweehVideos";

type DayData = {
  markers?: SurahMarker[];
};

type DayPageClientProps = {
  initialDay: number;
};

export default function DayPageClient({ initialDay }: DayPageClientProps) {
  const router = useRouter();

  const fallbackDay = availableTaraweehDays[0] ?? 1;
  const safeInitialDay = availableTaraweehDays.includes(initialDay) ? initialDay : fallbackDay;

  const [selectedDay, setSelectedDay] = useState(safeInitialDay);
  const [markers, setMarkers] = useState<SurahMarker[]>([]);
  const [manualVideoId, setManualVideoId] = useState("");
  const [seekTime, setSeekTime] = useState<number | undefined>(undefined);
  const hasInitializedSeekReset = useRef(false);

  const dayVideoId = getVideoIdForDay(selectedDay);
  const effectiveVideoId = manualVideoId || dayVideoId;

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const videoId = params.get("video")?.trim() ?? "";
    const seekParam = params.get("t");
    const parsedSeek = seekParam ? Number.parseInt(seekParam, 10) : NaN;
    setManualVideoId(videoId);
    if (Number.isFinite(parsedSeek) && parsedSeek > 0) {
      setSeekTime(parsedSeek);
    }
  }, []);

  useEffect(() => {
    if (selectedDay !== safeInitialDay) {
      setSelectedDay(safeInitialDay);
    }
  }, [safeInitialDay, selectedDay]);

  useEffect(() => {
    if (!hasInitializedSeekReset.current) {
      hasInitializedSeekReset.current = true;
      return;
    }
    setSeekTime(undefined);
  }, [selectedDay, effectiveVideoId]);

  useEffect(() => {
    let isMounted = true;

    async function loadIndex() {
      try {
        const response = await fetch(`/data/day-${selectedDay}.json`, { cache: "no-store" });
        if (!response.ok) {
          if (isMounted) {
            setMarkers([]);
          }
          return;
        }

        const data = (await response.json()) as DayData;
        if (isMounted) {
          setMarkers(Array.isArray(data.markers) ? data.markers : []);
        }
      } catch {
        if (isMounted) {
          setMarkers([]);
        }
      }
    }

    loadIndex();

    return () => {
      isMounted = false;
    };
  }, [selectedDay]);

  function handleDayChange(day: number) {
    const params = new URLSearchParams(window.location.search);
    const query = params.toString();
    const pathname = `/day/${day}`;
    router.push(query ? `${pathname}?${query}` : pathname);
    setSelectedDay(day);
  }

  return (
    <main className="app-shell px-5 py-10 sm:px-8 sm:py-14 lg:py-16">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 sm:gap-10">
        <header className="px-2 text-left sm:px-3">
          <p className="label-caps">Andalus Taraweeh Archive</p>
          <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="font-[var(--font-heading)] text-3xl leading-none text-ivory sm:text-4xl">Ramadan Day {selectedDay}</h1>
              <p className="mt-2 text-sm text-muted">{getDateForRamadanDay(selectedDay)}</p>
            </div>
            <Link href="/" className="rounded-full border border-line px-4 py-2 text-sm text-ivory">
              Back to Home
            </Link>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-12">
          <div className="space-y-6 lg:col-span-8">
            <VideoPlayer videoId={effectiveVideoId} startAt={seekTime} />
            <section className="tile-shell px-6 py-7 sm:px-7 sm:py-8">
              <SurahIndex markers={markers} onSeek={setSeekTime} />
            </section>
          </div>

          <aside className="space-y-6 lg:col-span-4">
            <section className="tile-shell px-6 py-7 sm:px-7 sm:py-8">
              <DaySelector days={availableTaraweehDays} selectedDay={selectedDay} onDayChange={handleDayChange} />
            </section>

            <section className="tile-shell px-6 py-7 sm:px-7 sm:py-8">
              <RecitersInfo compact />
            </section>
          </aside>
        </section>
      </div>
    </main>
  );
}
