import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const DEFAULT_CHANNEL_HANDLE = "AndalusGlasgow";
const DEFAULT_CHANNEL_ID = "UCCOx4Ju1abMFKUGKYBo5dJw";

type YouTubeChannelListResponse = {
  items?: Array<{ id?: string }>;
};

type YouTubeSearchListResponse = {
  items?: Array<{
    id?: {
      videoId?: string;
      channelId?: string;
    };
    snippet?: {
      title?: string;
      liveBroadcastContent?: string;
      publishedAt?: string;
    };
  }>;
};

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`YouTube API ${response.status}: ${body}`);
  }
  return (await response.json()) as T;
}

async function resolveChannelId(apiKey: string): Promise<string> {
  const explicitChannelId = process.env.YOUTUBE_CHANNEL_ID?.trim();
  if (explicitChannelId) {
    return explicitChannelId;
  }

  const handle = (process.env.YOUTUBE_CHANNEL_HANDLE || DEFAULT_CHANNEL_HANDLE).replace(/^@/, "");
  const channelsUrl =
    `https://www.googleapis.com/youtube/v3/channels?part=id&forHandle=${encodeURIComponent(handle)}&key=${encodeURIComponent(apiKey)}`;

  const byHandle = await fetchJson<YouTubeChannelListResponse>(channelsUrl);
  const handleChannelId = byHandle.items?.[0]?.id?.trim();
  if (handleChannelId) {
    return handleChannelId;
  }

  return DEFAULT_CHANNEL_ID;
}

async function getLiveStreamForChannel(apiKey: string, channelId: string) {
  const liveSearchUrl =
    `https://www.googleapis.com/youtube/v3/search?part=id,snippet&channelId=${encodeURIComponent(channelId)}&eventType=live&type=video&order=date&maxResults=5&key=${encodeURIComponent(apiKey)}`;
  const payload = await fetchJson<YouTubeSearchListResponse>(liveSearchUrl);
  const liveItems =
    payload.items
      ?.filter((item) => item.id?.videoId && item.snippet?.liveBroadcastContent === "live")
      .sort((a, b) => {
        const at = Date.parse(a.snippet?.publishedAt || "");
        const bt = Date.parse(b.snippet?.publishedAt || "");
        return Number.isFinite(bt) && Number.isFinite(at) ? bt - at : 0;
      }) || [];

  const item = liveItems[0];
  if (!item?.id?.videoId) {
    return null;
  }

  return {
    videoId: item.id.videoId,
    title: item.snippet?.title || "",
  };
}

export async function GET() {
  const apiKey = process.env.Youtube_API_key?.trim();
  if (!apiKey) {
    return NextResponse.json(
      {
        live: false,
        reason: "missing_api_key",
        checkedAt: new Date().toISOString(),
      },
      { status: 500, headers: { "Cache-Control": "no-store" } }
    );
  }

  try {
    const channelId = await resolveChannelId(apiKey);
    const live = await getLiveStreamForChannel(apiKey, channelId);
    return NextResponse.json(
      {
        live: Boolean(live),
        channelId,
        videoId: live?.videoId || null,
        title: live?.title || null,
        checkedAt: new Date().toISOString(),
      },
      { headers: { "Cache-Control": "no-store" } }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown_error";
    return NextResponse.json(
      {
        live: false,
        reason: "youtube_api_error",
        message,
        checkedAt: new Date().toISOString(),
      },
      { status: 502, headers: { "Cache-Control": "no-store" } }
    );
  }
}
