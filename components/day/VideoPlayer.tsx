type VideoPlayerProps = {
  videoId?: string;
  startAt?: number;
};

export default function VideoPlayer({ videoId, startAt }: VideoPlayerProps) {
  if (!videoId) {
    return (
      <section className="video-shell px-6 py-14 text-center">
        <p className="mx-auto max-w-xl text-sm leading-7 text-muted sm:text-base">
          No video is configured for this day yet. Add a YouTube ID to publish it.
        </p>
      </section>
    );
  }

  const params = new URLSearchParams({
    rel: "0"
  });

  if (startAt && startAt > 0) {
    params.set("start", String(startAt));
    params.set("autoplay", "1");
  }

  const src = `https://www.youtube.com/embed/${videoId}?${params.toString()}`;

  return (
    <section className="video-shell p-4 sm:p-5">
      <div className="relative aspect-video w-full overflow-hidden rounded-2xl bg-black">
        <iframe
          key={`${videoId}-${startAt ?? 0}`}
          className="absolute inset-0 h-full w-full"
          src={src}
          title="Taraweeh livestream"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          referrerPolicy="strict-origin-when-cross-origin"
          allowFullScreen
        />
      </div>
    </section>
  );
}
