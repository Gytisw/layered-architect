#!/usr/bin/env python3
"""
Constraint Add Script
Safely adds constraints to the layered architecture constraint registry.
"""

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

from log_utils import init_logger
VALID_LAYERS = ["L1", "L2", "L3", "L4"]
VALID_TYPES = [
    "performance",
    "security",
    "scalability",
    "reliability",
    "maintainability",
    "compliance",
    "technology",
    "team",
    "budget",
    "timeline",
]
VAGUE_TERMS = [
    "fast",
    "good",
    "secure",
    "better",
    "best",
    "improve",
    "optimize",
    "proper",
    "correct",
    "right",
]

CONSTRAINTS_FILE = Path(".plan") / "constraints.yml"
LEGACY_CONSTRAINTS_FILE = Path("constraints.yml")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Add a constraint to the layered architecture registry"
    )
    parser.add_argument(
        "--layer",
        required=True,
        choices=VALID_LAYERS,
        help="Layer identifier (L1, L2, L3, or L4)",
    )
    parser.add_argument(
        "--type", required=True, choices=VALID_TYPES, help="Constraint type"
    )
    parser.add_argument("--text", required=True, help="Constraint description text")
    return parser.parse_args()


NON_METRIC_TYPES = {"compliance", "technology", "team", "budget", "timeline"}


def validate_constraint_text(text: str, constraint_type: str | None = None) -> tuple[bool, str]:
    text_lower = text.lower()

    for term in VAGUE_TERMS:
        if term in text_lower:
            return False, f"Constraint text contains vague term: '{term}'"

    if len(text) < 10:
        return False, "Constraint text is too short (minimum 10 characters)"

    has_metric = bool(re.search(r"\d+", text))
    has_comparison = any(op in text for op in ["<", ">", "<=", ">=", "=", "%"])
    has_units = any(
        unit in text_lower
        for unit in [
            "ms",
            "sec",
            "seconds",
            "minutes",
            "hours",
            "mb",
            "gb",
            "kb",
            "bytes",
            "req/s",
            "rps",
            "tps",
            "%",
            "percent",
        ]
    )

    if constraint_type not in NON_METRIC_TYPES and not (
        has_metric or has_comparison or has_units
    ):
        return False, (
            "Constraint text must be measurable. "
            "Include numbers, comparison operators (</>), or units (ms, %, etc.)"
        )

    return True, ""


def load_constraints() -> dict:
    if not CONSTRAINTS_FILE.exists():
        if LEGACY_CONSTRAINTS_FILE.exists():
            with open(LEGACY_CONSTRAINTS_FILE, "r") as f:
                return yaml.safe_load(f) or {"version": "1.0.0", "constraints": []}
        return {"version": "1.0.0", "constraints": []}

    with open(CONSTRAINTS_FILE, "r") as f:
        return yaml.safe_load(f) or {"version": "1.0.0", "constraints": []}


def save_constraints(data: dict) -> None:
    CONSTRAINTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CONSTRAINTS_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def check_duplicate(constraints: list, text: str) -> bool:
    text_normalized = text.lower().strip()
    for constraint in constraints:
        if constraint.get("text", "").lower().strip() == text_normalized:
            return True
    return False


def generate_constraint_id(constraints: list) -> str:
    max_num = 0

    for constraint in constraints:
        constraint_id = constraint.get("id", "")
        match = re.match(r"CON-(\d+)", constraint_id)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)

    next_num = max_num + 1
    return f"CON-{next_num:03d}"


def increment_version(version: str) -> str:
    if isinstance(version, (int, float)):
        major = int(version)
        return f"{major}.0.1"
    if not isinstance(version, str):
        return "1.0.0"

    parts = version.split(".")
    if len(parts) == 3:
        try:
            major, minor, patch = parts
            new_patch = int(patch) + 1
            return f"{major}.{minor}.{new_patch}"
        except ValueError:
            pass
    if len(parts) == 2 and all(p.isdigit() for p in parts):
        major, minor = parts
        return f"{major}.{minor}.1"
    if len(parts) == 1 and parts[0].isdigit():
        major = parts[0]
        return f"{major}.0.1"
    return version


def main():
    logger = init_logger("constraint_add")
    args = parse_args()

    is_valid, error_msg = validate_constraint_text(args.text, args.type)
    if not is_valid:
        print(f"✗ Validation error: {error_msg}")
        logger.log("error", "validation_failed", "Constraint validation failed", {"error": error_msg})
        sys.exit(1)

    data = load_constraints()
    constraints = data.get("constraints", [])

    if check_duplicate(constraints, args.text):
        print("✗ Error: A constraint with this text already exists")
        logger.log("error", "duplicate_constraint", "Duplicate constraint", {"text": args.text})
        sys.exit(1)

    constraint_id = generate_constraint_id(constraints)

    new_constraint = {
        "id": constraint_id,
        "layer": args.layer,
        "type": args.type,
        "text": args.text.strip(),
    }

    constraints.append(new_constraint)
    data["constraints"] = constraints

    current_version = data.get("version", "1.0.0")
    data["version"] = increment_version(current_version)

    save_constraints(data)

    print(f"✓ Constraint added: {constraint_id}")
    print(f"  Layer: {args.layer}")
    print(f"  Type: {args.type}")
    print(f"  Text: {args.text}")
    logger.log(
        "info",
        "constraint_added",
        "Constraint added",
        {"id": constraint_id, "layer": args.layer, "type": args.type},
    )


if __name__ == "__main__":
    main()
