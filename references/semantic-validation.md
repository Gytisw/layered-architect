# Semantic Cross-Layer Validation (Sharded)

Use subagents to validate cross-layer coherence without running scripts.
Each subagent reads only two layers (or constraints + one layer) to reduce
context overload.

## Recommended Shards

- **Shard A:** L1 ↔ L2 (constraints → system choices)
- **Shard B:** L2 ↔ L3 (interfaces, subsystems → modules)
- **Shard C:** L3 ↔ L4 (modules → files/implementation details)
- **Shard D:** constraints.yml ↔ L2/L3/L4 (traceability)
- **Shard E:** dependencies.yml ↔ L3/L4 (graph ↔ module/file alignment)
- **Shard F (Optional):** L0 ↔ L1 (only if L0 exists)
- **Shard G (Optional):** L4 ↔ L5 (only if L5 exists)

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

## Evidence Checklist (Per Shard)

Each shard should include evidence references for:

- **Shard A (L1↔L2):**
  - L1 Constraints section
  - L2 Subsystems/Interfaces section
- **Shard B (L2↔L3):**
  - L2 Interfaces
  - L3 API Contracts / Modules
- **Shard C (L3↔L4):**
  - L3 Module list / Responsibilities
  - L4 File Structure / Implementation Details
- **Shard D (constraints.yml↔L2/L3/L4):**
  - `constraints.yml` entry IDs
  - At least one constraint reference in L2/L3/L4
- **Shard E (dependencies.yml↔L3/L4):**
  - `dependencies.yml` nodes + edges
  - L3 Modules and L4 File Structure
- **Shard F (L0↔L1, optional):**
  - L0 goals/non-goals/open questions
  - L1 Vision/Constraints/Success Criteria
- **Shard G (L4↔L5, optional):**
  - L4 Validation Commands / Build & Deployment
  - L5 SLOs / Readiness checks / Rollback

## Aggregation Guidance

The orchestrator should:
- Deduplicate overlapping findings across shards.
- Escalate severity if multiple shards report the same violation.
- Produce a single "Semantic Validation Summary" list.

## Gate

Run semantic validation **after** scripted validation.
If any **blocker** findings exist, do not proceed to implementation.
