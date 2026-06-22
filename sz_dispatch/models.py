from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class TaskKind(str, Enum):
    EXTRACT = "extract"
    CLASSIFY = "classify"
    FORMAT = "format"
    SUMMARIZE = "summarize"
    ANALYZE = "analyze"
    CODE = "code"
    WRITE = "write"
    JUDGE = "judge"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class TaskSpec:
    task_id: str
    title: str
    instruction: str
    kind: TaskKind = TaskKind.ANALYZE
    context: str = ""
    dependencies: tuple[str, ...] = ()
    acceptance: tuple[str, ...] = ()
    max_output_tokens: int = 800
    priority: int = 50
    risk: int = 1
    model_class: str = "worker"

    def validate(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id is required")
        if not self.title.strip():
            raise ValueError(f"{self.task_id}: title is required")
        if not self.instruction.strip():
            raise ValueError(f"{self.task_id}: instruction is required")
        if self.max_output_tokens < 32:
            raise ValueError(f"{self.task_id}: max_output_tokens too small")
        if self.risk not in range(0, 6):
            raise ValueError(f"{self.task_id}: risk must be 0..5")


@dataclass(slots=True)
class DispatchPlan:
    objective: str
    tasks: tuple[TaskSpec, ...]
    waves: tuple[tuple[str, ...], ...]
    concurrency: int
    fanout_enabled: bool
    estimated_input_tokens: int
    estimated_output_tokens: int
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "tasks": [asdict(t) for t in self.tasks],
            "waves": [list(w) for w in self.waves],
            "concurrency": self.concurrency,
            "fanout_enabled": self.fanout_enabled,
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimated_output_tokens": self.estimated_output_tokens,
            "reasons": list(self.reasons),
        }


@dataclass(slots=True)
class WorkerResult:
    task_id: str
    status: TaskStatus
    output: str = ""
    attempts: int = 0
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None
    evidence: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()


@dataclass(slots=True)
class RunReport:
    objective: str
    results: tuple[WorkerResult, ...]
    final_output: str
    total_latency_ms: int
    total_input_tokens: int
    total_output_tokens: int
    passed: int
    failed: int
    skipped: int
    claim_ceiling: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "results": [asdict(r) for r in self.results],
            "final_output": self.final_output,
            "total_latency_ms": self.total_latency_ms,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "claim_ceiling": self.claim_ceiling,
            "notes": list(self.notes),
        }
