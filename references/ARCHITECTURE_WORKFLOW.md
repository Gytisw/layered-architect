# Architecture Workflow (Canonical)

**STRICT MODE: DO NOT PROCEED WITH WARNINGS OR ERRORS.**
**FOLLOW THE STAGING SEQUENCE. DO NOT SKIP GATES.**
**IF YOU MUST ASSUME, ASK THE USER OR LOG IT EXPLICITLY.**

This is the single, canonical workflow. If you deviate, results are invalid.

---

## Tool Limits (Claude Code)
- AskUserQuestion supports **1–4 questions** per call
- Each question supports **2–4 options**
- Split questions when more options are needed

---

## Required Artifacts

- `.plan/gates.yml` — workflow state (generated at init)
- `.plan/constraints.yml` — constraint registry
- `.plan/dependencies.yml` — dependency graph (status: complete)
- `.plan/research.md|json` — required when research gate applies
- `.plan/semantic-validation.md|json` — required before completion

---

## Staged Sequence (Do Not Skip)

### Stage 0 — Project Status
Command:
```
python scripts/arch.py doctor --path .
```
Gate:
- If no `.plan`, initialize.

### Stage 1 — Initialize
Command:
```
python scripts/arch.py init --path .
```
Gate:
- `.plan/gates.yml` exists.

### Stage 2 — L0/L1 Gating
- Ask L0 trigger questions.
- Ask L1 questions (minimal or thorough).

**STRICT MODE: DO NOT PROCEED WITH WARNINGS OR ERRORS.**

### Stage 3 — L1 (Meta‑Architecture)
- Fill L1, update constraints.
- Validate:
```
python scripts/arch.py validate --path .plan
```

### Stage 4 — Research Approval (After L1)
- Propose research plan to user.
- If approved: set `research_approved: true` in `.plan/gates.yml`.
- Record research in `.plan/research.md|json`.

### Stage 5 — L2 (System Architecture)
- Fill L2, include External Dependencies if applicable.
- Validate via `arch.py validate`.

### Stage 6 — Dependencies Gate
- Populate `.plan/dependencies.yml` (schema‑compliant).
- Set `status: complete`.
- Validate:
```
python scripts/arch.py deps --path .plan
```

### Stage 7 — L3 (Component Design)
- Fill L3 with module specs and APIs.
- Validate via `arch.py validate`.

### Stage 8 — L4 (Implementation)
- Fill L4 (file structure, patterns, validation commands).
- Validate via `arch.py validate`.

### Stage 9 — L5 (Optional)
- If L5 triggers apply, complete L5.
- Validate via `arch.py validate`.

### Stage 10 — Semantic Validation (Required)
- Run sharded semantic validation (A–E, plus F/G if applicable).
- Save report to `.plan/semantic-validation.md|json`.
- Set `semantic_completed: true` in `.plan/gates.yml`.

### Stage 11 — Final Gate
```
python scripts/arch.py validate --path .plan
```

**STRICT MODE: DO NOT PROCEED WITH WARNINGS OR ERRORS.**
**FOLLOW THE STAGING SEQUENCE. DO NOT SKIP GATES.**
**IF YOU MUST ASSUME, ASK THE USER OR LOG IT EXPLICITLY.**

---

## Wizard Commands

- `python scripts/arch.py run --path .plan` — guided flow, blocks on missing gates
- `python scripts/arch.py status --path .plan` — gate status table
- `python scripts/arch.py next --path .plan` — single next required action
