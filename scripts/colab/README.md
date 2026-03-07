# Colab Chunk Worker

This worker runs in Colab and processes transcript requests from Google Drive in chunked mode.

## Folder Contract

- Requests in: `.../requests/pending/*.json`
- Worker moves active requests to: `.../requests/processing/`
- Response JSON out: `.../responses/{request_id}.json`
- Transcript out: `.../transcripts/{request_id}.json`
- Per-chunk cache: `.../transcripts/_chunks/{request_id}/chunk-XXX.json`

## Why this is resilient

- Chunked transcription (default 600s).
- If Colab disconnects, completed chunk JSON files are reused on restart.
- Requests left in `processing/` are resumed automatically on next start.

## Run in Colab

```bash
pip install faster-whisper yt-dlp requests
```

Create a local config (do not commit it):

```bash
cp scripts/colab/local_config.example.json scripts/colab/local_config.json
```

If you want a committed empty placeholder in your own workflow, use:

```bash
cp scripts/colab/local_config.template.json scripts/colab/local_config.json
```

Then set `drive_root` in `scripts/colab/local_config.json` and run:

```bash
python scripts/colab/drive_transcription_worker.py
```

Optional custom config path:

```bash
python scripts/colab/drive_transcription_worker.py --config /path/to/local_config.json
```

If running outside this repo, copy `drive_transcription_worker.py` into Colab and run it directly.

## Device mode (CPU/GPU)

Worker device defaults are controlled by config:

```json
{
  "transcription": {
    "device": "auto",
    "compute_type": ""
  }
}
```

- `device`: `auto` (default), `cpu`, or `cuda` (`gpu` alias is accepted in requests).
- `compute_type`: optional override.
  - empty -> defaults to `float16` for CUDA, `int8` for CPU.
  - if CPU + `float16` is requested, worker coerces to `int8`.

Runtime safeguard:
- Worker now tries requested CUDA config first.
- If CUDA model init fails (for example CUDA driver/runtime mismatch), worker automatically falls back to CPU `int8` and continues.

## Optional: push transcripts back via ngrok webhook

This keeps Google Drive for request/audio caching, but sends transcript results directly back to your local machine over HTTP.

### 1) Start local webhook receiver

On your local machine (same machine running `run_day_remote_loop.py`):

```bash
python scripts/colab/local_transcript_webhook.py \
  --host 127.0.0.1 \
  --port 8765 \
  --drive-config scripts/colab/local_config.json \
  --token "REPLACE_WITH_STRONG_TOKEN"
```

### 2) Expose receiver with ngrok

```bash
python scripts/colab/start_ngrok.py --config scripts/colab/local_config.json
```

Copy the HTTPS forwarding URL and append `/ingest/transcript`.

### 3) Configure callback in Colab worker config

In `scripts/colab/local_config.json` used by the Colab worker, add:

```json
{
  "callback": {
    "enabled": true,
    "url": "https://YOUR-SUBDOMAIN.ngrok-free.app/ingest/transcript",
    "bearer_token": "REPLACE_WITH_STRONG_TOKEN",
    "timeout_seconds": 20,
    "retry_attempts": 3,
    "retry_backoff_seconds": 2.0,
    "verify_tls": true,
    "send_on_cache_hit": true
  }
}
```

Behavior:
- Worker still writes Drive `responses/` + `transcripts/` as fallback.
- Worker additionally POSTs `done/failed` events to webhook.
- Local webhook writes received transcript/response into local Drive bridge paths immediately, so `run_day_remote_loop.py` can consume without waiting for Drive sync.

## Optional: Firestore request/status control plane

You can move request + status coordination to Firestore while still keeping Drive for audio/transcript artifacts.

Config block in `scripts/colab/local_config.json`:

```json
{
  "firestore": {
    "enabled": true,
    "project_id": "<FIRESTORE_PROJECT_ID>",
    "api_key": "<FIRESTORE_WEB_API_KEY>",
    "database_id": "(default)",
    "session_id": "<SESSION_ID>",
    "requests_collection": "andalus_transcription_requests",
    "runtime_collection": "andalus_transcription_runtime"
  }
}
```

When enabled:
- Local loop submits requests into `requests_collection`.
- Worker claims `status=queued` requests for the configured `session_id`.
- Worker updates `status` + progress fields (chunks done/eta/percent).
- Local loop polls Firestore status and still resolves transcript from Drive path.
- Local loop publishes webhook URL/token into `runtime_collection/{session_id}`.
- Worker reads callback URL/token from that runtime doc (Firestore-first), then falls back to request callback fields only if runtime doc is missing.

## Security notes

- Keep all real tokens/keys/paths in `scripts/colab/local_config.json` only.
- `scripts/colab/local_config.json` is gitignored.
- Use `scripts/colab/local_config.example.json` as the committed placeholder template.

## Request fields

Important request fields:

- `request_id`
- `youtube_url` or `source_audio_path`
- `start_sec`, `end_sec` (optional window)
- `model` (e.g. `large-v3`)
- `device` (optional: `auto`, `cpu`, `cuda`)
- `chunk_seconds` (e.g. `600`)
- `vad_filter` + optional `vad_parameters`
- `output_transcript_path`
