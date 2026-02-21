"use client";

import type { SurahMarker } from "@/components/day/SurahIndex";
import {
  dayCorpusSummaries,
  getValidatedDayHighlights,
  isQuranTextReference,
  isTafsirReference,
  type DayHighlightItem,
} from "@/data/dayHighlights";

type DayHighlightsProps = {
  day: number;
  markers: SurahMarker[];
  selectedPartId?: string | null;
  partMarkers?: Record<string, SurahMarker[]>;
  partLabels?: Record<string, string>;
  onSeek?: (seconds: number) => void;
  onSeekInPart?: (partId: string, seconds: number) => void;
};

type AyahRange = {
  surahNumber: number;
  startAyah: number;
  endAyah: number;
};

function parseAyahRef(ayahRef: string): AyahRange | null {
  const match = ayahRef.trim().match(/^(\d+):(\d+)(?:-(\d+))?$/);
  if (!match) return null;
  const surahNumber = Number.parseInt(match[1], 10);
  const startAyah = Number.parseInt(match[2], 10);
  const endAyah = Number.parseInt(match[3] || match[2], 10);
  if (!Number.isFinite(surahNumber) || !Number.isFinite(startAyah) || !Number.isFinite(endAyah)) {
    return null;
  }
  return {
    surahNumber,
    startAyah: Math.min(startAyah, endAyah),
    endAyah: Math.max(startAyah, endAyah),
  };
}

function findSeekTime(item: DayHighlightItem, markers: SurahMarker[]): number | null {
  const parsed = parseAyahRef(item.ayahRef);
  if (!parsed) return null;

  const candidates = markers
    .filter((marker) => {
      if (marker.surah_number !== parsed.surahNumber) return false;
      return marker.ayah >= parsed.startAyah && marker.ayah <= parsed.endAyah;
    })
    .sort((a, b) => a.time - b.time);

  return candidates[0]?.time ?? null;
}

function findSeekInParts(
  item: DayHighlightItem,
  selectedPartId: string | null | undefined,
  markers: SurahMarker[],
  partMarkers: Record<string, SurahMarker[]> | undefined
): { time: number | null; partId: string | null; location: "current" | "other" | "missing" } {
  const currentSeek = findSeekTime(item, markers);
  if (currentSeek !== null) {
    return { time: currentSeek, partId: selectedPartId ?? null, location: "current" };
  }

  if (!partMarkers) {
    return { time: null, partId: null, location: "missing" };
  }

  const partIds = Object.keys(partMarkers).sort((a, b) => Number(a) - Number(b));
  for (const partId of partIds) {
    if (partId === selectedPartId) {
      continue;
    }
    const seek = findSeekTime(item, partMarkers[partId] || []);
    if (seek !== null) {
      return { time: seek, partId, location: "other" };
    }
  }

  return { time: null, partId: null, location: "missing" };
}

export default function DayHighlights({
  day,
  markers,
  selectedPartId,
  partMarkers,
  partLabels,
  onSeek,
  onSeekInPart,
}: DayHighlightsProps) {
  const items = getValidatedDayHighlights(day);
  const corpusSummary = dayCorpusSummaries[day];
  if (!items.length && !corpusSummary) {
    return null;
  }

  return (
    <section className="tile-shell px-6 py-7 sm:px-7 sm:py-8">
      <div className="space-y-2">
        <span className="inline-flex rounded-full border border-sand/35 bg-sand/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.16em] text-sand">
          AI Beta
        </span>
        <p className="label-caps">Indexed Highlights</p>
        <h3 className="font-[var(--font-heading)] text-2xl leading-tight text-ivory sm:text-3xl">Duas & Famous Ayat</h3>
        <p className="text-sm text-muted">AI-generated guidance aid. Verify details with trusted scholars and primary tafsir sources.</p>
      </div>

      {corpusSummary ? (
        <article className="mt-6 rounded-2xl border border-line/90 bg-charcoalSoft/65 px-4 py-4 sm:px-5">
          <p className="text-xs uppercase tracking-[0.16em] text-sand">{corpusSummary.title}</p>
          <p className="mt-2 text-sm leading-7 text-muted">{corpusSummary.summary}</p>
          <div className="mt-3 space-y-1.5">
            {corpusSummary.themes.map((theme) => (
              <p key={theme} className="text-xs leading-6 text-muted">
                • {theme}
              </p>
            ))}
          </div>
        </article>
      ) : null}

      <div className="mt-6 space-y-3">
        {items.map((item) => {
          const target = findSeekInParts(item, selectedPartId, markers, partMarkers);
          const tafsirReference = item.references.find(isTafsirReference);
          if (!tafsirReference) {
            return null;
          }
          const quranReference = item.references.find(isQuranTextReference);
          const genericReference = item.references.find((reference) => reference !== tafsirReference && reference !== quranReference);
          const openReference = genericReference || quranReference;
          return (
            <details
              key={`${item.ayahRef}-${item.shortTitle}`}
              className="group rounded-2xl border border-line/90 bg-charcoalSoft/65 px-4 py-3 open:border-sand/40 sm:px-5"
            >
              <summary className="cursor-pointer list-none">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.16em] text-sand">{item.themeType}</p>
                    <p className="mt-1 text-sm font-semibold text-ivory sm:text-base">{item.shortTitle}</p>
                    <p className="mt-1 text-xs text-muted">Ayah: {item.ayahRef}</p>
                  </div>
                  <span className="pt-1 text-xs text-muted group-open:text-sand">Open</span>
                </div>
              </summary>

              <div className="mt-4 space-y-3 text-sm text-muted">
                <p className="leading-7">{item.summary}</p>
                <p className="text-sm text-ivory/90">
                  <span className="font-semibold">Key takeaway:</span> {item.keyTakeaway}
                </p>

                <div className="space-y-1">
                  {item.whyNotable.map((point) => (
                    <p key={point} className="text-xs leading-6 text-muted">• {point}</p>
                  ))}
                </div>

                <div className="flex flex-wrap items-center gap-2 pt-1">
                  {target.location === "current" && target.time !== null ? (
                    <button
                      type="button"
                      onClick={() => onSeek?.(target.time as number)}
                      className="rounded-full border border-sand/35 bg-sand/10 px-3.5 py-1.5 text-xs font-semibold text-sand hover:border-sand/60"
                    >
                      Play Ayah
                    </button>
                  ) : null}

                  {target.location === "other" && target.time !== null && target.partId ? (
                    <button
                      type="button"
                      onClick={() => onSeekInPart?.(target.partId as string, target.time as number)}
                      className="rounded-full border border-sand/35 bg-sand/10 px-3.5 py-1.5 text-xs font-semibold text-sand hover:border-sand/60"
                    >
                      Open {(partLabels?.[target.partId] || `Part ${target.partId}`)} & Play
                    </button>
                  ) : (
                    target.location === "missing" ? (
                      <span className="rounded-full border border-line px-3.5 py-1.5 text-xs text-muted">
                        Timestamp not indexed yet
                      </span>
                    ) : null
                  )}

                  {tafsirReference ? (
                    <a
                      href={tafsirReference.url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-full border border-line px-3.5 py-1.5 text-xs text-ivory hover:border-sand/50 hover:text-sand"
                    >
                      Open Tafsir
                    </a>
                  ) : null}

                  {openReference ? (
                    <a
                      href={openReference.url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-full border border-line px-3.5 py-1.5 text-xs text-ivory hover:border-sand/50 hover:text-sand"
                    >
                      Open References
                    </a>
                  ) : null}
                </div>
              </div>
            </details>
          );
        })}
      </div>
    </section>
  );
}
