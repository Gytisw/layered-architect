#!/usr/bin/env python3
"""
Initialize a layered architecture project structure.

Usage:
    python init_architecture.py <project_name>
"""

import os
import sys
from pathlib import Path

from log_utils import init_logger

def print_usage():
    print("Usage: python init_architecture.py <project_name>")
    print("\nInitialize a layered architecture project with plan files.")
    sys.exit(1)


def create_directory_structure(project_name: str) -> Path:
    plan_dir = Path(project_name) / ".plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    return plan_dir


def create_l1_meta_architecture(plan_dir: Path):
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


def create_l2_system_architecture(plan_dir: Path):
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


def create_l3_component_design(plan_dir: Path):
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

## Decision Log
1. **Decision**: [Short statement]
   - **Rationale**: [Why]
   - **Impact**: [What it affects downstream]
"""
    (plan_dir / "L3-component-design.md").write_text(content)


def create_l4_implementation(plan_dir: Path):
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


def main():
    logger = init_logger("init_architecture")
    if len(sys.argv) < 2:
        print("Error: Project name is required.", file=sys.stderr)
        logger.log("error", "usage", "Missing project name")
        print_usage()

    project_name = sys.argv[1]
    if not project_name or not project_name.strip():
        print("Error: Project name cannot be empty.", file=sys.stderr)
        logger.log("error", "usage", "Empty project name")
        print_usage()

    try:
        plan_dir = create_directory_structure(project_name)
        create_l1_meta_architecture(plan_dir)
        create_l2_system_architecture(plan_dir)
        create_l3_component_design(plan_dir)
        create_l4_implementation(plan_dir)
        create_constraints_yml(plan_dir)
        create_checkpoint_yml(plan_dir)

        print(f"✓ Created layered architecture project: {project_name}")
        print(f"✓ Plan files created in: {plan_dir}")
        logger.log(
            "info",
            "init_complete",
            "Architecture plan initialized",
            {"project": project_name, "plan_dir": str(plan_dir)},
        )
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.log("error", "init_failed", "Initialization failed", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
