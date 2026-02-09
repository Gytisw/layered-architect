#!/usr/bin/env python3
"""
Validate semantic-validation report for required shards.
"""

import argparse
import re
import sys
from pathlib import Path

from path_utils import resolve_plan_dir
from log_utils import init_logger


def find_report(plan_dir: Path) -> Path | None:
    for ext in (".md", ".json"):
        candidate = plan_dir / f"semantic-validation{ext}"
        if candidate.exists():
            return candidate
    return None


def shard_present(content: str, shard: str) -> bool:
    # Accept shard a / shard_a / shard-a
    pattern = re.compile(rf"shard\s*{shard}|shard[_-]{shard}")
    return bool(pattern.search(content))


def validate_report(plan_dir: Path) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    report = find_report(plan_dir)
    if report is None:
        errors.append("semantic-validation report missing (.plan/semantic-validation.md or .json)")
        return warnings, errors

    content = report.read_text(encoding="utf-8").lower()
    required = ["a", "b", "c", "d", "e"]
    if (plan_dir / "L0-problem-framing.md").exists():
        required.append("f")
    if (plan_dir / "L5-operability-readiness.md").exists():
        required.append("g")

    missing = [f"SHARD {s.upper()}" for s in required if not shard_present(content, s)]
    if missing:
        warnings.append("Missing shards: " + ", ".join(missing))

    return warnings, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate semantic-validation report")
    parser.add_argument("--path", default=".plan", help="Path to .plan directory")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on warnings")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL logging")
    args = parser.parse_args()

    logger = init_logger("validate_semantic_report", enabled=not args.no_log)
    plan_dir = resolve_plan_dir(args.path)
    if not plan_dir or not plan_dir.exists():
        print(f"Error: .plan directory not found (searched from {args.path})")
        return 1

    warnings, errors = validate_report(plan_dir)

    if errors:
        print("Semantic validation errors:")
        for err in errors:
            print(f"- {err}")
    if warnings:
        print("Semantic validation warnings:")
        for warn in warnings:
            print(f"- {warn}")

    logger.log(
        "info",
        "semantic_validation_checked",
        "Semantic validation report checked",
        {"warnings": len(warnings), "errors": len(errors)},
    )

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
