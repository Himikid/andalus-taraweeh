import Link from "next/link";
import VideoPlayer from "@/components/day/VideoPlayer";

const PLACEHOLDER_VIDEO_ID = "WJGS2B673Zg";

export default function LiveOnPreviewPage() {
  return (
    <main className="app-shell px-5 py-12 sm:px-8 sm:py-16 lg:py-20">
      <div className="mx-auto w-full max-w-6xl">
        <div className="grid gap-6 lg:grid-cols-12">
          <section className="hero-shell px-6 py-12 sm:px-10 sm:py-14 lg:col-span-8">
            <div className="mx-auto flex w-full max-w-3xl flex-col gap-8 text-center">
              <p className="label-caps">Live Preview Only</p>
              <h1 className="font-[var(--font-heading)] text-[2.35rem] leading-[1.04] text-ivory sm:text-[3.1rem]">
                Andalus Taraweeh Is Live
              </h1>
              <p className="mx-auto max-w-xl text-sm leading-7 text-muted sm:text-base">
                This is a private design preview showing the live-state home experience with a placeholder stream.
              </p>

              <div className="mx-auto w-full max-w-2xl rounded-2xl border border-line bg-charcoalLift px-6 py-5">
                <p className="label-caps">Now Streaming</p>
                <p className="mt-2 text-2xl text-ivory sm:text-3xl">Taraweeh – Day 1</p>
                <p className="mt-1 text-sm text-muted">Join live now or continue from the latest indexed timestamp.</p>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-3">
                <Link
                  href="/day/1"
                  className="rounded-full border border-sand/30 bg-green px-6 py-2.5 text-sm font-semibold text-white hover:bg-[#377557]"
                >
                  Open Live Stream
                </Link>
                <Link href="/" className="rounded-full border border-line px-6 py-2.5 text-sm text-ivory hover:border-sand hover:text-sand">
                  Back Home
                </Link>
              </div>
            </div>
          </section>

          <section className="tile-shell px-6 py-7 sm:px-7 sm:py-8 lg:col-span-4">
            <p className="label-caps">Live Session Notes</p>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-muted">
              <li>Placeholder stream uses Day 1 video.</li>
              <li>UI keeps the same tone as the main site.</li>
              <li>No navigation entry is shown for this preview page.</li>
            </ul>
          </section>

          <section className="lg:col-span-12">
            <VideoPlayer videoId={PLACEHOLDER_VIDEO_ID} />
          </section>
        </div>
      </div>
    </main>
  );
}
