import { getDataFilePathForDay, getVideoPartsForDay, hasMultiplePartsForDay } from "@/data/taraweehVideos";

type RawMarker = {
  surah?: string;
  surah_number?: number;
  ayah?: number;
  juz?: number;
};

export type DaySurahSummary = {
  surahNumber: number;
  surahName: string;
  startAyah: number;
  endAyah: number;
};

export type DayArchiveMeta = {
  day: number;
  markerCount: number;
  streamParts: number;
  juzValues: number[];
  juzLabel: string;
  surahs: DaySurahSummary[];
  surahLabel: string;
  hasIndexedData: boolean;
};

const dayMetaCache = new Map<number, Promise<DayArchiveMeta>>();

function isFinitePositiveInt(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function toFinitePositiveInt(value: unknown): number | null {
  if (isFinitePositiveInt(value)) return Math.floor(value);
  if (typeof value === "string") {
    const parsed = Number.parseInt(value, 10);
    if (Number.isFinite(parsed) && parsed > 0) return parsed;
  }
  return null;
}

function normalizeMarkers(input: unknown): RawMarker[] {
  if (!Array.isArray(input)) return [];
  return input.filter((item): item is RawMarker => typeof item === "object" && item !== null);
}

function formatJuzLabel(values: number[]): string {
  if (!values.length) return "Juz pending";
  if (values.length === 1) return `Juz ${values[0]}`;

  const min = values[0];
  const max = values[values.length - 1];
  const contiguous = values.length === max - min + 1;
  if (contiguous) return `Juz ${min}-${max}`;

  const preview = values.slice(0, 3).join(", ");
  if (values.length > 3) return `Juz ${preview} +${values.length - 3}`;
  return `Juz ${preview}`;
}

function formatSurahLabel(surahs: DaySurahSummary[]): string {
  if (!surahs.length) return "Surah indexing in progress";
  const primary = surahs
    .slice(0, 2)
    .map((item) => item.surahName)
    .join(" · ");
  if (surahs.length <= 2) return primary;
  return `${primary} +${surahs.length - 2}`;
}

async function fetchMarkersFromPath(path: string): Promise<RawMarker[]> {
  try {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) return [];
    const payload = (await response.json()) as { markers?: unknown };
    return normalizeMarkers(payload.markers);
  } catch {
    return [];
  }
}

export async function fetchDayArchiveMeta(day: number): Promise<DayArchiveMeta> {
  const cached = dayMetaCache.get(day);
  if (cached) return cached;

  const pending = (async () => {
    try {
      const parts = getVideoPartsForDay(day);
      const paths = hasMultiplePartsForDay(day)
        ? parts.map((part) => getDataFilePathForDay(day, part.id))
        : [getDataFilePathForDay(day, null)];

      const markerBatches = await Promise.all(paths.map((path) => fetchMarkersFromPath(path)));
      const markers = markerBatches.flat();

      const juzSet = new Set<number>();
      const surahMap = new Map<number, { name: string; startAyah: number; endAyah: number }>();

      for (const marker of markers) {
        const juz = toFinitePositiveInt(marker.juz);
        if (juz !== null) {
          juzSet.add(juz);
        }

        const surahNumber = toFinitePositiveInt(marker.surah_number);
        const ayah = toFinitePositiveInt(marker.ayah);
        if (surahNumber === null || ayah === null) continue;
        const current = surahMap.get(surahNumber);
        const name = typeof marker.surah === "string" && marker.surah.trim() ? marker.surah.trim() : `Surah ${surahNumber}`;

        if (!current) {
          surahMap.set(surahNumber, { name, startAyah: ayah, endAyah: ayah });
        } else {
          current.startAyah = Math.min(current.startAyah, ayah);
          current.endAyah = Math.max(current.endAyah, ayah);
        }
      }

      const juzValues = [...juzSet].sort((a, b) => a - b);
      const surahs: DaySurahSummary[] = [...surahMap.entries()]
        .sort((a, b) => a[0] - b[0])
        .map(([surahNumber, value]) => ({
          surahNumber,
          surahName: value.name,
          startAyah: value.startAyah,
          endAyah: value.endAyah,
        }));

      return {
        day,
        markerCount: markers.length,
        streamParts: Math.max(1, parts.length),
        juzValues,
        juzLabel: formatJuzLabel(juzValues),
        surahs,
        surahLabel: formatSurahLabel(surahs),
        hasIndexedData: markers.length > 0,
      };
    } catch {
      return {
        day,
        markerCount: 0,
        streamParts: Math.max(1, getVideoPartsForDay(day).length),
        juzValues: [],
        juzLabel: "Juz pending",
        surahs: [],
        surahLabel: "Surah indexing in progress",
        hasIndexedData: false,
      };
    }
  })();

  dayMetaCache.set(day, pending);
  return pending;
}
