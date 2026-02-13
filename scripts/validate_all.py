#!/usr/bin/env python3
"""
Single-command validation wrapper for agents.
"""

import argparse
import json
import os
import re
import sys
from io import StringIO
from contextlib import redirect_stdout
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
import validate_research_evidence
from findings import make_finding, blocking_findings, next_fix_command

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
    "research_approval_receipt",
    "research_approved_by",
    "research_approved_at",
    "semantic_required",
    "semantic_completed",
    "semantic_completion_receipt",
    "semantic_completed_by",
    "semantic_completed_at",
    "dependencies_complete",
    "constraints_registry_present",
    "last_validation_report",
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


def _gate_receipts_valid(gates: Dict) -> List[str]:
    issues: List[str] = []
    if gates.get("research_approved"):
        for key in ("research_approval_receipt", "research_approved_by", "research_approved_at"):
            value = str(gates.get(key, "")).strip().lower()
            if not value or value == "none":
                issues.append(f"research_approved is true but {key} is missing")
    if gates.get("semantic_completed"):
        for key in ("semantic_completion_receipt", "semantic_completed_by", "semantic_completed_at"):
            value = str(gates.get(key, "")).strip().lower()
            if not value or value == "none":
                issues.append(f"semantic_completed is true but {key} is missing")
    return issues


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
    findings_all: List[Dict] = []

    def add_generic_finding(
        *,
        finding_id: str,
        severity: str,
        layer: str,
        file: Path,
        section: str,
        message: str,
        why_blocking: str,
        fix_hint: str,
        fix_command: str,
        line: int | None = None,
    ) -> None:
        findings_all.append(
            make_finding(
                finding_id=finding_id,
                severity=severity,
                layer=layer,
                file=str(file),
                section=section,
                line=line,
                message=message,
                why_blocking=why_blocking,
                fix_hint=fix_hint,
                fix_command=fix_command,
            )
        )

    gates, gate_errors = load_gates(plan_dir)
    if gate_errors:
        status = "ERROR" if args.strict else "WARN"
        results["gates"] = {"status": status, "errors": gate_errors}
        for idx, err in enumerate(gate_errors, start=1):
            add_generic_finding(
                finding_id=f"VAL-GATE-SCHEMA-{idx:03d}",
                severity="error" if args.strict else "warning",
                layer="GLOBAL",
                file=plan_dir / "gates.yml",
                section="gates.yml",
                message=err,
                why_blocking="Gate state is invalid and cannot be trusted for deterministic progression.",
                fix_hint="Repair missing/invalid keys in gates.yml using the documented schema.",
                fix_command="python scripts/arch.py status --path .plan",
            )
    else:
        receipt_issues = _gate_receipts_valid(gates)
        for idx, issue in enumerate(receipt_issues, start=1):
            add_generic_finding(
                finding_id=f"VAL-GATE-RECEIPT-{idx:03d}",
                severity="error" if args.strict else "warning",
                layer="GLOBAL",
                file=plan_dir / "gates.yml",
                section="gates.yml",
                message=issue,
                why_blocking="Manual gate state mutation bypasses approval and completion receipts.",
                fix_hint="Use arch.py research approve / arch.py semantic complete to set gate states.",
                fix_command="python scripts/arch.py status --path .plan",
            )

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
        section_lines: List[str] = []
        in_target = False
        for line in content.splitlines():
            match = header_pattern.match(line.strip())
            if match:
                title = normalize_header(match.group(1))
                if in_target:
                    break
                in_target = title in targets
                continue
            if in_target:
                section_lines.append(line)
        if not section_lines:
            return False
        generic_tokens = {
            "dependency",
            "dependencies",
            "purpose",
            "version",
            "constraint",
            "constraints",
            "optional",
            "required",
            "legacy",
            "n",
            "a",
        }
        for raw in section_lines:
            line = raw.strip()
            if not line or line.startswith("```"):
                continue
            if line.startswith("|") and re.match(r"^\|\s*-+\s*\|", line):
                continue
            normalized = re.sub(r"^[-*]\s+|^\d+\.\s+|^\|\s*|\s*\|$", "", line)
            normalized = re.sub(r"\*\*|`", "", normalized).strip()
            lowered = normalized.lower()
            if not lowered:
                continue
            if lowered in {"none", "n/a", "na", "tbd", "todo"}:
                continue
            if "[" in lowered and "]" in lowered:
                continue
            if lowered.startswith("if legacy"):
                continue
            tokens = [t for t in re.split(r"[^a-z0-9]+", lowered) if t]
            meaningful = [t for t in tokens if t not in generic_tokens and len(t) > 2]
            if meaningful:
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

    def find_report(basename: str) -> Path | None:
        for ext in (".md", ".json"):
            candidate = plan_dir / f"{basename}{ext}"
            if candidate.exists():
                return candidate
        return None

    gates_research_required = bool(gates.get("research_required", False))
    research_required = (
        gates_research_required or has_external_deps_section() or dependencies_has_external_nodes()
    )
    research_approved = bool(gates.get("research_approved", False))
    research_file = find_report("research")
    research_evidence_file = plan_dir / "research.evidence.json"

    if args.strict and research_required:
        early_messages: List[str] = []
        if not research_approved:
            early_messages.append("research_approved is false in .plan/gates.yml")
            add_generic_finding(
                finding_id="VAL-RESEARCH-APPROVAL",
                severity="error",
                layer="GLOBAL",
                file=plan_dir / "gates.yml",
                section="Research Gate",
                message="Research is required but not approved in .plan/gates.yml",
                why_blocking="Strict mode requires research approval before downstream architecture progression.",
                fix_hint="Request user approval and record it through arch.py research approve.",
                fix_command=f"python scripts/arch.py research approve --path {plan_dir} --approved-by <name> --confirm-user-approval",
            )
        if research_file is None:
            early_messages.append("Research log required (.plan/research.md or .json)")
            add_generic_finding(
                finding_id="VAL-RESEARCH-LOG",
                severity="error",
                layer="GLOBAL",
                file=plan_dir / "research.md",
                section="Research Gate",
                message="Research log required (.plan/research.md or .json)",
                why_blocking="Strict mode requires explicit research traceability before architecture progression.",
                fix_hint="Create a research log tied to concrete sources and decisions.",
                fix_command=f"python scripts/arch.py status --path {plan_dir}",
            )
        if not research_evidence_file.exists():
            early_messages.append("Research evidence required (.plan/research.evidence.json)")
            add_generic_finding(
                finding_id="VAL-RESEARCH-EVIDENCE-MISSING",
                severity="error",
                layer="GLOBAL",
                file=research_evidence_file,
                section="Research Gate",
                message="Research evidence required (.plan/research.evidence.json)",
                why_blocking="Strict mode forbids memory-only research summaries.",
                fix_hint="Create research.evidence.json with source, claim mapping, and executor metadata.",
                fix_command=f"python scripts/arch.py research approve --path {plan_dir} --approved-by <name> --confirm-user-approval",
            )
        elif research_approved:
            early_warnings, early_errors = validate_research_evidence.validate_evidence_file(
                plan_dir, evidence_path=research_evidence_file, strict=True
            )
            for idx, err in enumerate(early_errors, start=1):
                early_messages.append(err)
                add_generic_finding(
                    finding_id=f"VAL-RESEARCH-EVIDENCE-ERROR-{idx:03d}",
                    severity="error",
                    layer="GLOBAL",
                    file=research_evidence_file,
                    section="Research Evidence",
                    message=err,
                    why_blocking="Research evidence quality requirements are not satisfied.",
                    fix_hint="Fix evidence schema and claim/source traceability.",
                    fix_command=f"python scripts/arch.py research approve --path {plan_dir} --approved-by <name> --confirm-user-approval",
                )
        if early_messages:
            summary = {
                "overall": "FAIL",
                "mode": "strict",
                "blocking_warnings": False,
                "warnings": 0,
                "errors": len([f for f in findings_all if f.get("severity") == "error"]),
                "ready_for_execution": False,
                "findings": findings_all,
                "blocking_findings": blocking_findings(findings_all, strict=True),
                "next_fix_command": next_fix_command(findings_all, strict=True),
                "layers": {},
                "gates": results.get("gates", {}),
                "constraints": {},
                "dependencies": {},
                "consistency": {},
                "lint": {},
                "semantic_validation": {},
                "research": {
                    "status": "ERROR",
                    "required": True,
                    "approved": research_approved,
                    "file": research_file.name if research_file else None,
                    "evidence_file": research_evidence_file.name if research_evidence_file.exists() else None,
                    "messages": early_messages,
                },
            }
            if args.format == "json":
                print(json.dumps(summary, indent=2))
            else:
                print("Validation Summary")
                print("- Overall: FAIL")
                print("- Blocking Findings:")
                for finding in summary["blocking_findings"]:
                    print(
                        f"  [{finding.get('id')}] {finding.get('message')} | "
                        f"fix={finding.get('fix_command')}"
                    )
                print(f"- Next Fix Command: {summary['next_fix_command']}")
                print("FAIL: Strict mode blocked by research gate.")
            return 1

    layers = ["L0", "L1", "L2", "L3", "L4", "L5"]
    for layer in layers:
        optional_missing_ok = layer in {"L0", "L5"}
        if args.format == "json":
            with redirect_stdout(StringIO()):
                layer_findings = validate_layer.validate_layer(
                    plan_dir, layer, optional_missing_ok=optional_missing_ok
                )
        else:
            layer_findings = validate_layer.validate_layer(
                plan_dir, layer, optional_missing_ok=optional_missing_ok
            )
        if layer_findings is None:
            results[layer] = {"status": "ERROR", "warnings": None}
            add_generic_finding(
                finding_id=f"VAL-{layer}-FATAL",
                severity="error",
                layer=layer,
                file=plan_dir / f"{layer}-unknown.md",
                section=layer,
                message=f"{layer} validation failed due to fatal error.",
                why_blocking="Layer cannot be validated.",
                fix_hint=f"Run layer validation directly and fix file/path errors for {layer}.",
                fix_command=f"python scripts/arch.py validate --layer {layer} --path {plan_dir}",
            )
        else:
            warnings = len([f for f in layer_findings if f.get("severity") == "warning"])
            errors = len([f for f in layer_findings if f.get("severity") == "error"])
            status = "ERROR" if errors else ("WARN" if warnings else "OK")
            results[layer] = {"status": status, "warnings": warnings, "errors": errors}
            findings_all.extend(layer_findings)

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
    if args.format == "json":
        with redirect_stdout(StringIO()):
            checker.run()
    else:
        checker.run()
    for idx, err in enumerate(checker.errors, start=1):
        add_generic_finding(
            finding_id=f"VAL-CONSTRAINT-ERROR-{idx:03d}",
            severity="error",
            layer="GLOBAL",
            file=plan_dir / "constraints.yml",
            section="Constraint Registry",
            message=err,
            why_blocking="Constraint registry errors break traceability checks.",
            fix_hint="Fix constraint registry schema/content issues.",
            fix_command=f"python scripts/arch.py constraints check --path {plan_dir}",
        )
    for idx, warn in enumerate(checker.warnings, start=1):
        add_generic_finding(
            finding_id=f"VAL-CONSTRAINT-WARN-{idx:03d}",
            severity="warning",
            layer="GLOBAL",
            file=plan_dir / "constraints.yml",
            section="Constraint Registry",
            message=warn,
            why_blocking="Constraint quality issues reduce downstream consistency.",
            fix_hint="Address inconsistent, conflicting, or unreferenced constraints.",
            fix_command=f"python scripts/arch.py constraints check --path {plan_dir}",
        )
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
    for idx, err in enumerate(dep_errors, start=1):
        add_generic_finding(
            finding_id=f"VAL-DEPENDENCY-ERROR-{idx:03d}",
            severity="error",
            layer="GLOBAL",
            file=plan_dir / "dependencies.yml",
            section="Dependency Graph",
            message=err,
            why_blocking="Dependency graph must be valid before layer progression.",
            fix_hint="Fix dependency schema, status, nodes, or cycle errors.",
            fix_command=f"python scripts/arch.py deps --path {plan_dir} --strict",
        )
    for idx, warn in enumerate(dep_warnings, start=1):
        add_generic_finding(
            finding_id=f"VAL-DEPENDENCY-WARN-{idx:03d}",
            severity="warning",
            layer="GLOBAL",
            file=plan_dir / "dependencies.yml",
            section="Dependency Graph",
            message=warn,
            why_blocking="Dependency drift weakens cross-layer validation quality.",
            fix_hint="Align dependencies graph with L3/L4 design.",
            fix_command=f"python scripts/arch.py deps --path {plan_dir}",
        )
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
    for idx, warn in enumerate(consistency_warnings, start=1):
        add_generic_finding(
            finding_id=f"VAL-CONSISTENCY-WARN-{idx:03d}",
            severity="warning",
            layer="GLOBAL",
            file=plan_dir,
            section="Cross-layer Consistency",
            message=warn,
            why_blocking="Cross-layer drift can invalidate architecture quality gates.",
            fix_hint="Align referenced interfaces/modules/constraints between adjacent layers.",
            fix_command=f"python scripts/arch.py consistency --path {plan_dir}",
        )
    results["consistency"] = {
        "status": "OK" if not consistency_warnings else "WARN",
        "warnings": len(consistency_warnings),
    }

    # Lint
    linter = ArchitectureLinter(plan_dir)
    if args.format == "json":
        with redirect_stdout(StringIO()):
            lint_exit = linter.run()
    else:
        lint_exit = linter.run()
    for idx, issue in enumerate(linter.report.errors(), start=1):
        add_generic_finding(
            finding_id=f"VAL-LINT-ERROR-{idx:03d}",
            severity="error",
            layer="GLOBAL",
            file=Path(str(issue.file)),
            section="Lint",
            line=getattr(issue, "line", None),
            message=issue.message,
            why_blocking="Lint errors indicate malformed architecture docs.",
            fix_hint="Fix malformed markdown/content issues reported by linter.",
            fix_command=f"python scripts/arch.py lint --path {plan_dir} --strict",
        )
    for idx, issue in enumerate(linter.report.warnings(), start=1):
        add_generic_finding(
            finding_id=f"VAL-LINT-WARN-{idx:03d}",
            severity="warning",
            layer="GLOBAL",
            file=Path(str(issue.file)),
            section="Lint",
            line=getattr(issue, "line", None),
            message=issue.message,
            why_blocking="Lint warnings represent quality defects under strict mode.",
            fix_hint="Resolve warning-level lint issues in architecture docs.",
            fix_command=f"python scripts/arch.py lint --path {plan_dir} --strict",
        )
    results["lint"] = {
        "status": "OK" if lint_exit == 0 else "ERROR",
        "warnings": len(linter.report.warnings()),
        "errors": len(linter.report.errors()),
    }

    # Semantic validation + research gates
    semantic_required = bool(gates.get("semantic_required", True)) if gates else True
    semantic_completed = bool(gates.get("semantic_completed", False))

    # Semantic validation report
    if semantic_required:
        task_capable = bool(os.getenv("LAYERED_ARCH_TASK_CAPABLE"))
        semantic_warnings, semantic_errors = validate_semantic_report.validate_report(
            plan_dir, task_capable=task_capable
        )
        for idx, err in enumerate(semantic_errors, start=1):
            add_generic_finding(
                finding_id=f"VAL-SEMANTIC-ERROR-{idx:03d}",
                severity="error",
                layer="GLOBAL",
                file=plan_dir / "semantic-validation.md",
                section="Semantic Validation",
                message=err,
                why_blocking="Semantic validation artifacts are invalid.",
                fix_hint="Repair semantic report and shard coverage.",
                fix_command=f"python scripts/arch.py semantic validate --path {plan_dir} --strict",
            )
        for idx, warn in enumerate(semantic_warnings, start=1):
            add_generic_finding(
                finding_id=f"VAL-SEMANTIC-WARN-{idx:03d}",
                severity="warning",
                layer="GLOBAL",
                file=plan_dir / "semantic-validation.md",
                section="Semantic Validation",
                message=warn,
                why_blocking="Incomplete semantic validation can hide cross-layer drift.",
                fix_hint="Complete missing shards/findings/evidence/executor metadata.",
                fix_command=f"python scripts/arch.py semantic validate --path {plan_dir} --strict",
            )
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
            add_generic_finding(
                finding_id="VAL-SEMANTIC-GATE",
                severity="error" if args.strict else "warning",
                layer="GLOBAL",
                file=plan_dir / "gates.yml",
                section="Semantic Gate",
                message=msg,
                why_blocking="Semantic completion must be receipt-backed before progression.",
                fix_hint="Run semantic validation and complete the semantic gate using arch.py.",
                fix_command=f"python scripts/arch.py semantic complete --path {plan_dir} --completed-by <name>",
            )
            if args.strict:
                results["semantic_validation"]["status"] = "ERROR"
            elif results["semantic_validation"]["status"] == "OK":
                results["semantic_validation"]["status"] = "WARN"
            results["semantic_validation"]["gate"] = msg
    else:
        results["semantic_validation"] = {"status": "SKIP", "required": False}

    # Research log gate
    research_status = "OK"
    research_messages: List[str] = []
    if research_required and not research_approved:
        research_messages.append("research_approved is false in .plan/gates.yml")
        add_generic_finding(
            finding_id="VAL-RESEARCH-APPROVAL",
            severity="error" if args.strict else "warning",
            layer="GLOBAL",
            file=plan_dir / "gates.yml",
            section="Research Gate",
            message="research_approved is false in .plan/gates.yml",
            why_blocking="Research-required architecture cannot progress without explicit approval.",
            fix_hint="Obtain user approval and record it via arch.py research approve.",
            fix_command=f"python scripts/arch.py research approve --path {plan_dir} --approved-by <name> --confirm-user-approval",
        )
        research_status = "ERROR" if args.strict else "WARN"
    if research_required and research_file is None:
        research_messages.append("Research log required (.plan/research.md or .json)")
        add_generic_finding(
            finding_id="VAL-RESEARCH-LOG",
            severity="error" if args.strict else "warning",
            layer="GLOBAL",
            file=plan_dir / "research.md",
            section="Research Gate",
            message="Research log required (.plan/research.md or .json)",
            why_blocking="Research decisions must be explicitly logged for auditability.",
            fix_hint="Create .plan/research.md from references/research-template.md.",
            fix_command=f"python scripts/arch.py status --path {plan_dir}",
        )
        research_status = "ERROR" if args.strict else "WARN"
    if research_required and not research_evidence_file.exists():
        research_messages.append("Research evidence required (.plan/research.evidence.json)")
        add_generic_finding(
            finding_id="VAL-RESEARCH-EVIDENCE-MISSING",
            severity="error" if args.strict else "warning",
            layer="GLOBAL",
            file=research_evidence_file,
            section="Research Gate",
            message="Research evidence required (.plan/research.evidence.json)",
            why_blocking="Evidence bundle is mandatory to prevent hallucinated research.",
            fix_hint="Create research.evidence.json with sources, claims, and decision impacts.",
            fix_command=f"python scripts/arch.py research approve --path {plan_dir} --approved-by <name> --confirm-user-approval",
        )
        research_status = "ERROR" if args.strict else "WARN"
    if research_required and research_evidence_file.exists():
        research_warnings, research_errors = validate_research_evidence.validate_evidence_file(
            plan_dir, evidence_path=research_evidence_file, strict=args.strict
        )
        for idx, err in enumerate(research_errors, start=1):
            add_generic_finding(
                finding_id=f"VAL-RESEARCH-EVIDENCE-ERROR-{idx:03d}",
                severity="error",
                layer="GLOBAL",
                file=research_evidence_file,
                section="Research Evidence",
                message=err,
                why_blocking="Research evidence quality requirements are not satisfied.",
                fix_hint="Fix evidence schema and claim/source traceability.",
                fix_command=f"python scripts/arch.py research approve --path {plan_dir} --approved-by <name> --confirm-user-approval",
            )
            research_status = "ERROR"
        for idx, warn in enumerate(research_warnings, start=1):
            add_generic_finding(
                finding_id=f"VAL-RESEARCH-EVIDENCE-WARN-{idx:03d}",
                severity="warning",
                layer="GLOBAL",
                file=research_evidence_file,
                section="Research Evidence",
                message=warn,
                why_blocking="Research evidence may be incomplete or low confidence.",
                fix_hint="Tighten evidence quality and include missing details.",
                fix_command=f"python scripts/arch.py research approve --path {plan_dir} --approved-by <name> --confirm-user-approval",
            )
            if research_status == "OK":
                research_status = "WARN"

    results["research"] = {
        "status": research_status,
        "required": research_required,
        "approved": research_approved,
        "file": research_file.name if research_file else None,
        "evidence_file": research_evidence_file.name if research_evidence_file.exists() else None,
        "messages": research_messages,
    }

    warnings_total = len([f for f in findings_all if f.get("severity") == "warning"])
    errors_total = len([f for f in findings_all if f.get("severity") == "error"])
    ready = errors_total == 0 and (warnings_total == 0 or not args.strict)
    blocking = blocking_findings(findings_all, strict=args.strict)
    summary = {
        "overall": "PASS" if ready else "FAIL",
        "mode": "strict" if args.strict else "soft",
        "blocking_warnings": bool(args.strict and warnings_total > 0),
        "warnings": warnings_total,
        "errors": errors_total,
        "ready_for_execution": ready,
        "findings": findings_all,
        "blocking_findings": blocking,
        "next_fix_command": next_fix_command(findings_all, strict=args.strict),
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
            print(
                f"  {layer}: {entry.get('status')} "
                f"(warnings: {entry.get('warnings', 0)}, errors: {entry.get('errors', 0)})"
            )
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
        if summary.get("blocking_findings"):
            print("- Blocking Findings:")
            for finding in summary["blocking_findings"]:
                line = finding.get("line")
                loc = f"{finding.get('file')}:{line}" if line else finding.get("file")
                print(
                    "  "
                    f"[{finding.get('id')}] {finding.get('severity').upper()} "
                    f"{finding.get('message')} | source={loc} | "
                    f"section={finding.get('section')} | fix={finding.get('fix_command')}"
                )
        if summary.get("next_fix_command"):
            print(f"- Next Fix Command: {summary['next_fix_command']}")
        if args.strict and (warnings_total > 0 or errors_total > 0):
            print("✗ STRICT MODE: WARNINGS ARE BLOCKING. FIX BEFORE PROCEEDING.")
            print("FAIL: Validation produced blocking findings under strict mode.")
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
