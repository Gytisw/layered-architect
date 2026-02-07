# Agent Usage Guide

This guide is for AI agents using the layered-architect skill.

## Quick Start (Agent Pattern)

1. Check deps:
   `python scripts/check_deps.py`
2. Detect docs vs fresh start:
   `python scripts/start_arch.py`
3. If existing docs:
   - `python scripts/map_architecture.py --suggest`
   - `python scripts/map_architecture.py --apply`
4. If you already drafted elsewhere:
   `python scripts/import_plan.py --source /path/to/draft.md --target .plan`
5. Validate once:
   `python scripts/validate_all.py --path .plan --format json`

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
| `init_architecture.py` | fresh project | ✅ |
| `map_architecture.py` | adapting existing docs | ✅ if docs exist |
| `import_plan.py` | you already drafted content | ✅ if draft exists |
| `validate_all.py` | one-shot validation | ✅ |
| `validate_layer.py` | diagnose one layer | optional |
| `check_constraints.py` | constraints deep check | optional |
| `extract_constraints.py` | L1 markdown → YAML | optional |
| `generate_adrs.py` | create ADRs | optional |
| `generate_diagrams.py` | mermaid/plantuml | optional |
| `checkpoint_manager.py` | manual checkpoints | optional |

## Notes

- L0 and L5 are optional. Missing files should not block validation.
- Use Question tool if available; otherwise ask text prompts with numeric choices.
