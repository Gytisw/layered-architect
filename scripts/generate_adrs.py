#!/usr/bin/env python3
"""
Generate ADR files from Decision Logs in layered architecture docs.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

from log_utils import init_logger
from path_utils import resolve_plan_dir

DECISION_HEADERS = [
    "Decision Log",
    "Decisions",
    "Decision Records",
    "Architecture Decisions",
]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "decision"


def find_section(content: str, header_names: List[str]) -> Optional[str]:
    lines = content.splitlines()
    section_lines: List[str] = []
    in_section = False

    header_pattern = re.compile(r"^#{2,4}\s+(.+)$")
    for line in lines:
        match = header_pattern.match(line.strip())
        if match:
            title = match.group(1).strip()
            if any(title.lower() == h.lower() for h in header_names):
                in_section = True
                section_lines = []
                continue
            if in_section:
                break
        if in_section:
            section_lines.append(line)

    if not section_lines:
        return None
    return "\n".join(section_lines).strip()


def parse_decision_block(block: str) -> List[Dict[str, str]]:
    decisions: List[Dict[str, str]] = []
    current: Dict[str, str] = {}

    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        clean = re.sub(r"[`*_]+", "", line)

        decision_match = re.search(r"\bDecision\b\s*:\s*(.+)", clean, re.IGNORECASE)
        rationale_match = re.search(r"\bRationale\b\s*:\s*(.+)", clean, re.IGNORECASE)
        impact_match = re.search(r"\bImpact\b\s*:\s*(.+)", clean, re.IGNORECASE)

        if decision_match:
            if current.get("decision"):
                decisions.append(current)
                current = {}
            current["decision"] = decision_match.group(1).strip()
            continue
        if rationale_match:
            current["rationale"] = rationale_match.group(1).strip()
            continue
        if impact_match:
            current["impact"] = impact_match.group(1).strip()
            continue

    if current.get("decision"):
        decisions.append(current)
    return decisions


def parse_yaml_decisions(content: str) -> List[Dict[str, str]]:
    yaml_match = re.search(r"```yaml\s*(.*?)```", content, re.DOTALL)
    if not yaml_match:
        return []
    try:
        data = yaml.safe_load(yaml_match.group(1))
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    decision_log = data.get("decision_log", [])
    results: List[Dict[str, str]] = []
    if isinstance(decision_log, list):
        for item in decision_log:
            if not isinstance(item, dict):
                continue
            decision = item.get("decision") or item.get("id") or "Decision"
            results.append(
                {
                    "decision": str(decision),
                    "rationale": str(item.get("rationale", "TBD")),
                    "impact": str(item.get("impact", "TBD")),
                }
            )
    return results


def extract_decisions_from_file(path: Path) -> List[Dict[str, str]]:
    content = path.read_text(encoding="utf-8")
    decisions = parse_yaml_decisions(content)

    section = find_section(content, DECISION_HEADERS)
    if section:
        decisions.extend(parse_decision_block(section))

    # Deduplicate by decision text.
    seen = set()
    deduped = []
    for item in decisions:
        key = item.get("decision", "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def render_adr(index: int, decision: Dict[str, str], layer: str, source: str) -> str:
    title = decision.get("decision", "Decision").strip()
    rationale = decision.get("rationale", "TBD").strip()
    impact = decision.get("impact", "TBD").strip()
    return (
        f"# ADR-{index:03d}: {title}\n\n"
        f"## Status\nProposed\n\n"
        f"## Context\nFrom layer: {layer}\nSource: {source}\n\n"
        f"## Decision\n{title}\n\n"
        f"## Rationale\n{rationale}\n\n"
        f"## Consequences\n{impact}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ADRs from Decision Logs")
    parser.add_argument(
        "--path",
        default=".plan",
        help="Path to .plan directory (default: .plan)",
    )
    parser.add_argument(
        "--out",
        default="decisions",
        help="Output directory for ADRs (default: decisions under .plan)",
    )
    args = parser.parse_args()

    plan_dir = resolve_plan_dir(args.path)
    if not plan_dir or not plan_dir.exists():
        print(f"Error: .plan directory not found (searched from {args.path})")
        print("AGENT FIX:")
        print("  cd /path/to/project && python scripts/generate_adrs.py --path .plan")
        print("  python scripts/generate_adrs.py --path /path/to/project/.plan")
        return 1

    out_dir = plan_dir / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    logger = init_logger("generate_adrs")

    layer_files = [
        ("L0", plan_dir / "L0-problem-framing.md"),
        ("L1", plan_dir / "L1-meta-architecture.md"),
        ("L2", plan_dir / "L2-system-architecture.md"),
        ("L3", plan_dir / "L3-component-design.md"),
        ("L4", plan_dir / "L4-implementation.md"),
        ("L5", plan_dir / "L5-operability-readiness.md"),
    ]

    all_decisions: List[Tuple[str, Path, Dict[str, str]]] = []
    for layer, file_path in layer_files:
        if not file_path.exists():
            continue
        for decision in extract_decisions_from_file(file_path):
            all_decisions.append((layer, file_path, decision))

    if not all_decisions:
        print("No decision logs found. No ADRs generated.")
        return 0

    index_lines = ["# Architecture Decision Records", ""]
    for idx, (layer, source, decision) in enumerate(all_decisions, start=1):
        title = decision.get("decision", "Decision")
        slug = slugify(title)
        adr_name = f"ADR-{idx:03d}-{slug}.md"
        adr_path = out_dir / adr_name
        adr_path.write_text(
            render_adr(idx, decision, layer, source.name), encoding="utf-8"
        )
        index_lines.append(f"- {adr_name} ({layer})")

    (out_dir / "README.md").write_text("\n".join(index_lines), encoding="utf-8")
    logger.log(
        "info",
        "adrs_generated",
        "ADRs generated",
        {"count": len(all_decisions), "output": str(out_dir)},
    )
    print(f"Generated {len(all_decisions)} ADRs in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
