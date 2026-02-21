export type TaraweehDayPart = {
  id: string;
  videoId: string;
  label?: string;
  dataFile?: string;
};

type TaraweehDayConfig = string | TaraweehDayPart[];

export const taraweehVideos: Record<number, TaraweehDayConfig> = {
  1: "WJGS2B673Zg",
  2: [
    { id: "1", label: "Part 1", videoId: "NiX9yY-MQZA" },
    { id: "2", label: "Part 2", videoId: "SmzUUfP6fEc" },
  ],
  3: "Mi-NZobDLmA",
  4: "",
  5: "",
  6: "",
  7: "",
  8: "",
  9: "",
  10: "",
  11: "",
  12: "",
  13: "",
  14: "",
  15: "",
  16: "",
  17: "",
  18: "",
  19: "",
  20: "",
  21: "",
  22: "",
  23: "",
  24: "",
  25: "",
  26: "",
  27: "",
  28: "",
  29: "",
  30: "",
};

function isConfiguredVideoId(videoId: string) {
  return Boolean(videoId) && !videoId.startsWith("YOUTUBE_VIDEO_ID_");
}

function normalizeParts(day: number): TaraweehDayPart[] {
  const config = taraweehVideos[day];
  if (!config) {
    return [];
  }

  if (typeof config === "string") {
    return isConfiguredVideoId(config)
      ? [{ id: "1", label: "Main", videoId: config }]
      : [];
  }

  return config
    .map((part, index) => ({
      id: String(part.id || index + 1),
      label: part.label || `Part ${index + 1}`,
      videoId: part.videoId || "",
      dataFile: part.dataFile,
    }))
    .filter((part) => isConfiguredVideoId(part.videoId));
}

export const availableTaraweehDays = Object.keys(taraweehVideos)
  .map((day) => Number(day))
  .filter((day) => normalizeParts(day).length > 0)
  .sort((a, b) => a - b);

export function getVideoPartsForDay(day: number): TaraweehDayPart[] {
  return normalizeParts(day);
}

export function hasMultiplePartsForDay(day: number) {
  return normalizeParts(day).length > 1;
}

export function getDefaultPartIdForDay(day: number): string | null {
  const parts = normalizeParts(day);
  return parts[0]?.id ?? null;
}

export function getVideoIdForDay(day: number, partId?: string | null) {
  const parts = normalizeParts(day);
  if (!parts.length) {
    return "";
  }

  if (!partId) {
    return parts[0].videoId;
  }

  return parts.find((part) => part.id === partId)?.videoId ?? "";
}

export function getDataFilePathForDay(day: number, partId?: string | null) {
  const parts = normalizeParts(day);
  if (!parts.length) {
    return `/data/day-${day}.json`;
  }

  if (!partId || parts.length === 1) {
    return `/data/day-${day}.json`;
  }

  const part = parts.find((item) => item.id === partId);
  if (!part) {
    return `/data/day-${day}.json`;
  }
  if (part.dataFile?.trim()) {
    const normalized = part.dataFile.startsWith("/") ? part.dataFile : `/data/${part.dataFile}`;
    return normalized;
  }
  return `/data/day-${day}-part-${part.id}.json`;
}
