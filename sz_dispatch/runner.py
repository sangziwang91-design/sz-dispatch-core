from __future__ import annotations

import asyncio
import time
from dataclasses import replace

from .adapters import ModelAdapter
from .models import DispatchPlan, RunReport, TaskSpec, TaskStatus, WorkerResult


class DispatchRunner:
    def __init__(
        self,
        adapter: ModelAdapter,
        *,
        max_retries: int = 1,
        timeout_seconds: float = 120.0,
        backoff_seconds: float = 0.05,
    ) -> None:
        self.adapter = adapter
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.backoff_seconds = backoff_seconds

    async def _run_one(self, task: TaskSpec, semaphore: asyncio.Semaphore) -> WorkerResult:
        attempts = 0
        last: WorkerResult | None = None
        while attempts <= self.max_retries:
            attempts += 1
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        self.adapter.run(task), timeout=self.timeout_seconds
                    )
                except asyncio.TimeoutError:
                    result = WorkerResult(
                        task_id=task.task_id,
                        status=TaskStatus.FAILED,
                        error="timeout",
                    )
            last = replace(result, attempts=attempts)
            if last.status == TaskStatus.PASSED:
                return last
            if attempts <= self.max_retries:
                await asyncio.sleep(self.backoff_seconds * (2 ** (attempts - 1)))
        assert last is not None
        return last

    async def run(self, plan: DispatchPlan) -> RunReport:
        started = time.perf_counter()
        by_id = {t.task_id: t for t in plan.tasks}
        results: dict[str, WorkerResult] = {}
        semaphore = asyncio.Semaphore(plan.concurrency)

        for wave in plan.waves:
            runnable: list[TaskSpec] = []
            for task_id in wave:
                task = by_id[task_id]
                failed_dep = next(
                    (
                        dep
                        for dep in task.dependencies
                        if results.get(dep) is None
                        or results[dep].status != TaskStatus.PASSED
                    ),
                    None,
                )
                if failed_dep:
                    results[task_id] = WorkerResult(
                        task_id=task_id,
                        status=TaskStatus.SKIPPED,
                        error=f"dependency not passed: {failed_dep}",
                    )
                else:
                    runnable.append(task)
            completed = await asyncio.gather(
                *(self._run_one(task, semaphore) for task in runnable)
            )
            for result in completed:
                results[result.task_id] = result

        ordered = tuple(results[t.task_id] for t in plan.tasks)
        passed = sum(r.status == TaskStatus.PASSED for r in ordered)
        failed = sum(r.status == TaskStatus.FAILED for r in ordered)
        skipped = sum(r.status == TaskStatus.SKIPPED for r in ordered)
        final_output = self._synthesize(plan, ordered)
        claim = (
            "VERIFIED: mock/runtime execution completed for this plan only"
            if failed == 0 and skipped == 0
            else "PARTIAL: one or more tasks failed or were skipped"
        )
        return RunReport(
            objective=plan.objective,
            results=ordered,
            final_output=final_output,
            total_latency_ms=int((time.perf_counter() - started) * 1000),
            total_input_tokens=sum(r.input_tokens for r in ordered),
            total_output_tokens=sum(r.output_tokens for r in ordered),
            passed=passed,
            failed=failed,
            skipped=skipped,
            claim_ceiling=claim,
            notes=plan.reasons,
        )

    @staticmethod
    def _synthesize(plan: DispatchPlan, results: tuple[WorkerResult, ...]) -> str:
        lines = [f"# {plan.objective}"]
        for result in results:
            lines.append(f"\n## {result.task_id} · {result.status.value.upper()}")
            if result.output:
                lines.append(result.output)
            if result.error:
                lines.append(f"ERROR: {result.error}")
        return "\n".join(lines)
