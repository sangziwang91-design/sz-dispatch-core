from __future__ import annotations

import asyncio
import json
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

    @staticmethod
    def _apply_acceptance(task: TaskSpec, result: WorkerResult) -> WorkerResult:
        if result.status != TaskStatus.PASSED or not task.acceptance:
            return result

        evidence = list(result.evidence)
        unknowns = list(result.unknowns)
        failures: list[str] = []
        output = result.output or ""

        for raw in task.acceptance:
            criterion = raw.strip()
            lower = criterion.lower()
            if lower == "nonempty":
                passed = bool(output.strip())
            elif lower == "json":
                try:
                    json.loads(output)
                    passed = True
                except json.JSONDecodeError:
                    passed = False
            elif lower.startswith("contains:"):
                needle = criterion.split(":", 1)[1]
                passed = bool(needle) and needle in output
            elif lower.startswith("not_contains:"):
                needle = criterion.split(":", 1)[1]
                passed = bool(needle) and needle not in output
            else:
                unknowns.append(f"acceptance_unverified:{criterion}")
                continue

            if passed:
                evidence.append(f"acceptance_pass:{criterion}")
            else:
                failures.append(criterion)
                evidence.append(f"acceptance_fail:{criterion}")

        if failures:
            return replace(
                result,
                status=TaskStatus.FAILED,
                error="acceptance failed: " + ", ".join(failures),
                evidence=tuple(evidence),
                unknowns=tuple(unknowns),
            )
        return replace(result, evidence=tuple(evidence), unknowns=tuple(unknowns))

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
            last = self._apply_acceptance(task, replace(result, attempts=attempts))
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
        acceptance_unknowns = sum(len(r.unknowns) for r in ordered)
        acceptance_evidence = sum(
            1 for r in ordered for item in r.evidence if item.startswith("acceptance_pass:")
        )
        if failed or skipped:
            claim = "PARTIAL: one or more tasks failed or were skipped"
        elif acceptance_unknowns:
            claim = (
                "EXECUTED_WITH_UNVERIFIED_ACCEPTANCE: workers returned successfully, "
                "but one or more declared acceptance criteria were not machine-checkable"
            )
        elif acceptance_evidence:
            claim = (
                "CHECKED: runtime execution and declared deterministic acceptance "
                "passed for this plan only"
            )
        else:
            claim = (
                "EXECUTED: workers returned successfully for this plan; "
                "no deterministic acceptance criteria were checked"
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
