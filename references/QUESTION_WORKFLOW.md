# Question Workflow (Canonical)

This is the only canonical questioning guide.
Use it together with `references/ARCHITECTURE_WORKFLOW.md`.

## Platform Limits

- Claude Code: **1–4 questions** per call, **2–4 options** each.
- If more options are required, split into multiple calls.

## Non-Negotiable Rules

- In **thorough** mode, do not stop at product-level questions; also cover stack, data model, failure modes, and operability.
- In **thorough** mode, collect at least 8 answered fields before finalizing L1.
- If user answers with ambiguity (`auto-generate`, `best suited`, `you choose`, `whatever`), ask constrained follow-up questions before drafting.
- Do not proceed to next layer until the current layer has measurable inputs.
- After any file edit, run:
  - `python scripts/arch.py status --path .plan`
  - `python scripts/arch.py next --path .plan`
- Before drafting the next layer, require:
  - `python scripts/arch.py stage enter --path .plan --layer <target>`

## Stage Question Coverage

## Stage 0 (Session Setup)
- Validation mode: strict or soft
- Question depth: minimal or thorough
- Greenfield or adaptation

## Stage 1 (L0/L1 Triggers)
- Ask if requirements are clear.
- Ask if production-readiness concerns exist.
- Workflow will auto-trigger L0/L5 markers; confirm only when needed.

## Stage 2 (L1 Inputs)
Minimum required:
- Problem intent and users
- Measurable scale and latency
- 3–20 measurable constraints
- Risks and success metrics

Thorough mode must additionally capture:
- Security/compliance expectations
- Data retention boundaries
- Explicit trade-offs and rejected options

## Stage 3 (L2 Inputs)
Minimum required:
- Subsystems and ownership boundaries
- Interfaces and data flow
- External dependencies

Thorough mode must additionally capture:
- Auth model and SLA targets
- Migration constraints
- Dependency research needs and decision impact

## Stage 4 (L3/L4 Inputs)
Minimum required:
- Module APIs and dependency graph
- Implementation structure and validation commands

Thorough mode must additionally capture:
- Error handling and resilience patterns
- Build/deploy strategy
- Traceability from constraints to modules/files

## Stage 5 (L5 Inputs, when required)
Minimum required:
- SLO/SLI targets
- Rollback, RPO/RTO, and alerting

Thorough mode must additionally capture:
- Security controls and threat model evidence
- Cost guardrails and runbook readiness

## Forced Follow-Up Patterns

If user says:
- `auto-generate` -> ask concrete target metrics and constraints.
- `best suited` -> present 2–4 explicit stack choices with tradeoffs.
- `you choose` -> choose default only after showing options and getting approval.
- `whatever` / vague response -> request bounded options and measurable targets; do not infer silently.

## Research Trigger Questions

When external dependencies are involved, ask:
- Is fresh market/spec/security research required before L2 finalization?
- If yes, user approval is mandatory and evidence bundle is required:
  - `.plan/research.md`
  - `.plan/research.evidence.json`

Never mark research approved without explicit user approval and evidence validation.
Never claim research completion from model memory alone.
