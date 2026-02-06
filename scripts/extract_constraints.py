#!/usr/bin/env python3
"""
Extract CON-### constraints from L1 markdown and populate constraints.yml.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

from log_utils import init_logger

CONSTRAINT_ID_PATTERN = re.compile(r"\bCON-\d{3,}\b")


def strip_code_blocks(lines: List[str]) -> List[str]:
    cleaned = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        cleaned.append(line)
    return cleaned


def extract_constraints_from_text(text: str) -> Dict[str, str]:
    constraints: Dict[str, str] = {}
    for line in strip_code_blocks(text.splitlines()):
        if "CON-" not in line:
            continue
        ids = CONSTRAINT_ID_PATTERN.findall(line)
        if not ids:
            continue

        clean_line = re.sub(r"^[-*]\s+|\d+\.\s+", "", line).strip()

        # If table row, try to pick column after ID as text.
        if "|" in line:
            cols = [c.strip() for c in line.split("|") if c.strip()]
            for idx, col in enumerate(cols):
                if CONSTRAINT_ID_PATTERN.search(col):
                    if idx + 1 < len(cols):
                        clean_line = cols[idx + 1]
                    else:
                        clean_line = col
                    break

        for cid in ids:
            if cid not in constraints:
                constraints[cid] = clean_line or "TBD"
    return constraints


def increment_version(version: str) -> str:
    if isinstance(version, (int, float)):
        major = int(version)
        return f"{major}.0.1"
    if not isinstance(version, str):
        return "1.0.0"

    parts = version.split(".")
    if len(parts) == 3:
        try:
            major, minor, patch = parts
            new_patch = int(patch) + 1
            return f"{major}.{minor}.{new_patch}"
        except ValueError:
            pass
    if len(parts) == 2 and all(p.isdigit() for p in parts):
        major, minor = parts
        return f"{major}.{minor}.1"
    if len(parts) == 1 and parts[0].isdigit():
        major = parts[0]
        return f"{major}.0.1"
    return version


def resolve_l1_file(path: Path) -> Path | None:
    if path.is_file():
        return path
    if path.is_dir():
        candidate = path / "L1-meta-architecture.md"
        if candidate.exists():
            return candidate
    return None


def load_constraints(path: Path) -> Tuple[Dict, List[Dict]]:
    if not path.exists():
        return {"version": "1.0.0", "constraints": []}, []
    data = yaml.safe_load(path.read_text()) or {"version": "1.0.0", "constraints": []}
    constraints = data.get("constraints", [])
    if not isinstance(constraints, list):
        constraints = []
    return data, constraints


def save_constraints(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract CON-### constraints from L1 markdown into constraints.yml"
    )
    parser.add_argument(
        "path",
        help="Path to L1 markdown file or directory containing L1-meta-architecture.md",
    )
    parser.add_argument(
        "--out",
        help="Output constraints.yml path (default: .plan/constraints.yml)",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing constraints.yml (default behavior)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite constraints.yml instead of merging",
    )

    args = parser.parse_args()
    logger = init_logger("extract_constraints")

    target = Path(args.path).resolve()
    l1_file = resolve_l1_file(target)
    if not l1_file:
        print("Error: Could not find L1-meta-architecture.md at the given path")
        sys.exit(1)

    out_path = Path(args.out) if args.out else l1_file.parent / "constraints.yml"
    out_path = out_path.resolve()

    text = l1_file.read_text(encoding="utf-8")
    extracted = extract_constraints_from_text(text)

    data, existing = load_constraints(out_path)
    existing_ids = {c.get("id") for c in existing if isinstance(c, dict)}

    merged = list(existing) if (args.merge or not args.overwrite) else []
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

    data["constraints"] = merged
    if added > 0:
        data["version"] = increment_version(data.get("version", "1.0.0"))

    save_constraints(out_path, data)

    print(f"Extracted {len(extracted)} constraints from {l1_file.name}")
    print(f"Added {added} new constraints to {out_path}")
    logger.log(
        "info",
        "constraints_extracted",
        "Constraints extracted",
        {"l1_file": str(l1_file), "out": str(out_path), "added": added},
    )


if __name__ == "__main__":
    main()
