type VideoPlayerProps = {
  videoId?: string;
};

export default function VideoPlayer({ videoId }: VideoPlayerProps) {
  if (!videoId) {
    return (
      <div className="w-full overflow-hidden rounded-xl border border-white/10 bg-panel">
        <div className="flex aspect-video items-center justify-center px-6 text-center text-sm text-emerald-100/70 sm:text-base">
          No livestream selected yet. Add a YouTube ID in the local Taraweeh config.
        </div>
      </div>
    );
  }

  return (
    <div className="w-full overflow-hidden rounded-xl border border-white/10 bg-panel shadow-lg shadow-black/30">
      <div className="relative aspect-video w-full">
        <iframe
          className="absolute inset-0 h-full w-full"
          src={`https://www.youtube.com/embed/${videoId}`}
          title="Taraweeh livestream"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          referrerPolicy="strict-origin-when-cross-origin"
          allowFullScreen
        />
      </div>
    </div>
  );
}
