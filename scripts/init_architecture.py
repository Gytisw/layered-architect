#!/usr/bin/env python3
"""
Initialize a layered architecture project structure.

Usage:
    python init_architecture.py <project_name>
    python init_architecture.py --path /path/to/project
    python init_architecture.py --here
"""

import argparse
import sys
from pathlib import Path

from log_utils import init_logger


def create_directory_structure(project_root: str | Path) -> Path:
    root = Path(project_root)
    if root.name == ".plan":
        plan_dir = root
    else:
        plan_dir = root / ".plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    return plan_dir


def create_l1_meta_architecture(plan_dir: Path, profile: str = "blank"):
    if profile == "agent-ai":
        content = """# Meta-Architecture

## Vision
Build an agent workflow architecture that is measurable, testable, and easy to evolve with clear operational boundaries.

## Constraints
- [ ] CON-001: p95 API latency target is defined and measurable.
- [ ] CON-002: Throughput target is defined for expected peak load.
- [ ] CON-003: Data handling and retention requirements are explicit.

## Principles
1. Decisions must be traceable to explicit constraints.
2. Architecture should optimize for observability and operability.
3. External dependencies require fresh research evidence.

## Success Criteria
- Architecture passes strict validation with zero warnings.
- Constraints are traceable from L1 through L4.

## Decision Log
1. **Decision**: Start with a layered architecture workflow.
   - **Rationale**: Reduces architectural drift and undocumented assumptions.
   - **Impact**: All downstream layers must preserve traceability.

## Risk Register
1. **Risk**: Scope ambiguity causes unstable architecture decisions.
   - **Severity**: High
   - **Mitigation**: Trigger L0 when ambiguity markers are present.
   - **Owner**: Architecture lead
"""
    else:
        content = """# Meta-Architecture

## Vision
[Describe the system's purpose in 1-2 sentences]

## Constraints
- [ ] CON-001: [Specific, testable constraint]
- [ ] CON-002: [Specific, testable constraint]

## Principles
1. [Actionable principle]
2. [Actionable principle]

## Success Criteria
- [Measurable target with metric]
- [Measurable target with metric]

## Decision Log
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]

## Risk Register
1. **Risk**: [Description]
   - **Severity**: [Low/Medium/High]
   - **Mitigation**: [Action]
   - **Owner**: [Role/Team]
"""
    (plan_dir / "L1-meta-architecture.md").write_text(content)


def create_l2_system_architecture(plan_dir: Path, profile: str = "blank"):
    if profile == "agent-ai":
        content = """# System Architecture

## Overview
Define subsystems, boundaries, and interfaces with explicit mapping to L1 constraints.

## Subsystems
- **Ingestion**: Receives and validates events.
- **Storage**: Persists events and metadata.
- **Query**: Serves analytical and operational queries.

## Boundaries
Define ownership boundaries and what each subsystem explicitly does not own.

## Data Flow
Describe write path and read path separately.

## Interfaces
List API contracts, auth model, and SLA expectations.

## External Dependencies
- [Dependency]: [Purpose, version, and research evidence reference]

## Migration Strategy
[If legacy systems exist, outline migration approach]

## Tradeoff Matrix
| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| A | | | |
| B | | | |

## Decision Log
1. **Decision**: Keep write and read paths explicit.
   - **Rationale**: Prevent hidden coupling and performance regressions.
   - **Impact**: L3 must mirror boundary ownership.
"""
    else:
        content = """# System Architecture

## Overview
[High-level description of the system]

## Subsystems
- **Subsystem A**: [Purpose and responsibility]
- **Subsystem B**: [Purpose and responsibility]

## Boundaries
[Boundary definitions and ownership]

## Data Flow
[Description of how data moves through the system]

## Interfaces
[APIs, protocols, or interfaces the system exposes]

## External Dependencies
- [Dependency 1]: [Purpose and version constraint]
- [Dependency 2]: [Purpose and version constraint]

## Migration Strategy
[If legacy systems exist, outline migration approach]

## Tradeoff Matrix
| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| A | | | |
| B | | | |

## Decision Log
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]
"""
    (plan_dir / "L2-system-architecture.md").write_text(content)


def create_l3_component_design(plan_dir: Path, profile: str = "blank"):
    if profile == "agent-ai":
        content = """# Component Design

## Modules

### Ingestion Module

#### Responsibilities
- Validate and normalize incoming events
- Enforce auth and rate-limit policies

#### Public Interface
```python
class IngestionModule:
    def method_name(self, param: Type) -> ReturnType:
        \"\"\"Interface contract with explicit error behavior.\"\"\"
        pass
```

#### Internal Structure
[Describe internal classes and failure handling strategy]

### Query Module

#### Responsibilities
- Translate request-level queries to storage contracts
- Return bounded and measurable responses

#### Public Interface
```python
class QueryModule:
    def method_name(self, param: Type) -> ReturnType:
        \"\"\"Interface contract with strict validation guarantees.\"\"\"
        pass
```

## API Contracts
- [Endpoint or method signature + error conditions]

## Dependencies
- Component A depends on [Component B]
- Canonical graph lives in `.plan/dependencies.yml`

## Decision Log
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]
"""
    else:
        content = """# Component Design

## Modules

### Component A

#### Responsibilities
- [Responsibility 1]
- [Responsibility 2]

#### Public Interface
```python
class ComponentA:
    def method_name(self, param: Type) -> ReturnType:
        \"\"\"[Docstring description]\"\"\"
        pass
```

#### Internal Structure
[Description of internal classes/modules]

### Component B

#### Responsibilities
- [Responsibility 1]
- [Responsibility 2]

#### Public Interface
```python
class ComponentB:
    def method_name(self, param: Type) -> ReturnType:
        \"\"\"[Docstring description]\"\"\"
        pass
```

## API Contracts
- [Endpoint or method signature + error conditions]

## Dependencies
- Component A depends on [Component B]
- Canonical graph lives in `.plan/dependencies.yml`

## Decision Log
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]
"""
    (plan_dir / "L3-component-design.md").write_text(content)


def create_l4_implementation(plan_dir: Path, profile: str = "blank"):
    if profile == "agent-ai":
        content = """# Implementation

## File Structure
```
project/
├── .plan/
├── services/
│   ├── ingestion/
│   ├── storage/
│   └── query/
├── sdk/
└── tests/
```

## Code Patterns
- Explicit boundary ownership per subsystem
- Deterministic validation gates before progression

## Implementation Details
- Include reliability and failure-mode handling for each module

## Validation Commands
```bash
python scripts/arch.py status --path .plan
python scripts/arch.py validate --path .plan --strict
```

## Implementation Order
1. [ ] [First task to implement]
2. [ ] [Second task to implement]
3. [ ] [Third task to implement]

## Testing Strategy
- Unit tests: [Coverage target and approach]
- Integration tests: [Approach and scope]

## Build & Deployment
[Instructions for building and deploying]

## Decision Log
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]
"""
    else:
        content = """# Implementation

## File Structure
```
project/
├── src/
│   ├── __init__.py
│   ├── module_a.py
│   └── module_b.py
├── tests/
│   ├── __init__.py
│   ├── test_module_a.py
│   └── test_module_b.py
└── requirements.txt
```

## Code Patterns
- [Pattern 1] (e.g., Repository, CQRS, Hexagonal)
- [Pattern 2]

## Implementation Details
- [Key implementation notes, constraints, or performance considerations]

## Validation Commands
```bash
# Example: unit tests, lint, validation scripts
```

## Implementation Order
1. [ ] [First task to implement]
2. [ ] [Second task to implement]
3. [ ] [Third task to implement]

## Testing Strategy
- Unit tests: [Coverage target and approach]
- Integration tests: [Approach and scope]

## Build & Deployment
[Instructions for building and deploying]

## Decision Log
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]
"""
    (plan_dir / "L4-implementation.md").write_text(content)


def create_constraints_yml(plan_dir: Path):
    content = """constraints: []
version: "1.0.0"
"""
    (plan_dir / "constraints.yml").write_text(content)


def create_checkpoint_yml(plan_dir: Path):
    content = """current_layer: null
last_completed: null
validation_status: {}
"""
    (plan_dir / "checkpoint.yml").write_text(content)


def create_gates_yml(plan_dir: Path, mode: str = "strict", question_depth: str = "minimal"):
    content = f"""mode: {mode}
question_depth: {question_depth}
l0_required: false
l5_required: false
research_required: false
research_approved: false
research_approval_receipt: null
research_approved_by: null
research_approved_at: null
semantic_required: true
semantic_completed: false
semantic_completion_receipt: null
semantic_completed_by: null
semantic_completed_at: null
dependencies_complete: false
constraints_registry_present: false
last_validation_report: null
last_step: init
"""
    (plan_dir / "gates.yml").write_text(content)


def create_dependencies_yml(plan_dir: Path):
    content = """version: "1.0.0"
status: draft
nodes:
  - name: component_a
  - name: component_b
edges:
  - from: component_a
    to: component_b
constraints:
  acyclic: true
notes: ""
"""
    (plan_dir / "dependencies.yml").write_text(content)


def create_support_dirs(plan_dir: Path):
    (plan_dir / "decisions").mkdir(parents=True, exist_ok=True)
    (plan_dir / "diagrams").mkdir(parents=True, exist_ok=True)


def main():
    logger = init_logger("init_architecture")
    parser = argparse.ArgumentParser(
        description="Initialize layered architecture plan files."
    )
    parser.add_argument(
        "project",
        nargs="?",
        help="Project name or path (creates a new directory).",
    )
    parser.add_argument(
        "--path",
        help="Path to an existing project root or .plan directory.",
    )
    parser.add_argument(
        "--here",
        action="store_true",
        help="Initialize .plan in the current directory.",
    )
    parser.add_argument(
        "--profile",
        default="agent-ai",
        choices=["agent-ai", "blank"],
        help="Template profile to seed architecture files.",
    )
    parser.add_argument(
        "--mode",
        default="strict",
        choices=["strict", "soft"],
        help="Validation mode to seed in gates.yml.",
    )
    parser.add_argument(
        "--question-depth",
        default="minimal",
        choices=["minimal", "thorough"],
        help="Question depth to seed in gates.yml.",
    )
    args = parser.parse_args()

    if args.here and args.path:
        print("Error: --here and --path cannot be used together.", file=sys.stderr)
        logger.log("error", "usage", "Conflicting flags: --here and --path")
        sys.exit(1)

    if args.here:
        project_root = Path(".").resolve()
    elif args.path:
        project_root = Path(args.path).expanduser().resolve()
    elif args.project and args.project.strip():
        project_root = Path(args.project).expanduser().resolve()
        cwd = Path(".").resolve()
        if project_root.parent == cwd and project_root.name == cwd.name:
            print(
                "Note: You appear to be inside a project with the same name. "
                "Use --path . to initialize in the current directory and avoid nesting."
            )
    else:
        print("Error: Project name or --path is required.", file=sys.stderr)
        logger.log("error", "usage", "Missing project name/path")
        parser.print_usage()
        sys.exit(1)

    try:
        plan_dir = create_directory_structure(project_root)
        profile = args.profile
        create_l1_meta_architecture(plan_dir, profile=profile)
        create_l2_system_architecture(plan_dir, profile=profile)
        create_l3_component_design(plan_dir, profile=profile)
        create_l4_implementation(plan_dir, profile=profile)
        create_constraints_yml(plan_dir)
        create_checkpoint_yml(plan_dir)
        create_gates_yml(plan_dir, mode=args.mode, question_depth=args.question_depth)
        create_dependencies_yml(plan_dir)
        create_support_dirs(plan_dir)

        project_label = project_root.name if project_root.name != ".plan" else project_root.parent.name
        print(f"✓ Created layered architecture project: {project_label}")
        print(f"✓ Plan files created in: {plan_dir}")
        logger.log(
            "info",
            "init_complete",
            "Architecture plan initialized",
            {"project": str(project_root), "plan_dir": str(plan_dir)},
        )
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.log("error", "init_failed", "Initialization failed", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
