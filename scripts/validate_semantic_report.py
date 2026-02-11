#!/usr/bin/env python3
"""
Validate semantic-validation report for required shards.
"""

import argparse
import json
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


SHARD_HEADER_RE = re.compile(r"^##\s*Shard\s*([A-G])\b.*$", re.IGNORECASE | re.MULTILINE)


def _split_markdown_shards(content: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(SHARD_HEADER_RE.finditer(content))
    for i, match in enumerate(matches):
        shard = match.group(1).upper()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections[shard] = content[start:end].strip()
    return sections


def _parse_json_shards(content: str) -> dict[str, dict]:
    try:
        data = json.loads(content)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    shards = data.get("shards", {})
    if not isinstance(shards, dict):
        return {}
    parsed: dict[str, dict] = {}
    for key, value in shards.items():
        shard_key = str(key).strip().upper()
        if shard_key in {"A", "B", "C", "D", "E", "F", "G"} and isinstance(value, dict):
            parsed[shard_key] = value
    return parsed


def validate_report(plan_dir: Path, task_capable: bool = False) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    report = find_report(plan_dir)
    if report is None:
        errors.append("semantic-validation report missing (.plan/semantic-validation.md or .json)")
        return warnings, errors

    content = report.read_text(encoding="utf-8")
    required = ["a", "b", "c", "d", "e"]
    if (plan_dir / "L0-problem-framing.md").exists():
        required.append("f")
    if (plan_dir / "L5-operability-readiness.md").exists():
        required.append("g")

    md_sections = _split_markdown_shards(content)
    json_sections = _parse_json_shards(content) if report.suffix.lower() == ".json" else {}

    missing: list[str] = []
    shard_executors: dict[str, str] = {}
    for shard in required:
        key = shard.upper()
        if key not in md_sections and key not in json_sections:
            missing.append(f"SHARD {key}")
            continue

        if key in json_sections:
            section = json_sections[key]
            status = str(section.get("status", "")).strip().lower()
            executor = str(section.get("executor", "")).strip()
            evidence = section.get("evidence_refs", [])
            findings = section.get("findings", [])
            if status not in {"pass", "warn", "fail"}:
                warnings.append(f"SHARD {key}: missing or invalid status")
            if not executor:
                warnings.append(f"SHARD {key}: missing executor metadata")
            else:
                shard_executors[key] = executor
            if not isinstance(evidence, list) or not evidence:
                warnings.append(f"SHARD {key}: missing evidence references")
            if status in {"warn", "fail"} and (not isinstance(findings, list) or not findings):
                warnings.append(f"SHARD {key}: WARN/FAIL requires non-empty findings")
            continue

        section = md_sections[key]
        status_match = re.search(r"status\s*:\s*(pass|warn|fail)", section, re.IGNORECASE)
        if not status_match:
            warnings.append(f"SHARD {key}: missing status")
            status_value = ""
        else:
            status_value = status_match.group(1).lower()
        executor_match = re.search(r"executor(?:_id)?\s*:\s*([^\n]+)", section, re.IGNORECASE)
        if not executor_match:
            warnings.append(f"SHARD {key}: missing executor metadata")
        else:
            shard_executors[key] = executor_match.group(1).strip()
        evidence_match = re.search(r"evidence(?:_refs?|_ref)?\s*:\s*([^\n]+)", section, re.IGNORECASE)
        if not evidence_match:
            warnings.append(f"SHARD {key}: missing evidence references")
        finding_present = bool(re.search(r"finding_id\s*:\s*", section, re.IGNORECASE))
        if status_value in {"warn", "fail"} and not finding_present:
            warnings.append(f"SHARD {key}: WARN/FAIL requires finding_id entries")

    if missing:
        warnings.append("Missing shards: " + ", ".join(missing))

    if task_capable:
        required_keys = [s.upper() for s in required]
        missing_executor = [s for s in required_keys if s not in shard_executors]
        if missing_executor:
            warnings.append(
                "Task-capable mode requires executor per shard; missing executors for: "
                + ", ".join(missing_executor)
            )
        else:
            unique_count = len(set(shard_executors.values()))
            if unique_count != len(required_keys):
                warnings.append(
                    "Task-capable mode requires one executor per shard; found reused executor ids"
                )

    return warnings, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate semantic-validation report")
    parser.add_argument("--path", default=".plan", help="Path to .plan directory")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on warnings")
    parser.add_argument(
        "--task-capable",
        action="store_true",
        help="Require one executor per shard (fanout enforcement)",
    )
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL logging")
    args = parser.parse_args()

    logger = init_logger("validate_semantic_report", enabled=not args.no_log)
    plan_dir = resolve_plan_dir(args.path)
    if not plan_dir or not plan_dir.exists():
        print(f"Error: .plan directory not found (searched from {args.path})")
        return 1

    warnings, errors = validate_report(plan_dir, task_capable=args.task_capable)

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
