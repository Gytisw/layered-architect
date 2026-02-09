#!/usr/bin/env python3
"""
Guided start script to detect fresh vs existing projects and suggest next steps.
"""

import os
import sys
from pathlib import Path

from log_utils import init_logger

EXCLUDE_DIRS = {".git", ".plan", "node_modules", "dist", "build", "out", "venv", ".venv", "__pycache__", "skills"}


def find_markdown_files(root: Path) -> int:
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if filename.lower().endswith(".md"):
                count += 1
    return count


def main() -> None:
    logger = init_logger("start_arch")
    root = Path(".").resolve()
    plan_dir = root / ".plan"

    if plan_dir.exists():
        has_layers = any(plan_dir.glob("L*-*.md"))
        if has_layers:
            print("Detected existing .plan directory with layer files.")
            print("Suggested next steps:")
            print("- Continue with the next layer in .plan/")
            print("- Validate the current layer: python scripts/arch.py validate --layer L# --path .plan")
            logger.log(
                "info",
                "plan_detected",
                "Existing .plan directory with layer files",
                {"plan_dir": str(plan_dir)},
            )
            return

    md_count = find_markdown_files(root)
    if md_count > 0:
        print("No .plan directory found, but existing documentation is present.")
        print("Suggested next steps:")
        print("- Generate a mapping: python scripts/arch.py map --suggest")
        print("- Review/edit plan.map.yml")
        print("- Generate .plan summaries: python scripts/arch.py map --apply")
        logger.log("info", "docs_detected", "Docs detected without .plan", {"md_files": md_count})
        return

    print("No .plan directory and no documentation detected.")
    print("Suggested next steps:")
    print("- Initialize in current repo: python scripts/arch.py init --path .")
    print("- Or create a new folder: python scripts/arch.py init <project_name>")
    logger.log("info", "fresh_start", "No .plan or docs detected")


if __name__ == "__main__":
    main()
