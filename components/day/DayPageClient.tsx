"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import DaySelector from "@/components/day/DaySelector";
import DayHighlights from "@/components/day/DayHighlights";
import NowReciting from "@/components/day/NowReciting";
import SurahIndex, { type SurahMarker } from "@/components/day/SurahIndex";
import VideoPlayer from "@/components/day/VideoPlayer";
import { getDateForRamadanDay } from "@/data/ramadan";
import {
  availableTaraweehDays,
  getDataFilePathForDay,
  getDefaultPartIdForDay,
  getVideoIdForDay,
  getVideoPartsForDay,
  hasMultiplePartsForDay,
} from "@/data/taraweehVideos";

type DayData = {
  markers?: SurahMarker[];
};

type DayPageClientProps = {
  initialDay: number;
};

function smoothReciterLabels(markers: SurahMarker[]): SurahMarker[] {
  if (!markers.length) {
    return markers;
  }

  const timeline = markers
    .slice()
    .sort((a, b) => a.time - b.time)
    .map((marker) => ({ ...marker }));

  const isSheikh = (reciter?: string) => reciter === "Hasan" || reciter === "Samir";

  const nextSheikh: Array<string | undefined> = new Array(timeline.length).fill(undefined);
  let next: string | undefined;
  for (let i = timeline.length - 1; i >= 0; i -= 1) {
    if (isSheikh(timeline[i].reciter)) {
      next = timeline[i].reciter;
    }
    nextSheikh[i] = next;
  }

  let previousSheikh: string | undefined;
  for (let i = 0; i < timeline.length; i += 1) {
    const marker = timeline[i];
    if (isSheikh(marker.reciter)) {
      previousSheikh = marker.reciter;
      continue;
    }
    if (marker.reciter === "Talk") {
      marker.reciter = previousSheikh || nextSheikh[i] || "Unknown";
    }
  }

  return timeline;
}

export default function DayPageClient({ initialDay }: DayPageClientProps) {
  const router = useRouter();

  const fallbackDay = availableTaraweehDays[0] ?? 1;
  const safeInitialDay = availableTaraweehDays.includes(initialDay) ? initialDay : fallbackDay;

  const [selectedDay, setSelectedDay] = useState(safeInitialDay);
  const [markers, setMarkers] = useState<SurahMarker[]>([]);
  const [partMarkers, setPartMarkers] = useState<Record<string, SurahMarker[]>>({});
  const [manualVideoId, setManualVideoId] = useState("");
  const [selectedPartId, setSelectedPartId] = useState<string | null>(getDefaultPartIdForDay(safeInitialDay));
  const [seekTime, setSeekTime] = useState<number | undefined>(undefined);
  const [seekNonce, setSeekNonce] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const hasInitializedSeekReset = useRef(false);
  const skipNextSeekReset = useRef(false);

  const dayParts = getVideoPartsForDay(selectedDay);
  const dayVideoId = getVideoIdForDay(selectedDay, selectedPartId);
  const effectiveVideoId = manualVideoId || dayVideoId;

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const videoId = params.get("video")?.trim() ?? "";
    const partId = params.get("part")?.trim() ?? "";
    const seekParam = params.get("t");
    const parsedSeek = seekParam ? Number.parseInt(seekParam, 10) : NaN;
    setManualVideoId(videoId);
    if (partId) {
      setSelectedPartId(partId);
    }
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
    const defaultPart = getDefaultPartIdForDay(selectedDay);
    if (!selectedPartId || !dayParts.some((part) => part.id === selectedPartId)) {
      setSelectedPartId(defaultPart);
    }
  }, [dayParts, selectedDay, selectedPartId]);

  useEffect(() => {
    if (!hasInitializedSeekReset.current) {
      hasInitializedSeekReset.current = true;
      return;
    }
    if (skipNextSeekReset.current) {
      skipNextSeekReset.current = false;
      return;
    }
    setSeekTime(undefined);
  }, [selectedDay, selectedPartId, effectiveVideoId]);

  useEffect(() => {
    let isMounted = true;

    async function loadIndex() {
      try {
        const primaryPath = getDataFilePathForDay(selectedDay, selectedPartId);
        const fallbackPath = `/data/day-${selectedDay}.json`;
        const candidates = primaryPath === fallbackPath ? [primaryPath] : [primaryPath, fallbackPath];

        for (const path of candidates) {
          const response = await fetch(path, { cache: "no-store" });
          if (!response.ok) {
            continue;
          }
          const data = (await response.json()) as DayData;
          if (isMounted) {
            setMarkers(Array.isArray(data.markers) ? smoothReciterLabels(data.markers) : []);
          }
          return;
        }

        if (isMounted) {
          setMarkers([]);
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
  }, [selectedDay, selectedPartId]);

  useEffect(() => {
    let isMounted = true;

    async function loadPartMarkers() {
      const parts = getVideoPartsForDay(selectedDay);
      if (!parts.length) {
        if (isMounted) {
          setPartMarkers({});
        }
        return;
      }

      const nextMap: Record<string, SurahMarker[]> = {};
      for (const part of parts) {
        try {
          const response = await fetch(getDataFilePathForDay(selectedDay, part.id), { cache: "no-store" });
          if (!response.ok) {
            continue;
          }
          const data = (await response.json()) as DayData;
          nextMap[part.id] = Array.isArray(data.markers) ? smoothReciterLabels(data.markers) : [];
        } catch {
          // ignore missing or malformed part JSON
        }
      }

      if (isMounted) {
        setPartMarkers(nextMap);
      }
    }

    void loadPartMarkers();

    return () => {
      isMounted = false;
    };
  }, [selectedDay]);

  function handleDayChange(day: number) {
    const params = new URLSearchParams(window.location.search);
    const defaultPart = getDefaultPartIdForDay(day);
    if (defaultPart) {
      params.set("part", defaultPart);
    } else {
      params.delete("part");
    }
    params.delete("t");
    const query = params.toString();
    const pathname = `/day/${day}`;
    router.push(query ? `${pathname}?${query}` : pathname);
    setSelectedDay(day);
    setSelectedPartId(defaultPart);
  }

  function handlePartChange(partId: string) {
    handlePartChangeWithSeek(partId);
  }

  function handlePartChangeWithSeek(partId: string, seconds?: number) {
    const params = new URLSearchParams(window.location.search);
    params.set("part", partId);
    if (typeof seconds === "number" && Number.isFinite(seconds)) {
      params.set("t", String(Math.max(0, Math.floor(seconds))));
    } else {
      params.delete("t");
    }
    const query = params.toString();
    const pathname = `/day/${selectedDay}`;
    router.push(query ? `${pathname}?${query}` : pathname);
    if (typeof seconds === "number" && Number.isFinite(seconds)) {
      skipNextSeekReset.current = true;
      setSeekTime(seconds);
      setSeekNonce((value) => value + 1);
    }
    setSelectedPartId(partId);
  }

  function handleSeek(seconds: number) {
    setSeekTime(seconds);
    setSeekNonce((value) => value + 1);
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
            <VideoPlayer videoId={effectiveVideoId} startAt={seekTime} seekNonce={seekNonce} onTimeUpdate={setCurrentTime} />
            <section className="tile-shell px-6 py-7 sm:px-7 sm:py-8">
              {hasMultiplePartsForDay(selectedDay) ? (
                <div className="mb-5">
                  <p className="label-caps">Choose Stream Part</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {dayParts.map((part) => {
                      const isActive = selectedPartId === part.id;
                      return (
                        <button
                          key={part.id}
                          type="button"
                          onClick={() => handlePartChange(part.id)}
                          className={`rounded-full border px-3.5 py-1.5 text-xs ${
                            isActive
                              ? "border-sand bg-sand/10 text-sand"
                              : "border-line text-muted hover:border-sand/40 hover:text-ivory"
                          }`}
                        >
                          {part.label || `Part ${part.id}`}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : null}
              <NowReciting markers={markers} currentTime={currentTime} />
            </section>
            <section className="tile-shell px-6 py-7 sm:px-7 sm:py-8">
              <SurahIndex markers={markers} onSeek={handleSeek} />
            </section>
            <DayHighlights
              day={selectedDay}
              markers={markers}
              selectedPartId={selectedPartId}
              partMarkers={partMarkers}
              partLabels={Object.fromEntries(dayParts.map((part) => [part.id, part.label || `Part ${part.id}`]))}
              onSeek={handleSeek}
              onSeekInPart={handlePartChangeWithSeek}
            />
          </div>

          <aside className="space-y-6 lg:col-span-4">
            <section className="tile-shell px-6 py-7 sm:px-7 sm:py-8">
              <DaySelector days={availableTaraweehDays} selectedDay={selectedDay} onDayChange={handleDayChange} />
            </section>
          </aside>
        </section>
      </div>
    </main>
  );
}
