# Adoption Guide

## Start thin

Do not paste every reference file into a permanent system prompt. Install the skill and let the client load details only when relevant.

Recommended layers:

1. `SKILL.md` — portable universal workflow;
2. `PERSONAL-OVERLAY.md` — user-specific habits;
3. task-local packet — current objective, inputs, permissions, and acceptance;
4. tool and repository state — source of truth for mutable facts.

## Remove before adding

Before adding a rule, ask:

- Does an existing rule already cover this failure?
- Can a test, schema, CI check, permission gate, or source-control rule enforce it better?
- Did the failure repeat, or was it a one-off?
- Will the rule damage casual conversation or creative work?

A useful promotion threshold is: add a permanent rule only after a failure repeats or causes material cost. Keep isolated failures in a local note instead of expanding the kernel.

## Personalization matrix

| Area | Universal core | Personal overlay |
|---|---|---|
| No fabricated execution | keep | do not weaken |
| Permission for irreversible actions | keep | add domain-specific actions |
| Evidence labels | keep | simplify wording if needed |
| Task packet | conditional | choose preferred fields |
| Project categories | none | add your own domains |
| Timezone | none | set your own |
| Writing voice | none | define locally |
| Handoff format | compact default | customize |
| Retrospective | optional | enable or remove |

## Installation tests

After installing, try three prompts:

1. a casual question — the skill should not force a task packet;
2. a file or code task — the agent should inspect before claiming modification;
3. an impossible completion request — the agent should return `PARTIAL`, `BLOCKED`, or `UNKNOWN` rather than invent evidence.

## Maintenance rule

Change the skill only when there is a verified failure, a changed client specification, or a measurable simplification. Do not version a wording preference as a capability upgrade.
