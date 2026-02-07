#!/usr/bin/env python3
"""
Generate Mermaid and PlantUML diagrams from L2 System Architecture.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

from log_utils import init_logger
from path_utils import resolve_plan_dir

SUBSYSTEM_HEADERS = ["Subsystems", "Subsystem Inventory", "Subsystem Overview", "Components"]
DATAFLOW_HEADERS = ["Data Flow", "Data Flow Diagrams", "Dataflow", "Data Flows"]


def find_section(content: str, headers: List[str]) -> List[str]:
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
    return section_lines


def parse_subsystems(lines: List[str]) -> List[str]:
    subsystems: List[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^[-*]\s+", stripped):
            name = re.sub(r"^[-*]\s+", "", stripped)
            name = re.sub(r"\*\*|\*", "", name).strip()
            if name:
                subsystems.append(name)
        elif re.match(r"^\d+\.\s+", stripped):
            name = re.sub(r"^\d+\.\s+", "", stripped)
            if name:
                subsystems.append(name)
    return subsystems


def parse_dataflow(lines: List[str]) -> List[Tuple[str, str]]:
    edges: List[Tuple[str, str]] = []
    arrow_pattern = re.compile(r"(.+?)\s*[-=]*>\s*(.+)")
    for line in lines:
        match = arrow_pattern.search(line)
        if match:
            src = match.group(1).strip()
            dst = match.group(2).strip()
            if src and dst:
                edges.append((src, dst))
    return edges


def render_mermaid(subsystems: List[str], edges: List[Tuple[str, str]]) -> str:
    lines = ["flowchart LR"]
    for name in subsystems:
        lines.append(f'  {slug(name)}["{name}"]')
    for src, dst in edges:
        lines.append(f'  {slug(src)} --> {slug(dst)}')
    return "\n".join(lines) + "\n"


def render_plantuml(subsystems: List[str], edges: List[Tuple[str, str]]) -> str:
    lines = ["@startuml", "skinparam componentStyle rectangle"]
    for name in subsystems:
        lines.append(f'component "{name}" as {slug(name)}')
    for src, dst in edges:
        lines.append(f"{slug(src)} --> {slug(dst)}")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "node"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate diagrams from L2 docs")
    parser.add_argument("--path", default=".plan", help="Path to .plan directory")
    parser.add_argument(
        "--out", default="diagrams", help="Output directory under .plan"
    )
    parser.add_argument(
        "--format",
        choices=["mermaid", "plantuml", "both"],
        default="both",
        help="Diagram format to generate",
    )
    args = parser.parse_args()

    plan_dir = resolve_plan_dir(args.path) or Path(args.path).resolve()
    l2_file = plan_dir / "L2-system-architecture.md"
    if not l2_file.exists():
        print(f"Error: L2 file not found: {l2_file}")
        sys.exit(1)

    content = l2_file.read_text(encoding="utf-8")
    subsystems = parse_subsystems(find_section(content, SUBSYSTEM_HEADERS))
    edges = parse_dataflow(find_section(content, DATAFLOW_HEADERS))

    out_dir = plan_dir / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    logger = init_logger("generate_diagrams")

    if args.format in ("mermaid", "both"):
        mermaid = render_mermaid(subsystems, edges)
        (out_dir / "system-flow.mmd").write_text(mermaid, encoding="utf-8")
    if args.format in ("plantuml", "both"):
        plantuml = render_plantuml(subsystems, edges)
        (out_dir / "system-flow.puml").write_text(plantuml, encoding="utf-8")

    logger.log(
        "info",
        "diagrams_generated",
        "Diagrams generated",
        {"subsystems": len(subsystems), "edges": len(edges), "out": str(out_dir)},
    )
    print(f"Generated diagrams in {out_dir}")


if __name__ == "__main__":
    main()
