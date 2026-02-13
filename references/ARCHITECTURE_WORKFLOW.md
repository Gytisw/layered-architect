# Architecture Workflow (Canonical)

**STRICT MODE: DO NOT PROCEED WITH WARNINGS OR ERRORS.**  
**FOLLOW THE STAGING SEQUENCE. DO NOT SKIP GATES.**  
**DO NOT MANUALLY EDIT `.plan/gates.yml`. USE `arch.py` GATE COMMANDS ONLY.**
**AFTER EVERY FILE WRITE/EDIT: RUN `arch.py status` THEN `arch.py next`.**
**DO NOT START THE NEXT LAYER UNTIL THE CURRENT BLOCKER IS RESOLVED.**

This is the only accepted workflow for agents.

## Tool Limits

- Claude Code AskUserQuestion: 1–4 questions per call, 2–4 options each.

## Unified CLI Only

Use only:
- `python scripts/arch.py ...`

Do not run legacy scripts directly in agent workflow.

## Required Artifacts

- `.plan/gates.yml`
- `.plan/constraints.yml`
- `.plan/dependencies.yml`
- `.plan/research.md` (when research required)
- `.plan/research.evidence.json` (when research required)
- `.plan/semantic-validation.md|json`

## Golden Sequence

1. Detect state
```bash
python scripts/arch.py doctor --path .
```

2. Initialize (profile defaults to `agent-ai`)
```bash
python scripts/arch.py init --path . --mode <strict|soft> --question-depth <minimal|thorough>
```

3. Draft layers in order (L0/L1/L2/L3/L4/L5 as required)

Before drafting each layer:
```bash
python scripts/arch.py stage enter --path .plan --layer <L0|L1|L2|L3|L4|L5>
```

4. After each file edit
```bash
python scripts/arch.py status --path .plan
python scripts/arch.py next --path .plan
```

5. Validate before progression
```bash
python scripts/arch.py validate --path .plan --strict
```

6. If research required (auto-triggered by external deps markers)
- Create:
  - `.plan/research.md`
  - `.plan/research.evidence.json`
- Evidence must include claim-to-source mapping, retrieval timestamps, and executor metadata.
- Memory-only summaries are invalid evidence in strict mode.
- Approve:
```bash
python scripts/arch.py research approve --path .plan --approved-by <name> --confirm-user-approval
```

7. Dependency gate (must be complete)
```bash
python scripts/arch.py deps --path .plan --strict
```

8. Semantic gate (required)
```bash
python scripts/arch.py semantic scaffold --path .plan
# run one validator/subagent per required shard
python scripts/arch.py semantic aggregate --path .plan
python scripts/arch.py semantic validate --path .plan --strict
python scripts/arch.py semantic complete --path .plan --completed-by <name>
```
- If task/subagent fanout is available, semantic report must include one executor per required shard.

9. Final validation + gate sync
```bash
python scripts/arch.py validate --path .plan --strict --format json > .plan/last-validation.json
python scripts/arch.py gate sync --path .plan --from .plan/last-validation.json
```

## Gate Authority Rules

- `research_approved` must be set only via `arch.py research approve`.
- `semantic_completed` must be set only via `arch.py semantic complete`.
- Derived fields are synced only via `arch.py gate sync`.
- Manual edits to these fields are treated as invalid receipt state and block strict progression.

## Completion Rule

Architecture is complete only when:
- strict validation is PASS,
- blocking findings are zero,
- semantic completion receipt exists,
- research evidence is approved when required,
- validation stamp is fresh.
