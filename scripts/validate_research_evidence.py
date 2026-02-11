#!/usr/bin/env python3
"""
Validate research evidence bundle used by the research gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from log_utils import init_logger
from path_utils import resolve_plan_dir


ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def _is_valid_ts(value: str) -> bool:
    return bool(ISO_TS_RE.match(str(value).strip()))


def _is_valid_source_ref(value: str) -> bool:
    text = str(value).strip()
    return text.startswith("http://") or text.startswith("https://") or text.startswith("urn:")


def validate_evidence_data(data: Dict, strict: bool = True) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    errors: List[str] = []

    required = ["version", "generated_at", "research_scope", "executor", "sources", "claims"]
    for key in required:
        if key not in data:
            errors.append(f"Missing field: {key}")

    if errors:
        return warnings, errors

    if not _is_valid_ts(data.get("generated_at", "")):
        errors.append("generated_at must be ISO-8601 UTC (e.g., 2026-02-11T10:00:00Z)")

    executor = data.get("executor")
    if not isinstance(executor, dict):
        errors.append("executor must be an object")
    else:
        mode = str(executor.get("mode", "")).strip()
        if mode not in {"subagent", "websearch", "hybrid", "manual_user_input"}:
            errors.append("executor.mode must be one of: subagent, websearch, hybrid, manual_user_input")
        task_ids = executor.get("task_ids", [])
        if mode in {"subagent", "hybrid"} and (not isinstance(task_ids, list) or not task_ids):
            errors.append("executor.task_ids must include at least one id for subagent/hybrid mode")
        if mode == "manual_user_input" and strict:
            warnings.append("executor.mode is manual_user_input; ensure user-provided evidence is complete")

    sources = data.get("sources")
    source_ids = set()
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty array")
    else:
        for idx, src in enumerate(sources, start=1):
            if not isinstance(src, dict):
                errors.append(f"sources[{idx}] must be an object")
                continue
            sid = str(src.get("id", "")).strip()
            ref = src.get("url") or src.get("reference")
            ts = src.get("retrieved_at")
            if not sid:
                errors.append(f"sources[{idx}] missing id")
            else:
                source_ids.add(sid)
            if not ref or not _is_valid_source_ref(str(ref)):
                errors.append(f"sources[{idx}] requires valid url/reference (http/https/urn)")
            if not ts or not _is_valid_ts(str(ts)):
                errors.append(f"sources[{idx}] requires retrieved_at in ISO-8601 UTC")

    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty array")
    else:
        for idx, claim in enumerate(claims, start=1):
            if not isinstance(claim, dict):
                errors.append(f"claims[{idx}] must be an object")
                continue
            cid = str(claim.get("id", "")).strip()
            text = str(claim.get("text", "")).strip()
            claim_sources = claim.get("source_ids", [])
            impacts = claim.get("decision_impacts", [])
            if not cid:
                errors.append(f"claims[{idx}] missing id")
            if not text:
                errors.append(f"claims[{idx}] missing text")
            if not isinstance(claim_sources, list) or not claim_sources:
                errors.append(f"claims[{idx}] must include at least one source_ids entry")
            else:
                for sid in claim_sources:
                    if sid not in source_ids:
                        errors.append(f"claims[{idx}] references unknown source id: {sid}")
            if not isinstance(impacts, list) or not impacts:
                errors.append(f"claims[{idx}] must include decision_impacts")

    return warnings, errors


def validate_evidence_file(plan_dir: Path, evidence_path: Path | None = None, strict: bool = True) -> Tuple[List[str], List[str]]:
    evidence = evidence_path or (plan_dir / "research.evidence.json")
    warnings: List[str] = []
    errors: List[str] = []
    if not evidence.exists():
        errors.append(f"Research evidence file missing: {evidence}")
        return warnings, errors

    try:
        data = json.loads(evidence.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Failed to parse evidence JSON: {exc}")
        return warnings, errors
    if not isinstance(data, dict):
        errors.append("Evidence JSON root must be an object")
        return warnings, errors
    return validate_evidence_data(data, strict=strict)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate research evidence bundle")
    parser.add_argument("--path", default=".plan", help="Path to .plan directory")
    parser.add_argument("--evidence", help="Path to research.evidence.json")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on warnings")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL logging")
    args = parser.parse_args()

    logger = init_logger("validate_research_evidence", enabled=not args.no_log)
    plan_dir = resolve_plan_dir(args.path)
    if not plan_dir or not plan_dir.exists():
        print(f"Error: .plan directory not found (searched from {args.path})")
        return 1

    evidence = Path(args.evidence).expanduser().resolve() if args.evidence else None
    warnings, errors = validate_evidence_file(plan_dir, evidence_path=evidence, strict=args.strict)

    if errors:
        print("Research evidence errors:")
        for err in errors:
            print(f"- {err}")
    if warnings:
        print("Research evidence warnings:")
        for warn in warnings:
            print(f"- {warn}")

    logger.log(
        "info",
        "research_evidence_checked",
        "Research evidence validation complete",
        {"warnings": len(warnings), "errors": len(errors)},
    )

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
