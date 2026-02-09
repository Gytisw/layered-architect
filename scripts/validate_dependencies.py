#!/usr/bin/env python3
"""
Validate dependency graph defined in .plan/dependencies.yml.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

try:
    import yaml
except ImportError:
    yaml = None

from log_utils import init_logger
from path_utils import resolve_plan_dir


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def parse_nodes(nodes_raw) -> List[str]:
    nodes: List[str] = []
    if isinstance(nodes_raw, list):
        for item in nodes_raw:
            if isinstance(item, str):
                nodes.append(item.strip())
            elif isinstance(item, dict):
                name = item.get("name") or item.get("id") or ""
                if name:
                    nodes.append(str(name).strip())
    return [n for n in nodes if n]


def parse_edges(edges_raw) -> List[Tuple[str, str]]:
    edges: List[Tuple[str, str]] = []
    if isinstance(edges_raw, list):
        for item in edges_raw:
            if isinstance(item, dict):
                src = item.get("from") or item.get("src") or item.get("source")
                dst = item.get("to") or item.get("dst") or item.get("target")
                if src and dst:
                    edges.append((str(src).strip(), str(dst).strip()))
            elif isinstance(item, str):
                match = re.split(r"\s*->\s*|\s*=>\s*", item.strip())
                if len(match) == 2:
                    edges.append((match[0].strip(), match[1].strip()))
    return [(a, b) for a, b in edges if a and b]


def detect_cycles(nodes: List[str], edges: List[Tuple[str, str]]) -> List[List[str]]:
    graph: Dict[str, List[str]] = {n: [] for n in nodes}
    for src, dst in edges:
        graph.setdefault(src, []).append(dst)

    cycles: List[List[str]] = []
    visited: Set[str] = set()
    stack: Set[str] = set()
    path: List[str] = []

    def dfs(node: str):
        visited.add(node)
        stack.add(node)
        path.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in stack:
                idx = path.index(neighbor)
                cycles.append(path[idx:] + [neighbor])
        path.pop()
        stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node)
    return cycles


def extract_l3_modules(plan_dir: Path) -> Set[str]:
    l3_file = plan_dir / "L3-component-design.md"
    if not l3_file.exists():
        return set()
    content = l3_file.read_text(encoding="utf-8")
    modules: Set[str] = set()

    # Collect bullets under "Modules" section if present
    in_modules = False
    header_pattern = re.compile(r"^#{2,4}\s+(.+)$")
    for line in content.splitlines():
        match = header_pattern.match(line.strip())
        if match:
            title = match.group(1).strip().lower()
            in_modules = title in {"modules", "module specifications", "components"}
            continue
        if in_modules and re.match(r"^[-*]\s+", line.strip()):
            name = re.sub(r"^[-*]\s+", "", line.strip())
            name = re.sub(r"\*\*|\*", "", name).strip()
            if name:
                modules.add(name)

    # Also collect ### headings as module names
    for line in content.splitlines():
        match = re.match(r"^#{3,4}\s+(.+)$", line.strip())
        if match:
            name = match.group(1).strip()
            if name.lower() not in {"responsibilities", "public interface", "internal structure"}:
                modules.add(name)

    return modules


def create_stub_dependencies(plan_dir: Path, modules: Optional[Set[str]] = None) -> None:
    dep_file = plan_dir / "dependencies.yml"
    nodes = []
    if modules:
        for name in sorted(modules):
            nodes.append({"name": name})
    else:
        nodes = [{"name": "component_a"}, {"name": "component_b"}]

    data = {
        "version": "1.0.0",
        "status": "draft",
        "nodes": nodes,
        "edges": [],
        "constraints": {"acyclic": True},
        "notes": "",
    }
    dep_file.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


def validate_dependencies(
    plan_dir: Path, auto_stub: bool = False, no_write: bool = False
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    dep_file = plan_dir / "dependencies.yml"
    if not dep_file.exists():
        if auto_stub and not no_write and yaml is not None:
            modules = extract_l3_modules(plan_dir)
            create_stub_dependencies(plan_dir, modules or None)
            errors.append(
                "dependencies.yml was missing; created stub with status: draft. "
                "Fill and set status: complete."
            )
            return warnings, errors
        errors.append("dependencies.yml not found in .plan/")
        return warnings, errors

    if yaml is None:
        errors.append("PyYAML missing; cannot parse dependencies.yml")
        return warnings, errors

    try:
        data = yaml.safe_load(dep_file.read_text()) or {}
    except Exception as exc:
        errors.append(f"Failed to parse dependencies.yml: {exc}")
        return warnings, errors

    if "modules" in data:
        errors.append(
            "Legacy 'modules' schema detected. Use nodes/edges per schemas/dependencies.schema.json"
        )

    if "nodes" not in data or "edges" not in data:
        errors.append(
            "dependencies.yml missing required 'nodes' or 'edges' (see schemas/dependencies.schema.json)"
        )
        return warnings, errors

    status = str(data.get("status", "draft")).strip().lower()
    if status != "complete":
        errors.append("dependencies.yml status is not 'complete'")

    nodes = parse_nodes(data.get("nodes", []))
    edges = parse_edges(data.get("edges", []))

    if not nodes:
        errors.append("dependencies.yml has no nodes defined")
        return warnings, errors

    node_set = {n for n in nodes}
    for src, dst in edges:
        if src not in node_set:
            errors.append(f"Edge source not in nodes: {src}")
        if dst not in node_set:
            errors.append(f"Edge target not in nodes: {dst}")

    constraints = data.get("constraints", {})
    acyclic = True
    if isinstance(constraints, dict):
        acyclic = constraints.get("acyclic", True)

    if acyclic:
        cycles = detect_cycles(nodes, edges)
        if cycles:
            errors.append(f"Dependency graph contains cycles: {cycles}")

    l3_modules = extract_l3_modules(plan_dir)
    if l3_modules:
        normalized_nodes = {normalize(n) for n in nodes}
        normalized_modules = {normalize(m) for m in l3_modules}
        missing = normalized_modules - normalized_nodes
        extra = normalized_nodes - normalized_modules
        if missing:
            warnings.append("Dependencies graph missing L3 modules: " + ", ".join(sorted(missing)))
        if extra:
            warnings.append("Dependencies graph has nodes not in L3 modules: " + ", ".join(sorted(extra)))
        if len(nodes) > 1 and not edges:
            warnings.append("Multiple nodes but no edges defined in dependencies.yml")

    return warnings, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate dependencies.yml")
    parser.add_argument("--path", default=".plan", help="Path to .plan directory")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on warnings")
    parser.add_argument(
        "--auto-stub",
        action="store_true",
        help="Create a stub dependencies.yml if missing",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Disable any auto writes (pairs with --auto-stub)",
    )
    args = parser.parse_args()

    plan_dir = resolve_plan_dir(args.path)
    if not plan_dir or not plan_dir.exists():
        print(f"Error: .plan directory not found (searched from {args.path})")
        print("AGENT FIX:")
        print("  cd /path/to/project && python scripts/arch.py deps --path .plan")
        print("  python scripts/arch.py deps --path /path/to/project/.plan")
        return 1

    logger = init_logger("validate_dependencies")
    warnings, errors = validate_dependencies(
        plan_dir, auto_stub=args.auto_stub, no_write=args.no_write
    )

    if errors:
        print("Dependency graph errors:")
        for err in errors:
            print(f"- {err}")
    if warnings:
        print("Dependency graph warnings:")
        for w in warnings:
            print(f"- {w}")

    logger.log(
        "info",
        "dependencies_validated",
        "Dependency validation complete",
        {"warnings": len(warnings), "errors": len(errors)},
    )

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
