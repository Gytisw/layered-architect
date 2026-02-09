---
name: layered-architect
description: Guide for planning complex software architectures using a staged, gated workflow. Use when designing system architecture, planning technical structure, creating design docs, or reviewing architectures.
---

# Layered Architecture Planning (Agent Rules)

**STRICT MODE: DO NOT PROCEED WITH WARNINGS OR ERRORS.**
**FOLLOW THE STAGING SEQUENCE. DO NOT SKIP GATES.**
**IF YOU MUST ASSUME, ASK THE USER OR LOG IT EXPLICITLY.**

Start here:
- `references/ARCHITECTURE_WORKFLOW.md`
- `references/INDEX.md`

## When to Use
- New system architecture
- Complex feature design
- Multi‑component system planning
- Architecture review / refactor plan

## Canonical Workflow (Required)
- Always follow `references/ARCHITECTURE_WORKFLOW.md`.
- Use **only** the unified CLI `python scripts/arch.py ...`.
- Do **not** run legacy scripts directly.

## Core Commands (Unified CLI)
- `python scripts/arch.py run --path .plan` — guided workflow, blocks on gates
- `python scripts/arch.py status --path .plan` — gate status
- `python scripts/arch.py next --path .plan` — next required action
- `python scripts/arch.py validate --path .plan` — strict validation gate

## Enforcement Rules

**STRICT MODE: DO NOT PROCEED WITH WARNINGS OR ERRORS.**

- Validation warnings are **blocking** in strict mode.
- If soft mode is requested, the user must explicitly approve proceeding.
- Do not declare completion until semantic validation is completed.

## Research Gate

**FOLLOW THE STAGING SEQUENCE. DO NOT SKIP GATES.**

- After L1, propose a research plan.
- If approved, set `research_approved: true` in `.plan/gates.yml`.
- If external dependencies exist, **research is required** and must be logged in:
  - `.plan/research.md` or `.plan/research.json`

## Semantic Validation Gate

**STRICT MODE: DO NOT PROCEED WITH WARNINGS OR ERRORS.**

- After scripted validation, run sharded semantic validation.
- Save report to `.plan/semantic-validation.md` (or `.json`).
- Set `semantic_completed: true` in `.plan/gates.yml`.
- Completion is invalid without this report.

## Questioning Rules

- Use `references/interactive-questions.md` and `references/question-guide.md`.
- Claude Code limits: **1–4 questions** per call, **2–4 options** each.
- Split questions when more options are required.
- Avoid vague answers: quantify or follow up.

## Required Artifacts

- `.plan/gates.yml` (workflow state)
- `.plan/constraints.yml`
- `.plan/dependencies.yml` (status: complete)
- `.plan/research.md|json` (when required)
- `.plan/semantic-validation.md|json`

## Layer Summary

- **L0**: Problem framing (optional; only if triggers apply)
- **L1**: Meta‑architecture (vision, constraints, principles, success criteria)
- **L2**: System architecture (subsystems, boundaries, data flow, interfaces)
- **L3**: Component design (modules, APIs, dependencies)
- **L4**: Implementation (file structure, patterns, validation commands)
- **L5**: Operability & readiness (optional; only if triggers apply)

See `references/layer-guide.md` for definitions of done.

## Final Gate

Run:
```
python scripts/arch.py validate --path .plan
```

**STRICT MODE: DO NOT PROCEED WITH WARNINGS OR ERRORS.**
