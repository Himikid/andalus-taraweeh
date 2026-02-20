import Link from "next/link";
import Header from "@/components/home/Header";
import LiveStatus from "@/components/home/LiveStatus";
import QuranInsights from "@/components/home/QuranInsights";
import RecitersInfo from "@/components/shared/RecitersInfo";
import { getDateForRamadanDay } from "@/data/ramadan";
import { availableTaraweehDays, getVideoPartsForDay } from "@/data/taraweehVideos";

export default function HomePage() {
  const latestDay = availableTaraweehDays.at(-1) ?? null;

  return (
    <main className="app-shell px-5 py-12 sm:px-8 sm:py-16 lg:py-20">
      <div className="mx-auto w-full max-w-6xl">
        <div className="grid gap-5 sm:gap-6 lg:grid-cols-12">
          <section className="hero-shell px-6 py-14 sm:px-10 sm:py-16 lg:col-span-8">
            <div className="mx-auto flex w-full max-w-3xl flex-col gap-12">
              <Header />

              <LiveStatus />

              <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
                {latestDay ? (
                  <Link
                    href={`/day/${latestDay}`}
                    className="rounded-full border border-sand/30 bg-green px-6 py-2.5 text-sm font-semibold text-white hover:bg-[#377557]"
                  >
                    Open Latest Livestream
                  </Link>
                ) : (
                  <span className="rounded-full border border-line px-6 py-2.5 text-sm text-muted">
                    Waiting for first upload
                  </span>
                )}
              </div>
            </div>
          </section>

          <QuranInsights className="lg:col-span-4" />

          <section id="published-days" className="tile-shell px-6 py-8 sm:px-8 sm:py-9 lg:col-span-8">
            <div className="space-y-3">
              <p className="label-caps">Archive</p>
              <h2 className="font-[var(--font-heading)] text-3xl leading-[1.05] text-ivory sm:text-4xl">Published Days</h2>
            </div>

            {availableTaraweehDays.length ? (
              <ul className="mt-7 divide-y divide-line border-y border-line">
                {availableTaraweehDays.map((day) => (
                  <li key={day}>
                    <Link href={`/day/${day}`} className="flex items-center justify-between gap-4 py-4">
                      <div>
                        <p className="text-sm font-medium text-ivory sm:text-base">Ramadan Day {day}</p>
                        <p className="mt-1 text-sm text-muted">{getDateForRamadanDay(day)}</p>
                        {getVideoPartsForDay(day).length > 1 ? (
                          <p className="mt-1 text-xs text-sand">{getVideoPartsForDay(day).length} stream parts</p>
                        ) : null}
                      </div>
                      <span className="text-sm text-sand">Open</span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-7 text-sm text-muted">
                No livestream days are published yet. Add YouTube IDs in <span className="text-ivory">data/taraweehVideos.ts</span>.
              </p>
            )}
          </section>

          <section className="tile-shell px-6 py-8 sm:px-8 sm:py-9 lg:col-span-4">
            <RecitersInfo />
          </section>
        </div>
      </div>
    </main>
  );
}
