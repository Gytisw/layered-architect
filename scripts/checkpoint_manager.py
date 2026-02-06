#!/usr/bin/env python3
"""
Checkpoint Manager for Architecture Planning
Manages save/load of checkpoint state during L1-L4 architecture planning.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

from log_utils import init_logger

CHECKPOINT_DIR = Path(".plan")
CHECKPOINT_FILE = CHECKPOINT_DIR / "checkpoint.yml"
LAYERS = ["L1", "L2", "L3", "L4"]


def detect_current_state() -> dict[str, Any]:
    validation_status = {}
    last_completed = None
    current_layer = None
    layer_files = {
        "L1": CHECKPOINT_DIR / "L1-meta-architecture.md",
        "L2": CHECKPOINT_DIR / "L2-system-architecture.md",
        "L3": CHECKPOINT_DIR / "L3-component-design.md",
        "L4": CHECKPOINT_DIR / "L4-implementation.md",
    }

    for layer in LAYERS:
        layer_file = layer_files.get(layer, CHECKPOINT_DIR / f"{layer}.md")

        if layer_file.exists():
            content = layer_file.read_text()

            if (
                "✓" in content
                or "COMPLETE" in content.upper()
                or "DONE" in content.upper()
            ):
                validation_status[layer] = "PASSED"
                last_completed = layer
            elif (
                "IN_PROGRESS" in content.upper()
                or "WIP" in content.upper()
                or "🔄" in content
            ):
                validation_status[layer] = "IN_PROGRESS"
                if current_layer is None:
                    current_layer = layer
            else:
                validation_status[layer] = "NOT_STARTED"
        else:
            validation_status[layer] = "NOT_STARTED"

    if current_layer is None:
        if last_completed is None:
            current_layer = "L1"
        elif last_completed == "L4":
            current_layer = "L4"
        else:
            current_layer = LAYERS[LAYERS.index(last_completed) + 1]

    constraint_version = detect_constraint_version()

    return {
        "current_layer": current_layer,
        "last_completed": last_completed,
        "validation_status": validation_status,
        "constraint_registry_version": constraint_version,
        "timestamp": datetime.now().isoformat(),
    }


def detect_constraint_version() -> int:
    plan_constraint_file = CHECKPOINT_DIR / "constraints.yml"
    legacy_constraint_file = Path("constraints.yml")

    for constraint_file in [plan_constraint_file, legacy_constraint_file]:
        if constraint_file.exists():
            try:
                data = yaml.safe_load(constraint_file.read_text())
                return data.get("version", 1)
            except Exception:
                pass
    return 1


def ensure_checkpoint_dir() -> None:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def save_checkpoint() -> None:
    ensure_checkpoint_dir()
    logger = init_logger("checkpoint_manager")

    state = detect_current_state()

    with open(CHECKPOINT_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Checkpoint saved to {CHECKPOINT_FILE}")
    print(f"  Current Layer: {state['current_layer']}")
    print(f"  Last Completed: {state['last_completed'] or 'None'}")
    print(f"  Timestamp: {state['timestamp']}")
    logger.log(
        "info",
        "checkpoint_saved",
        "Checkpoint saved",
        {"current_layer": state["current_layer"], "last_completed": state["last_completed"]},
    )


def load_checkpoint() -> dict[str, Any] | None:
    if not CHECKPOINT_FILE.exists():
        return None

    try:
        with open(CHECKPOINT_FILE, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        return None


def display_checkpoint(checkpoint: dict[str, Any] | None) -> None:
    if checkpoint is None:
        print("No checkpoint found.")
        print(f"Expected at: {CHECKPOINT_FILE.absolute()}")
        print("\nRun 'checkpoint_manager.py save' to create one.")
        return

    print("Current Checkpoint:")
    print(f"  Layer: {checkpoint.get('current_layer', 'N/A')}")
    print(f"  Last Completed: {checkpoint.get('last_completed', 'None')}")

    validation = checkpoint.get("validation_status", {})
    validation_str = ", ".join([f"{k}={v}" for k, v in validation.items()])
    print(f"  Validation: {validation_str}")

    print(
        f"  Constraint Version: {checkpoint.get('constraint_registry_version', 'N/A')}"
    )
    print(f"  Timestamp: {checkpoint.get('timestamp', 'N/A')}")


def list_checkpoints() -> None:
    checkpoint = load_checkpoint()

    if checkpoint is None:
        print("No checkpoints available.")
        return

    print("Checkpoint History:")
    print("-" * 40)
    print(f"1. {CHECKPOINT_FILE.name}")
    print(f"   Layer: {checkpoint.get('current_layer', 'N/A')}")
    print(f"   Status: {checkpoint.get('timestamp', 'N/A')}")
    print()
    print("(Only current checkpoint available in MVP)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage checkpoints for architecture planning"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    save_parser = subparsers.add_parser(
        "save", help="Save current state to checkpoint.yml"
    )
    save_parser.set_defaults(func=save_checkpoint)

    load_parser = subparsers.add_parser("load", help="Load and display last checkpoint")
    load_parser.set_defaults(func=lambda: display_checkpoint(load_checkpoint()))

    list_parser = subparsers.add_parser("list", help="List all checkpoints")
    list_parser.set_defaults(func=list_checkpoints)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func()


if __name__ == "__main__":
    main()
