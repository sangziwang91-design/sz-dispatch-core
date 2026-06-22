from __future__ import annotations

from collections import defaultdict, deque

from .models import DispatchPlan, TaskKind, TaskSpec
from .util import compact_context, dedupe_preserve, estimate_tokens

_SIMPLE_KINDS = {TaskKind.EXTRACT, TaskKind.CLASSIFY, TaskKind.FORMAT, TaskKind.SUMMARIZE}


def _topological_waves(tasks: tuple[TaskSpec, ...]) -> tuple[tuple[str, ...], ...]:
    ids = {t.task_id for t in tasks}
    indegree = {t.task_id: 0 for t in tasks}
    children: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        for dep in task.dependencies:
            if dep not in ids:
                raise ValueError(f"{task.task_id}: unknown dependency {dep}")
            if dep == task.task_id:
                raise ValueError(f"{task.task_id}: self dependency")
            indegree[task.task_id] += 1
            children[dep].append(task.task_id)
    ready = deque(sorted(k for k, v in indegree.items() if v == 0))
    waves: list[tuple[str, ...]] = []
    visited = 0
    while ready:
        wave = tuple(ready)
        ready.clear()
        waves.append(wave)
        visited += len(wave)
        for node in wave:
            for child in sorted(children[node]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
    if visited != len(tasks):
        raise ValueError("dependency cycle detected")
    return tuple(waves)


def _dedupe_tasks(tasks: list[TaskSpec]) -> tuple[TaskSpec, ...]:
    seen: set[tuple[str, str]] = set()
    out: list[TaskSpec] = []
    for task in tasks:
        task.validate()
        key = (" ".join(task.title.lower().split()), " ".join(task.instruction.lower().split()))
        if key in seen:
            continue
        seen.add(key)
        out.append(task)
    ids = [t.task_id for t in out]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task_id")
    return tuple(out)


def build_plan(
    objective: str,
    tasks: list[TaskSpec],
    *,
    max_concurrency: int = 5,
    token_budget: int = 12000,
    min_fanout_tasks: int = 3,
) -> DispatchPlan:
    if not objective.strip():
        raise ValueError("objective is required")
    if max_concurrency < 1:
        raise ValueError("max_concurrency must be >= 1")
    if token_budget < 256:
        raise ValueError("token_budget too small")

    clean = _dedupe_tasks(tasks)
    if not clean:
        raise ValueError("at least one task is required")

    normalized: list[TaskSpec] = []
    for task in clean:
        ctx = compact_context(task.context, task.instruction)
        acceptance = dedupe_preserve(task.acceptance)
        normalized.append(
            TaskSpec(
                task_id=task.task_id,
                title=task.title,
                instruction=task.instruction,
                kind=task.kind,
                context=ctx,
                dependencies=task.dependencies,
                acceptance=acceptance,
                max_output_tokens=task.max_output_tokens,
                priority=task.priority,
                risk=task.risk,
                model_class=task.model_class,
            )
        )
    clean = tuple(normalized)
    waves = _topological_waves(clean)

    estimated_input = sum(estimate_tokens(t.instruction + t.context) for t in clean)
    estimated_output = sum(t.max_output_tokens for t in clean)
    independent = max((len(w) for w in waves), default=1)
    fanout = independent >= min_fanout_tasks and len(clean) >= min_fanout_tasks

    reasons: list[str] = []
    if not fanout:
        reasons.append("独立任务不足，避免为并行支付规划与综合开销")
    else:
        reasons.append(f"最大独立波次包含 {independent} 个任务，可并行")

    total_est = estimated_input + estimated_output
    if total_est > token_budget:
        reasons.append(f"估算 token {total_est} 超过预算 {token_budget}，降低输出上限")
        scale = max(0.25, token_budget / total_est)
        clean = tuple(
            TaskSpec(
                task_id=t.task_id,
                title=t.title,
                instruction=t.instruction,
                kind=t.kind,
                context=t.context,
                dependencies=t.dependencies,
                acceptance=t.acceptance,
                max_output_tokens=max(64, int(t.max_output_tokens * scale)),
                priority=t.priority,
                risk=t.risk,
                model_class=t.model_class,
            )
            for t in clean
        )
        estimated_output = sum(t.max_output_tokens for t in clean)

    high_risk = sum(1 for t in clean if t.risk >= 4)
    if high_risk:
        reasons.append(f"{high_risk} 个高风险任务需要终审，不允许小模型结论直接发布")

    concurrency = 1 if not fanout else min(max_concurrency, independent)
    return DispatchPlan(
        objective=objective.strip(),
        tasks=clean,
        waves=waves,
        concurrency=concurrency,
        fanout_enabled=fanout,
        estimated_input_tokens=estimated_input,
        estimated_output_tokens=estimated_output,
        reasons=tuple(reasons),
    )
