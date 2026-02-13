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


def parse_node_identities(nodes_raw) -> Set[str]:
    identities: Set[str] = set()
    if not isinstance(nodes_raw, list):
        return identities
    for item in nodes_raw:
        if isinstance(item, str):
            if item.strip():
                identities.add(item.strip())
            continue
        if not isinstance(item, dict):
            continue
        for key in ("name", "id", "module"):
            value = item.get(key)
            if value and str(value).strip():
                identities.add(str(value).strip())
    return identities


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


def canonical_component_name(text: str) -> str:
    cleaned = normalize(text)
    tokens = [t for t in cleaned.split() if t]
    stop_words = {"module", "service", "layer", "component", "subsystem"}
    tokens = [t for t in tokens if t not in stop_words]
    return " ".join(tokens)


def extract_l3_modules(plan_dir: Path) -> Set[str]:
    l3_file = plan_dir / "L3-component-design.md"
    if not l3_file.exists():
        return set()
    content = l3_file.read_text(encoding="utf-8")
    modules: Set[str] = set()

    # Collect only explicit module headers under "Modules" section.
    in_modules = False
    header_pattern = re.compile(r"^(#{2,4})\s+(.+)$")
    for line in content.splitlines():
        match = header_pattern.match(line.strip())
        if match:
            hashes = match.group(1)
            level = len(hashes)
            title = match.group(2).strip().lower()
            if level == 2:
                in_modules = title in {"modules", "module specifications", "components"}
                continue
            if in_modules and level == 3:
                name = match.group(2).strip()
                name_l = name.lower()
                if name_l not in {"responsibilities", "public interface", "internal structure", "overview"}:
                    modules.add(name)
                continue
            if in_modules and level == 4:
                name = match.group(2).strip()
                if re.match(r"(?i)^module\s*:", name):
                    modules.add(re.sub(r"(?i)^module\s*:\s*", "", name).strip())
                continue
            if in_modules and level == 2:
                in_modules = False
            continue

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

    nodes_raw = data.get("nodes", [])
    nodes = parse_nodes(nodes_raw)
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
        identities = parse_node_identities(nodes_raw)
        normalized_nodes = {canonical_component_name(n) for n in identities if canonical_component_name(n)}
        normalized_modules = {canonical_component_name(m) for m in l3_modules if canonical_component_name(m)}
        missing = sorted(normalized_modules - normalized_nodes)
        extra = sorted(normalized_nodes - normalized_modules)
        if missing:
            preview = ", ".join(missing[:8])
            suffix = "" if len(missing) <= 8 else f" (+{len(missing) - 8} more)"
            warnings.append("Dependencies graph missing L3 modules: " + preview + suffix)
        if extra:
            preview = ", ".join(extra[:8])
            suffix = "" if len(extra) <= 8 else f" (+{len(extra) - 8} more)"
            warnings.append("Dependencies graph has nodes not in L3 modules: " + preview + suffix)
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
        for idx, err in enumerate(errors, start=1):
            print(f"- [DEP-ERR-{idx:03d}] {err}")
    if warnings:
        print("Dependency graph warnings:")
        for idx, w in enumerate(warnings, start=1):
            print(f"- [DEP-WARN-{idx:03d}] {w}")
    if errors or warnings:
        print("Next fix command:")
        print(f"  python scripts/arch.py deps --path {plan_dir} --strict")

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
