# Agent Usage Guide

This guide is for AI agents using the layered-architect skill.

## Quick Start (Agent Pattern)

Preferred (unified CLI):
```
python scripts/arch.py doctor --json
python scripts/arch.py init --path .
python scripts/arch.py validate --path .plan --auto-constraints --auto-deps
```

1. Check deps:
   `python scripts/arch.py check-deps`
2. Detect next step:
   `python scripts/arch.py doctor --json`
3. If existing docs:
   `python scripts/arch.py map --suggest --apply`
4. If you already drafted elsewhere:
   `python scripts/arch.py import --source /path/to/draft.md --target .plan`
5. If starting fresh in current repo:
   `python scripts/arch.py init --path .`
6. Validate once (auto-constraints + auto-deps):
   `python scripts/arch.py validate --path .plan --auto-constraints --auto-deps`
7. Dependency graph gate (finalize):
   `python scripts/arch.py deps --path .plan`
8. Semantic cross-layer validation (subagents, required gate):
   `references/semantic-validation.md`

Read-only:
`LAYERED_ARCHITECT_READONLY=1 python scripts/arch.py validate --path .plan`

## Common Agent Errors & Fixes

- **Layer file not found**
  - Fix: `python scripts/arch.py validate --path /path/to/.plan`
- **Wrong working directory**
  - Fix: `cd /path/to/project` then re-run
- **constraints.yml missing**
  - Fix: `python scripts/arch.py validate --path .plan --auto-constraints`
- **Files already exist**
  - Fix: use edit/update instead of write

## Unified CLI (Only)

All actions must be performed through `python scripts/arch.py ...`.
Do not run legacy scripts directly.

## Notes

- L0 and L5 are optional. Missing files should not block validation.
- **Strict mode:** warnings block progression unless the user explicitly approves soft mode.
- **Semantic validation is required** after scripted validation (use sharded subagents).
- **Research gate:** for time-sensitive decisions (libraries, cloud services, compliance, pricing),
  delegate research or use web search before finalizing L2/L3. Record sources in
  `.plan/research.md` (or `.plan/research.json`) or document explicit assumptions.
- Use Question tool if available; otherwise ask text prompts with numeric choices.
- If you cannot execute commands in your environment, delegate the script runs to
  an execution-capable agent and continue after results are returned.
- ADRs are written to `.plan/decisions/` by default; init creates this directory.
- When working outside the skill directory, run scripts via the skill path
  (e.g., `/path/to/skills/layered-architect/scripts/...`) instead of `./scripts/...`.
- Dependency graph is required to proceed past L3; set `status: complete` in `.plan/dependencies.yml`.
