from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Protocol

import httpx

from .models import TaskSpec, WorkerResult, TaskStatus
from .util import estimate_tokens, stable_hash


class ModelAdapter(Protocol):
    async def run(self, task: TaskSpec) -> WorkerResult: ...


@dataclass(slots=True)
class MockAdapter:
    latency_ms: int = 10
    fail_task_ids: frozenset[str] = frozenset()
    transient_failures: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.transient_failures is None:
            self.transient_failures = {}

    async def run(self, task: TaskSpec) -> WorkerResult:
        started = time.perf_counter()
        await asyncio.sleep(self.latency_ms / 1000)
        if task.task_id in self.fail_task_ids:
            return WorkerResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                attempts=1,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error="mock permanent failure",
            )
        remaining = self.transient_failures.get(task.task_id, 0)
        if remaining > 0:
            self.transient_failures[task.task_id] = remaining - 1
            return WorkerResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                attempts=1,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error="mock transient failure",
            )
        payload = {
            "task_id": task.task_id,
            "title": task.title,
            "kind": task.kind.value,
            "answer": f"MOCK-{stable_hash([task.instruction, task.context])}",
            "acceptance": list(task.acceptance),
        }
        output = json.dumps(payload, ensure_ascii=False)
        return WorkerResult(
            task_id=task.task_id,
            status=TaskStatus.PASSED,
            output=output,
            attempts=1,
            latency_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=estimate_tokens(task.instruction + task.context),
            output_tokens=estimate_tokens(output),
        )


@dataclass(slots=True)
class OpenAIResponsesAdapter:
    model: str
    api_key: str | None = None
    timeout_seconds: float = 120.0
    base_url: str = "https://api.openai.com/v1"

    async def run(self, task: TaskSpec) -> WorkerResult:
        key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            return WorkerResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                attempts=1,
                error="OPENAI_API_KEY is not set",
            )
        prompt = (
            "You are a bounded worker. Perform only the task below. "
            "Return concise output. Mark uncertainty as UNKNOWN.\n\n"
            f"TASK: {task.title}\nINSTRUCTION: {task.instruction}\n"
            f"ACCEPTANCE: {list(task.acceptance)}\nCONTEXT:\n{task.context}"
        )
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/responses",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": prompt,
                        "max_output_tokens": task.max_output_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # boundary: preserve provider error
            return WorkerResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                attempts=1,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=f"{type(exc).__name__}: {exc}",
            )

        output = data.get("output_text") or ""
        if not output:
            parts: list[str] = []
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"}:
                        parts.append(content.get("text", ""))
            output = "\n".join(p for p in parts if p)
        usage = data.get("usage", {})
        if not output:
            return WorkerResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                attempts=1,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error="provider returned no text output",
            )
        return WorkerResult(
            task_id=task.task_id,
            status=TaskStatus.PASSED,
            output=output,
            attempts=1,
            latency_ms=int((time.perf_counter() - started) * 1000),
            input_tokens=int(usage.get("input_tokens", 0) or 0),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
        )
