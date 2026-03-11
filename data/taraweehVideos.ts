export type TaraweehDayPart = {
  id: string;
  videoId: string;
  label?: string;
  dataFile?: string;
};

type TaraweehDayConfig = string | TaraweehDayPart[];

export const taraweehVideos: Record<number, TaraweehDayConfig> = {
  1: [{ id: "1", label: "Main", videoId: "WJGS2B673Zg", dataFile: "day-1-v2.json" }],
  2: [
    { id: "1", label: "Part 1", videoId: "NiX9yY-MQZA" },
    { id: "2", label: "Part 2", videoId: "SmzUUfP6fEc" },
  ],
  3: "Mi-NZobDLmA",
  4: "QxnylahNG_U",
  5: "spsbGlCUzA8",
  6: "y5wPrvVE7Hk",
  7: "jsueko6chpY",
  8: "7oBXnmyN4QY",
  9: "eB8kFf1pHK4",
  10: "iuBHEwqjN2s",
  11: "CPlqoaW1wEI",
  12: "-A-Q-bpob-U",
  13: "7-ReoGsMAQ4",
  14: "ouP177I4-rw",
  15: "aJKRHigADcM",
  16: [
    { id: "1", label: "Part 1", videoId: "0hfVGkWiofY" },
    { id: "2", label: "Part 2", videoId: "L7UEM2RM-SY" },
  ],
  17: "8J4moM97CmQ",
  18: "veZ0C8mDPBM",
  19: "ahaVOumf0VY",
  20: "LCfjDuedxOE",
  21: "tdSBLDI3-XQ",
  22: "CKVzy5ecWWc",
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

  if (!partId) {
    const first = parts[0];
    if (first?.dataFile?.trim()) {
      return first.dataFile.startsWith("/") ? first.dataFile : `/data/${first.dataFile}`;
    }
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
