#!/usr/bin/env python3
"""
Unified CLI for layered-architect.
"""

import argparse
import json
import sys
from pathlib import Path

import init_architecture
import validate_all
import validate_layer
import validate_dependencies
import map_architecture
import import_plan
from path_utils import resolve_plan_dir


def run_main(module_main, argv) -> int:
    old_argv = sys.argv[:]
    sys.argv = argv
    try:
        result = module_main()
        if isinstance(result, int):
            return result
        return 0
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        return 1
    finally:
        sys.argv = old_argv


def cmd_init(args) -> int:
    argv = ["init_architecture.py"]
    if args.here:
        argv.append("--here")
    if args.path:
        argv.extend(["--path", args.path])
    if args.project:
        argv.append(args.project)
    return run_main(init_architecture.main, argv)


def cmd_validate(args) -> int:
    if args.layer:
        argv = ["validate_layer.py", "--layer", args.layer]
        if args.path:
            argv.extend(["--path", args.path])
        if args.soft:
            argv.append("--soft")
        if args.strict:
            argv.append("--strict")
        return run_main(validate_layer.main, argv)

    argv = ["validate_all.py"]
    if args.path:
        argv.extend(["--path", args.path])
    if args.format:
        argv.extend(["--format", args.format])
    if args.strict:
        argv.append("--strict")
    if args.auto_constraints:
        argv.append("--auto-constraints")
    if args.auto_deps:
        argv.append("--auto-deps")
    if args.no_write:
        argv.append("--no-write")
    return run_main(validate_all.main, argv)


def cmd_deps(args) -> int:
    argv = ["validate_dependencies.py"]
    if args.path:
        argv.extend(["--path", args.path])
    if args.strict:
        argv.append("--strict")
    if args.auto_stub:
        argv.append("--auto-stub")
    if args.no_write:
        argv.append("--no-write")
    return run_main(validate_dependencies.main, argv)


def cmd_map(args) -> int:
    argv = ["map_architecture.py"]
    if args.map:
        argv.extend(["--map", args.map])
    if args.suggest:
        argv.append("--suggest")
    if args.apply:
        argv.append("--apply")
    if args.out_dir:
        argv.extend(["--out-dir", args.out_dir])
    if args.cite:
        argv.append("--cite")
    if args.max_words is not None:
        argv.extend(["--max-words", str(args.max_words)])
    if args.max_bullets is not None:
        argv.extend(["--max-bullets", str(args.max_bullets)])
    return run_main(map_architecture.main, argv)


def cmd_import(args) -> int:
    argv = ["import_plan.py", "--source", args.source]
    if args.target:
        argv.extend(["--target", args.target])
    if args.layer:
        argv.extend(["--layer", args.layer])
    return run_main(import_plan.main, argv)


def find_docs(root: Path) -> bool:
    for path in root.rglob("*.md"):
        if ".plan" in path.parts or ".git" in path.parts:
            continue
        return True
    return False


def cmd_doctor(args) -> int:
    plan_dir = resolve_plan_dir(args.path)
    result = {"status": "unknown", "next_step": "", "reason": ""}
    if not plan_dir or not plan_dir.exists():
        root = Path(args.path or ".").resolve()
        if find_docs(root):
            result.update(
                {
                    "status": "docs_no_plan",
                    "next_step": "python scripts/arch.py map --suggest --apply",
                    "reason": "Documentation exists but .plan is missing",
                }
            )
            if args.json:
                print(json.dumps(result, indent=2))
                return 0
            print("No .plan directory found, but documentation exists.")
            print("Next step: python scripts/arch.py map --suggest --apply")
            return 0
        result.update(
            {
                "status": "fresh_start",
                "next_step": "python scripts/arch.py init --path .",
                "reason": "No .plan or docs detected",
            }
        )
        if args.json:
            print(json.dumps(result, indent=2))
            return 0
        print("No .plan directory and no documentation found.")
        print("Next step: python scripts/arch.py init --path .")
        return 0

    dep_file = plan_dir / "dependencies.yml"
    if not dep_file.exists():
        result.update(
            {
                "status": "deps_missing",
                "next_step": "python scripts/arch.py deps --auto-stub --path .plan",
                "reason": "dependencies.yml missing",
            }
        )
        if args.json:
            print(json.dumps(result, indent=2))
            return 0
        print("dependencies.yml is missing.")
        print("Next step: python scripts/arch.py deps --auto-stub --path .plan")
        return 0

    try:
        import yaml  # type: ignore
        data = yaml.safe_load(dep_file.read_text()) or {}
        status = str(data.get("status", "draft")).strip().lower()
        if status != "complete":
            result.update(
                {
                    "status": "deps_incomplete",
                    "next_step": "Finalize dependencies.yml and set status: complete",
                    "reason": "dependencies.yml status is not complete",
                }
            )
            if args.json:
                print(json.dumps(result, indent=2))
                return 0
            print("dependencies.yml is not complete.")
            print("Next step: finalize dependencies.yml and set status: complete")
            return 0
    except Exception:
        result.update(
            {
                "status": "deps_invalid",
                "next_step": "Fix dependencies.yml format",
                "reason": "dependencies.yml could not be parsed",
            }
        )
        if args.json:
            print(json.dumps(result, indent=2))
            return 0
        print("dependencies.yml could not be parsed.")
        print("Next step: fix dependencies.yml format")
        return 0

    for layer_file in [
        "L1-meta-architecture.md",
        "L2-system-architecture.md",
        "L3-component-design.md",
        "L4-implementation.md",
    ]:
        if not (plan_dir / layer_file).exists():
            result.update(
                {
                    "status": "layer_missing",
                    "next_step": f"Complete {layer_file}",
                    "reason": f"{layer_file} missing in .plan",
                }
            )
            if args.json:
                print(json.dumps(result, indent=2))
                return 0
            print(f"Missing {layer_file}.")
            print("Next step: complete the missing layer file")
            return 0

    result.update(
        {
            "status": "ready",
            "next_step": "python scripts/arch.py validate --path .plan --auto-constraints --auto-deps",
            "reason": "All core artifacts present",
        }
    )
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print("All core artifacts present.")
    print("Next step: python scripts/arch.py validate --path .plan --auto-constraints --auto-deps")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified CLI for layered-architect")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize .plan structure")
    p_init.add_argument("project", nargs="?", help="Project name or path")
    p_init.add_argument("--path", help="Path to existing project root or .plan")
    p_init.add_argument("--here", action="store_true", help="Initialize in current dir")
    p_init.set_defaults(func=cmd_init)

    p_validate = sub.add_parser("validate", help="Validate architecture")
    p_validate.add_argument("--path", help="Path to .plan or project")
    p_validate.add_argument("--format", choices=["text", "json"])
    p_validate.add_argument("--strict", action="store_true")
    p_validate.add_argument("--auto-constraints", action="store_true")
    p_validate.add_argument("--auto-deps", action="store_true")
    p_validate.add_argument("--no-write", action="store_true")
    p_validate.add_argument("--layer", help="Validate a single layer (debug)")
    p_validate.add_argument("--soft", action="store_true", help="Soft gate for layer")
    p_validate.set_defaults(func=cmd_validate)

    p_deps = sub.add_parser("deps", help="Validate dependency graph")
    p_deps.add_argument("--path", help="Path to .plan")
    p_deps.add_argument("--strict", action="store_true")
    p_deps.add_argument("--auto-stub", action="store_true")
    p_deps.add_argument("--no-write", action="store_true")
    p_deps.set_defaults(func=cmd_deps)

    p_map = sub.add_parser("map", help="Map existing docs into .plan")
    p_map.add_argument("--map", help="Path to plan.map.yml")
    p_map.add_argument("--suggest", action="store_true")
    p_map.add_argument("--apply", action="store_true")
    p_map.add_argument("--out-dir", help="Output dir for .plan")
    p_map.add_argument("--cite", action="store_true")
    p_map.add_argument("--max-words", type=int)
    p_map.add_argument("--max-bullets", type=int)
    p_map.set_defaults(func=cmd_map)

    p_import = sub.add_parser("import", help="Import existing draft")
    p_import.add_argument("--source", required=True)
    p_import.add_argument("--target")
    p_import.add_argument("--layer")
    p_import.set_defaults(func=cmd_import)

    p_doctor = sub.add_parser("doctor", help="Suggest next action")
    p_doctor.add_argument("--path", help="Path to project or .plan")
    p_doctor.add_argument("--json", action="store_true", help="Emit JSON output")
    p_doctor.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
