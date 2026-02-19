"use client";

import { useEffect, useState } from "react";

const LIVESTREAM_START_HOUR = 20;
const LIVESTREAM_END_HOUR = 21;
const LIVESTREAM_END_MINUTE = 30;
const GLASGOW_TIMEZONE = "Europe/London";

function getLondonNow() {
  return new Date(new Date().toLocaleString("en-US", { timeZone: GLASGOW_TIMEZONE }));
}

function formatCountdown(totalMs: number) {
  const clamped = Math.max(0, totalMs);
  const totalSeconds = Math.floor(clamped / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return [hours, minutes, seconds].map((value) => value.toString().padStart(2, "0")).join(":");
}

export default function LiveStatus() {
  const [, setTick] = useState(Date.now());

  useEffect(() => {
    const interval = window.setInterval(() => setTick(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, []);

  const londonNow = getLondonNow();

  const liveStart = new Date(londonNow);
  liveStart.setHours(LIVESTREAM_START_HOUR, 0, 0, 0);

  const liveEnd = new Date(londonNow);
  liveEnd.setHours(LIVESTREAM_END_HOUR, LIVESTREAM_END_MINUTE, 0, 0);

  const isLive = londonNow >= liveStart && londonNow < liveEnd;

  const countdown = (() => {
    const nextStart = new Date(liveStart);
    if (londonNow >= nextStart) {
      nextStart.setDate(nextStart.getDate() + 1);
    }
    return formatCountdown(nextStart.getTime() - londonNow.getTime());
  })();

  return (
    <div className="space-y-4 text-center">
      <p className="label-caps">Isha Salat 7:45pm</p>

      {isLive ? (
        <>
          <p className="font-[var(--font-heading)] text-4xl leading-none text-ivory sm:text-5xl">Live Now</p>
          <p className="text-sm text-muted">Now streaming from Andalus Centre Glasgow.</p>
        </>
      ) : (
        <>
          <p className="font-[var(--font-heading)] text-5xl leading-none text-ivory sm:text-6xl">8:00pm</p>
          <p className="label-caps !tracking-[0.18em]">Taraweeh Livestream Starts</p>
          <p className="text-sm text-muted">Beginning after Isha prayer.</p>
          <p className="font-mono text-base text-muted">{countdown}</p>
        </>
      )}
    </div>
  );
}
