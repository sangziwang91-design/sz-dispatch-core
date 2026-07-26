# Evidence Protocol

## Purpose

The protocol controls **what an agent may claim**, not merely how polished the answer sounds.

## Evidence classes

| Class | Examples | Supports |
|---|---|---|
| Direct runtime evidence | tool receipt, command output, test log, file diff, commit | claims about the observed run and covered scope |
| Inspectable source | file path and lines, authoritative page, supplied source range | claims contained in that source |
| User report | user statement without independent verification | `USER-REPORTED` state only |
| Generated material | plan, example, draft, search summary, model explanation | existence of that generated material only |
| No evidence | memory, assumption, unsupported completion language | no completion or state-change claim |

## Valid evidence references

A useful `evidence_ref` identifies a real, reviewable object, for example:

- tool name plus returned receipt identifier;
- repository, path, branch, and commit;
- file path plus line range or hash;
- command and captured output;
- test suite, test count, and log;
- explicit source excerpt location;
- database record identifier;
- user message containing the stated fact.

A label such as `EVIDENCE-001` is not sufficient unless it resolves to one of those objects.

## Invalid evidence references

- “internal check completed”;
- “see above” without a stable location;
- a restatement of the conclusion;
- an invented path, hash, commit, test count, or receipt;
- a search summary presented as full-document reading;
- code shown in chat presented as code already written to a repository.

## Claim record

Use the smallest record that makes the claim reviewable:

```yaml
claim: "Updated the parser to reject empty identifiers"
status: VERIFIED
evidence_ref:
  - "src/parser.py diff at commit <sha>"
  - "tests/test_parser.py::test_empty_identifier"
artifact: "src/parser.py"
coverage:
  changed_files: 2
  tests_run: 8
  tests_passed: 8
limitations:
  - "No integration test against the production service"
```

`coverage` replaces decorative counts. Use `not_applicable` when there is no meaningful count.

## Claim ceiling examples

- A unit test proves that tested behavior under that environment passed. It does not prove production reliability.
- Reading a retrieved excerpt proves the excerpt was read. It does not prove the whole file was read.
- Creating a draft proves a draft exists. It does not prove it was sent, accepted, or published.
- A generated patch proves a patch was generated. It does not prove the target file changed.
- A branch commit proves repository state changed on that branch. It does not prove merge, deployment, or user adoption.

## Persistent evidence gaps

Track open gaps when they affect later state:

```yaml
open_evidence_gaps:
  - id: GAP-001
    claim_blocked: "production-safe"
    missing: "production integration test and monitoring evidence"
```

A later answer may close the gap only by pointing to new evidence. Rephrasing does not close it.

## Status language

Use:

- `VERIFIED`: supported within stated coverage;
- `PARTIAL`: some acceptance criteria met;
- `BLOCKED`: an external dependency, permission, or unavailable evidence prevents progress;
- `ROLLED_BACK`: attempted state change was reverted;
- `UNKNOWN`: current evidence cannot resolve the question;
- `USER-REPORTED`: asserted by the user but not independently checked.

## Version gate

A version increase requires:

```text
persistent artifact change
+ identifiable diff/hash/commit
+ relevant validation executed
+ validation passed within reported scope
```

Do not version plans, understanding, conversation summaries, or renamed prompts as if they were tested products.
