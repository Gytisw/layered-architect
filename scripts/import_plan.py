#!/usr/bin/env python3
"""
Import existing architecture content into .plan files.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List

from log_utils import init_logger
from path_utils import resolve_plan_dir

LAYER_FILES = {
    "L1": "L1-meta-architecture.md",
    "L2": "L2-system-architecture.md",
    "L3": "L3-component-design.md",
    "L4": "L4-implementation.md",
    "L5": "L5-operability-readiness.md",
}

LAYER_TITLES = {
    "L1": ["L1", "Meta-Architecture", "Meta Architecture"],
    "L2": ["L2", "System Architecture"],
    "L3": ["L3", "Component Design", "Components"],
    "L4": ["L4", "Implementation"],
    "L5": ["L5", "Operability", "Readiness"],
}


def split_by_layers(content: str) -> Dict[str, str]:
    header_pattern = re.compile(r"^#{1,4}\s+(.+)$")
    current_layer = None
    sections: Dict[str, List[str]] = {k: [] for k in LAYER_FILES}

    for line in content.splitlines():
        match = header_pattern.match(line.strip())
        if match:
            title = match.group(1).strip()
            for layer, markers in LAYER_TITLES.items():
                if any(marker.lower() in title.lower() for marker in markers):
                    current_layer = layer
                    break
        if current_layer:
            sections[current_layer].append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


def write_layer(plan_dir: Path, layer: str, text: str) -> None:
    plan_dir.mkdir(parents=True, exist_ok=True)
    target = plan_dir / LAYER_FILES[layer]
    target.write_text(text.strip() + "\n", encoding="utf-8")


def import_from_file(source: Path, plan_dir: Path, layer: str | None) -> int:
    content = source.read_text(encoding="utf-8")
    if layer:
        if layer not in LAYER_FILES:
            print(f"Error: unknown layer {layer}")
            return 1
        write_layer(plan_dir, layer, content)
        return 0

    parts = split_by_layers(content)
    if not parts:
        print("Error: Could not detect layer sections; use --layer to target a file.")
        return 1
    for layer_key, text in parts.items():
        write_layer(plan_dir, layer_key, text)
    return 0


def import_from_dir(source: Path, plan_dir: Path) -> int:
    found = False
    for layer, filename in LAYER_FILES.items():
        candidate = source / filename
        if candidate.exists():
            write_layer(plan_dir, layer, candidate.read_text(encoding="utf-8"))
            found = True
    if found:
        return 0

    # Fallback: find any markdown with L1/L2/etc in name.
    for md in source.glob("*.md"):
        for layer, filename in LAYER_FILES.items():
            if layer.lower() in md.name.lower():
                write_layer(plan_dir, layer, md.read_text(encoding="utf-8"))
                found = True
    if not found:
        print("Error: No matching layer files found in source directory")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Import existing content into .plan")
    parser.add_argument("--source", required=True, help="Source file or directory")
    parser.add_argument("--target", help="Target .plan directory")
    parser.add_argument("--layer", help="Single layer to import (L1-L5)")
    args = parser.parse_args()

    logger = init_logger("import_plan")
    source = Path(args.source).resolve()
    if not source.exists():
        print(f"Error: source not found: {source}")
        return 1

    if args.target:
        plan_dir = Path(args.target).resolve()
    else:
        plan_dir = resolve_plan_dir(None) or Path(".plan").resolve()
    if plan_dir.name != ".plan":
        plan_dir = plan_dir / ".plan"
    plan_dir.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        result = import_from_dir(source, plan_dir)
    else:
        result = import_from_file(source, plan_dir, args.layer)

    logger.log(
        "info",
        "import_complete",
        "Import complete",
        {"source": str(source), "target": str(plan_dir), "result": result},
    )
    return result


if __name__ == "__main__":
    sys.exit(main())
