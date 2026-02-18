"use client";

import { useEffect, useState } from "react";
import DaySelector from "@/components/DaySelector";
import Header from "@/components/Header";
import SurahIndex, { type SurahMarker } from "@/components/SurahIndex";
import VideoPlayer from "@/components/VideoPlayer";
import { taraweehVideos } from "@/data/taraweehVideos";

type DayData = {
  markers?: SurahMarker[];
};

export default function HomePage() {
  const [selectedDay, setSelectedDay] = useState(1);
  const [markers, setMarkers] = useState<SurahMarker[]>([]);
  const [manualVideoId, setManualVideoId] = useState("");
  const selectedDayVideo = taraweehVideos[selectedDay];
  const effectiveVideoId = manualVideoId || selectedDayVideo;

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const videoId = params.get("video")?.trim() ?? "";
    setManualVideoId(videoId);
  }, []);

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

  return (
    <main className="min-h-screen bg-charcoal px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-5xl flex-col items-center gap-6">
        <Header />

        <DaySelector selectedDay={selectedDay} onDayChange={setSelectedDay} />

        <VideoPlayer videoId={effectiveVideoId} />

        <SurahIndex markers={markers} />
      </div>
    </main>
  );
}
