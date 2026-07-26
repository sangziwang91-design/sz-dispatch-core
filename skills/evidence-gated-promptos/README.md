# Evidence-Gated PromptOS Skill

[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-open%20format-blue)](https://agentskills.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A portable Agent Skill for people who need AI systems to **separate plausible language from real execution**.

It packages a public-safe extraction of `SZ-PromptOS GPT v0.5` and its high-output personal workflow overlay into two clearly separated layers:

1. **Universal execution rules** — evidence boundaries, permission control, minimal task packets, repair loops, honest partial delivery, version gates, and stopping rules.
2. **Optional personal overlay** — communication routing and delivery habits developed during high-volume, multi-project research and engineering work.

The second layer is an example, not a universal standard. Users are expected to copy, delete, and adapt it.

## Why this exists

Heavy AI use can create a new kind of maintenance work: repeatedly correcting false continuity, simulated progress, inflated completion claims, over-structured replies, and accidental project expansion.

This skill does not try to make a model infallible. It narrows the goal:

> Important work should be inspectable, bounded, recoverable, and honestly incomplete when evidence is missing.

## What it is not

- not a general autonomous-agent framework;
- not proof that a model actually used a tool;
- not a substitute for tests, source control, approval gates, or domain review;
- not a requirement to turn casual conversation into project management;
- not a claim that one person's workflow is universally optimal.

## Repository structure

```text
evidence-gated-promptos/
├── SKILL.md                         # Activation and core workflow
├── references/
│   ├── CORE-KERNEL.md               # Full public PromptOS kernel
│   ├── EVIDENCE-PROTOCOL.md         # Claim and status rules
│   ├── PERSONAL-OVERLAY.md          # Optional author workflow
│   ├── TEMPLATES.md                 # Task packet, claim, handoff
│   ├── ADOPTION-GUIDE.md            # How to customize safely
│   ├── LIMITATIONS.md               # Failure modes and boundaries
│   └── EXAMPLES.md                  # A/B/C examples
├── assets/                          # Copyable templates
├── scripts/validate_skill.py        # Dependency-free validator
├── tests/test_validate_skill.py
└── .github/workflows/               # CI validation when standalone
```

The layout follows the open [Agent Skills specification](https://agentskills.io/specification): a required `SKILL.md` with YAML frontmatter, plus optional `references/`, `scripts/`, and `assets/` for progressive disclosure. OpenAI describes Skills as reusable, shareable workflows and follows the same open standard.

## Install

### Skills-compatible agent

Clone or copy this directory as a folder named `evidence-gated-promptos` into the skills directory supported by your client. For clients following the common project convention:

```bash
mkdir -p .agents/skills
git clone <repository-url> .agents/skills/evidence-gated-promptos
```

Then restart or reload the client so it can discover the `name` and `description` in `SKILL.md`.

### Manual use

Ask the agent to read `SKILL.md` before a complex task. Load referenced files only when the task requires them.

## Typical triggers

- “Inspect these files, fix the bug, run tests, and report exactly what changed.”
- “Continue this project, but do not infer the current branch or experiment status from memory.”
- “Separate sourced findings from inference and user-reported facts.”
- “Do not call this complete unless you have an inspectable artifact and validation evidence.”
- “Create a handoff that another agent can resume without inventing continuity.”

## Validation

Run the bundled dependency-free checks:

```bash
python scripts/validate_skill.py .
python -m unittest discover -s tests -v
```

The validator checks required frontmatter, naming rules, description length, main-file size, required resources, and relative Markdown links.

When available, also run the official reference validator:

```bash
skills-ref validate .
```

## Design principles

- **Progressive disclosure:** keep `SKILL.md` thin; load detail only when needed.
- **Claim ceiling:** evidence supports only the claim it can actually prove.
- **Minimum sufficient process:** add structure only when it changes reliability or delivery.
- **Failure preservation:** partial and blocked states are legitimate outcomes.
- **Personal overlays are optional:** workflow preference is not universal truth.
- **Stop at acceptance:** do not build a new framework to avoid finishing the task.

## Status

`0.1.0` is the first public skill package. It validates structure and internal references. It has not been shown to eliminate hallucination, guarantee tool use, or improve every task type.

## Author

SangZi Wang / 王桑梓  
ORCID: [0009-0003-7947-4531](https://orcid.org/0009-0003-7947-4531)

## License

MIT. See [LICENSE](LICENSE).
