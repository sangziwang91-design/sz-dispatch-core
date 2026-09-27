# SZ Dispatch Core v0.1 · Validation Report

**Date:** 2026-09-22  
**Environment:** current sandbox, Python 3.13.5  
**Release status:** experimental alpha

## Result

- Deterministic tests collected: **57**
- Passed: **57**
- Failed: **0**
- Python compilation: **PASS**
- Example plan: **PASS**
- Example mock run: **5 passed / 0 failed / 0 skipped**

## Verified scope

The tests cover:

1. schema and task validation;
2. duplicate and dependency detection;
3. token estimation and deterministic context compaction;
4. budget scaling;
5. fan-out threshold and concurrency cap;
6. DAG wave generation;
7. actual `asyncio` parallel execution with the mock adapter;
8. retry, timeout boundary, failure isolation, and dependency skipping;
9. report counts, serialization, and claim-boundary invariants;
10. end-to-end mock plan execution;
11. deterministic acceptance for `nonempty`, `json`, `contains:<text>`, and `not_contains:<text>`;
12. explicit UNKNOWN handling for unsupported natural-language acceptance;
13. reuse of the existing retry budget when deterministic acceptance fails.

## Not verified

- Live OpenAI API connectivity;
- provider-specific response compatibility over time;
- model quality differences;
- model selection from `model_class`;
- actual provider token billing;
- real rate limits and 429 behavior;
- cost, latency, or answer-quality improvement;
- production reliability.

These remain **UNKNOWN** until a separately authorized live evaluation is run with credentials stored outside the repository.

## Claim ceiling

> This package is a sandbox-verified orchestration core and mock execution harness. Declared deterministic acceptance can now be checked for the bounded grammar above; unsupported criteria remain unverified. This is not evidence that multi-model dispatch saves money, improves quality, or is production-ready.
