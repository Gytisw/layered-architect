#!/usr/bin/env python3
"""
Single-command validation wrapper for agents.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

from log_utils import init_logger
from path_utils import resolve_plan_dir
import validate_layer
from check_constraints import ConstraintChecker
from lint_architecture import ArchitectureLinter
import check_consistency


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate all layers and checks")
    parser.add_argument("--path", help="Path to project or .plan directory")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit non-zero on warnings"
    )
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL logging")
    args = parser.parse_args()

    logger = init_logger("validate_all", enabled=not args.no_log)
    plan_dir = resolve_plan_dir(args.path) or Path(".plan").resolve()
    if not plan_dir.exists():
        print(f"Error: .plan directory not found (searched from {args.path or 'cwd'})")
        return 1

    results: Dict[str, Dict] = {}
    warnings_total = 0
    errors_total = 0

    layers = ["L0", "L1", "L2", "L3", "L4", "L5"]
    for layer in layers:
        optional_missing_ok = layer in {"L0", "L5"}
        warnings = validate_layer.validate_layer(
            plan_dir, layer, optional_missing_ok=optional_missing_ok
        )
        if warnings is None:
            results[layer] = {"status": "ERROR", "warnings": None}
            errors_total += 1
        else:
            results[layer] = {"status": "OK", "warnings": len(warnings)}
            warnings_total += len(warnings)

    # Constraints
    checker = ConstraintChecker(plan_dir.parent)
    checker.run()
    if checker.errors:
        errors_total += len(checker.errors)
    warnings_total += len(checker.warnings)
    results["constraints"] = {
        "status": "OK" if not checker.errors else "ERROR",
        "warnings": len(checker.warnings),
        "errors": len(checker.errors),
    }

    # Consistency
    consistency_warnings: List[str] = []
    check_consistency.check_constraints(plan_dir, consistency_warnings)
    check_consistency.check_interfaces(plan_dir, consistency_warnings)
    check_consistency.check_modules_vs_files(plan_dir, consistency_warnings)
    results["consistency"] = {
        "status": "OK" if not consistency_warnings else "WARN",
        "warnings": len(consistency_warnings),
    }
    warnings_total += len(consistency_warnings)

    # Lint
    linter = ArchitectureLinter(plan_dir.parent)
    lint_exit = linter.run()
    results["lint"] = {
        "status": "OK" if lint_exit == 0 else "ERROR",
        "warnings": len(linter.report.warnings()),
        "errors": len(linter.report.errors()),
    }
    if lint_exit != 0:
        errors_total += 1

    ready = errors_total == 0 and (warnings_total == 0 or not args.strict)
    summary = {
        "overall": "PASS" if ready else "FAIL",
        "warnings": warnings_total,
        "errors": errors_total,
        "ready_for_execution": ready,
        "layers": {k: v for k, v in results.items() if k in layers},
        "constraints": results["constraints"],
        "consistency": results["consistency"],
        "lint": results["lint"],
    }

    if args.format == "json":
        print(json.dumps(summary, indent=2))
    else:
        print("Validation Summary")
        print(f"- Overall: {summary['overall']}")
        print(f"- Warnings: {warnings_total}")
        print(f"- Errors: {errors_total}")
        for layer in layers:
            entry = summary["layers"].get(layer, {})
            print(f"  {layer}: {entry.get('status')} (warnings: {entry.get('warnings')})")
        print(f"- Constraints: {summary['constraints']['status']}")
        print(f"- Consistency: {summary['consistency']['status']}")
        print(f"- Lint: {summary['lint']['status']}")

    logger.log("info", "validate_all_complete", "Validation complete", summary)
    if not ready:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
