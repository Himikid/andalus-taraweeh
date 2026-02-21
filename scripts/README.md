# AI Processing Layer (Local)

This folder contains the local-only Python pipeline for generating day JSON files used by the static frontend.

## What it does

- Pulls audio from YouTube URL or local file.
- Normalizes audio to 16kHz mono.
- Detects rakaat starts using combined audio-boundary and Fatiha-anchor signals.
- Transcribes Arabic recitation (best effort).
- Matches transcript to Quran corpus for surah/ayah markers (best effort).
- Assigns reciter labels (`Hasan` / `Samir` / `Talk`) via voice-embedding profile matching.
- Emits reciter switch timestamps for UI jump tags.
- Overwrites `public/data/day-{N}.json`.

## Install Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements-ai.txt
```

You also need system binaries:

- `ffmpeg`
- `yt-dlp`

On macOS:

```bash
brew install ffmpeg yt-dlp
```

## One-time Quran corpus fetch

```bash
python scripts/fetch_quran_corpus.py
```

This saves:

- `data/quran/quran_arabic.json`

## Process a day from YouTube

```bash
python scripts/process_day.py --day 1 --youtube-url "https://youtu.be/WJGS2B673Zg" --bootstrap-reciters
```

## Process a day from local audio

```bash
python scripts/process_day.py --day 2 --audio-file data/audio/day-2.wav
```

## Process split uploads as parts

```bash
python scripts/process_day.py --day 2 --part 1 --youtube-url "https://youtu.be/..."
python scripts/process_day.py --day 2 --part 2 --youtube-url "https://youtu.be/..."
```

This writes:

- `public/data/day-2-part-1.json`
- `public/data/day-2-part-2.json`

Then set day config in `data/taraweehVideos.ts` to parts with matching `id`s.

## Fast tuning on first 15 minutes

This runs multiple matcher configs, validates each, and writes the best candidate to `public/data/day-{N}.json`.

```bash
python scripts/tune_day.py --day 1 --audio-file data/audio/day-1/source.wav --max-audio-seconds 900
```

Tuning artifacts:

- `data/ai/tuning/day-{N}/leaderboard.json`
- `data/ai/tuning/day-{N}/candidate-*.json`

## Autonomous matcher agent (branch-per-trial)

Fixed spec + strategy loop:

- spec: `scripts/agent/spec_v1.json`
- runner: `scripts/run_matcher_agent.py`
- stage worker: `scripts/agent_trial_worker.py`

Run:

```bash
python scripts/run_matcher_agent.py --run-id day123
```

Resume a stopped run:

```bash
python scripts/run_matcher_agent.py --resume-run-id day123
```

Behavior:

- Creates isolated trial worktrees under `data/ai/agent/runs/<run-id>/worktrees/`
- Creates per-trial branches named `codex/agent-...`
- Evaluates `quick -> medium -> full` stages using a fixed scoring spec
- Writes continuous logs to stdout while running
- Stores best-so-far metadata so Ctrl+C is safe

Key artifacts:

- state: `data/ai/agent/runs/<run-id>/state.json`
- leaderboard: `data/ai/agent/runs/<run-id>/leaderboard.json`
- best trial: `data/ai/agent/runs/<run-id>/best/best-trial.json`
- best patch vs base: `data/ai/agent/runs/<run-id>/best/best.diff`

Optional process-day overrides used by the agent:

- `--transcript-cache-override <path>`
- `--match-overrides-json <path>`

## Validation reports

Transcript-based validation:

```bash
python scripts/validate_day.py --day-json public/data/day-1.json
```

Strict audio spot-check validation (re-transcribes marker clips):

```bash
python scripts/validate_day.py \
  --day-json public/data/day-1.json \
  --audio-file data/audio/day-1/source.wav \
  --audio-check-samples 12
```

Reports are saved under:

- `data/ai/reports/`

## Output

The pipeline overwrites:

- `public/data/day-{N}.json`

Then you commit + push that JSON (and any profile updates) to trigger Vercel redeploy.

## Reciter behavior

- With `--bootstrap-reciters` on day 1, it builds/stabilizes voice profiles at:
  - `data/ai/reciter_profiles.json`
- Later days classify reciters from profile similarity (plus smoothing for noisy flips).

## Day JSON fields

Generated `public/data/day-{N}.json` includes:

- `markers`: ayah timeline entries with `surah`, `ayah`, `juz`, `time`, `reciter`, `confidence`
- `rakaat`: detected rakah starts and reciter labels
- `reciter_switches`: detected switch points with jump timestamps
- `prayers`: legacy grouped view (every 2 rakaat)

## Vercel impact

This Python layer does not run on Vercel by default.

Your Next.js deploy remains static and unaffected because Vercel builds from `npm run build` only.
