---
name: layered-architect
description: Guide for planning complex software architectures using a 4-layer hierarchical approach. Use when designing system architecture, planning technical structure, creating design documents, or reviewing existing architectures. Helps prevent context exhaustion and hallucination by breaking architecture into manageable layers with validation gates.
---

# Layered Architecture Planning

## Overview

Layered architecture planning helps AI agents design complex software systems without hitting context limits or hallucinating. It breaks architecture into four manageable layers with validation gates between them.

## When to Use This Skill

Use this skill when you need to:
- Design the architecture for a complex system
- Plan the system structure for a new service
- Create technical design documentation
- Architecture review of an existing system
- Design document for a complex feature

## The 4-Layer Framework

### L1: Meta-Architecture
Define vision, constraints, principles, and success criteria.

**Content:**
- Vision and Goals (1-2 sentences)
- Constraints (5-7 maximum, specific and testable)
- Principles (3-5 maximum, actionable)
- Success Criteria (measurable targets)
- Decision Log (key decisions + rationale)
- Risk Register (top risks with mitigation)

### L2: System Architecture  
Define subsystems, boundaries, data flow, and interfaces.

**Content:**
- Subsystem Inventory
- Boundary Definitions
- Data Flow Diagrams
- Interface Contracts
- Migration Strategy (if legacy systems exist)
- Tradeoff Matrix
- Decision Log
- Constraint inheritance from L1

### L3: Component Design
Define modules, APIs, dependencies, and contracts.

**Content:**
- Module Specifications
- API Contracts
- Dependency Graph
- Implementation Notes
- Decision Log

**Dependency Graph (Required):**
Maintain `.plan/dependencies.yml` and mark `status: complete` before proceeding to L4.
Use `python scripts/validate_dependencies.py --path .plan` to validate.

### L4: Implementation
Define code structure, patterns, and file organization.

**Content:**
- File Structure
- Code Patterns
- Implementation Details
- Validation Commands
- Decision Log

## Optional Layers (L0/L5)

Use optional layers only when triggers apply to avoid bloat:

- **L0 Problem Framing (Optional):** Use when requirements are unclear, scope is fuzzy, or goals conflict. If skipped, record a short skip reason.
- **L5 Operability & Readiness (Optional):** Use when moving toward delivery or when reliability, security, or cost require explicit readiness checks. If skipped, record a short skip reason.

**Agent Gate:** Ask explicit yes/no trigger questions before L1 and after L4.
If you skip L0/L5, add a one-line skip reason near the top of L1/L4 or in `checkpoint.yml`.

## Guided Questioning (Agent Flow)

At the start, ask the user:
- Do you want **strict** validation (fail on warnings) or **soft** validation (warn only)?
- Do you want **minimal** or **thorough** questioning?

Question sets by layer live in: `references/question-guide.md`.

Default behavior: validation is **strict** unless the user opts into soft mode.

Optional domain-specific prompts: `references/domain-profiles.md`.

**Interactive requirement:** If the platform supports a Question tool, use it
for discrete choices and do not proceed to a new layer until the user has
provided specific, quantified answers (no vague "fast/secure/scalable").
Avoid "All of the above" or catch-all answers in required questions.

**Completion criteria:** See `references/layer-guide.md` for "definition of done"
guidance per layer.

Interactive decision trees: `references/interactive-questions.md`.

Agent workflow guide: `references/agent-usage-guide.md`.

## Dependency Preflight

Before using scripts, run:
- `python scripts/check_deps.py`

If missing deps are reported, install:
- `pip install -r requirements.txt` or `uv pip install -r requirements.txt`

## Guided Start (Fresh vs Existing Docs)

If the project status is unclear, run:
- `python scripts/start_arch.py`

## PRD Stage (Post-Architecture)

After L1–L4 (and L5 if used) are finalized, generate a PRD aligned to the architecture using:
- `assets/template-prd.md`

## Agent Usage (L0/L5)

If L0 or L5 triggers apply, use the templates in:
- `assets/template-l0-problem-framing.md`
- `assets/template-l5-operability-readiness.md`

## Optional Adapter (Universal Mapping)

To adapt existing documentation into L0–L5 without changing the original structure:

1. Generate a mapping: `python scripts/map_architecture.py --suggest`
2. Review/edit `plan.map.yml`
3. Generate summaries: `python scripts/map_architecture.py --apply`

If `.plan/constraints.yml` is missing, the adapter will generate a stub registry
from any `CON-###` references found in mapped sources.

Mapping schema reference: `schemas/plan-map.schema.json`

## Platform Notes (Plan/Permission Modes)

- **OpenCode Plan Mode:** File writes and command execution may be restricted. Run the mapping step in a mode that allows `python scripts/map_architecture.py` and writing to `.plan/` (or redirect output to an allowed path).
- **Claude Code Plan Mode:** If plan mode is enabled, allow the Bash command for `python scripts/map_architecture.py` and permit writes to `.plan/**` in `.claude/settings.json`.

## Quick Start

Preferred (unified CLI):
```bash
python scripts/arch.py doctor
python scripts/arch.py init --path .
python scripts/arch.py validate --path .plan --auto-constraints --auto-deps
```

Direct scripts:

1. **Initialize planning:**
   ```bash
   # In current repo
   python scripts/init_architecture.py --path .

   # Or create a new folder
   python scripts/init_architecture.py "my-project"
   ```

2. **Work through layers sequentially:**
   - Edit `L1-meta-architecture.md`
   - Run `python scripts/validate_layer.py L1`
   - Edit `L2-system-architecture.md`
   - Run `python scripts/validate_layer.py L2`
   - Continue through L3 and L4

3. **Validate constraints:**
   ```bash
   python scripts/check_constraints.py
   ```

   If L1 constraints are in markdown only:
   ```bash
   python scripts/extract_constraints.py .plan/L1-meta-architecture.md
   ```

4. **Save progress:**
   ```bash
   python scripts/checkpoint_manager.py save
   ```

Agent-friendly alternative:
```bash
python scripts/validate_all.py --path .plan --format json
```

Minimal agent quickstart:
`references/agent-quickstart.md`

Auto-sync constraints when registry is empty:
```bash
python scripts/validate_all.py --path .plan --auto-constraints
```

Auto-create dependency stub if missing:
```bash
python scripts/validate_all.py --path .plan --auto-deps
```

## Layer Isolation Protocol

**Critical Rule:** Only the current layer and parent summary are loaded into context.

- When working on L2: Load L2 + L1 summary
- When working on L3: Load L3 + L2 summary
- Never load full architecture at once

This prevents context exhaustion and maintains coherence.

## Validation Gates

Soft gates between layers provide warnings without blocking:

- **L1→L2 Gate:** Check constraints are specific, principles are actionable
- **L2→L3 Gate:** Check system boundaries are closed, interfaces are defined
- **L3→L4 Gate:** Check dependencies form DAG, interfaces have signatures
- **Dependency Graph Gate:** `.plan/dependencies.yml` must exist and have `status: complete`

See [references/validation-patterns.md](references/validation-patterns.md) for detailed criteria.

## Semantic Cross-Layer Validation (Subagents)

After scripted validation, run sharded semantic checks using subagents to
compare adjacent layers. Guidance and required report schema:
`references/semantic-validation.md`.

## Constraint Registry

Track architectural constraints in `constraints.yml`:

```yaml
constraints:
  - id: CON-001
    layer: L1
    text: "System must support 10,000 concurrent users"
    type: performance
    validates_against: [L2-subsystem-capacity, L3-module-scaling]
```

See [references/constraint-examples.md](references/constraint-examples.md) for examples.

If constraints exist only in L1 markdown, extract them with:
`python scripts/extract_constraints.py .plan/L1-meta-architecture.md`

## Dependency Graph

Create and maintain `.plan/dependencies.yml` as the canonical dependency graph.
Validation is gated on `status: complete` and an acyclic graph.

## Resources

- **Detailed Layer Guide:** [references/layer-guide.md](references/layer-guide.md)
- **Validation Patterns:** [references/validation-patterns.md](references/validation-patterns.md)
- **Constraint Examples:** [references/constraint-examples.md](references/constraint-examples.md)
- **Scripts:** [scripts/](scripts/) - Validation and utility scripts
- **Templates:** [assets/](assets/) - Example architectures

## Cross-Platform Compatibility

This skill is designed as a **Universal Package** that works across multiple agentic coding platforms.

## Best Practices

1. **Limit constraints** to 5-7 per layer
2. **Make constraints specific** - "API latency < 200ms" not "API should be fast"
3. **Checkpoint after each layer** - Never lose progress
4. **Validate constraints** - Run check_constraints.py regularly
5. **Use soft gates** - Warnings provide visibility without blocking exploration
6. **Share across teams** - The Universal Package works with any agent, enabling consistent architecture practices across your organization
