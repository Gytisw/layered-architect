---
name: layered-architect
description: Deterministic layered architecture workflow with strict gate enforcement, verifiable research, and semantic cross-layer validation.
---

# Layered Architect (Agent Rules)

**STRICT MODE: DO NOT PROCEED WITH WARNINGS OR ERRORS.**  
**FOLLOW THE STAGING SEQUENCE. DO NOT SKIP GATES.**  
**DO NOT MANUALLY EDIT `.plan/gates.yml`.**

Start here:
- `references/ARCHITECTURE_WORKFLOW.md`
- `references/QUESTION_WORKFLOW.md`
- `references/INDEX.md`

## Unified CLI Only

Use only:
- `python scripts/arch.py ...`

Do not run legacy scripts directly.

## Mandatory Execution Pattern

1. `python scripts/arch.py doctor --path .`
2. `python scripts/arch.py init --path .`
3. Draft layer content in order.
4. After each file edit:
   - `python scripts/arch.py status --path .plan`
   - `python scripts/arch.py next --path .plan`
5. Validate before progression:
   - `python scripts/arch.py validate --path .plan --strict`

## Gate Operations (CLI Authority)

- Sync derived gates:
  - `python scripts/arch.py gate sync --path .plan --from .plan/last-validation.json`
- Approve research:
  - `python scripts/arch.py research approve --path .plan --approved-by <name> --confirm-user-approval`
- Complete semantic gate:
  - `python scripts/arch.py semantic complete --path .plan --completed-by <name>`

If any gate receipt is missing or stale, progression is invalid.

## Research Gate

If external dependencies are detected, research is required.

Required artifacts:
- `.plan/research.md`
- `.plan/research.evidence.json`

In strict mode, missing evidence blocks progression.
If runtime cannot execute web/subagent research, request user-provided evidence and remain blocked until supplied.

## Semantic Gate

Run semantic validation after scripted validation:
- `python scripts/arch.py semantic validate --path .plan --strict`

Then mark completion via CLI:
- `python scripts/arch.py semantic complete --path .plan --completed-by <name>`

Do not declare completion without semantic completion receipt.

## Questioning Rules

Use canonical guide:
- `references/QUESTION_WORKFLOW.md`

Thorough mode must include technical-depth questions (stack, data model, operability, failure modes), not only product intent.
Ambiguous user answers must trigger constrained follow-up questions.

## Completion Criteria

Architecture is complete only when:
- strict validation passes,
- blocking findings are zero,
- required research artifacts and approvals exist,
- semantic completion receipt exists,
- validation stamp is fresh.
