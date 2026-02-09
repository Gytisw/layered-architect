#!/usr/bin/env python3
"""
Unified CLI for layered-architect.
"""

import argparse
import json
import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import check_consistency
import check_constraints
import check_deps
import checkpoint_manager
import constraint_add
import extract_constraints
import generate_adrs
import generate_diagrams
import init_architecture
import import_plan
import lint_architecture
import map_architecture
import validate_all
import validate_dependencies
import validate_layer
import validate_semantic_report
from path_utils import resolve_plan_dir

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


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


@contextmanager
def pushd(path: Optional[Path]):
    if not path:
        yield
        return
    old = Path(".").resolve()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


GATES_REQUIRED_FIELDS = [
    "mode",
    "question_depth",
    "l0_required",
    "l5_required",
    "research_required",
    "research_approved",
    "semantic_required",
    "semantic_completed",
    "dependencies_complete",
    "constraints_registry_present",
    "last_step",
]


def resolve_plan_and_root(path_arg: Optional[str]) -> Tuple[Optional[Path], Optional[Path]]:
    plan_dir = resolve_plan_dir(path_arg)
    if plan_dir:
        return plan_dir, plan_dir.parent
    if path_arg:
        root = Path(path_arg).expanduser().resolve()
        if root.name == ".plan":
            return root, root.parent
        return None, root
    return None, None


def load_gates(plan_dir: Path) -> Tuple[Dict, List[str]]:
    errors: List[str] = []
    if yaml is None:
        errors.append("PyYAML missing; cannot parse gates.yml")
        return {}, errors
    gates_path = plan_dir / "gates.yml"
    if not gates_path.exists():
        errors.append("gates.yml missing in .plan/")
        return {}, errors
    try:
        data = yaml.safe_load(gates_path.read_text()) or {}
    except Exception as exc:
        errors.append(f"Failed to parse gates.yml: {exc}")
        return {}, errors
    if not isinstance(data, dict):
        errors.append("gates.yml is not a valid mapping")
        return {}, errors
    missing = [k for k in GATES_REQUIRED_FIELDS if k not in data]
    if missing:
        errors.append("gates.yml missing required keys: " + ", ".join(missing))
    return data, errors


def find_report(plan_dir: Path, basename: str) -> Optional[Path]:
    for ext in (".md", ".json"):
        candidate = plan_dir / f"{basename}{ext}"
        if candidate.exists():
            return candidate
    return None


def has_external_deps_section(plan_dir: Path) -> bool:
    l2_file = plan_dir / "L2-system-architecture.md"
    if not l2_file.exists():
        return False
    content = l2_file.read_text(encoding="utf-8")
    header_pattern = re.compile(r"^#{2,4}\s+(.+)$")
    targets = {
        "external dependencies",
        "dependencies",
        "third party dependencies",
        "third-party dependencies",
    }
    for line in content.splitlines():
        match = header_pattern.match(line.strip())
        if match:
            title = match.group(1).strip().lower()
            if title in targets:
                return True
    return False


def dependencies_has_external_nodes(plan_dir: Path) -> bool:
    dep_file = plan_dir / "dependencies.yml"
    if not dep_file.exists() or yaml is None:
        return False
    try:
        data = yaml.safe_load(dep_file.read_text()) or {}
    except Exception:
        return False
    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        return False
    for node in nodes:
        if isinstance(node, dict):
            node_type = str(node.get("type", "")).strip().lower()
            if node_type in {"external", "infrastructure", "vendor", "third_party", "third-party"}:
                return True
    return False


def dependency_status(plan_dir: Path) -> str:
    dep_file = plan_dir / "dependencies.yml"
    if not dep_file.exists() or yaml is None:
        return "missing"
    try:
        data = yaml.safe_load(dep_file.read_text()) or {}
    except Exception:
        return "invalid"
    status = str(data.get("status", "draft")).strip().lower()
    return status or "draft"

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
        if args.strict or not args.soft:
            argv.append("--strict")
        if args.soft:
            argv.append("--soft")
        return run_main(validate_layer.main, argv)

    argv = ["validate_all.py"]
    if args.path:
        argv.extend(["--path", args.path])
    if args.format:
        argv.extend(["--format", args.format])
    if args.strict or not args.soft:
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


def cmd_check_deps(args) -> int:
    return run_main(check_deps.main, ["check_deps.py"])


def cmd_constraints_check(args) -> int:
    plan_dir, root = resolve_plan_and_root(args.path)
    with pushd(root):
        return run_main(check_constraints.main, ["check_constraints.py"])


def cmd_constraints_extract(args) -> int:
    argv = ["extract_constraints.py", args.path]
    if args.out:
        argv.extend(["--out", args.out])
    if args.merge:
        argv.append("--merge")
    if args.overwrite:
        argv.append("--overwrite")
    return run_main(extract_constraints.main, argv)


def cmd_constraints_add(args) -> int:
    argv = [
        "constraint_add.py",
        "--layer",
        args.layer,
        "--type",
        args.type,
        "--text",
        args.text,
    ]
    plan_dir, root = resolve_plan_and_root(args.path)
    with pushd(root):
        return run_main(constraint_add.main, argv)


def cmd_lint(args) -> int:
    argv = ["lint_architecture.py", args.path or "."]
    if args.strict:
        argv.append("--strict")
    return run_main(lint_architecture.main, argv)


def cmd_consistency(args) -> int:
    argv = ["check_consistency.py"]
    if args.path:
        argv.extend(["--path", args.path])
    return run_main(check_consistency.main, argv)


def cmd_adrs(args) -> int:
    argv = ["generate_adrs.py"]
    if args.path:
        argv.extend(["--path", args.path])
    if args.out:
        argv.extend(["--out", args.out])
    return run_main(generate_adrs.main, argv)


def cmd_diagrams(args) -> int:
    argv = ["generate_diagrams.py"]
    if args.path:
        argv.extend(["--path", args.path])
    if args.out:
        argv.extend(["--out", args.out])
    if args.format:
        argv.extend(["--format", args.format])
    return run_main(generate_diagrams.main, argv)


def cmd_checkpoint_save(args) -> int:
    plan_dir, root = resolve_plan_and_root(args.path)
    with pushd(root):
        return run_main(checkpoint_manager.main, ["checkpoint_manager.py", "save"])


def cmd_checkpoint_load(args) -> int:
    plan_dir, root = resolve_plan_and_root(args.path)
    with pushd(root):
        return run_main(checkpoint_manager.main, ["checkpoint_manager.py", "load"])


def cmd_checkpoint_status(args) -> int:
    plan_dir, root = resolve_plan_and_root(args.path)
    with pushd(root):
        return run_main(checkpoint_manager.main, ["checkpoint_manager.py", "list"])


def cmd_semantic(args) -> int:
    argv = ["validate_semantic_report.py"]
    if args.path:
        argv.extend(["--path", args.path])
    if args.strict:
        argv.append("--strict")
    return run_main(validate_semantic_report.main, argv)


def cmd_status(args) -> int:
    plan_dir, _ = resolve_plan_and_root(args.path)
    if not plan_dir or not plan_dir.exists():
        print("No .plan directory found.")
        print("Next step: python scripts/arch.py init --path .")
        return 1

    gates, gate_errors = load_gates(plan_dir)
    l0_required = bool(gates.get("l0_required", False))
    l5_required = bool(gates.get("l5_required", False))
    semantic_required = bool(gates.get("semantic_required", True))
    semantic_completed = bool(gates.get("semantic_completed", False))
    research_required = bool(gates.get("research_required", False))
    if has_external_deps_section(plan_dir) or dependencies_has_external_nodes(plan_dir):
        research_required = True
    research_approved = bool(gates.get("research_approved", False))

    def fmt(ok: bool, skip: bool = False) -> str:
        if skip:
            return "SKIP"
        return "OK" if ok else "BLOCK"

    l0_exists = (plan_dir / "L0-problem-framing.md").exists()
    l1_exists = (plan_dir / "L1-meta-architecture.md").exists()
    l2_exists = (plan_dir / "L2-system-architecture.md").exists()
    l3_exists = (plan_dir / "L3-component-design.md").exists()
    l4_exists = (plan_dir / "L4-implementation.md").exists()
    l5_exists = (plan_dir / "L5-operability-readiness.md").exists()

    constraints_present = (plan_dir / "constraints.yml").exists()
    dep_status = dependency_status(plan_dir)
    dep_complete = dep_status == "complete"
    research_log = find_report(plan_dir, "research")
    semantic_report = find_report(plan_dir, "semantic-validation")

    print("Gate Status")
    print(f"- Mode: {gates.get('mode', 'unknown')}")
    print(f"- Question depth: {gates.get('question_depth', 'unknown')}")
    print(f"- gates.yml: {fmt(not gate_errors)}")
    if gate_errors:
        for err in gate_errors:
            print(f"  - {err}")
    print(f"- L0 required: {l0_required} ({fmt(l0_exists, skip=not l0_required)})")
    print(f"- L1 present: {fmt(l1_exists)}")
    print(f"- Constraints registry: {fmt(constraints_present)}")
    print(f"- Research required: {research_required} ({fmt(research_approved, skip=not research_required)})")
    print(f"- Research log: {fmt(bool(research_log), skip=not research_required)}")
    print(f"- L2 present: {fmt(l2_exists)}")
    print(f"- Dependencies status: {dep_status} ({fmt(dep_complete)})")
    print(f"- L3 present: {fmt(l3_exists)}")
    print(f"- L4 present: {fmt(l4_exists)}")
    print(f"- L5 required: {l5_required} ({fmt(l5_exists, skip=not l5_required)})")
    print(f"- Semantic report: {fmt(bool(semantic_report), skip=not semantic_required)}")
    print(f"- Semantic completed: {fmt(semantic_completed, skip=not semantic_required)}")
    return 0


def next_required_action(plan_dir: Path, gates: Dict, gate_errors: List[str]) -> str:
    if gate_errors:
        return "Fix .plan/gates.yml to include all required keys (see schemas/gates.schema.json)."
    l0_required = bool(gates.get("l0_required", False))
    l5_required = bool(gates.get("l5_required", False))
    semantic_required = bool(gates.get("semantic_required", True))
    semantic_completed = bool(gates.get("semantic_completed", False))
    research_required = bool(gates.get("research_required", False))
    if has_external_deps_section(plan_dir) or dependencies_has_external_nodes(plan_dir):
        research_required = True
    research_approved = bool(gates.get("research_approved", False))

    l0_file = plan_dir / "L0-problem-framing.md"
    l1_file = plan_dir / "L1-meta-architecture.md"
    l2_file = plan_dir / "L2-system-architecture.md"
    l3_file = plan_dir / "L3-component-design.md"
    l4_file = plan_dir / "L4-implementation.md"
    l5_file = plan_dir / "L5-operability-readiness.md"

    if l0_required and not l0_file.exists():
        return "Complete L0: .plan/L0-problem-framing.md"
    if not l1_file.exists():
        return "Complete L1: .plan/L1-meta-architecture.md"
    if not (plan_dir / "constraints.yml").exists():
        return "Create constraints registry: arch.py constraints extract --path .plan/L1-meta-architecture.md"
    if research_required and not research_approved:
        return "Get user approval for research and set research_approved: true in .plan/gates.yml"
    if research_required and not find_report(plan_dir, "research"):
        return "Create research log: .plan/research.md (see references/research-template.md)"
    if not l2_file.exists():
        return "Complete L2: .plan/L2-system-architecture.md"
    if dependency_status(plan_dir) != "complete":
        return "Complete dependency graph: .plan/dependencies.yml (status: complete) and run arch.py deps"
    if not l3_file.exists():
        return "Complete L3: .plan/L3-component-design.md"
    if not l4_file.exists():
        return "Complete L4: .plan/L4-implementation.md"
    if l5_required and not l5_file.exists():
        return "Complete L5: .plan/L5-operability-readiness.md"
    if semantic_required and not find_report(plan_dir, "semantic-validation"):
        return "Create semantic validation report: .plan/semantic-validation.md"
    if semantic_required and not semantic_completed:
        return "Set semantic_completed: true in .plan/gates.yml after review"
    return "Run final validation: python scripts/arch.py validate --path .plan"


def cmd_next(args) -> int:
    plan_dir, _ = resolve_plan_and_root(args.path)
    if not plan_dir or not plan_dir.exists():
        print("Next step: python scripts/arch.py init --path .")
        return 1
    gates, gate_errors = load_gates(plan_dir)
    print(next_required_action(plan_dir, gates, gate_errors))
    return 0


def cmd_run(args) -> int:
    plan_dir, _ = resolve_plan_and_root(args.path)
    if not plan_dir or not plan_dir.exists():
        print("No .plan directory found.")
        print("Next step: python scripts/arch.py init --path .")
        return 1
    gates, gate_errors = load_gates(plan_dir)
    if gate_errors:
        print("Gate errors detected:")
        for err in gate_errors:
            print(f"- {err}")
        print("BLOCKED: Fix gates.yml before proceeding.")
        return 1
    next_action = next_required_action(plan_dir, gates, gate_errors)
    if next_action.startswith("Run final validation"):
        mode = str(gates.get("mode", "strict")).strip().lower()
        argv = ["validate_all.py", "--path", str(plan_dir)]
        if mode == "soft":
            argv.append("--soft")
        else:
            argv.append("--strict")
        return run_main(validate_all.main, argv)
    print("BLOCKED: Next required action:")
    print(f"- {next_action}")
    return 1


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
    p_validate.add_argument("--soft", action="store_true", help="Soft gate for full validation")
    p_validate.add_argument("--auto-constraints", action="store_true")
    p_validate.add_argument("--auto-deps", action="store_true")
    p_validate.add_argument("--no-write", action="store_true")
    p_validate.add_argument("--layer", help="Validate a single layer (debug)")
    p_validate.set_defaults(func=cmd_validate)

    p_check_deps = sub.add_parser("check-deps", help="Check Python dependencies")
    p_check_deps.set_defaults(func=cmd_check_deps)

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

    p_constraints = sub.add_parser("constraints", help="Constraint registry tools")
    c_sub = p_constraints.add_subparsers(dest="constraints_cmd", required=True)
    p_c_check = c_sub.add_parser("check", help="Check constraint conflicts")
    p_c_check.add_argument("--path", help="Path to project or .plan")
    p_c_check.set_defaults(func=cmd_constraints_check)

    p_c_extract = c_sub.add_parser("extract", help="Extract constraints from L1")
    p_c_extract.add_argument("--path", required=True, help="Path to L1 file or directory")
    p_c_extract.add_argument("--out", help="Output constraints.yml path")
    p_c_extract.add_argument("--merge", action="store_true")
    p_c_extract.add_argument("--overwrite", action="store_true")
    p_c_extract.set_defaults(func=cmd_constraints_extract)

    p_c_add = c_sub.add_parser("add", help="Add a constraint to registry")
    p_c_add.add_argument("--path", help="Path to project or .plan")
    p_c_add.add_argument("--layer", required=True, choices=constraint_add.VALID_LAYERS)
    p_c_add.add_argument("--type", required=True, choices=constraint_add.VALID_TYPES)
    p_c_add.add_argument("--text", required=True)
    p_c_add.set_defaults(func=cmd_constraints_add)

    p_lint = sub.add_parser("lint", help="Lint architecture docs")
    p_lint.add_argument("--path", help="Path to search (default: .)")
    p_lint.add_argument("--strict", action="store_true")
    p_lint.set_defaults(func=cmd_lint)

    p_consistency = sub.add_parser("consistency", help="Cross-layer consistency checks")
    p_consistency.add_argument("--path", help="Path to .plan")
    p_consistency.set_defaults(func=cmd_consistency)

    p_adrs = sub.add_parser("adrs", help="Generate ADRs from decision logs")
    p_adrs.add_argument("--path", help="Path to .plan")
    p_adrs.add_argument("--out", help="Output dir under .plan")
    p_adrs.set_defaults(func=cmd_adrs)

    p_diagrams = sub.add_parser("diagrams", help="Generate diagrams from L2")
    p_diagrams.add_argument("--path", help="Path to .plan")
    p_diagrams.add_argument("--out", help="Output dir under .plan")
    p_diagrams.add_argument("--format", choices=["mermaid", "plantuml", "both"])
    p_diagrams.set_defaults(func=cmd_diagrams)

    p_checkpoint = sub.add_parser("checkpoint", help="Checkpoint management")
    cp_sub = p_checkpoint.add_subparsers(dest="checkpoint_cmd", required=True)
    p_cp_save = cp_sub.add_parser("save", help="Save checkpoint")
    p_cp_save.add_argument("--path", help="Path to project or .plan")
    p_cp_save.set_defaults(func=cmd_checkpoint_save)
    p_cp_load = cp_sub.add_parser("load", help="Load checkpoint")
    p_cp_load.add_argument("--path", help="Path to project or .plan")
    p_cp_load.set_defaults(func=cmd_checkpoint_load)
    p_cp_status = cp_sub.add_parser("status", help="List checkpoint status")
    p_cp_status.add_argument("--path", help="Path to project or .plan")
    p_cp_status.set_defaults(func=cmd_checkpoint_status)

    p_semantic = sub.add_parser("semantic", help="Validate semantic report shards")
    p_semantic.add_argument("--path", help="Path to .plan")
    p_semantic.add_argument("--strict", action="store_true")
    p_semantic.set_defaults(func=cmd_semantic)

    p_doctor = sub.add_parser("doctor", help="Suggest next action")
    p_doctor.add_argument("--path", help="Path to project or .plan")
    p_doctor.add_argument("--json", action="store_true", help="Emit JSON output")
    p_doctor.set_defaults(func=cmd_doctor)

    p_status = sub.add_parser("status", help="Show gate status")
    p_status.add_argument("--path", help="Path to .plan or project")
    p_status.set_defaults(func=cmd_status)

    p_next = sub.add_parser("next", help="Show next required action")
    p_next.add_argument("--path", help="Path to .plan or project")
    p_next.set_defaults(func=cmd_next)

    p_run = sub.add_parser("run", help="Guided workflow runner")
    p_run.add_argument("--path", help="Path to .plan or project")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
