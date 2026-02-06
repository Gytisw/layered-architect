#!/usr/bin/env python3
"""
Dependency preflight for layered-architect scripts.
Reports missing Python packages and a safe install command.
"""

import sys

REQUIRED = [
    ("yaml", "pyyaml"),
]


def main() -> None:
    missing = []
    for module, package in REQUIRED:
        try:
            __import__(module)
        except Exception:
            missing.append(package)

    if not missing:
        print("All dependencies are installed.")
        sys.exit(0)

    print("Missing dependencies:")
    for pkg in missing:
        print(f"- {pkg}")

    print("\nInstall with one of:")
    print("  pip install -r requirements.txt")
    print("  uv pip install -r requirements.txt")
    sys.exit(1)


if __name__ == "__main__":
    main()
