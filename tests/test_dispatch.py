from __future__ import annotations

import asyncio
import json
import time

import pytest

from sz_dispatch.adapters import MockAdapter
from sz_dispatch.models import TaskKind, TaskSpec, TaskStatus
from sz_dispatch.planner import build_plan
from sz_dispatch.runner import DispatchRunner
from sz_dispatch.util import compact_context, dedupe_preserve, estimate_tokens, stable_hash


def task(i: int, **kw) -> TaskSpec:
    base = dict(
        task_id=f"T{i}",
        title=f"Task {i}",
        instruction=f"Do task {i}",
        kind=TaskKind.ANALYZE,
        context="context",
        max_output_tokens=200,
    )
    base.update(kw)
    return TaskSpec(**base)


def run(coro):
    return asyncio.run(coro)


# 01-10: schema and plan validity

def test_01_empty_objective_rejected():
    with pytest.raises(ValueError):
        build_plan("", [task(1)])


def test_02_empty_tasks_rejected():
    with pytest.raises(ValueError):
        build_plan("x", [])


def test_03_duplicate_task_id_rejected():
    with pytest.raises(ValueError):
        build_plan("x", [task(1), task(1, title="other")])


def test_04_duplicate_semantic_task_deduped():
    t1 = task(1, title="Same", instruction="Do it")
    t2 = task(2, title=" same ", instruction=" do   it ")
    p = build_plan("x", [t1, t2])
    assert len(p.tasks) == 1


def test_05_unknown_dependency_rejected():
    with pytest.raises(ValueError):
        build_plan("x", [task(1, dependencies=("NOPE",))])


def test_06_self_dependency_rejected():
    with pytest.raises(ValueError):
        build_plan("x", [task(1, dependencies=("T1",))])


def test_07_cycle_rejected():
    with pytest.raises(ValueError):
        build_plan("x", [task(1, dependencies=("T2",)), task(2, dependencies=("T1",))])


def test_08_small_token_limit_rejected():
    with pytest.raises(ValueError):
        build_plan("x", [task(1, max_output_tokens=10)])


def test_09_invalid_risk_rejected():
    with pytest.raises(ValueError):
        build_plan("x", [task(1, risk=6)])


def test_10_plan_serializes():
    p = build_plan("x", [task(1)])
    assert json.dumps(p.to_dict(), default=str)


# 11-20: token/context/dedup discipline

def test_11_token_estimate_empty_zero():
    assert estimate_tokens("") == 0


def test_12_token_estimate_cjk_nonzero():
    assert estimate_tokens("中文测试") >= 4


def test_13_token_estimate_latin_reasonable():
    assert 2 <= estimate_tokens("abcdefgh") <= 3


def test_14_stable_hash_stable():
    assert stable_hash({"a": 1}) == stable_hash({"a": 1})


def test_15_stable_hash_changes():
    assert stable_hash({"a": 1}) != stable_hash({"a": 2})


def test_16_dedupe_preserves_order():
    assert dedupe_preserve(["A", "B", "a"]) == ("A", "B")


def test_17_acceptance_deduped():
    p = build_plan("x", [task(1, acceptance=("A", "A", "B"))])
    assert p.tasks[0].acceptance == ("A", "B")


def test_18_short_context_unchanged():
    assert compact_context("abc", "x") == "abc"


def test_19_long_context_compacted():
    c = "无关句子。" * 1000 + "关键目标分析。"
    out = compact_context(c, "关键目标", max_chars=200)
    assert len(out) <= 200 and "关键目标" in out


def test_20_budget_scales_output():
    p = build_plan("x", [task(i, max_output_tokens=1000) for i in range(1, 6)], token_budget=1200)
    assert sum(t.max_output_tokens for t in p.tasks) < 5000


# 21-30: fanout, waves and concurrency

def test_21_one_task_no_fanout():
    p = build_plan("x", [task(1)])
    assert not p.fanout_enabled and p.concurrency == 1


def test_22_two_tasks_no_fanout():
    p = build_plan("x", [task(1), task(2)])
    assert not p.fanout_enabled


def test_23_three_independent_enable_fanout():
    p = build_plan("x", [task(1), task(2), task(3)])
    assert p.fanout_enabled


def test_24_concurrency_capped():
    p = build_plan("x", [task(i) for i in range(1, 8)], max_concurrency=4)
    assert p.concurrency == 4


def test_25_wave_structure():
    p = build_plan("x", [task(1), task(2), task(3, dependencies=("T1", "T2"))])
    assert p.waves == (("T1", "T2"), ("T3",))


def test_26_chain_three_waves():
    p = build_plan("x", [task(1), task(2, dependencies=("T1",)), task(3, dependencies=("T2",))])
    assert len(p.waves) == 3


def test_27_sorted_wave_ids():
    p = build_plan("x", [task(3), task(1), task(2)])
    assert p.waves[0] == ("T1", "T2", "T3")


def test_28_parallel_runtime_faster_than_serial():
    tasks = [task(i) for i in range(1, 5)]
    p = build_plan("x", tasks, max_concurrency=4)
    started = time.perf_counter()
    r = run(DispatchRunner(MockAdapter(latency_ms=40), max_retries=0).run(p))
    elapsed = time.perf_counter() - started
    assert r.passed == 4 and elapsed < 0.13


def test_29_dependency_forces_second_wave():
    tasks = [task(1), task(2), task(3, dependencies=("T1", "T2"))]
    p = build_plan("x", tasks, max_concurrency=3)
    started = time.perf_counter()
    r = run(DispatchRunner(MockAdapter(latency_ms=30), max_retries=0).run(p))
    elapsed = time.perf_counter() - started
    assert r.passed == 3 and elapsed >= 0.05


def test_30_reason_mentions_parallel_wave():
    p = build_plan("x", [task(1), task(2), task(3)])
    assert any("并行" in x for x in p.reasons)


# 31-40: failure, retry, skip and report truthfulness

def test_31_all_mock_tasks_pass():
    p = build_plan("x", [task(1), task(2), task(3)])
    r = run(DispatchRunner(MockAdapter(), max_retries=0).run(p))
    assert r.passed == 3 and r.failed == 0


def test_32_permanent_failure_recorded():
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(MockAdapter(fail_task_ids=frozenset({"T1"})), max_retries=0).run(p))
    assert r.failed == 1 and r.results[0].error


def test_33_transient_failure_retried():
    adapter = MockAdapter(transient_failures={"T1": 1})
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(adapter, max_retries=1).run(p))
    assert r.passed == 1 and r.results[0].attempts == 2


def test_34_retry_limit_respected():
    adapter = MockAdapter(transient_failures={"T1": 3})
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(adapter, max_retries=1).run(p))
    assert r.failed == 1 and r.results[0].attempts == 2


def test_35_failed_dependency_skips_child():
    p = build_plan("x", [task(1), task(2, dependencies=("T1",))])
    r = run(DispatchRunner(MockAdapter(fail_task_ids=frozenset({"T1"})), max_retries=0).run(p))
    assert r.results[1].status == TaskStatus.SKIPPED


def test_36_sibling_not_blocked_by_failure():
    p = build_plan("x", [task(1), task(2), task(3)])
    r = run(DispatchRunner(MockAdapter(fail_task_ids=frozenset({"T1"})), max_retries=0).run(p))
    assert r.passed == 2 and r.failed == 1


def test_37_partial_claim_on_failure():
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(MockAdapter(fail_task_ids=frozenset({"T1"})), max_retries=0).run(p))
    assert r.claim_ceiling.startswith("PARTIAL")


def test_38_verified_claim_on_all_pass():
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(MockAdapter(), max_retries=0).run(p))
    assert r.claim_ceiling.startswith("VERIFIED")


def test_39_report_counts_consistent():
    p = build_plan("x", [task(1), task(2, dependencies=("T1",))])
    r = run(DispatchRunner(MockAdapter(fail_task_ids=frozenset({"T1"})), max_retries=0).run(p))
    assert r.passed + r.failed + r.skipped == 2


def test_40_report_serializes():
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(MockAdapter(), max_retries=0).run(p))
    assert json.dumps(r.to_dict(), ensure_ascii=False, default=str)


# 41-50: end-to-end invariants and boundaries

def test_41_output_order_matches_task_order():
    p = build_plan("x", [task(3), task(1), task(2)])
    r = run(DispatchRunner(MockAdapter(), max_retries=0).run(p))
    assert [x.task_id for x in r.results] == ["T3", "T1", "T2"]


def test_42_mock_output_is_structured_json():
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(MockAdapter(), max_retries=0).run(p))
    assert json.loads(r.results[0].output)["task_id"] == "T1"


def test_43_input_token_accounting_nonzero():
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(MockAdapter(), max_retries=0).run(p))
    assert r.total_input_tokens > 0


def test_44_output_token_accounting_nonzero():
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(MockAdapter(), max_retries=0).run(p))
    assert r.total_output_tokens > 0


def test_45_high_risk_reason_added():
    p = build_plan("x", [task(1, risk=5)])
    assert any("高风险" in x for x in p.reasons)


def test_46_no_fanout_reason_added():
    p = build_plan("x", [task(1)])
    assert any("避免" in x for x in p.reasons)


def test_47_budget_reason_added():
    p = build_plan("x", [task(i, max_output_tokens=1000) for i in range(1, 5)], token_budget=1000)
    assert any("超过预算" in x for x in p.reasons)


def test_48_final_output_contains_failures():
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(MockAdapter(fail_task_ids=frozenset({"T1"})), max_retries=0).run(p))
    assert "ERROR:" in r.final_output


def test_49_example_shape_end_to_end():
    tasks = [
        task(1, kind=TaskKind.EXTRACT),
        task(2, kind=TaskKind.EXTRACT),
        task(3, kind=TaskKind.EXTRACT),
        task(4, dependencies=("T1", "T2", "T3")),
        task(5, dependencies=("T4",), kind=TaskKind.JUDGE, risk=5),
    ]
    p = build_plan("research", tasks, max_concurrency=3)
    r = run(DispatchRunner(MockAdapter(), max_retries=0).run(p))
    assert r.passed == 5 and len(p.waves) == 3


def test_50_no_false_production_claim():
    p = build_plan("x", [task(1)])
    r = run(DispatchRunner(MockAdapter(), max_retries=0).run(p))
    text = json.dumps(r.to_dict(), ensure_ascii=False, default=str)
    assert "生产级" not in text and "节省" not in r.claim_ceiling
