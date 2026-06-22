# SZ Dispatch Core

[![tests](https://github.com/sangziwang91-design/sz-dispatch-core/actions/workflows/tests.yml/badge.svg)](https://github.com/sangziwang91-design/sz-dispatch-core/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: alpha](https://img.shields.io/badge/status-alpha-orange.svg)](#claim-ceiling)

**Evidence-first DAG dispatch core for bounded LLM workloads.**

SZ Dispatch Core is a small Python reference implementation for deciding when to fan out independent LLM tasks, executing dependency-aware waves, and preserving failures instead of hiding them behind a polished final answer.

It is intentionally **not** a general agent platform, a provider quota bypass, or proof that multi-model orchestration saves money.

## What it does

- validates and deduplicates bounded task specifications;
- builds a dependency DAG and topological execution waves;
- refuses fan-out when fewer than three tasks are genuinely independent;
- compacts task context deterministically before dispatch;
- enforces a rough token budget and output caps;
- runs bounded asynchronous workers with concurrency control;
- applies timeout, retry, exponential backoff, and failure isolation;
- skips downstream tasks when dependencies fail;
- emits a structured report with an explicit claim ceiling;
- supports a deterministic mock adapter and an optional OpenAI Responses API adapter.

## What it does not do

- choose different live models from `model_class` automatically;
- programmatically verify acceptance criteria;
- provide an independent judge or human approval interface;
- prove real token, cost, latency, or quality improvements;
- bypass ChatGPT or API account limits;
- provide production-grade persistence, leasing, queues, or distributed recovery.

## Architecture

```text
User objective
      │
Deterministic planner
      │
Dependency DAG → topological waves
      │
Bounded async workers (1–5 by default)
      │
Failure-preserving synthesis
      │
Structured report + claim ceiling
```

The optimization target is not “more agents.” It is:

```text
useful independent information gain
──────────────────────────────────────
input + output + latency + coordination + merge-error cost
```

## Quick start

Requires Python 3.11+.

```bash
python -m pip install -e ".[test]"
pytest
```

Plan an example without calling a model:

```bash
python -m sz_dispatch.cli examples/research_batch.json --mode plan
```

Run the deterministic mock adapter:

```bash
python -m sz_dispatch.cli examples/research_batch.json --mode mock
```

Optional live OpenAI Responses API run:

```bash
export OPENAI_API_KEY="..."
python -m sz_dispatch.cli examples/research_batch.json \
  --mode live \
  --model "<model-id-available-to-your-account>"
```

Never put an API key in a browser artifact, repository, task file, or issue.

## Task specification

```json
{
  "objective": "Extract, compare, and audit three documents",
  "tasks": [
    {
      "task_id": "T1",
      "title": "Extract document A",
      "instruction": "Return method, sample, finding, and limitation as compact JSON.",
      "kind": "extract",
      "context": "Document A text...",
      "acceptance": ["contains method", "contains limitation"],
      "max_output_tokens": 300
    }
  ]
}
```

`acceptance` is currently included in the worker prompt but is **not** programmatically enforced. Treat it as guidance, not verified completion.

## Validation

The repository includes 50 deterministic tests covering schema validation, dependency failures, context compaction, budget scaling, DAG waves, actual `asyncio` concurrency in the sandbox, retry behavior, failure isolation, dependency skipping, serialization, and claim-boundary invariants.

See [VALIDATION_REPORT.md](VALIDATION_REPORT.md).

## Claim ceiling

Verified in the current sandbox:

- planner and DAG behavior;
- concurrency control with the mock adapter;
- timeout/retry/failure handling;
- deterministic report generation;
- 50 local tests passing.

Not verified:

- live provider connectivity;
- real account rate limits or 429 behavior;
- cross-model routing quality;
- actual provider billing;
- cost, token, latency, or answer-quality improvement;
- production reliability.

> **Current status:** sandbox-verified orchestration core and mock execution harness; live benefits remain unproven.

## 中文说明

这是一个面向有限 LLM 子任务的实验性 DAG 调度内核。它只在任务确实独立时启用并行，并保留失败、跳过和未验证边界。当前 50 项测试证明的是本地调度逻辑，不证明真实 API 一定省钱、提速或提高答案质量。

## License

MIT. See [LICENSE](LICENSE).
