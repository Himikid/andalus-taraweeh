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

## Project structure

- `app/`
  - `page.tsx` home page
  - `day/[day]/page.tsx` day route
  - `layout.tsx` app layout + metadata
  - `globals.css` theme and shared styles
- `components/home/`
  - `Header.tsx`
  - `LiveStatus.tsx`
- `components/day/`
  - `DayPageClient.tsx`
  - `DaySelector.tsx`
  - `VideoPlayer.tsx`
  - `SurahIndex.tsx`
- `components/shared/`
  - `RecitersInfo.tsx`
- `data/`
  - `taraweehVideos.ts`
  - `ramadan.ts`
- `public/data/`
  - AI-ready day marker JSON files
