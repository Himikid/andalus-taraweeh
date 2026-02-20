"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import VideoPlayer from "@/components/day/VideoPlayer";
import LiveStatus from "@/components/home/LiveStatus";

type HomeLiveBlockProps = {
  latestDay: number | null;
  manualVideoId?: string | null;
  manualTitle?: string;
};

type LiveStatusResponse = {
  live?: boolean;
  videoId?: string | null;
  title?: string | null;
};

const POLL_MS = 30000;

export default function HomeLiveBlock({ latestDay, manualVideoId = null, manualTitle = "" }: HomeLiveBlockProps) {
  const [liveVideoId, setLiveVideoId] = useState<string | null>(manualVideoId);
  const [liveTitle, setLiveTitle] = useState<string>(manualTitle);

  useEffect(() => {
    if (manualVideoId) {
      setLiveVideoId(manualVideoId);
      setLiveTitle(manualTitle);
      return;
    }

    let active = true;

    async function pollLiveStatus() {
      try {
        const response = await fetch("/api/live-status", { cache: "no-store" });
        if (!response.ok) {
          if (active) {
            setLiveVideoId(null);
            setLiveTitle("");
          }
          return;
        }

        const payload = (await response.json()) as LiveStatusResponse;
        if (!active) {
          return;
        }
        if (payload.live && payload.videoId) {
          setLiveVideoId(payload.videoId);
          setLiveTitle(payload.title || "");
        } else {
          setLiveVideoId(null);
          setLiveTitle("");
        }
      } catch {
        if (active) {
          setLiveVideoId(null);
          setLiveTitle("");
        }
      }
    }

    void pollLiveStatus();
    const timer = window.setInterval(() => {
      void pollLiveStatus();
    }, POLL_MS);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [manualTitle, manualVideoId]);

  const hasLiveVideo = Boolean(liveVideoId);
  const latestDayHref = useMemo(() => {
    if (!latestDay) return null;
    return `/day/${latestDay}`;
  }, [latestDay]);

  return (
    <>
      <LiveStatus forceLive={hasLiveVideo} />
      {hasLiveVideo ? (
        <div className="space-y-4 pt-1">
          <div className="mx-auto w-full max-w-3xl rounded-2xl border border-sand/35 bg-charcoalLift/90 px-4 py-4 shadow-[0_18px_50px_rgba(0,0,0,0.26)] sm:px-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-sand/45 bg-sand/10 px-3 py-1">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#ff7a7a] opacity-70" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#ff9b9b]" />
                </span>
                <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-ivory">Live</span>
              </div>
              <p className="text-xs text-muted">{manualVideoId ? "Manual live override enabled" : "Auto-updates from YouTube channel"}</p>
            </div>
            {liveTitle ? (
              <p className="mt-3 text-sm text-ivory/95 sm:text-base">{liveTitle}</p>
            ) : null}
          </div>

          <div className="live-player-glow">
            <VideoPlayer videoId={liveVideoId || undefined} />
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link href="#published-days" className="rounded-full border border-line px-6 py-2.5 text-sm text-ivory hover:border-sand hover:text-sand">
              Browse Archive
            </Link>
            {latestDayHref ? (
              <Link
                href={latestDayHref}
                className="rounded-full border border-sand/30 bg-green/80 px-6 py-2.5 text-sm font-semibold text-white hover:bg-green"
              >
                Open Latest Day
              </Link>
            ) : null}
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
          {latestDay ? (
            <Link
              href={`/day/${latestDay}`}
              className="rounded-full border border-sand/30 bg-green px-6 py-2.5 text-sm font-semibold text-white hover:bg-[#377557]"
            >
              Open Latest Livestream
            </Link>
          ) : (
            <span className="rounded-full border border-line px-6 py-2.5 text-sm text-muted">Waiting for first upload</span>
          )}
        </div>
      )}
    </>
  );
}
