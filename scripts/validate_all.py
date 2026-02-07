#!/usr/bin/env python3
"""
Single-command validation wrapper for agents.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

from log_utils import init_logger
from path_utils import resolve_plan_dir
import validate_layer
from check_constraints import ConstraintChecker
from lint_architecture import ArchitectureLinter
import check_consistency
import extract_constraints
import validate_dependencies


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
    parser.add_argument(
        "--auto-constraints",
        action="store_true",
        help="Auto-populate constraints.yml from L1 when registry is empty",
    )
    parser.add_argument(
        "--auto-deps",
        action="store_true",
        help="Create stub dependencies.yml if missing",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Disable any automatic file updates (pairs with --auto-constraints)",
    )
    args = parser.parse_args()

    logger = init_logger("validate_all", enabled=not args.no_log)
    plan_dir = resolve_plan_dir(args.path)
    if not plan_dir or not plan_dir.exists():
        print(f"Error: .plan directory not found (searched from {args.path or 'cwd'})")
        print("AGENT FIX:")
        print("  cd /path/to/project && python scripts/validate_all.py --path .plan")
        print("  python scripts/validate_all.py --path /path/to/project/.plan")
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

    # Optional auto-constraints
    auto_added = 0
    readonly = bool(os.getenv("LAYERED_ARCHITECT_READONLY") or args.no_write)
    if args.auto_constraints and not readonly:
        try:
            l1_file = plan_dir / "L1-meta-architecture.md"
            constraints_file = plan_dir / "constraints.yml"
            if l1_file.exists():
                data, existing = extract_constraints.load_constraints(constraints_file)
                existing_ids = {c.get("id") for c in existing if isinstance(c, dict)}
                if not existing_ids:
                    extracted = extract_constraints.extract_constraints_from_text(
                        l1_file.read_text(encoding="utf-8")
                    )
                    merged = list(existing)
                    added = 0
                    for cid, ctext in extracted.items():
                        if cid in existing_ids:
                            continue
                        merged.append(
                            {
                                "id": cid,
                                "layer": "L1",
                                "type": "unspecified",
                                "text": ctext,
                            }
                        )
                        added += 1
                    if merged:
                        data["constraints"] = merged
                        data["version"] = extract_constraints.increment_version(
                            data.get("version", "1.0.0")
                        )
                        extract_constraints.save_constraints(constraints_file, data)
                        auto_added = added
        except Exception as exc:
            logger.log(
                "warning",
                "auto_constraints_failed",
                "Auto constraints extraction failed",
                {"error": str(exc)},
            )

    # Constraints
    checker = ConstraintChecker(plan_dir)
    checker.run()
    if checker.errors:
        errors_total += len(checker.errors)
    warnings_total += len(checker.warnings)
    results["constraints"] = {
        "status": "OK" if not checker.errors else "ERROR",
        "warnings": len(checker.warnings),
        "errors": len(checker.errors),
    }
    if auto_added:
        results["constraints"]["auto_added"] = auto_added

    # Dependencies
    dep_warnings, dep_errors = validate_dependencies.validate_dependencies(
        plan_dir, auto_stub=args.auto_deps, no_write=readonly
    )
    if dep_errors:
        errors_total += len(dep_errors)
    warnings_total += len(dep_warnings)
    results["dependencies"] = {
        "status": "OK" if not dep_errors else "ERROR",
        "warnings": len(dep_warnings),
        "errors": len(dep_errors),
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
    linter = ArchitectureLinter(plan_dir)
    lint_exit = linter.run()
    results["lint"] = {
        "status": "OK" if lint_exit == 0 else "ERROR",
        "warnings": len(linter.report.warnings()),
        "errors": len(linter.report.errors()),
    }
    warnings_total += len(linter.report.warnings())
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
        "dependencies": results["dependencies"],
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
        print(f"- Dependencies: {summary['dependencies']['status']}")
        print(f"- Consistency: {summary['consistency']['status']}")
        print(f"- Lint: {summary['lint']['status']}")

    logger.log("info", "validate_all_complete", "Validation complete", summary)
    if not ready:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
