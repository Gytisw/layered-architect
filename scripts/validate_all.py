#!/usr/bin/env python3
"""
Single-command validation wrapper for agents.
"""

import argparse
import json
import os
import re
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

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


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

    # Semantic validation + research gates
    def find_report(basename: str) -> Path | None:
        for ext in (".md", ".json"):
            candidate = plan_dir / f"{basename}{ext}"
            if candidate.exists():
                return candidate
        return None

    def normalize_header(text: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
        return " ".join(cleaned.split())

    def has_external_deps_section() -> bool:
        l2_file = plan_dir / "L2-system-architecture.md"
        if not l2_file.exists():
            return False
        content = l2_file.read_text(encoding="utf-8")
        header_pattern = re.compile(r"^#{2,4}\s+(.+)$")
        targets = {
            normalize_header("External Dependencies"),
            normalize_header("Dependencies"),
            normalize_header("Third-Party Dependencies"),
        }
        for line in content.splitlines():
            match = header_pattern.match(line.strip())
            if match and normalize_header(match.group(1)) in targets:
                return True
        return False

    def dependencies_has_external_nodes() -> bool:
        dep_file = plan_dir / "dependencies.yml"
        if not dep_file.exists() or yaml is None:
            return False
        try:
            data = yaml.safe_load(dep_file.read_text()) or {}
        except Exception:
            return False
        nodes = data.get("nodes", [])
        for node in nodes:
            if isinstance(node, dict):
                node_type = str(node.get("type", "")).strip().lower()
                if node_type in {"external", "infrastructure", "vendor", "third_party", "third-party"}:
                    return True
        return False

    # Semantic validation report
    semantic_file = find_report("semantic-validation")
    semantic_missing = semantic_file is None
    missing_shards: list[str] = []
    if semantic_file and semantic_file.suffix == ".md":
        content = semantic_file.read_text(encoding="utf-8").lower()
        required_shards = ["shard a", "shard b", "shard c", "shard d", "shard e"]
        if (plan_dir / "L0-problem-framing.md").exists():
            required_shards.append("shard f")
        if (plan_dir / "L5-operability-readiness.md").exists():
            required_shards.append("shard g")
        for shard in required_shards:
            if shard not in content:
                missing_shards.append(shard.upper())

    if semantic_missing:
        status = "ERROR" if args.strict else "WARN"
        msg = "Semantic validation report missing (.plan/semantic-validation.md or .json)"
        if args.strict:
            errors_total += 1
        else:
            warnings_total += 1
        results["semantic_validation"] = {"status": status, "message": msg}
    else:
        if missing_shards:
            warnings_total += 1
        results["semantic_validation"] = {
            "status": "WARN" if missing_shards else "OK",
            "file": semantic_file.name,
            "missing_shards": missing_shards,
        }

    # Research log gate
    research_required = has_external_deps_section() or dependencies_has_external_nodes()
    research_file = find_report("research")
    if research_required and research_file is None:
        status = "ERROR" if args.strict else "WARN"
        msg = "Research log required for external dependencies (.plan/research.md or .json)"
        if args.strict:
            errors_total += 1
        else:
            warnings_total += 1
        results["research"] = {"status": status, "required": True, "message": msg}
    else:
        results["research"] = {
            "status": "OK",
            "required": research_required,
            "file": research_file.name if research_file else None,
        }

    ready = errors_total == 0 and (warnings_total == 0 or not args.strict)
    summary = {
        "overall": "PASS" if ready else "FAIL",
        "mode": "strict" if args.strict else "soft",
        "blocking_warnings": bool(args.strict and warnings_total > 0),
        "warnings": warnings_total,
        "errors": errors_total,
        "ready_for_execution": ready,
        "layers": {k: v for k, v in results.items() if k in layers},
        "constraints": results["constraints"],
        "dependencies": results["dependencies"],
        "consistency": results["consistency"],
        "lint": results["lint"],
        "semantic_validation": results.get("semantic_validation", {}),
        "research": results.get("research", {}),
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
        if summary.get("semantic_validation"):
            print(f"- Semantic Validation: {summary['semantic_validation'].get('status')}")
            if summary["semantic_validation"].get("status") in {"WARN", "ERROR"}:
                msg = summary["semantic_validation"].get("message", "")
                if msg:
                    print(f"  {msg}")
        if summary.get("research"):
            print(f"- Research: {summary['research'].get('status')}")
            if summary["research"].get("status") in {"WARN", "ERROR"}:
                msg = summary["research"].get("message", "")
                if msg:
                    print(f"  {msg}")
        if args.strict and warnings_total > 0:
            print("✗ STRICT MODE: WARNINGS ARE BLOCKING. FIX BEFORE PROCEEDING.")
            print("FAIL: Validation produced warnings under strict mode.")
        elif args.strict:
            print("PASS: Validation clean under strict mode.")
        elif warnings_total > 0:
            print("SOFT MODE: Warnings present. Proceed only with explicit user approval.")

    logger.log("info", "validate_all_complete", "Validation complete", summary)
    if not ready:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
