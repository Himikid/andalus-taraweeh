# Andalus Taraweeh

A live + archived Ramadan recitation platform for **Andalus Centre Glasgow**, built to make Quran recitation easier to access, follow, and understand.

---

## What Is Taraweeh?

**Taraweeh** is a special nightly prayer in Ramadan.
In many mosques, long portions of the Quran are recited each night.

This app helps people:

- watch live Taraweeh streams
- revisit previous nights as an archive
- track where recitation is in the Quran (`surah` and `ayah`)
- read Arabic text with English translation while listening

## Why This Platform Matters

This platform focuses on clarity and accessibility:

- helps people stay connected to nightly recitation
- gives context to what is being recited in real time
- makes long recitations navigable and searchable
- preserves recitation history night-by-night

---

## Why This App Is Special

| Capability | Why it matters |
| --- | --- |
| Live + archive in one flow | Users can join now or catch up later without switching tools |
| Ayah-level timeline | Recitation is navigable like chapters in a technical media player |
| AI-assisted indexing | Converts long-form recitation into structured timeline data |
| Multi-part day handling | Real-world upload splits are handled cleanly |
| Manual drift control | User can pause, step ayah-by-ayah, then re-sync instantly |

## AI-Enhanced Experience

The app uses a local Python pipeline to generate Quran timeline JSON that powers the frontend.

### AI pipeline responsibilities

- process recitation audio/transcript inputs
- align recitation against Quran ayat
- assign marker quality (`high`, `ambiguous`, `inferred`, `manual`)
- output structured day files consumed by the app

### Runtime behavior in UI

- **Now Reciting** auto-follows video time
- Arabic and English ayah text is shown for current marker
- users can **Pause**, step **back/forward**, and **Play** to re-sync

### Accuracy note

Indexing is AI-assisted and best effort. Some timestamps or matches may need manual correction.

---

## Product Walkthrough

1. Open a Ramadan day.
2. Play the livestream (or archive video).
3. Watch `Now Reciting` update with current `surah/ayah`.
4. Jump by indexed markers when needed.
5. If drift occurs, use manual controls and resume sync.

---

## Tech Stack

| Layer | Stack |
| --- | --- |
| Frontend | Next.js 14, React, TypeScript, TailwindCSS |
| Video | YouTube iframe player |
| Data runtime | JSON served from `public/data/*` |
| AI processing | Python scripts in `scripts/ai_pipeline/*` |
| Hosting | Vercel |

---

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Production preview

```bash
npm run build
npm run start
```

---

## Configuration

### YouTube day mapping

Edit: `data/taraweehVideos.ts`

Example for split uploads:

```ts
2: [
  { id: "1", label: "Part 1", videoId: "..." },
  { id: "2", label: "Part 2", videoId: "..." }
]
```

### Manual URL override

Use: `?video=VIDEO_ID`

Example:
`http://localhost:3000/day/1?video=dQw4w9WgXcQ`

---

## Data + AI Pipeline

### Day JSON files

- `public/data/day-{N}.json`
- split example: `public/data/day-2-part-1.json`, `public/data/day-2-part-2.json`

### Day JSON powers

- ayah/surah timestamp navigation
- reciter switch points
- prayer/rakah jump points
- now-reciting context

### Processing commands

- docs: `scripts/README.md`
- main: `python scripts/process_day.py ...`
- Quran corpus: `python scripts/fetch_quran_corpus.py`
- AI highlights prompt template: `data/ai/prompts/day-highlights-prompt.md`

The Python layer is local processing; it is not executed in Vercel runtime.

---

## Deploy (Vercel)

1. Push this repo to GitHub.
2. Import project in Vercel.
3. Keep default Next.js settings.
4. Deploy.

---

## Project Structure

- `app/` routes, layout, global styles
- `components/day/` day player + recitation UI
- `components/home/` homepage insights
- `components/shared/` shared UI blocks
- `data/` static config and day metadata
- `public/data/` generated Quran timeline JSON
- `scripts/` local AI/data processing pipeline
