import Link from "next/link";
import Header from "@/components/home/Header";
import LiveStatus from "@/components/home/LiveStatus";
import RecitersInfo from "@/components/shared/RecitersInfo";
import { getCurrentRamadanDay, getDateForRamadanDay } from "@/data/ramadan";
import { availableTaraweehDays } from "@/data/taraweehVideos";

export default function HomePage() {
  const currentDay = getCurrentRamadanDay();
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
                  <Link href={`/day/${latestDay}`} className="rounded-full bg-[#4ca77b] px-6 py-2.5 text-sm font-semibold text-white">
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

          <section className="tile-shell flex flex-col justify-between px-6 py-7 sm:px-7 sm:py-8 lg:col-span-4">
            <div className="space-y-4">
              <p className="label-caps">Quran Reflection</p>
              <p className="arabic-basmala text-2xl leading-relaxed text-ivory sm:text-[2rem]">
                ٱللَّهُ نَزَّلَ أَحْسَنَ ٱلْحَدِيثِ
              </p>
              <p className="text-sm leading-7 text-muted">
                “God bestows from on high the best of all teachings in the shape of a divine writ fully consistent within itself.”
              </p>
              <p className="text-xs text-muted">Qur&apos;an 39:23 — Muhammad Asad</p>

              <div className="border-t border-line pt-4">
                <p className="arabic-basmala text-xl leading-relaxed text-ivory sm:text-[1.65rem]">
                  فَاقْرَءُوا مَا تَيَسَّرَ مِنَ ٱلْقُرْءَانِ
                </p>
                <p className="mt-2 text-sm leading-7 text-muted">
                  “Read, then, as much of the Qur&apos;an as may be easy for you.”
                </p>
                <p className="text-xs text-muted">Qur&apos;an 73:20 — Muhammad Asad</p>
              </div>
            </div>

            <p className="mt-8 text-sm leading-7 text-muted">Today is Ramadan Day {currentDay ?? "-"}.</p>
          </section>

          <section id="published-days" className="tile-shell px-6 py-8 sm:px-8 sm:py-9 lg:col-span-7">
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
                      </div>
                      <span className="text-sm text-green">Open</span>
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

          <section className="tile-shell px-6 py-8 sm:px-8 sm:py-9 lg:col-span-5">
            <RecitersInfo />
          </section>
        </div>
      </div>
    </main>
  );
}
