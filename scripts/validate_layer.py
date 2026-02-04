#!/usr/bin/env python3
"""
Layer validation script for layered architecture.
Implements SOFT gates - warnings only, returns 0 even with issues.
"""

import sys
import re
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

LAYER_REQUIREMENTS = {
    "L0": {
        "file": "L0-problem-framing.md",
        "yaml_required": True,
        "yaml_required_keys": [
            "layer",
            "title",
            "goals",
            "non_goals",
            "stakeholders",
            "assumptions",
            "open_questions",
            "success_criteria_draft",
            "decision_readiness",
        ],
    },
    "L1": {
        "file": "01-Vision.md",
        "sections": ["Vision", "Constraints", "Principles", "Success Criteria"],
        "min_constraints": 3,
        "max_constraints": 7,
    },
    "L2": {
        "file": "02-Architecture.md",
        "sections": ["Subsystems", "Boundaries", "Data Flow", "Interfaces"],
    },
    "L3": {
        "file": "03-Components.md",
        "sections": ["Modules", "API Contracts", "Dependencies"],
    },
    "L4": {
        "file": "04-Implementation.md",
        "sections": ["File Structure", "Code Patterns"],
    },
    "L5": {
        "file": "L5-operability-readiness.md",
        "yaml_required": True,
        "yaml_required_keys": [
            "layer",
            "title",
            "slos",
            "observability",
            "security_controls",
            "deployment",
            "data_protection",
            "cost_guardrails",
            "readiness_checks",
            "readiness_status",
            "residual_risks",
        ],
    },
}


def get_arch_dir():
    """Get the architecture directory path."""
    script_dir = Path(__file__).parent

    if script_dir.name == "scripts":
        arch_dir = script_dir.parent / "architecture"
    else:
        arch_dir = script_dir / "architecture"

    return arch_dir


def find_layer_file(arch_dir, layer):
    """Find the markdown file for a given layer."""
    if layer not in LAYER_REQUIREMENTS:
        return None

    file_path = arch_dir / LAYER_REQUIREMENTS[layer]["file"]

    if file_path.exists():
        return file_path

    patterns = [
        f"{layer}*.md",
        f"*{layer}*.md",
        f"{layer.lower()}*.md",
    ]

    for pattern in patterns:
        matches = list(arch_dir.glob(pattern))
        if matches:
            return matches[0]

    return None


def parse_sections(file_path):
    """Extract sections from a markdown file."""
    sections_found = {}

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    header_pattern = r"^#{2,4}\s+(.+)$"

    for line in content.split("\n"):
        match = re.match(header_pattern, line.strip())
        if match:
            section_name = match.group(1).strip()
            sections_found[section_name] = True

    return sections_found, content


def count_constraints(content):
    """Count constraints in L1 content."""
    patterns = [
        r"(?:^|\n)\s*[-*]\s+(?:Constraint:)?\s*[^\n]+",
        r"(?:^|\n)\s*\d+\.\s+(?:Constraint:)?\s*[^\n]+",
    ]

    total = 0
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        total += len(matches)

    return total


def check_previous_layer_complete(arch_dir, current_layer):
    """Check if previous layer is complete."""
    layer_order = ["L1", "L2", "L3", "L4"]

    try:
        current_idx = layer_order.index(current_layer)
    except ValueError:
        if current_layer == "L5":
            prev_file = find_layer_file(arch_dir, "L4")
            return prev_file is not None
        return None

    if current_idx == 0:
        return None

    prev_layer = layer_order[current_idx - 1]
    prev_file = find_layer_file(arch_dir, prev_layer)

    return prev_file is not None


def validate_layer(arch_dir, layer):
    """Validate a specific layer and return list of issues."""
    warnings = []

    if layer not in LAYER_REQUIREMENTS:
        print(f"✗ ERROR: Unknown layer '{layer}'")
        print(f"  Valid layers: {', '.join(LAYER_REQUIREMENTS.keys())}")
        return None

    file_path = find_layer_file(arch_dir, layer)

    if not file_path:
        print(f"✗ ERROR: Layer {layer} file not found")
        print(f"  Expected: {LAYER_REQUIREMENTS[layer]['file']}")
        print(f"  in: {arch_dir}")
        return None

    print(f"Validating {layer}...")
    print(f"  File: {file_path}")
    print()

    prev_complete = check_previous_layer_complete(arch_dir, layer)
    if prev_complete is not None:
        if prev_complete:
            print("✓ Previous layer complete")
        else:
            print("⚠ WARNING: Previous layer not found (validation may be incomplete)")
            warnings.append("Previous layer incomplete")

    requirements = LAYER_REQUIREMENTS[layer]
    if requirements.get("yaml_required"):
        if yaml is None:
            print("✗ ERROR: PyYAML required for YAML validation")
            print("  Install with: pip install pyyaml")
            return None

        content = file_path.read_text(encoding="utf-8")
        yaml_match = re.search(r"```yaml\\s*(.*?)```", content, re.DOTALL)
        if not yaml_match:
            print("⚠ WARNING: YAML block not found")
            warnings.append("YAML block not found")
        else:
            try:
                data = yaml.safe_load(yaml_match.group(1))
                if not isinstance(data, dict):
                    print("⚠ WARNING: YAML block did not parse as an object")
                    warnings.append("YAML block invalid")
                else:
                    if data.get("layer") != layer:
                        print(
                            f"⚠ WARNING: YAML layer '{data.get('layer')}' does not match {layer}"
                        )
                        warnings.append("YAML layer mismatch")
                    for key in requirements.get("yaml_required_keys", []):
                        if key not in data:
                            print(f"⚠ WARNING: Missing YAML field: {key}")
                            warnings.append(f"Missing YAML field: {key}")
            except Exception as e:
                print(f"⚠ WARNING: YAML parse error: {e}")
                warnings.append("YAML parse error")
    else:
        sections_found, content = parse_sections(file_path)
        for section in requirements["sections"]:
            found = any(
                section.lower() == s.lower() or section in s for s in sections_found.keys()
            )

            if found:
                print(f"✓ {section} section found")
            else:
                print(f"⚠ WARNING: {section} section not found")
                warnings.append(f"Missing {section} section")

    if layer == "L1":
        constraint_count = count_constraints(content)
        min_req = requirements.get("min_constraints", 3)
        max_req = requirements.get("max_constraints", 7)

        if constraint_count < min_req:
            print(
                f"⚠ WARNING: Only {constraint_count} constraints found (recommend {min_req}-{max_req})"
            )
            warnings.append(f"Too few constraints ({constraint_count})")
        elif constraint_count > max_req:
            print(
                f"⚠ WARNING: {constraint_count} constraints found (recommend {min_req}-{max_req})"
            )
            warnings.append(f"Too many constraints ({constraint_count})")
        else:
            print(f"✓ Constraint count in recommended range ({constraint_count})")

    print()

    if warnings:
        print(f"✓ Validation complete - {len(warnings)} warning(s)")
    else:
        print("✓ Validation complete - no issues found")

    return warnings


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: validate_layer.py <L0|L1|L2|L3|L4|L5>")
        print()
        print("Validates a specified layer in the layered architecture.")
        print("Returns exit code 0 even with warnings (soft gate behavior).")
        print()
        print("Examples:")
        print("  python validate_layer.py L1")
        print("  python validate_layer.py L2")
        print("  python validate_layer.py L0")
        print("  python validate_layer.py L5")
        sys.exit(1)

    layer = sys.argv[1].upper()
    arch_dir = get_arch_dir()

    if not arch_dir.exists():
        print(f"✗ ERROR: Architecture directory not found: {arch_dir}")
        print()
        print("Expected structure:")
        print("  layered-architect/")
        print("    architecture/")
        print("      01-Vision.md")
        print("      02-Architecture.md")
        print("      03-Components.md")
        print("      04-Implementation.md")
        print("    scripts/")
        print("      validate_layer.py")
        sys.exit(2)

    result = validate_layer(arch_dir, layer)

    if result is None:
        sys.exit(3)

    sys.exit(0)


if __name__ == "__main__":
    main()
