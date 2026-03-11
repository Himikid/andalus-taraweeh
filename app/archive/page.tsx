import Link from "next/link";
import ArchiveGrid from "@/components/archive/ArchiveGrid";
import { availableTaraweehDays } from "@/data/taraweehVideos";

export default function ArchivePage() {
  const days = [...availableTaraweehDays].sort((a, b) => b - a);

  return (
    <main className="app-shell px-5 py-12 sm:px-8 sm:py-16">
      <div className="mx-auto w-full max-w-6xl space-y-6">
        <header className="tile-shell px-6 py-8 sm:px-8 sm:py-9">
          <p className="label-caps">Archive</p>
          <h1 className="mt-3 font-[var(--font-heading)] text-3xl leading-[1.05] text-ivory sm:text-4xl">Full Taraweeh Archive</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-muted">
            Browse every published day with a quick breakdown of indexed Juz and Surah coverage.
          </p>
          <div className="mt-5">
            <Link href="/" className="inline-flex items-center rounded-full border border-line px-5 py-2 text-sm text-ivory hover:border-sand hover:text-sand">
              Back Home
            </Link>
          </div>
        </header>

        <ArchiveGrid days={days} />
      </div>
    </main>
  );
}
