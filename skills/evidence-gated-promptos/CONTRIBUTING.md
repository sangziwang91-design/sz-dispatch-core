# Contributing

Contributions are welcome when they make the skill simpler, more portable, more testable, or more honest about evidence.

## Before proposing a rule

Show at least one of:

- a reproducible failure across representative tasks;
- a client/specification change;
- a measurable reduction in complexity or false activation;
- a validation defect in the repository.

Do not add a permanent rule only because one model produced one awkward answer.

## Pull requests

1. Keep `SKILL.md` below 500 lines.
2. Put detailed guidance in one-level `references/` files.
3. Preserve the A/B/C activation boundary.
4. Do not weaken permission gates or allow fabricated evidence.
5. Add or update tests for structural changes.
6. Run:

```bash
python scripts/validate_skill.py .
python -m unittest discover -s tests -v
```

Explain what changed, why, the evidence, and the possible downside.
