# Andalus Taraweeh

Live Ramadan Taraweeh streaming and archive experience for **Andalus Centre Glasgow**.

## Quick Navigation

- [What Is Taraweeh?](#what-is-taraweeh)
- [Why This Project Exists](#why-this-project-exists)
- [Feature Highlights](#feature-highlights)
- [How It Works](#how-it-works)
- [Run Locally](#run-locally)
- [Data + AI Pipeline](#data--ai-pipeline)
- [Deploy](#deploy)
- [Project Structure](#project-structure)

## What Is Taraweeh?

Taraweeh is a special nightly prayer in Ramadan.
It usually includes long Quran recitation in congregation after the night prayer (`Isha`).

## Why This Project Exists

Many people cannot attend every night physically. This app makes it easier to:

- watch the live stream
- catch up on previous nights
- follow exactly where recitation is (`surah` / `ayah`)

## Feature Highlights

| Area | What users get |
| --- | --- |
| Live + Archive | Published Ramadan day streams in one place |
| Multi-part support | Day pages can include Part 1 / Part 2 uploads |
| Quran timeline | Indexed recitation markers by `surah`, `ayah`, `juz`, and time |
| Now Reciting | Arabic + English ayah display with current recitation context |
| Manual control | Pause, step backward/forward, then resume live sync |
| Home insights | Latest position, coverage stats, and cross-day surah navigation |

## How It Works

1. **Video layer** serves YouTube streams by Ramadan day.
2. **Indexed JSON** (`public/data/day-*.json`) powers ayah-aware navigation.
3. **Now Reciting UI** follows video time and can be manually stepped.
4. **Local Python pipeline** generates and validates Quran timeline JSON.

## Tech Stack

| Layer | Tools |
| --- | --- |
| Frontend | Next.js 14, React, TypeScript, TailwindCSS |
| Data Runtime | Static JSON from `public/data/*` |
| Processing | Python scripts in `scripts/ai_pipeline/*` |
| Hosting | Vercel |

## Run Locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Production Preview

```bash
npm run build
npm run start
```

## Configuration

### Update YouTube IDs

Edit `data/taraweehVideos.ts`.

For split uploads:

```ts
2: [
  { id: "1", label: "Part 1", videoId: "..." },
  { id: "2", label: "Part 2", videoId: "..." }
]
```

### Manual URL override

Use `?video=VIDEO_ID`

Example:
`http://localhost:3000/day/1?video=dQw4w9WgXcQ`

## Data + AI Pipeline

### Day JSON location

- `public/data/day-{N}.json`
- Multi-part example: `public/data/day-2-part-1.json`, `public/data/day-2-part-2.json`

### Day JSON usage

The day page uses indexed data for:

- ayah/surah timestamp navigation
- reciter switch points
- prayer/rakah jump points
- now-reciting context

### AI processing layer (local)

- Docs: `scripts/README.md`
- Main command: `python scripts/process_day.py ...`
- Quran corpus fetch: `python scripts/fetch_quran_corpus.py`

This Python processing is local and separate from Vercel runtime.

## Deploy

1. Push this repo to GitHub.
2. Import the repo in Vercel.
3. Keep default Next.js settings.
4. Deploy.

## Project Structure

- `app/` routes, layout, global styles
- `components/day/` day page video + recitation UI
- `components/home/` homepage panels and insights
- `components/shared/` reusable shared UI
- `data/` day metadata and static config
- `public/data/` generated indexed Quran timeline JSON
- `scripts/` local AI/data processing pipeline
