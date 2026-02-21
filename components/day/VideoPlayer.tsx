"use client";

import { useEffect, useRef } from "react";

type VideoPlayerProps = {
  videoId?: string;
  startAt?: number;
  seekNonce?: number;
  onTimeUpdate?: (seconds: number) => void;
};

type YTPlayer = {
  destroy: () => void;
  seekTo: (seconds: number, allowSeekAhead: boolean) => void;
  playVideo: () => void;
  getCurrentTime: () => number;
  getPlayerState?: () => number;
  isMuted?: () => boolean;
  unMute?: () => void;
};

type YTNamespace = {
  Player: new (
    element: HTMLElement,
    options: {
      videoId: string;
      playerVars?: Record<string, string | number>;
      events?: {
        onReady?: () => void;
        onStateChange?: (event: { data: number }) => void;
      };
    },
  ) => YTPlayer;
};

declare global {
  interface Window {
    YT?: YTNamespace;
    onYouTubeIframeAPIReady?: () => void;
  }
}

let youtubeApiPromise: Promise<YTNamespace> | null = null;

function loadYouTubeApi() {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("YouTube API unavailable during SSR."));
  }

  if (window.YT?.Player) {
    return Promise.resolve(window.YT);
  }

  if (youtubeApiPromise) {
    return youtubeApiPromise;
  }

  youtubeApiPromise = new Promise<YTNamespace>((resolve, reject) => {
    const existingScript = document.querySelector('script[src="https://www.youtube.com/iframe_api"]');

    const onReady = () => {
      if (window.YT?.Player) {
        resolve(window.YT);
      } else {
        reject(new Error("YouTube API loaded but Player is unavailable."));
      }
    };

    window.onYouTubeIframeAPIReady = onReady;

    if (!existingScript) {
      const script = document.createElement("script");
      script.src = "https://www.youtube.com/iframe_api";
      script.async = true;
      script.onerror = () => reject(new Error("Failed to load YouTube API."));
      document.head.appendChild(script);
      return;
    }

    const timer = window.setInterval(() => {
      if (window.YT?.Player) {
        window.clearInterval(timer);
        onReady();
      }
    }, 80);
  });

  return youtubeApiPromise;
}

export default function VideoPlayer({ videoId, startAt, seekNonce, onTimeUpdate }: VideoPlayerProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const playerRef = useRef<YTPlayer | null>(null);
  const tickerRef = useRef<number | null>(null);
  const startAtRef = useRef<number | undefined>(startAt);
  const lastTimeRef = useRef<number>(0);
  const stalledTicksRef = useRef<number>(0);

  useEffect(() => {
    startAtRef.current = startAt;
  }, [startAt]);

  useEffect(() => {
    const mountNode = mountRef.current;
    if (!videoId || !mountNode) {
      return;
    }
    const safeVideoId = videoId;

    let isActive = true;

    async function initPlayer() {
      try {
        const YT = await loadYouTubeApi();
        if (!isActive || !mountNode) return;

        if (playerRef.current) {
          playerRef.current.destroy();
          playerRef.current = null;
        }

        playerRef.current = new YT.Player(mountNode, {
          videoId: safeVideoId,
          playerVars: {
            rel: 0,
            playsinline: 1,
            modestbranding: 1,
            enablejsapi: 1,
            origin: window.location.origin,
            start: startAtRef.current && startAtRef.current > 0 ? startAtRef.current : 0,
          },
          events: {
            onReady: () => {
              if (!playerRef.current) return;
              if (startAtRef.current && startAtRef.current > 0) {
                playerRef.current.seekTo(startAtRef.current, true);
                playerRef.current.playVideo();
              }
            },
            onStateChange: ({ data }) => {
              // Reset stall tracker once playback is moving again.
              if (data === 1) {
                stalledTicksRef.current = 0;
              }
            },
          },
        });

        tickerRef.current = window.setInterval(() => {
          const player = playerRef.current;
          if (!player) return;
          const current = Number(player.getCurrentTime() || 0);
          const state = typeof player.getPlayerState === "function" ? Number(player.getPlayerState()) : 0;

          if (state === 1) {
            const delta = current - lastTimeRef.current;
            if (delta < 0.08 && document.visibilityState === "visible") {
              stalledTicksRef.current += 1;
            } else {
              stalledTicksRef.current = 0;
            }
            if (stalledTicksRef.current >= 5) {
              try {
                if (typeof player.isMuted === "function" && player.isMuted() && typeof player.unMute === "function") {
                  player.unMute();
                }
                player.playVideo();
              } catch {
                // best effort recovery for occasional YouTube stalls
              } finally {
                stalledTicksRef.current = 0;
              }
            }
          } else {
            stalledTicksRef.current = 0;
          }

          lastTimeRef.current = current;
          const time = Math.floor(current);
          onTimeUpdate?.(time);
        }, 1000);
      } catch {
        // leave video area empty if script load fails
      }
    }

    initPlayer();

    return () => {
      isActive = false;
      if (tickerRef.current) {
        window.clearInterval(tickerRef.current);
        tickerRef.current = null;
      }
      if (playerRef.current) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
      mountNode.innerHTML = "";
    };
  }, [videoId, onTimeUpdate]);

  useEffect(() => {
    if (!playerRef.current || !startAt || startAt <= 0) {
      return;
    }
    playerRef.current.seekTo(startAt, true);
    playerRef.current.playVideo();
    onTimeUpdate?.(startAt);
  }, [onTimeUpdate, seekNonce, startAt]);

  if (!videoId) {
    return (
      <section className="video-shell px-6 py-14 text-center">
        <p className="mx-auto max-w-xl text-sm leading-7 text-muted sm:text-base">
          No video is configured for this day yet. Add a YouTube ID to publish it.
        </p>
      </section>
    );
  }

  return (
    <section className="video-shell p-4 sm:p-5">
      <div className="relative aspect-video w-full overflow-hidden rounded-2xl bg-black">
        <div ref={mountRef} className="absolute inset-0 h-full w-full" />
      </div>
    </section>
  );
}
