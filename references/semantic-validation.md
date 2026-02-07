# Semantic Cross-Layer Validation (Sharded)

Use subagents to validate cross-layer coherence without running scripts.
Each subagent reads only two layers (or constraints + one layer) to reduce
context overload.

## Recommended Shards

- **Shard A:** L1 ↔ L2 (constraints → system choices)
- **Shard B:** L2 ↔ L3 (interfaces, subsystems → modules)
- **Shard C:** L3 ↔ L4 (modules → files/implementation details)
- **Shard D:** constraints.yml ↔ L2/L3/L4 (traceability)

## Output Schema (Required)

Each shard must return findings using this schema:

```
- finding_id: CV-001
  boundary: L1-L2 | L2-L3 | L3-L4 | Constraints
  severity: blocker | major | minor | info
  issue: "Short summary"
  evidence: "Quoted snippet or section reference"
  expected: "What should be true per constraints/layer"
  suggested_fix: "Concrete edit or action"
```

## Aggregation Guidance

The orchestrator should:
- Deduplicate overlapping findings across shards.
- Escalate severity if multiple shards report the same violation.
- Produce a single "Semantic Validation Summary" list.

## Gate

Run semantic validation **after** scripted validation.
If any **blocker** findings exist, do not proceed to implementation.
