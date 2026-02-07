# Agent Quickstart (Minimal)

Use the unified CLI to minimize context overhead:

1. Detect next step:
   `python scripts/arch.py doctor --json`

2. Initialize if needed:
   `python scripts/arch.py init --path .`

3. Validate in one shot:
   `python scripts/arch.py validate --path .plan --auto-constraints --auto-deps`

4. Finalize dependency graph:
   Edit `.plan/dependencies.yml` and set `status: complete`, then:
   `python scripts/arch.py deps --path .plan`

5. Run semantic cross-layer validation:
   See `references/semantic-validation.md`
