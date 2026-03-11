import Header from "@/components/home/Header";
import HomeLiveBlock from "@/components/home/HomeLiveBlock";
import PublishedDays from "@/components/home/PublishedDays";
import QuranInsights from "@/components/home/QuranInsights";
import RecitersInfo from "@/components/shared/RecitersInfo";
import { manualLiveTitle, manualLiveVideoId } from "@/data/liveOverride";
import { availableTaraweehDays } from "@/data/taraweehVideos";

export default function HomePage() {
  const orderedDays = [...availableTaraweehDays].sort((a, b) => b - a);
  const latestDay = orderedDays[0] ?? null;
  const recentDays = orderedDays.slice(0, 5);

  return (
    <main className="app-shell px-5 py-12 sm:px-8 sm:py-16 lg:py-20">
      <div className="mx-auto w-full max-w-6xl">
        <div className="grid gap-5 sm:gap-6 lg:grid-cols-12 lg:items-start">
          <section className="hero-shell px-6 py-14 sm:px-10 sm:py-16 lg:col-span-8">
            <div className="mx-auto flex w-full max-w-3xl flex-col gap-12">
              <Header />

              <HomeLiveBlock latestDay={latestDay} manualVideoId={manualLiveVideoId} manualTitle={manualLiveTitle} />
            </div>
          </section>

          <QuranInsights className="lg:col-span-4" />

          <section id="published-days" className="tile-shell px-6 py-8 sm:px-8 sm:py-9 lg:col-span-8">
            <div className="space-y-3">
              <p className="label-caps">Archive</p>
              <h2 className="font-[var(--font-heading)] text-3xl leading-[1.05] text-ivory sm:text-4xl">Published Days</h2>
            </div>

            <PublishedDays days={recentDays} />
          </section>

          <section className="tile-shell px-6 py-8 sm:px-8 sm:py-9 lg:col-span-4">
            <RecitersInfo />
          </section>
        </div>
      </div>
    </main>
  );
}
