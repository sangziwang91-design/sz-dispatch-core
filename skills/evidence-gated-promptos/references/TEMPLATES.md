# Templates

Use only the minimum fields required by the task.

## Minimal task packet

```yaml
task_object: ""
primary_objective: ""
inputs: []
current_state:
  status: UNKNOWN
  evidence_ref: []
acceptance: []
output: ""
permissions:
  allowed: []
  requires_explicit_authorization: []
prohibitions: []
stop_condition: ""
```

## Completion claim

```yaml
claim: ""
status: VERIFIED | PARTIAL | BLOCKED | ROLLED_BACK | UNKNOWN | USER-REPORTED
evidence_ref: []
artifact: none
coverage: not_applicable
limitations: []
```

## Evidence gap

```yaml
id: GAP-001
blocked_claim: ""
missing_evidence: ""
last_checked: ""
close_only_with: ""
```

## Compact handoff

```markdown
### Handoff
- Time anchor:
- Current state:
- Completed:
- Incomplete:
- Evidence:
- Limits:
- One next action:
- Forbidden inference:
- Reusable material:
```

## Error repair record

```yaml
original_error: ""
reproduction: ""
root_cause: ""
change: ""
targeted_validation: []
affected_regression: []
remaining_risk: []
```
