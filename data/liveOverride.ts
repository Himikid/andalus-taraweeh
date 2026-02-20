const MANUAL_LIVE_URL = "";

function extractYouTubeVideoId(input: string): string | null {
  const trimmed = input.trim();
  if (!trimmed) return null;

  if (/^[A-Za-z0-9_-]{11}$/.test(trimmed)) {
    return trimmed;
  }

  try {
    const url = new URL(trimmed);
    const host = url.hostname.replace(/^www\./, "");
    if (host === "youtu.be") {
      const pathId = url.pathname.replace("/", "").trim();
      return /^[A-Za-z0-9_-]{11}$/.test(pathId) ? pathId : null;
    }
    if (host.endsWith("youtube.com")) {
      const v = url.searchParams.get("v")?.trim() || "";
      return /^[A-Za-z0-9_-]{11}$/.test(v) ? v : null;
    }
  } catch {
    return null;
  }

  return null;
}

export const manualLiveVideoId = extractYouTubeVideoId(MANUAL_LIVE_URL);
export const manualLiveTitle = manualLiveVideoId ? "Manual Live Override" : "";
