# Agent Usage Guide

This guide is for AI agents using the layered-architect skill.

## Quick Start (Agent Pattern)

Preferred (unified CLI):
```
python scripts/arch.py doctor
python scripts/arch.py init --path .
python scripts/arch.py validate --path .plan --auto-constraints --auto-deps
```

1. Check deps:
   `python scripts/check_deps.py`
2. Detect docs vs fresh start:
   `python scripts/start_arch.py`
3. If existing docs:
   - `python scripts/map_architecture.py --suggest`
   - `python scripts/map_architecture.py --apply`
4. If you already drafted elsewhere:
   `python scripts/import_plan.py --source /path/to/draft.md --target .plan`
5. If starting fresh in current repo:
   `python scripts/init_architecture.py --path .`
6. Validate once:
   `python scripts/validate_all.py --path .plan --format json`
7. Optional auto-sync of constraints:
   `python scripts/validate_all.py --path .plan --auto-constraints`
8. Dependency graph gate:
   `python scripts/validate_dependencies.py --path .plan`
9. Semantic cross-layer validation (subagents):
   `references/semantic-validation.md`

Read-only:
`LAYERED_ARCHITECT_READONLY=1 python scripts/validate_all.py --path .plan`

## Common Agent Errors & Fixes

- **Layer file not found**
  - Fix: `python scripts/validate_layer.py --layer L1 --path /path/to/.plan`
- **Wrong working directory**
  - Fix: `cd /path/to/project` then re-run
- **constraints.yml missing**
  - Fix: `python scripts/extract_constraints.py .plan/L1-meta-architecture.md`
- **Files already exist**
  - Fix: use edit/update instead of write

## Script Purpose (Agent View)

| Script | When to Use | Required |
|---|---|---|
| `check_deps.py` | first run | ✅ |
| `arch.py` | unified CLI | ✅ |
| `init_architecture.py` | fresh project | ✅ |
| `map_architecture.py` | adapting existing docs | ✅ if docs exist |
| `import_plan.py` | you already drafted content | ✅ if draft exists |
| `validate_all.py` | one-shot validation | ✅ |
| `validate_layer.py` | diagnose one layer | optional |
| `check_constraints.py` | constraints deep check | optional |
| `extract_constraints.py` | L1 markdown → YAML | optional |
| `validate_dependencies.py` | dependencies.yml gate | ✅ |
| `generate_adrs.py` | create ADRs | optional |
| `generate_diagrams.py` | mermaid/plantuml | optional |
| `checkpoint_manager.py` | manual checkpoints | optional |

## Notes

- L0 and L5 are optional. Missing files should not block validation.
- Use Question tool if available; otherwise ask text prompts with numeric choices.
- If you cannot execute commands in your environment, delegate the script runs to
  an execution-capable agent and continue after results are returned.
- ADRs are written to `.plan/decisions/` by default; init creates this directory.
- When working outside the skill directory, run scripts via the skill path
  (e.g., `/path/to/skills/layered-architect/scripts/...`) instead of `./scripts/...`.
- Dependency graph is required to proceed past L3; set `status: complete` in `.plan/dependencies.yml`.
