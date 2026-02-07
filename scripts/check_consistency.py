#!/usr/bin/env python3
"""
Cross-layer semantic consistency checks for layered architecture docs.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

from log_utils import init_logger
from path_utils import resolve_plan_dir

CONSTRAINT_ID_PATTERN = re.compile(r"\bCON-\d{3,}\b")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def extract_constraints_from_text(text: str) -> Set[str]:
    return set(CONSTRAINT_ID_PATTERN.findall(text))


def find_section(content: str, headers: List[str]) -> str:
    lines = content.splitlines()
    section_lines: List[str] = []
    in_section = False
    header_pattern = re.compile(r"^#{2,4}\s+(.+)$")
    for line in lines:
        match = header_pattern.match(line.strip())
        if match:
            title = match.group(1).strip()
            if any(title.lower() == h.lower() for h in headers):
                in_section = True
                section_lines = []
                continue
            if in_section:
                break
        if in_section:
            section_lines.append(line)
    return "\n".join(section_lines)


def extract_bullets(block: str) -> List[str]:
    items = []
    for line in block.splitlines():
        stripped = line.strip()
        if re.match(r"^[-*]\s+", stripped):
            items.append(re.sub(r"^[-*]\s+", "", stripped).strip())
    return items


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def check_constraints(
    plan_dir: Path, warnings: List[str]
) -> Tuple[Set[str], Set[str]]:
    constraints_file = plan_dir / "constraints.yml"
    if not constraints_file.exists():
        warnings.append("constraints.yml not found in .plan/")
        return set(), set()

    data = yaml.safe_load(constraints_file.read_text()) or {}
    registry = set()
    for item in data.get("constraints", []):
        if isinstance(item, dict) and item.get("id"):
            registry.add(item["id"])

    l2 = extract_constraints_from_text(read_text(plan_dir / "L2-system-architecture.md"))
    l3 = extract_constraints_from_text(read_text(plan_dir / "L3-component-design.md"))
    l4 = extract_constraints_from_text(read_text(plan_dir / "L4-implementation.md"))
    referenced = l2 | l3 | l4

    for cid in sorted(registry - referenced):
        warnings.append(f"Constraint {cid} is defined but not referenced in L2/L3/L4")
    for cid in sorted(referenced - registry):
        warnings.append(f"Constraint {cid} is referenced but missing from constraints.yml")

    return registry, referenced


def check_interfaces(plan_dir: Path, warnings: List[str]) -> None:
    l2 = read_text(plan_dir / "L2-system-architecture.md")
    l3 = read_text(plan_dir / "L3-component-design.md")
    l2_block = find_section(l2, ["Interfaces", "Interface Contracts", "Interface Definitions"])
    l3_block = find_section(l3, ["API Contracts", "Interfaces", "API Definitions"])
    l2_items = [normalize(x) for x in extract_bullets(l2_block)]
    l3_items = [normalize(x) for x in extract_bullets(l3_block)]
    if l2_items and l3_items:
        matches = sum(1 for item in l2_items if any(item in api for api in l3_items))
        if matches == 0:
            warnings.append("No L2 interfaces appear to match L3 API contracts")


def check_modules_vs_files(plan_dir: Path, warnings: List[str]) -> None:
    l3 = read_text(plan_dir / "L3-component-design.md")
    l4 = read_text(plan_dir / "L4-implementation.md")
    modules_block = find_section(l3, ["Modules", "Module Specifications", "Components"])
    modules = [normalize(x) for x in extract_bullets(modules_block)]
    file_block = ""
    if "```" in l4:
        match = re.search(r"```[\w-]*\s*(.*?)```", l4, re.DOTALL)
        if match:
            file_block = match.group(1)
    file_paths = normalize(file_block)
    for module in modules:
        if module and module not in file_paths:
            warnings.append(f"L3 module '{module}' not found in L4 file structure")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-layer consistency checks")
    parser.add_argument("--path", default=".plan", help="Path to .plan directory")
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 if any warnings found"
    )
    args = parser.parse_args()

    plan_dir = resolve_plan_dir(args.path) or Path(args.path).resolve()
    if not plan_dir.exists():
        print(f"Error: plan directory not found: {plan_dir}")
        return 1

    logger = init_logger("check_consistency")
    warnings: List[str] = []

    check_constraints(plan_dir, warnings)
    check_interfaces(plan_dir, warnings)
    check_modules_vs_files(plan_dir, warnings)

    if warnings:
        print("Consistency checks produced warnings:")
        for w in warnings:
            print(f"- {w}")
    else:
        print("Consistency checks passed with no warnings.")

    logger.log(
        "info",
        "consistency_check_complete",
        "Consistency checks complete",
        {"warnings": len(warnings)},
    )

    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
