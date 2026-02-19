# andalus-taraweeh

A production-ready Ramadan livestream site for **Andalus Centre Glasgow** built with Next.js 14, TypeScript, and TailwindCSS.

## Local development

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Production preview

```bash
npm run build
npm run start
```

## Deploy to Vercel

1. Push this repository to GitHub.
2. Import the repo in Vercel.
3. Keep default Next.js settings.
4. Deploy.

## Update YouTube IDs

Edit:

- `data/taraweehVideos.ts`

Set day keys (`1` to `30`) to real YouTube video IDs.

## Manual URL override

Use:

- `?video=VIDEO_ID`

Example:

- `http://localhost:3000/day/1?video=dQw4w9WgXcQ`

## Surah index JSON hook

Place day JSON files in:

- `public/data/day-{N}.json`

Example:

- `public/data/day-1.json`

If day data exists, the site shows grouped surah markers. If not, the section stays hidden.

Generated day JSON now includes:

- `markers` with `surah`, `ayah`, `juz`, `time`, `reciter`, `confidence`
- `rakaat` start timestamps
- `reciter_switches` timestamps

The day page uses these for:

- clickable rakah jump points
- reciter switch jump points
- ayah/surah timestamp navigation

## AI local processing layer

A local Python pipeline is included for daily audio processing and JSON generation.

- Docs: `scripts/README.md`
- Main command: `python scripts/process_day.py ...`
- Quran corpus fetch: `python scripts/fetch_quran_corpus.py`

The Python code is local-only and does not affect Vercel runtime.

## Home insights

The home page includes a Quran insights panel that is computed from indexed day JSON files:

- latest detected Quran position (`surah`, `ayah`, `juz`, timestamp)
- estimated progress indicator (by Juz)
- surah-based navigation across published days
- AI disclaimer (best-effort indexing accuracy)

## Project structure

- `app/`
  - `page.tsx` home page
  - `day/[day]/page.tsx` day route
  - `layout.tsx` app layout + metadata
  - `globals.css` theme and shared styles
- `components/home/`
  - `Header.tsx`
  - `LiveStatus.tsx`
  - `QuranInsights.tsx`
- `components/day/`
  - `DayPageClient.tsx`
  - `DaySelector.tsx`
  - `PrayerStarts.tsx`
  - `VideoPlayer.tsx`
  - `SurahIndex.tsx`
- `components/shared/`
  - `RecitersInfo.tsx`
- `data/`
  - `taraweehVideos.ts`
  - `ramadan.ts`
- `scripts/`
  - `process_day.py`
  - `fetch_quran_corpus.py`
  - `ai_pipeline/*`
- `public/data/`
  - generated day marker JSON files
