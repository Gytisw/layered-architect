# Layered Architect

Agent-first skill for planning and reviewing complex software architectures using a layered approach. Designed to keep context small, reduce hallucinations, and make architecture work repeatable across agentic tools.

## Highlights

- 4 core layers (L1–L4) with optional L0/L5 gates
- Constraint registry with traceability
- Validation and linting scripts (soft gates by default)
- Universal adapter to map existing docs into L0–L5 summaries
- Templates and references to keep outputs consistent

## Repo Layout

- `SKILL.md` Skill instructions and platform notes
- `assets/` Templates and example architectures
- `references/` Guides and validation criteria
- `schemas/` JSON schemas for layers and mappings
- `scripts/` Validation, linting, and adapter tools

## Installation

### Codex CLI / IDE extensions

Codex loads skills from repo-scoped and user-scoped locations. Place this folder at one of the locations below and restart Codex:

- Repo-scoped: `$CWD/.codex/skills/layered-architect/`
- Repo-scoped (parent): `$CWD/../.codex/skills/layered-architect/`
- Repo root: `$REPO_ROOT/.codex/skills/layered-architect/`
- User-scoped: `$CODEX_HOME/skills/layered-architect/` (default `~/.codex/skills/`)
- Admin: `/etc/codex/skills/layered-architect/`

See the official Codex skills docs for the full list of supported locations and scopes.

### Other tools (OpenCode, Claude Code, Gemini CLI, Cursor)

Place the `layered-architect` folder into your tool’s skill/plugins directory and restart the tool. See your tool’s docs for the exact path and permission settings.

## Quick Start (New Architecture)

1. Initialize a `.plan` directory with layer files:
   - `python scripts/init_architecture.py my-project`
2. Fill each layer, validating after each step:
   - `python scripts/validate_layer.py L1`
   - `python scripts/validate_layer.py L2`
   - `python scripts/validate_layer.py L3`
   - `python scripts/validate_layer.py L4`
3. Track constraints and check for conflicts:
   - `python scripts/check_constraints.py`

## Optional Layers (L0/L5)

Use optional layers only when triggers apply:

- L0 Problem Framing: unclear requirements, fuzzy scope, conflicting goals
- L5 Operability & Readiness: delivery readiness, high reliability/security, cost guardrails

Templates are in:

- `assets/template-l0-problem-framing.md`
- `assets/template-l5-operability-readiness.md`

## Universal Adapter (Existing Docs → L0–L5)

Use the adapter to map any repo’s documentation into L0–L5 summaries without changing original files.

1. Generate a suggested mapping:
   - `python scripts/map_architecture.py --suggest`
2. Review/edit `plan.map.yml`
3. Generate summaries into `.plan/`:
   - `python scripts/map_architecture.py --apply`

Outputs:

- `.plan/L0-problem-framing.md`
- `.plan/L1-meta-architecture.md`
- `.plan/L2-system-architecture.md`
- `.plan/L3-component-design.md`
- `.plan/L4-implementation.md`
- `.plan/L5-operability-readiness.md`

## Validation and Linting

- Validate a layer (soft gate):
  - `python scripts/validate_layer.py L0`
  - `python scripts/validate_layer.py L1`
  - `python scripts/validate_layer.py L2`
  - `python scripts/validate_layer.py L3`
  - `python scripts/validate_layer.py L4`
  - `python scripts/validate_layer.py L5`
- Lint architecture markdown:
  - `python scripts/lint_architecture.py .`
- Check dependency cycles:
  - `python scripts/dependency_graph.py --check --path .plan`

## Requirements

- Python 3
- PyYAML for YAML-based scripts:
  - `pip install pyyaml`

## Agent Usage Tips

- Keep the agent’s context scoped to the current layer plus the parent summary.
- Use the adapter to normalize legacy docs before validating.
- Run validations in build/accept-edits modes if plan modes block file writes.

## Contributing

Issues and PRs welcome. Keep changes small, agent-friendly, and consistent with the layered schema.

## License

Add a LICENSE file before publishing if you want to allow reuse.
