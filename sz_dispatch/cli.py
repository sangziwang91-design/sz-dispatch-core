from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .adapters import MockAdapter, OpenAIResponsesAdapter
from .models import TaskKind, TaskSpec
from .planner import build_plan
from .runner import DispatchRunner


def _load_spec(path: str) -> tuple[str, list[TaskSpec]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    tasks = [
        TaskSpec(
            task_id=item["task_id"],
            title=item["title"],
            instruction=item["instruction"],
            kind=TaskKind(item.get("kind", "analyze")),
            context=item.get("context", ""),
            dependencies=tuple(item.get("dependencies", [])),
            acceptance=tuple(item.get("acceptance", [])),
            max_output_tokens=int(item.get("max_output_tokens", 800)),
            priority=int(item.get("priority", 50)),
            risk=int(item.get("risk", 1)),
            model_class=item.get("model_class", "worker"),
        )
        for item in data["tasks"]
    ]
    return data["objective"], tasks


async def _main_async(args: argparse.Namespace) -> int:
    objective, tasks = _load_spec(args.spec)
    plan = build_plan(
        objective,
        tasks,
        max_concurrency=args.concurrency,
        token_budget=args.token_budget,
    )
    if args.mode == "plan":
        print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2, default=str))
        return 0
    if args.mode == "mock":
        adapter = MockAdapter(latency_ms=args.mock_latency)
    else:
        if not args.model:
            raise SystemExit("--model is required in live mode")
        adapter = OpenAIResponsesAdapter(model=args.model)
    report = await DispatchRunner(adapter, max_retries=args.retries).run(plan)
    output = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, default=str)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    print(output)
    return 0 if report.failed == 0 else 2


def main() -> None:
    parser = argparse.ArgumentParser(description="SZ Dispatch Core")
    parser.add_argument("spec")
    parser.add_argument("--mode", choices=["plan", "mock", "live"], default="plan")
    parser.add_argument("--model", help="OpenAI model ID for live mode")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--token-budget", type=int, default=12000)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--mock-latency", type=int, default=10)
    parser.add_argument("--output")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_main_async(args)))


if __name__ == "__main__":
    main()
