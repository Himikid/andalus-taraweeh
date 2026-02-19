"use client";

export type PrayerStart = {
  start: number;
  label: string;
  reciter?: string;
};

type PrayerStartsProps = {
  prayers: PrayerStart[];
  reciterSwitches?: {
    time: number;
    from: string;
    to: string;
    label: string;
  }[];
  title?: string;
  onSeek?: (seconds: number) => void;
};

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export default function PrayerStarts({ prayers, reciterSwitches = [], title = "Rakah Start Timestamps", onSeek }: PrayerStartsProps) {
  if (!prayers.length) {
    return null;
  }

  return (
    <section className="w-full">
      <p className="label-caps">{title}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {prayers.map((prayer) => (
          <button
            key={`${prayer.label}-${prayer.start}`}
            type="button"
            onClick={() => onSeek?.(prayer.start)}
            className="rounded-full border border-line px-3 py-1.5 text-xs text-ivory hover:border-sand hover:text-sand"
          >
            {prayer.label} - {formatTime(prayer.start)}
          </button>
        ))}
      </div>

      {reciterSwitches.length ? (
        <div className="mt-6">
          <p className="label-caps">Reciter Switches</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {reciterSwitches.map((switchPoint) => (
              <button
                key={`${switchPoint.time}-${switchPoint.from}-${switchPoint.to}`}
                type="button"
                onClick={() => onSeek?.(switchPoint.time)}
                className="rounded-full border border-line px-3 py-1.5 text-xs text-ivory hover:border-sand hover:text-sand"
              >
                {formatTime(switchPoint.time)} · {switchPoint.from} to {switchPoint.to}
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
