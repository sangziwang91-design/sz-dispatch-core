from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable


def estimate_tokens(text: str) -> int:
    """Conservative language-agnostic estimate; never presented as provider billing truth."""
    if not text:
        return 0
    cjk = len(re.findall(r"[\u3400-\u9fff]", text))
    latin = len(text) - cjk
    return max(1, cjk + (latin + 3) // 4)


def stable_hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def dedupe_preserve(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = " ".join(item.lower().split())
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return tuple(out)


def compact_context(context: str, instruction: str, max_chars: int = 3200) -> str:
    """Cheap deterministic slicer: keeps instruction-overlapping sentences, then leading context."""
    context = " ".join(context.split())
    if len(context) <= max_chars:
        return context
    terms = {t.lower() for t in re.findall(r"[A-Za-z0-9_\-]{3,}|[\u3400-\u9fff]{2,}", instruction)}
    sentences = re.split(r"(?<=[。！？.!?])\s*", context)
    scored: list[tuple[int, int, str]] = []
    for idx, sentence in enumerate(sentences):
        low = sentence.lower()
        score = sum(1 for t in terms if t in low)
        scored.append((score, -idx, sentence))
    chosen: list[str] = []
    size = 0
    for _, _, sentence in sorted(scored, reverse=True):
        if not sentence:
            continue
        if size + len(sentence) + 1 > max_chars:
            continue
        chosen.append(sentence)
        size += len(sentence) + 1
    if not chosen:
        return context[:max_chars]
    return " ".join(chosen)
