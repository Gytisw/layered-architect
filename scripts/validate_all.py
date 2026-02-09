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
import validate_semantic_report

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


GATES_REQUIRED_FIELDS = [
    "mode",
    "question_depth",
    "l0_required",
    "l5_required",
    "research_required",
    "research_approved",
    "semantic_required",
    "semantic_completed",
    "dependencies_complete",
    "constraints_registry_present",
    "last_step",
]


def load_gates(plan_dir: Path) -> tuple[Dict, List[str]]:
    errors: List[str] = []
    if yaml is None:
        errors.append("PyYAML missing; cannot parse gates.yml")
        return {}, errors
    gates_path = plan_dir / "gates.yml"
    if not gates_path.exists():
        errors.append("gates.yml missing in .plan/")
        return {}, errors
    try:
        data = yaml.safe_load(gates_path.read_text()) or {}
    except Exception as exc:
        errors.append(f"Failed to parse gates.yml: {exc}")
        return {}, errors
    if not isinstance(data, dict):
        errors.append("gates.yml is not a valid mapping")
        return {}, errors
    missing = [k for k in GATES_REQUIRED_FIELDS if k not in data]
    if missing:
        errors.append("gates.yml missing required keys: " + ", ".join(missing))
    return data, errors


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
        print("  cd /path/to/project && python scripts/arch.py validate --path .plan")
        print("  python scripts/arch.py validate --path /path/to/project/.plan")
        return 1

    results: Dict[str, Dict] = {}
    warnings_total = 0
    errors_total = 0

    gates, gate_errors = load_gates(plan_dir)
    if gate_errors:
        status = "ERROR" if args.strict else "WARN"
        if args.strict:
            errors_total += 1
        else:
            warnings_total += 1
        results["gates"] = {"status": status, "errors": gate_errors}

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

    gates_research_required = bool(gates.get("research_required", False))
    research_required = (
        gates_research_required or has_external_deps_section() or dependencies_has_external_nodes()
    )
    research_approved = bool(gates.get("research_approved", False))
    semantic_required = bool(gates.get("semantic_required", True)) if gates else True
    semantic_completed = bool(gates.get("semantic_completed", False))

    # Semantic validation report
    if semantic_required:
        semantic_warnings, semantic_errors = validate_semantic_report.validate_report(plan_dir)
        if semantic_errors:
            errors_total += len(semantic_errors)
        if semantic_warnings:
            warnings_total += len(semantic_warnings)
        semantic_status = "OK"
        if semantic_errors:
            semantic_status = "ERROR"
        elif semantic_warnings:
            semantic_status = "WARN"
        results["semantic_validation"] = {
            "status": semantic_status,
            "warnings": semantic_warnings,
            "errors": semantic_errors,
        }

        if not semantic_completed:
            msg = "semantic_completed is false in .plan/gates.yml"
            if args.strict:
                errors_total += 1
                results["semantic_validation"]["status"] = "ERROR"
            else:
                warnings_total += 1
                if results["semantic_validation"]["status"] == "OK":
                    results["semantic_validation"]["status"] = "WARN"
            results["semantic_validation"]["gate"] = msg
    else:
        results["semantic_validation"] = {"status": "SKIP", "required": False}

    # Research log gate
    research_file = find_report("research")
    research_status = "OK"
    research_messages: List[str] = []
    if research_required and not research_approved:
        research_messages.append("research_approved is false in .plan/gates.yml")
        if args.strict:
            errors_total += 1
            research_status = "ERROR"
        else:
            warnings_total += 1
            research_status = "WARN"
    if research_required and research_file is None:
        research_messages.append("Research log required (.plan/research.md or .json)")
        if args.strict:
            errors_total += 1
            research_status = "ERROR"
        else:
            warnings_total += 1
            research_status = "WARN"
    results["research"] = {
        "status": research_status,
        "required": research_required,
        "approved": research_approved,
        "file": research_file.name if research_file else None,
        "messages": research_messages,
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
        "gates": results.get("gates", {}),
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
        if summary.get("gates"):
            print(f"- Gates: {summary['gates'].get('status')}")
            for err in summary["gates"].get("errors", []):
                print(f"  {err}")
        print(f"- Constraints: {summary['constraints']['status']}")
        print(f"- Dependencies: {summary['dependencies']['status']}")
        print(f"- Consistency: {summary['consistency']['status']}")
        print(f"- Lint: {summary['lint']['status']}")
        if summary.get("semantic_validation"):
            print(f"- Semantic Validation: {summary['semantic_validation'].get('status')}")
            if summary["semantic_validation"].get("status") in {"WARN", "ERROR"}:
                for err in summary["semantic_validation"].get("errors", []):
                    print(f"  {err}")
                for warn in summary["semantic_validation"].get("warnings", []):
                    print(f"  {warn}")
                gate_msg = summary["semantic_validation"].get("gate")
                if gate_msg:
                    print(f"  {gate_msg}")
        if summary.get("research"):
            print(f"- Research: {summary['research'].get('status')}")
            if summary["research"].get("status") in {"WARN", "ERROR"}:
                for msg in summary["research"].get("messages", []):
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
