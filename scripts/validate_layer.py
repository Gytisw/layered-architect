#!/usr/bin/env python3
"""
Layer validation script for layered architecture.
Default behavior is STRICT (non-zero exit when warnings exist).
Use --soft to allow warnings without failure.
"""

import sys
import re
import os
import argparse
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from log_utils import init_logger
from path_utils import resolve_plan_dir
import validate_dependencies

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
            "decision_log",
        ],
    },
    "L1": {
        "file": "L1-meta-architecture.md",
        "sections": [
            "Vision",
            "Constraints",
            "Principles",
            "Success Criteria",
            "Decision Log",
            "Risk Register",
        ],
        "min_constraints": 3,
        "max_constraints": 20,
    },
    "L2": {
        "file": "L2-system-architecture.md",
        "sections": [
            "Subsystems",
            "Boundaries",
            "Data Flow",
            "Interfaces",
            "Migration Strategy",
            "Tradeoff Matrix",
            "Decision Log",
        ],
        "optional_sections": ["Migration Strategy"],
    },
    "L3": {
        "file": "L3-component-design.md",
        "sections": ["Modules", "API Contracts", "Dependencies", "Decision Log"],
    },
    "L4": {
        "file": "L4-implementation.md",
        "sections": [
            "File Structure",
            "Code Patterns",
            "Implementation Details",
            "Validation Commands",
            "Decision Log",
        ],
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
            "decision_log",
            "risk_register",
            "threat_model",
            "compliance_evidence",
        ],
    },
}

SECTION_ALIASES = {
    # L1
    "Vision": ["Vision & Goals", "Goals", "Problem Statement", "Overview"],
    "Constraints": ["Requirements", "Non-Functional Requirements", "Constraints & Requirements"],
    "Principles": ["Guiding Principles", "Design Principles"],
    "Success Criteria": ["Success Metrics", "Success Criteria & Metrics"],
    "Decision Log": ["Decisions", "Decision Records", "Architecture Decisions"],
    "Risk Register": ["Risk Assessment", "Risks", "Risk Log"],
    # L2
    "Subsystems": ["Subsystem Inventory", "Subsystem Overview", "Components"],
    "Boundaries": ["System Boundaries", "Boundary Definitions"],
    "Data Flow": ["Data Flow Diagrams", "Dataflow", "Data Flows"],
    "Interfaces": ["Interface Contracts", "Interface Definitions", "API Contracts"],
    "Migration Strategy": ["Migration Plan", "Migration"],
    "Tradeoff Matrix": ["Trade-Off Matrix", "Tradeoffs", "Trade-off Analysis", "Tradeoff Analysis"],
    # L3
    "Modules": ["Module Specifications", "Components"],
    "API Contracts": ["API Definitions", "Interface Contracts", "Interfaces"],
    "Dependencies": ["Dependency Graph", "Service Dependencies", "Module Dependencies"],
    # L4
    "File Structure": ["Project Structure", "Directory Structure"],
    "Code Patterns": ["Implementation Patterns", "Design Patterns"],
    "Implementation Details": ["Implementation Notes"],
    "Validation Commands": ["Validation", "Checks", "Quality Gates"],
}


def normalize_header(text: str) -> str:
    """Normalize header text for fuzzy matching."""
    cleaned = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    words = []
    for word in cleaned.split():
        if word.endswith("s") and len(word) > 3:
            word = word[:-1]
        words.append(word)
    return " ".join(words)


def section_variants(section: str) -> set[str]:
    variants = [section] + SECTION_ALIASES.get(section, [])
    return {normalize_header(v) for v in variants}


def get_arch_dir():
    """Get the default architecture directory path."""
    plan_dir = resolve_plan_dir(None)
    if plan_dir:
        return plan_dir
    return Path(".plan").resolve()


def resolve_arch_dir(path_arg):
    """Resolve architecture directory from a user-provided path."""
    return resolve_plan_dir(path_arg)


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


def extract_section_content(content: str, section_name: str) -> str:
    header_pattern = re.compile(r"^#{2,4}\s+(.+)$")
    variants = section_variants(section_name)
    in_section = False
    lines: list[str] = []
    for line in content.splitlines():
        match = header_pattern.match(line.strip())
        if match:
            title = match.group(1).strip()
            if normalize_header(title) in variants:
                in_section = True
                lines = []
                continue
            if in_section:
                break
        if in_section:
            lines.append(line)
    return "\n".join(lines).strip()


def count_constraints(content):
    """Count constraints in L1 content."""
    ids = re.findall(r"\bCON-\d{3,}\b", content, re.IGNORECASE)
    if ids:
        return len(set(ids))

    constraints_block = extract_section_content(content, "Constraints")
    if not constraints_block:
        constraints_block = content

    patterns = [
        r"(?:^|\n)\s*[-*]\s+(?:Constraint:)?\s*[^\n]+",
        r"(?:^|\n)\s*\d+\.\s+(?:Constraint:)?\s*[^\n]+",
    ]

    total = 0
    for pattern in patterns:
        matches = re.findall(pattern, constraints_block, re.IGNORECASE)
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


def validate_layer(arch_dir, layer, optional_missing_ok: bool = False):
    """Validate a specific layer and return list of issues."""
    warnings = []

    if layer not in LAYER_REQUIREMENTS:
        print(f"✗ ERROR: Unknown layer '{layer}'")
        print(f"  Valid layers: {', '.join(LAYER_REQUIREMENTS.keys())}")
        return None

    file_path = find_layer_file(arch_dir, layer)

    if not file_path:
        if optional_missing_ok and layer in {"L0", "L5"}:
            print(f"ℹ INFO: Optional layer {layer} file not found; skipping")
            return []
        print(f"✗ ERROR: Layer {layer} file not found")
        print(f"  Expected: {LAYER_REQUIREMENTS[layer]['file']}")
        print(f"  in: {arch_dir}")
        print()
        print("AGENT FIX:")
        print(f"  python scripts/arch.py validate --layer {layer} --path /path/to/.plan")
        print(f"  cd /path/to/project && python scripts/arch.py validate --layer {layer}")
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
        yaml_match = re.search(r"```yaml\s*(.*?)```", content, re.DOTALL)
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
        normalized_found = {normalize_header(s) for s in sections_found.keys()}
        optional_sections = set(requirements.get("optional_sections", []))
        for section in requirements["sections"]:
            variants = section_variants(section)
            found = any(v in normalized_found for v in variants)

            if found:
                print(f"✓ {section} section found")
            else:
                if section in optional_sections:
                    print(f"ℹ INFO: Optional {section} section not found")
                    continue
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

    # Dependency graph validation gate for L3/L4
    if layer in {"L3", "L4"}:
        dep_warnings, dep_errors = validate_dependencies.validate_dependencies(arch_dir)
        if dep_errors:
            print("✗ ERROR: Dependency graph validation failed:")
            for err in dep_errors:
                print(f"  - {err}")
            return None
        for warn in dep_warnings:
            print(f"⚠ WARNING: {warn}")
            warnings.append(warn)

    print()

    if warnings:
        print(f"✓ Validation complete - {len(warnings)} warning(s)")
    else:
        print("✓ Validation complete - no issues found")

    return warnings


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate a specified layer in the layered architecture."
    )
    # Optional positional target: layer or path
    parser.add_argument(
        "--soft",
        action="store_true",
        help="Soft gate: return 0 even with warnings",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Disable JSONL logging",
    )

    parser.add_argument(
        "target",
        nargs="?",
        help="Layer (L0-L5) or a path to a plan/architecture directory",
    )
    parser.add_argument(
        "--layer",
        help="Explicit layer to validate (L0-L5). Overrides positional target.",
    )
    parser.add_argument(
        "--path",
        help="Path to a plan/architecture directory. Overrides positional target.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all layers in order",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict gate (default). Non-zero exit if warnings found.",
    )
    args = parser.parse_args()
    logger = init_logger("validate_layer", enabled=not args.no_log)
    strict = args.strict or not args.soft

    target = args.layer or args.target
    path_arg = args.path

    layer = None
    arch_dir = None

    if target:
        upper = target.upper()
        if upper in LAYER_REQUIREMENTS:
            layer = upper
        else:
            path_arg = path_arg or target

    arch_dir = resolve_arch_dir(path_arg) if path_arg else get_arch_dir()
    if arch_dir is None:
        print("✗ ERROR: Invalid path provided for architecture directory")
        logger.log(
            "error",
            "arch_dir_invalid",
            "Invalid architecture directory path",
            {"path": path_arg},
        )
        sys.exit(2)

    if not arch_dir.exists():
        print(f"✗ ERROR: Architecture directory not found: {arch_dir}")
        print()
        print("Expected structure:")
        print("  layered-architect/")
        print("    .plan/")
        print("      L1-meta-architecture.md")
        print("      L2-system-architecture.md")
        print("      L3-component-design.md")
        print("      L4-implementation.md")
        print("    scripts/")
        print("      arch.py")
        print()
        print("AGENT FIX:")
        print("  cd /path/to/project && python scripts/arch.py validate --path .plan")
        print("  python scripts/arch.py validate --path /path/to/.plan")
        logger.log("error", "arch_dir_missing", "Architecture directory not found", {"arch_dir": str(arch_dir)})
        sys.exit(2)

    if args.all:
        layers = ["L0", "L1", "L2", "L3", "L4", "L5"]
    elif layer:
        layers = [layer]
    else:
        # If only a path was provided, default to all layers.
        layers = ["L0", "L1", "L2", "L3", "L4", "L5"]

    all_warnings = []
    for current_layer in layers:
        optional_missing_ok = current_layer in {"L0", "L5"} and (args.all or layer is None)
        result = validate_layer(arch_dir, current_layer, optional_missing_ok=optional_missing_ok)
        if result is None:
            logger.log(
                "error",
                "validation_failed",
                "Layer validation failed",
                {"layer": current_layer},
            )
            sys.exit(3)
        all_warnings.extend(result)

    logger.log(
        "info",
        "validation_complete",
        "Layer validation complete",
        {"layers": layers, "warnings": len(all_warnings)},
    )
    if strict and all_warnings:
        print("✗ STRICT MODE: WARNINGS ARE BLOCKING. FIX BEFORE PROCEEDING.")
        print("FAIL: Validation produced warnings under strict mode.")
        sys.exit(1)
    if strict:
        print("PASS: Validation clean under strict mode.")
    elif all_warnings:
        print("SOFT MODE: Warnings present. Proceed only with explicit user approval.")
    sys.exit(0)


if __name__ == "__main__":
    main()
