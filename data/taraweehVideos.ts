export const taraweehVideos: Record<number, string> = {
  1: "WJGS2B673Zg",
  2: "YOUTUBE_VIDEO_ID_2",
  3: "YOUTUBE_VIDEO_ID_3",
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
  30: ""
};

function isConfiguredVideoId(videoId: string) {
  return Boolean(videoId) && !videoId.startsWith("YOUTUBE_VIDEO_ID_");
}

export const availableTaraweehDays = Object.entries(taraweehVideos)
  .filter(([, videoId]) => isConfiguredVideoId(videoId))
  .map(([day]) => Number(day))
  .sort((a, b) => a - b);

export function getVideoIdForDay(day: number) {
  const videoId = taraweehVideos[day] ?? "";
  return isConfiguredVideoId(videoId) ? videoId : "";
}
