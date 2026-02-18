export type SurahMarker = {
  time: number;
  surah: string;
  ayah: number;
};

type SurahIndexProps = {
  markers: SurahMarker[];
};

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export default function SurahIndex({ markers }: SurahIndexProps) {
  if (!markers.length) {
    return null;
  }

  return (
    <section className="w-full rounded-xl border border-white/10 bg-panel/80 p-5">
      <h2 className="mb-4 text-lg font-medium text-white">Indexed Surahs</h2>
      <ul className="space-y-3">
        {markers.map((marker, index) => (
          <li key={`${marker.surah}-${marker.ayah}-${index}`} className="flex items-center justify-between gap-4 rounded-md border border-white/10 bg-charcoal/70 px-4 py-3 text-sm">
            <span className="text-emerald-100/90">
              {marker.surah} - Ayah {marker.ayah}
            </span>
            <span className="font-mono text-emerald-200/70">{formatTime(marker.time)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
