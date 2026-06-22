# Design notes

## Objective function

The goal is not to maximize worker count. It is to maximize:

`useful independent information gain / (input + output + latency + coordination + merge-error cost)`

## Minimal topology

```text
User objective
      │
Deterministic planner
      │
Wave 1: bounded independent workers
      │
Wave 2+: dependent analysis
      │
Failure-preserving synthesis
      │
Compact report + claim ceiling
```

## Why not 20 workers?

An additional worker is useful only when it contributes non-duplicative information. Shared context, repeated work, synchronization, and final merging can cost more than the parallelism saves.

The default policy therefore:

- disables fan-out for fewer than three independent tasks;
- caps concurrency;
- slices context before dispatch;
- preserves failures and skips blocked dependents;
- avoids claiming live benefits from mock execution.

## What is actually novel here?

The underlying techniques—DAGs, semaphores, retries, adapters, and asynchronous execution—are established engineering patterns. The value of this repository is the compact combination of those patterns with explicit refusal conditions and claim boundaries for LLM workloads.

## “Hidden backdoor” hypothesis

There is no evidence of a secret quota reserved for sophisticated users. The practical opportunity is the composition of public capabilities: bounded task specifications, structured outputs, code-level concurrency, model adapters, caching, batch processing, and independent validation.
