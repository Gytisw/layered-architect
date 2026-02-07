#!/usr/bin/env python3
"""
Path discovery helpers for layered-architect scripts.
"""

from pathlib import Path
from typing import Optional


def find_plan_dir(start: Path) -> Optional[Path]:
    """Find a .plan directory by walking up from a start path."""
    current = start.resolve()
    if current.is_file():
        current = current.parent
    if current.name == ".plan" and current.exists():
        return current

    for _ in range(6):
        candidate = current / ".plan"
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def resolve_plan_dir(path_arg: Optional[str]) -> Optional[Path]:
    if path_arg:
        path = Path(path_arg).expanduser()
        if path.is_dir() and path.name == ".plan":
            return path.resolve()
        if path.is_dir():
            plan = path / ".plan"
            if plan.exists():
                return plan.resolve()
            return path.resolve()
        if path.is_file():
            return path.parent.resolve()
    return find_plan_dir(Path("."))
