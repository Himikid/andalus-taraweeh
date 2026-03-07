# Architecture

This system is built as a local-first orchestration loop with remote GPU transcription workers.

## 1) High-level components

```mermaid
flowchart LR
    YT["YouTube"] --> LOOP["Local loop"]
    LOOP --> FS["Firestore queue"]
    FS --> CW["Colab worker"]
    CW --> WH["Webhook callback"]
    WH --> LOOP
    LOOP --> MM["Matching + merge"]
    MM --> OUT["day JSON output"]
    OUT --> UI["Next.js UI"]
```

## 2) Simple request flow

```mermaid
sequenceDiagram
    participant L as Local loop
    participant F as Firestore
    participant C as Colab worker
    participant W as Webhook
    participant M as Match+merge

    L->>F: Queue transcription request
    C->>F: Claim and process request
    C->>W: Send transcript callback
    W->>L: Deliver transcript
    L->>M: Run dual matcher merge
    M-->>L: Final marker JSON
```

## 3) Merge logic

1. Generate two transcripts: VAD on + VAD off.
2. Run both matcher modes on both transcripts (4 outputs).
3. Keep strongest per ayah key from legacy first, then two-stage.
4. Enforce monotonic Quran timeline.
5. Add bounded inferred markers only when gap constraints are satisfied.
6. Apply manual overrides and final boundary constraints.

## 4) Outputs

- Local artifacts:
  - `data/ai/remote_jobs/day-{N}/transcripts/*.json`
  - `data/ai/remote_jobs/day-{N}/outputs/*.json`
  - `data/ai/remote_jobs/day-{N}/state.json`
  - `data/ai/remote_jobs/day-{N}/iteration_report.json`
- Published artifacts:
  - `public/data/day-{N}.json`
  - `public/data/day-{N}-part-{M}.json`
