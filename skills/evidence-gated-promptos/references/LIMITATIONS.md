# Limitations and Anti-Patterns

## This skill cannot guarantee truth

Natural-language instructions can reduce unsupported claims, but they cannot independently prove that a model used a tool, read a complete file, or executed a command. Real reliability still depends on inspectable tools, tests, source control, permissions, and human review.

## Common anti-patterns

### 1. Process everywhere

Forcing packets, labels, and handoffs into casual conversation makes the system rigid and expensive. Keep the A/B/C activation boundary.

### 2. Invented evidence identifiers

A formatted `evidence_ref` can still be false. Require it to resolve to an actual source, path, receipt, log, or commit.

### 3. Universalizing one person's habits

The author's overlay reflects high-volume research and engineering use. Different users may need fewer fields, softer tone, no retrospective, or different permission gates.

### 4. Prompt-level enforcement replacing engineering controls

Use CI for tests, schemas for structure, version control for history, and access controls for permissions. Do not ask prose to do what software can enforce.

### 5. Decorative state machines

A status chain is useful only when each transition corresponds to an event. Do not report states that did not occur.

### 6. Version inflation

A new title, rewritten paragraph, or refined prompt is not automatically a new tested version.

### 7. Endless correction

The operating layer should reduce maintenance, not become the main work. Stop expanding rules when failures are detectable, consequential work is reviewable, and loss is bounded.

## Suitable tasks

- code and file changes;
- research with source boundaries;
- experiments and evaluations;
- publication packages;
- multi-turn project continuation;
- regulated or high-consequence workflows with human review.

## Poor fits

- casual conversation;
- open-ended play;
- tiny wording questions;
- pure creative work without factual or execution claims;
- tasks where the requested overhead exceeds the cost of a possible error.
