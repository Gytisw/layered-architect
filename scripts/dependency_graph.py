#!/usr/bin/env python3
"""
Dependency Graph Analyzer for Architecture Layers

Parses L2-system-architecture.md and L3-component-design.md to build
a dependency graph, detect circular dependencies, and output in DOT format.
"""

import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional


# Dependency patterns to search for in markdown
DEPENDENCY_PATTERNS = [
    # "Component A depends on Component B"
    re.compile(r"([^\n]+?)\s+depends\s+on\s+([^\n\.]+)", re.IGNORECASE),
    # "Component A requires Component B"
    re.compile(r"([^\n]+?)\s+requires\s+([^\n\.]+)", re.IGNORECASE),
    # "Component A uses Component B"
    re.compile(r"([^\n]+?)\s+uses\s+([^\n\.]+)", re.IGNORECASE),
]

# Component/subsystem name patterns
# Matches things like: auth-service, user-db, API Gateway, etc.
COMPONENT_PATTERNS = [
    re.compile(r"`([^`]+)`"),  # `component-name`
    re.compile(r"\*\*([^\*]+)\*\*"),  # **Component Name**
    re.compile(r"__(.+?)__"),  # __component__
]

# Skip these common words when extracting component names
SKIP_WORDS = {
    "the",
    "a",
    "an",
    "this",
    "that",
    "it",
    "its",
    "and",
    "or",
    "but",
    "if",
    "then",
    "else",
    "to",
    "from",
    "with",
    "for",
    "of",
    "in",
    "on",
    "at",
    "by",
    "service",
    "component",
    "module",
    "system",
    "layer",
    "database",
    "db",
    "cache",
    "api",
    "gateway",
}


def clean_component_name(name: str) -> str:
    """Clean and normalize component name."""
    name = name.strip()
    # Remove markdown formatting
    name = name.strip("`").strip("*").strip("_")
    # Remove common prefixes/suffixes
    name = re.sub(r"^(the|a|an)\s+", "", name, flags=re.IGNORECASE)
    return name.strip()


def extract_component_names(text: str) -> List[str]:
    """Extract potential component names from text."""
    components = []

    for pattern in COMPONENT_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            name = clean_component_name(match)
            if name and len(name) > 1 and name.lower() not in SKIP_WORDS:
                components.append(name)

    # Also look for CamelCase or snake-case identifiers
    # Pattern: word-word or WordWord
    identifier_pattern = re.compile(
        r"\b([a-z]+(?:-[a-z]+)+|[A-Z][a-z]+(?:[A-Z][a-z]+)+)\b"
    )
    for match in identifier_pattern.findall(text):
        name = match.strip()
        if name and name.lower() not in SKIP_WORDS:
            components.append(name)

    return list(set(components))  # Remove duplicates


def find_component_in_text(text: str, known_components: Set[str]) -> Optional[str]:
    """Find a known component name in text."""
    text_lower = text.lower()
    for comp in known_components:
        if comp.lower() in text_lower:
            return comp
    return None


def parse_dependencies(content: str) -> Dict[str, List[str]]:
    """
    Parse markdown content and extract dependencies.
    Returns: {component: [dependencies]}
    """
    dependencies = defaultdict(list)
    lines = content.split("\n")

    # First pass: collect all potential component names
    all_components = set()
    for line in lines:
        all_components.update(extract_component_names(line))

    # Second pass: find dependency relationships
    for line in lines:
        line = line.strip()
        if (
            not line
            or line.startswith("#")
            or line.startswith("-")
            or line.startswith("*")
        ):
            continue

        for pattern in DEPENDENCY_PATTERNS:
            matches = pattern.findall(line)
            for source_text, target_text in matches:
                source = clean_component_name(source_text)
                target = clean_component_name(target_text)

                # Try to extract better names if cleaning lost info
                if not source or len(source) < 2:
                    components = extract_component_names(source_text)
                    if components:
                        source = components[0]

                if not target or len(target) < 2:
                    components = extract_component_names(target_text)
                    if components:
                        target = components[0]

                # Skip if either is missing or they're the same
                if source and target and source.lower() != target.lower():
                    if source not in dependencies[target]:  # Avoid duplicates
                        dependencies[source].append(target)

    # Third pass: look for section headers that might define components
    # and list dependencies in bullet points
    current_component = None
    for line in lines:
        # Check for header (## Component Name)
        header_match = re.match(r"^#{2,4}\s+(.+)$", line)
        if header_match:
            header_text = header_match.group(1)
            components = extract_component_names(header_text)
            if components:
                current_component = components[0]
            continue

        # Check for bullet points under a component
        if current_component and (line.startswith("-") or line.startswith("*")):
            bullet_text = line[1:].strip()

            # Check for dependency keywords
            if any(
                keyword in bullet_text.lower()
                for keyword in ["depends", "requires", "uses"]
            ):
                components = extract_component_names(bullet_text)
                for comp in components:
                    if (
                        comp != current_component
                        and comp not in dependencies[current_component]
                    ):
                        dependencies[current_component].append(comp)

    return dict(dependencies)


def detect_cycles(dependencies: Dict[str, List[str]]) -> List[List[str]]:
    """
    Detect circular dependencies using DFS.
    Returns list of cycles found.
    """
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in dependencies.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        path.pop()
        rec_stack.remove(node)

    for node in dependencies:
        if node not in visited:
            dfs(node)

    return cycles


def topological_sort(dependencies: Dict[str, List[str]]) -> Tuple[List[str], bool]:
    """
    Perform topological sort using Kahn's algorithm.
    Returns: (sorted_nodes, has_cycle)
    """
    # Calculate in-degrees
    in_degree = defaultdict(int)
    all_nodes = set(dependencies.keys())

    for node, deps in dependencies.items():
        for dep in deps:
            all_nodes.add(dep)
            in_degree[dep] += 1

    # Add nodes with no dependencies
    for node in all_nodes:
        if node not in in_degree:
            in_degree[node] = 0

    # Start with nodes that have no dependencies
    queue = [node for node in all_nodes if in_degree[node] == 0]
    result = []

    while queue:
        node = queue.pop(0)
        result.append(node)

        for neighbor in dependencies.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    has_cycle = len(result) != len(all_nodes)
    return result, has_cycle


def generate_dot(dependencies: Dict[str, List[str]]) -> str:
    """Generate DOT format output."""
    lines = ["digraph Architecture {"]

    # Collect all nodes
    all_nodes = set(dependencies.keys())
    for deps in dependencies.values():
        all_nodes.update(deps)

    # Sort for consistent output
    all_nodes = sorted(all_nodes)

    # Generate edges
    edges = set()
    for source in sorted(dependencies.keys()):
        for target in sorted(dependencies[source]):
            edge = f'  "{source}" -> "{target}"'
            edges.add(edge)

    lines.extend(sorted(edges))
    lines.append("}")

    return "\n".join(lines)


def load_architecture_files(base_path: Path) -> Tuple[str, str]:
    """Load L2 and L3 architecture files."""
    l2_path = base_path / "L2-system-architecture.md"
    l3_path = base_path / "L3-component-design.md"

    l2_content = ""
    l3_content = ""

    if l2_path.exists():
        l2_content = l2_path.read_text(encoding="utf-8")
    else:
        print(f"Warning: {l2_path} not found", file=sys.stderr)

    if l3_path.exists():
        l3_content = l3_path.read_text(encoding="utf-8")
    else:
        print(f"Warning: {l3_path} not found", file=sys.stderr)

    return l2_content, l3_content


def merge_dependencies(
    l2_deps: Dict[str, List[str]], l3_deps: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """Merge dependencies from L2 and L3 files."""
    merged = defaultdict(list)

    for source, targets in l2_deps.items():
        merged[source].extend(targets)

    for source, targets in l3_deps.items():
        merged[source].extend(targets)

    # Remove duplicates while preserving order
    result = {}
    for source, targets in merged.items():
        seen = set()
        unique_targets = []
        for target in targets:
            if target not in seen:
                seen.add(target)
                unique_targets.append(target)
        result[source] = unique_targets

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Analyze dependencies in architecture layers"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only validate dependencies, do not output DOT",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to architecture markdown files (default: current directory)",
    )
    parser.add_argument(
        "--output", type=str, help="Output file for DOT format (default: stdout)"
    )

    args = parser.parse_args()

    base_path = Path(args.path).resolve()

    # Load architecture files
    l2_content, l3_content = load_architecture_files(base_path)

    if not l2_content and not l3_content:
        print("Error: No architecture files found", file=sys.stderr)
        sys.exit(1)

    # Parse dependencies
    l2_deps = parse_dependencies(l2_content)
    l3_deps = parse_dependencies(l3_content)

    # Merge dependencies
    all_deps = merge_dependencies(l2_deps, l3_deps)

    if not all_deps:
        if args.check:
            print("No dependencies found.")
            sys.exit(0)
        else:
            print("digraph Architecture {")
            print("}")
            sys.exit(0)

    # Detect cycles
    cycles = detect_cycles(all_deps)
    sorted_nodes, has_cycle_topo = topological_sort(all_deps)

    if cycles:
        print("Warning: Circular dependencies detected!", file=sys.stderr)
        for i, cycle in enumerate(cycles, 1):
            print(f"  Cycle {i}: {' -> '.join(cycle)}", file=sys.stderr)

    # Output based on mode
    if args.check:
        # Validation mode
        total_deps = sum(len(deps) for deps in all_deps.values())
        print(
            f"Total components: {len(set(all_deps.keys()) | set().union(*all_deps.values()) if all_deps else [])}"
        )
        print(f"Total dependencies: {total_deps}")

        if cycles:
            print(f"\nCycles detected: {len(cycles)}")
            sys.exit(2)
        else:
            print("\nNo circular dependencies found.")
            sys.exit(0)
    else:
        # DOT output mode
        dot_output = generate_dot(all_deps)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(dot_output, encoding="utf-8")
            print(f"DOT output written to {output_path}")
        else:
            print(dot_output)

        # Return appropriate exit code
        if cycles:
            sys.exit(2)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
