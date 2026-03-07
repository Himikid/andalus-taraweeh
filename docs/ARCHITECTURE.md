# Architecture

This system is built as a local-first orchestration loop with remote GPU transcription workers.

## 1) Component view

```mermaid
flowchart TB
    subgraph Sources["Source Media"]
        YT["YouTube livestreams / uploads"]
    end

    subgraph LocalHost["Local Machine"]
        LOOP["run_day_remote_loop.py"]
        PROC["process_day.py + ai_pipeline/*"]
        WEB["local_transcript_webhook.py"]
        CFG["local_config.json (gitignored)"]
        DAY["day_overrides.json"]
        QURAN["quran_arabic.json + asad cache"]
        OUT["public/data/day-*.json"]
    end

    subgraph CloudBridge["Bridge"]
        DRIVE["Google Drive bridge folders"]
        FIRE["Firestore control plane"]
        NG["ngrok public ingress"]
    end

    subgraph Colab["Colab Worker"]
        WORKER["drive_transcription_worker.py"]
        FW["faster-whisper"]
    end

    subgraph Frontend["Frontend"]
        UI["Next.js App Router UI"]
    end

    YT --> LOOP
    LOOP --> DRIVE
    LOOP --> FIRE
    LOOP --> PROC
    PROC --> DAY
    PROC --> QURAN
    PROC --> OUT

    FIRE --> WORKER
    DRIVE --> WORKER
    WORKER --> FW
    FW --> DRIVE
    WORKER --> NG
    NG --> WEB
    WEB --> DRIVE
    DRIVE --> LOOP

    OUT --> UI
```

## 2) Request lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant L as Local loop
    participant F as Firestore
    participant D as Drive
    participant C as Colab worker
    participant N as ngrok URL
    participant W as Local webhook
    participant P as process_day

    L->>F: Publish runtime doc (webhook URL + token)
    L->>F: Create queued request doc
    L->>D: Write request JSON (fallback path)
    C->>F: Poll + claim request
    C->>C: Download/normalize/chunk transcription
    C->>D: Write transcript + response files
    C->>N: POST transcript callback
    N->>W: Forward HTTPS request
    W->>D: Persist transcript + response locally
    L->>F: Poll status/progress
    L->>D: Resolve transcript artifact
    L->>P: Run matcher matrix (legacy/two_stage × vad_on/vad_off)
    P-->>L: Merged markers + diagnostics
    L->>D: Save local reports/artifacts
    L->>L: Copy final JSON -> public/data/day-*.json
```

## 3) Marker merge rules (dual VAD matrix)

1. Generate two transcripts: VAD on + VAD off.
2. Run both matcher modes on both transcripts (4 outputs).
3. Keep strongest per ayah key from legacy first, then two-stage.
4. Enforce monotonic Quran timeline.
5. Add bounded inferred markers only when gap constraints are satisfied.
6. Apply manual overrides and final boundary constraints.

## 4) Output contracts

- Local artifacts:
  - `data/ai/remote_jobs/day-{N}/transcripts/*.json`
  - `data/ai/remote_jobs/day-{N}/outputs/*.json`
  - `data/ai/remote_jobs/day-{N}/state.json`
  - `data/ai/remote_jobs/day-{N}/iteration_report.json`
- Published artifacts:
  - `public/data/day-{N}.json`
  - `public/data/day-{N}-part-{M}.json`
