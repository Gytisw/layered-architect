# Research Log

**Date:** YYYY-MM-DD
**Approved by:** [User / Stakeholder]
**Scope:** [What was researched]
**Evidence File:** `.plan/research.evidence.json`

## Sources
- Source 1: [link or reference]
- Source 2: [link or reference]

## Findings (Summary)
- Finding 1
- Finding 2

## Decisions Impacted
- Decision: [what changed based on research]
- Decision: [what changed based on research]

## Assumptions / Unknowns
- Assumption: [explicitly stated if research was limited]

## Risks
- Risk: [if research indicates a risk]

## Required Gate Notes

- Research approval must be done via CLI:
  - `python scripts/arch.py research approve --path .plan --approved-by <name> --confirm-user-approval`
- Do not manually edit `.plan/gates.yml`.
- Evidence bundle must include claims mapped to source IDs and decision impacts.
