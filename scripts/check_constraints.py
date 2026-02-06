#!/usr/bin/env python3
"""
Constraint Conflict Checker for Layered Architecture

Checks for constraint conflicts across all layers:
- Duplicate component/module names across layers
- Constraints mentioned in text but not in registry
- Circular references (A depends on B, B depends on A)
- Constraint count per layer (>7 warnings)
- Constraint contradictions (e.g., "fast" vs "simple")
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

from log_utils import init_logger

@dataclass
class Constraint:
    id: str
    name: str
    category: str
    priority: str
    conflicting: List[str] = field(default_factory=list)
    text: str = ""


@dataclass
class Component:
    name: str
    layer: str
    constraints: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class ConstraintChecker:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.constraints: Dict[str, Constraint] = {}
        self.components: Dict[str, List[Component]] = defaultdict(list)
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.layer_constraint_counts: Dict[str, int] = defaultdict(int)

    def load_constraints_registry(self) -> bool:
        """Load constraints.yml from .plan/ directory."""
        constraints_file = self.project_root / ".plan" / "constraints.yml"

        if not constraints_file.exists():
            self.errors.append(f"Constraints file not found: {constraints_file}")
            return False

        try:
            with open(constraints_file, "r") as f:
                data = yaml.safe_load(f)

            if not data or "constraints" not in data:
                self.errors.append("Invalid constraints file: no 'constraints' section")
                return False

            for item in data["constraints"]:
                if isinstance(item, str):
                    constraint = Constraint(
                        id=item,
                        name=item,
                        category="",
                        priority="",
                        conflicting=[],
                        text=item,
                    )
                    self.constraints[constraint.id] = constraint
                    continue
                if not isinstance(item, dict):
                    continue

                name = item.get("name") or item.get("text") or item.get("description") or ""
                constraint = Constraint(
                    id=item.get("id", ""),
                    name=name,
                    category=item.get("category") or item.get("type") or "",
                    priority=item.get("priority") or item.get("severity") or "",
                    conflicting=item.get("conflicting", []) if isinstance(item.get("conflicting", []), list) else [],
                    text=item.get("text", "") or name,
                )
                if constraint.id:
                    self.constraints[constraint.id] = constraint

            return True

        except yaml.YAMLError as e:
            self.errors.append(f"Failed to parse constraints.yml: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error loading constraints: {e}")
            return False

    def scan_layer_files(self) -> int:
        """Scan all L1-L4 markdown files for constraint references."""
        plan_dir = self.project_root / ".plan"
        files_scanned = 0

        layer_files = {
            "L1": plan_dir / "L1-meta-architecture.md",
            "L2": plan_dir / "L2-system-architecture.md",
            "L3": plan_dir / "L3-component-design.md",
            "L4": plan_dir / "L4-implementation.md",
        }

        for layer, layer_file in layer_files.items():
            if layer_file.exists():
                self._parse_layer_file(layer_file, layer)
                files_scanned += 1

        return files_scanned

    def _parse_layer_file(self, filepath: Path, layer: str) -> None:
        """Parse a single layer markdown file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Parse components (## headers)
            component_pattern = r"^##\s+(.+)$"
            components = re.findall(component_pattern, content, re.MULTILINE)

            for comp_name in components:
                component = Component(name=comp_name.strip(), layer=layer)
                self.components[comp_name.strip()].append(component)

            # Find constraint references (e.g., CON-001, CON-002)
            constraint_refs = re.findall(r"(CON-\d{3})", content)
            self.layer_constraint_counts[layer] += len(constraint_refs)

            # Add constraint refs to components
            for comp_name in components:
                # Find constraints mentioned near this component
                comp_section = self._extract_component_section(content, comp_name)
                if comp_section:
                    comp_constraints = re.findall(r"(CON-\d{3})", comp_section)
                    for comp_list in self.components[comp_name]:
                        if comp_list.layer == layer:
                            comp_list.constraints = list(set(comp_constraints))

                    # Parse dependencies
                    deps = self._extract_dependencies(comp_section)
                    for comp_list in self.components[comp_name]:
                        if comp_list.layer == layer:
                            comp_list.dependencies = deps

        except Exception as e:
            self.errors.append(f"Error parsing {filepath}: {e}")

    def _extract_component_section(
        self, content: str, component_name: str
    ) -> Optional[str]:
        """Extract the section for a specific component."""
        pattern = rf"##\s+{re.escape(component_name)}\s*\n(.*?)(?=##\s|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1) if match else None

    def _extract_dependencies(self, section: str) -> List[str]:
        """Extract dependencies mentioned in a component section."""
        deps = []

        # Look for dependency patterns
        dep_patterns = [
            r"[Dd]epends on[:\s]+([\w\s,]+)",
            r"[Rr]equires[:\s]+([\w\s,]+)",
            r"\*\*[Dd]ependencies\*\*:?\s*\n([\s\S]*?)(?=\n\n|\Z)",
        ]

        for pattern in dep_patterns:
            matches = re.findall(pattern, section)
            for match in matches:
                if isinstance(match, str):
                    # Split by commas and clean up
                    items = [d.strip() for d in re.split(r"[,\n]", match) if d.strip()]
                    deps.extend(items)

        return list(set(deps))

    def check_naming_collisions(self) -> None:
        """Detect duplicate component/module names across layers."""
        for name, instances in self.components.items():
            layers = set(comp.layer for comp in instances)
            if len(layers) > 1:
                layer_str = ", ".join(sorted(layers))
                self.warnings.append(f"Naming collision - '{name}' in {layer_str}")

    def check_undefined_constraints(self) -> None:
        """Detect constraints mentioned in text but not in registry."""
        # Get all referenced constraint IDs
        all_referenced = set()
        for name, instances in self.components.items():
            for comp in instances:
                all_referenced.update(comp.constraints)

        # Check against registry
        for ref_id in all_referenced:
            if ref_id not in self.constraints:
                self.warnings.append(f"Constraint {ref_id} referenced but not defined")

    def check_circular_dependencies(self) -> None:
        """Detect circular dependencies (basic check)."""
        # Build dependency graph
        graph = defaultdict(set)
        seen_pairs = set()

        for name, instances in self.components.items():
            for comp in instances:
                for dep in comp.dependencies:
                    graph[name].add(dep)

        # Check for simple cycles (A depends on B, B depends on A)
        for comp_a, deps_a in graph.items():
            for dep_b in deps_a:
                if dep_b in graph:
                    if comp_a in graph[dep_b]:
                        pair = tuple(sorted([comp_a, dep_b]))
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            self.warnings.append(
                                f"Circular dependency detected: {comp_a} ↔ {dep_b}"
                            )

    def check_constraint_count(self) -> None:
        """Check constraint count per layer (>7 warnings)."""
        for layer, count in self.layer_constraint_counts.items():
            if count > 7:
                self.warnings.append(f"Layer {layer} has {count} constraints (>7)")

    def check_contradictions(self) -> None:
        """Detect constraint contradictions (e.g., 'fast' vs 'simple')."""
        # Check for conflicting constraints on same component
        for name, instances in self.components.items():
            for comp in instances:
                constraint_ids = comp.constraints
                for i, id_a in enumerate(constraint_ids):
                    for id_b in constraint_ids[i + 1 :]:
                        if self._constraints_conflict(id_a, id_b):
                            self.warnings.append(
                                f"Contradiction in '{name}' ({comp.layer}): "
                                f"{id_a} conflicts with {id_b}"
                            )

    def _constraints_conflict(self, id_a: str, id_b: str) -> bool:
        """Check if two constraints conflict based on registry."""
        if id_a not in self.constraints or id_b not in self.constraints:
            return False

        constraint_a = self.constraints[id_a]
        constraint_b = self.constraints[id_b]

        # Check if they list each other as conflicting
        if id_b in constraint_a.conflicting or id_a in constraint_b.conflicting:
            return True

        # Known semantic contradictions
        semantic_conflicts = {
            ("fast", "simple"),
            ("secure", "fast"),
            ("scalable", "simple"),
            ("flexible", "strict"),
            ("generic", "specific"),
        }

        name_a = (constraint_a.name or constraint_a.text or "").lower()
        name_b = (constraint_b.name or constraint_b.text or "").lower()

        for conflict_a, conflict_b in semantic_conflicts:
            if (conflict_a in name_a and conflict_b in name_b) or (
                conflict_a in name_b and conflict_b in name_a
            ):
                return True

        return False

    def generate_report(self, files_scanned: int) -> str:
        """Generate the conflict report."""
        lines = ["Checking constraints..."]

        # Registry status
        if self.constraints:
            lines.append(f"✓ Registry loaded: {len(self.constraints)} constraints")
        else:
            lines.append("✗ Registry empty or not loaded")

        # Files scanned
        if files_scanned > 0:
            lines.append(f"✓ Scanned {files_scanned} layer files")
        else:
            lines.append("⚠ No layer files found")

        # Warnings
        for warning in self.warnings:
            lines.append(f"⚠ WARNING: {warning}")

        # Errors
        for error in self.errors:
            lines.append(f"✗ ERROR: {error}")

        # Summary
        if not self.warnings and not self.errors:
            lines.append("✓ All checks passed - no conflicts detected")
        else:
            lines.append(
                f"✓ Check complete - {len(self.warnings)} warning(s), {len(self.errors)} error(s)"
            )

        return "\n".join(lines)

    def run(self) -> str:
        """Run all checks and return report."""
        print("Checking constraints...")

        # Load registry
        if not self.load_constraints_registry():
            return self.generate_report(0)

        # Scan layer files
        files_scanned = self.scan_layer_files()

        # Run checks
        self.check_naming_collisions()
        self.check_undefined_constraints()
        self.check_circular_dependencies()
        self.check_constraint_count()
        self.check_contradictions()

        return self.generate_report(files_scanned)


def main():
    """Main entry point."""
    logger = init_logger("check_constraints")
    # Use current working directory as project root
    project_root = Path(".").resolve()

    checker = ConstraintChecker(project_root)
    report = checker.run()

    print(report)
    logger.log(
        "info",
        "constraint_check_complete",
        "Constraint check complete",
        {"warnings": len(checker.warnings), "errors": len(checker.errors)},
    )

    # Exit with error code if there are errors (not warnings)
    if checker.errors:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
