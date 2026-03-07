from __future__ import annotations

from time import perf_counter


def _format_seconds(value: float) -> str:
    total = max(0, int(round(value)))
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class PipelineProgress:
    def __init__(self, total_stages: int, name: str = "pipeline") -> None:
        self.total_stages = max(1, int(total_stages))
        self.name = name
        self.current_stage = 0
        self.timings: dict[str, float] = {}
        self.started_at = perf_counter()

    def begin(self, label: str) -> float:
        self.current_stage += 1
        progress = min(self.current_stage, self.total_stages)
        percent = int((progress / self.total_stages) * 100)

        eta_text = ""
        if self.timings:
            avg = sum(self.timings.values()) / len(self.timings)
            remaining = max(0, self.total_stages - (self.current_stage - 1))
            eta_seconds = avg * remaining
            eta_text = f" | ETA ~{_format_seconds(eta_seconds)}"

        print(
            f"[{self.name} {progress}/{self.total_stages} {percent:>3}%] {label}...{eta_text}",
            flush=True,
        )
        return perf_counter()

    def end(self, label: str, started_at: float) -> None:
        elapsed = perf_counter() - started_at
        self.timings[label] = round(elapsed, 2)
        print(f"[{self.name}] {label} done in {elapsed:.1f}s", flush=True)

    def summary(self) -> dict[str, float]:
        return dict(self.timings)

    def total_elapsed_seconds(self) -> float:
        return perf_counter() - self.started_at

