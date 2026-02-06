#!/usr/bin/env python3
"""
Architecture Mapping Adapter

Maps existing documentation into L0-L5 layer summaries using a flexible plan map.
Supports auto-suggested mapping and generation of .plan outputs.
"""

import argparse
import os
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

DEFAULT_MAP_PATH = "plan.map.yml"
DEFAULT_OUT_DIR = ".plan"

EXCLUDE_DIRS = {
    ".git",
    ".plan",
    "node_modules",
    "dist",
    "build",
    "out",
    "venv",
    ".venv",
    "__pycache__",
    "archive",
    "archives",
    "tmp",
    "skills",
}

LAYER_FILE_NAMES = {
    "L0": "L0-problem-framing.md",
    "L1": "L1-meta-architecture.md",
    "L2": "L2-system-architecture.md",
    "L3": "L3-component-design.md",
    "L4": "L4-implementation.md",
    "L5": "L5-operability-readiness.md",
}

LAYER_TITLES = {
    "L0": "Problem Framing (Generated)",
    "L1": "Meta-Architecture (Generated)",
    "L2": "System Architecture (Generated)",
    "L3": "Component Design (Generated)",
    "L4": "Implementation (Generated)",
    "L5": "Operability and Readiness (Generated)",
}

KEYWORDS = {
    "L0": [
        "prd",
        "scope",
        "roadmap",
        "strategy",
        "vision",
        "requirements",
        "goals",
        "stakeholder",
        "assessment",
        "mvp",
    ],
    "L1": [
        "architecture",
        "overview",
        "drivers",
        "tech-stack",
        "source-of-truth",
        "principles",
    ],
    "L2": [
        "orchestration",
        "pipeline",
        "data-layer",
        "schema",
        "workflow",
        "system",
        "integration",
        "flow",
    ],
    "L3": [
        "adapter",
        "spec",
        "api",
        "contract",
        "interface",
        "module",
        "design",
    ],
    "L4": [
        "implementation",
        "tdd",
        "testing",
        "build",
        "deployment",
        "task",
        "plan",
    ],
    "L5": [
        "audit",
        "risk",
        "operability",
        "reliability",
        "monitoring",
        "observability",
        "security",
        "compliance",
        "cost",
        "readiness",
        "incident",
    ],
}

CONSTRAINT_ID_PATTERN = re.compile(r"\bCON-\d{3,}\b")


def iter_markdown_files(root: Path) -> List[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if filename.lower().endswith(".md"):
                files.append(Path(dirpath) / filename)
    return files


def score_layer_for_path(path: Path) -> Tuple[str, int]:
    name = str(path).lower()
    best_layer = ""
    best_score = 0
    for layer, keywords in KEYWORDS.items():
        score = sum(1 for k in keywords if k in name)
        if score > best_score:
            best_score = score
            best_layer = layer
    return best_layer, best_score


def suggest_mapping(root: Path) -> Dict:
    mapping: Dict[str, Dict] = {"version": 1, "root": str(root), "layers": {}, "unmapped": []}
    files = iter_markdown_files(root)

    for file_path in files:
        layer, score = score_layer_for_path(file_path)
        if not layer or score == 0:
            mapping["unmapped"].append(str(file_path))
            continue
        mapping["layers"].setdefault(layer, {"sources": []})
        mapping["layers"][layer]["sources"].append(str(file_path))

    return mapping


def load_mapping(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "layers" not in data:
        raise ValueError("Invalid plan.map.yml (missing layers)")
    return data


def normalize_sources(layer_cfg: Dict) -> List[Path]:
    sources = []
    for item in layer_cfg.get("sources", []):
        if isinstance(item, str):
            sources.append(Path(item))
        elif isinstance(item, dict) and "path" in item:
            sources.append(Path(item["path"]))
    return sources


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


def extract_summary_lines(path: Path) -> List[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        try:
            text = path.read_text()
        except Exception:
            return []

    lines = strip_code_blocks(text.splitlines())
    headings = []
    bullets = []
    paragraphs = []

    current_para = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
            continue
        if stripped.startswith("#"):
            headings.append(re.sub(r"^#{1,6}\s+", "", stripped))
            continue
        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            bullets.append(re.sub(r"^[-*]\s+|\d+\.\s+", "", stripped))
            continue
        current_para.append(stripped)
    if current_para:
        paragraphs.append(" ".join(current_para))

    summary = []
    summary.extend(headings[:5])
    summary.extend(bullets[:10])

    for para in paragraphs[:2]:
        sentence = re.split(r"(?<=[.!?])\s+", para)[0]
        if sentence:
            summary.append(sentence)

    # De-dupe
    seen = set()
    deduped = []
    for item in summary:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(item.strip())
    return deduped


def extract_summary_lines_with_source(path: Path, root: Path, cite: bool) -> List[str]:
    lines = extract_summary_lines(path)
    if not cite:
        return lines
    rel = path.resolve().relative_to(root.resolve())
    return [f"{line} (source: {rel})" for line in lines]


def extract_constraints_from_paths(paths: List[Path]) -> Dict[str, str]:
    """Extract constraint IDs and best-effort text from markdown sources."""
    constraints: Dict[str, str] = {}
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            try:
                text = path.read_text()
            except Exception:
                continue

        for line in strip_code_blocks(text.splitlines()):
            if "CON-" not in line:
                continue
            ids = CONSTRAINT_ID_PATTERN.findall(line)
            if not ids:
                continue
            clean_line = re.sub(r"^[-*]\s+|\d+\.\s+", "", line).strip()
            for cid in ids:
                if cid not in constraints:
                    constraints[cid] = clean_line or "TBD"
    return constraints


def write_constraints_file(out_dir: Path, constraints: Dict[str, str]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / "constraints.yml"
    items = []
    for cid in sorted(constraints.keys()):
        items.append(
            {
                "id": cid,
                "layer": "L1",
                "type": "unspecified",
                "text": constraints[cid],
            }
        )
    data = {"version": "1.0.0", "constraints": items}
    file_path.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")
    return file_path


def limit_summary(lines: List[str], max_words: int, max_bullets: int) -> List[str]:
    limited = []
    word_count = 0
    for line in lines:
        words = line.split()
        if word_count + len(words) > max_words:
            break
        limited.append(line)
        word_count += len(words)
        if len(limited) >= max_bullets:
            break
    return limited


def gather_lines_for_keywords(lines: List[str], keywords: List[str]) -> List[str]:
    matched = []
    for line in lines:
        lower = line.lower()
        if any(k in lower for k in keywords):
            matched.append(line.strip())
    return matched


def load_all_lines(paths: List[Path]) -> List[str]:
    all_lines = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            try:
                text = path.read_text()
            except Exception:
                continue
        all_lines.extend(strip_code_blocks(text.splitlines()))
    return [line for line in all_lines if line.strip()]


def build_l0_yaml(all_lines: List[str]) -> Dict:
    goals = gather_lines_for_keywords(all_lines, ["goal", "objective", "vision"])
    non_goals = gather_lines_for_keywords(all_lines, ["out of scope", "non-goal"])
    stakeholders = gather_lines_for_keywords(all_lines, ["stakeholder", "owner"])
    assumptions = gather_lines_for_keywords(all_lines, ["assume", "assumption"])
    questions = [line for line in all_lines if line.strip().endswith("?")]
    success = gather_lines_for_keywords(all_lines, ["success", "metric", "kpi", "slo"])

    def take(items: List[str], count: int) -> List[str]:
        return items[:count] if items else []

    stakeholder_objs = []
    for item in take(stakeholders, 3):
        stakeholder_objs.append({"role": item[:40], "needs": "TBD from sources"})

    return {
        "layer": "L0",
        "title": "Generated L0",
        "triggered_by": "source mapping",
        "goals": take(goals, 3) or ["TBD from sources"],
        "non_goals": take(non_goals, 3),
        "stakeholders": stakeholder_objs or [{"role": "TBD", "needs": "TBD"}],
        "assumptions": [{"text": a, "confidence": "medium"} for a in take(assumptions, 3)]
        or [{"text": "TBD from sources", "confidence": "low"}],
        "open_questions": take(questions, 5),
        "success_criteria_draft": take(success, 3) or ["TBD from sources"],
        "decision_readiness": "not_ready",
        "decision_log": [
            {
                "id": "DEC-001",
                "decision": "TBD",
                "rationale": "TBD",
                "impact": "TBD",
            }
        ],
        "notes": "",
    }


def build_l5_yaml(all_lines: List[str]) -> Dict:
    slos = gather_lines_for_keywords(all_lines, ["slo", "sla", "availability", "latency"])
    metrics = gather_lines_for_keywords(all_lines, ["metric", "metrics"])
    logs = gather_lines_for_keywords(all_lines, ["log", "logging"])
    traces = gather_lines_for_keywords(all_lines, ["trace", "tracing"])
    alerts = gather_lines_for_keywords(all_lines, ["alert", "pager"])
    security = gather_lines_for_keywords(all_lines, ["security", "encrypt", "auth"])
    deploy = gather_lines_for_keywords(all_lines, ["deploy", "release", "rollback"])
    backups = gather_lines_for_keywords(all_lines, ["backup", "retention", "rpo", "rto"])
    costs = gather_lines_for_keywords(all_lines, ["cost", "budget", "spend"])
    runbooks = gather_lines_for_keywords(all_lines, ["runbook", "incident"])
    checks = gather_lines_for_keywords(all_lines, ["test", "check", "validation"])
    risks = gather_lines_for_keywords(all_lines, ["risk"])

    slo_items = []
    for item in slos[:3]:
        slo_items.append(
            {
                "name": item[:30] if item else "Availability",
                "sli": "TBD",
                "target": "TBD",
                "measurement": "TBD",
            }
        )
    if not slo_items:
        slo_items = [
            {
                "name": "Availability",
                "sli": "Successful requests / total requests",
                "target": "TBD",
                "measurement": "TBD",
            }
        ]

    return {
        "layer": "L5",
        "title": "Generated L5",
        "slos": slo_items,
        "observability": {
            "metrics": metrics[:3] or ["TBD"],
            "logs": logs[:3] or ["TBD"],
            "traces": traces[:3] or ["TBD"],
            "alerting": alerts[:3] or ["TBD"],
        },
        "security_controls": security[:3] or ["TBD"],
        "deployment": {
            "strategy": deploy[0] if deploy else "TBD",
            "rollback": deploy[1] if len(deploy) > 1 else "TBD",
            "environments": ["dev", "staging", "prod"],
        },
        "data_protection": {
            "backups": backups[0] if backups else "TBD",
            "retention": backups[1] if len(backups) > 1 else "TBD",
            "rpo": "TBD",
            "rto": "TBD",
        },
        "cost_guardrails": costs[:3] or ["TBD"],
        "runbooks": runbooks[:3],
        "readiness_checks": checks[:3] or ["TBD"],
        "readiness_status": "not_ready",
        "residual_risks": risks[:3],
        "dependencies": [],
        "decision_log": [
            {
                "id": "DEC-001",
                "decision": "TBD",
                "rationale": "TBD",
                "impact": "TBD",
            }
        ],
        "risk_register": [
            {
                "risk": "TBD",
                "severity": "Medium",
                "mitigation": "TBD",
                "owner": "TBD",
            }
        ],
        "threat_model": [],
        "compliance_evidence": [],
        "notes": "",
    }


def write_layer_file(
    out_dir: Path,
    layer: str,
    sources: List[Path],
    summary_lines: List[str],
    l0_yaml: Dict = None,
    l5_yaml: Dict = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / LAYER_FILE_NAMES[layer]

    lines = [f"# {layer} - {LAYER_TITLES[layer]}", ""]

    if layer == "L0" and l0_yaml:
        lines.append("```yaml")
        lines.append(yaml.dump(l0_yaml, sort_keys=False).strip())
        lines.append("```")
        lines.append("")
    if layer == "L5" and l5_yaml:
        lines.append("```yaml")
        lines.append(yaml.dump(l5_yaml, sort_keys=False).strip())
        lines.append("```")
        lines.append("")

    lines.append("## Sources")
    for src in sources:
        lines.append(f"- {src}")
    lines.append("")
    lines.append("## Summary")
    for item in summary_lines:
        lines.append(f"- {item}")
    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Map and summarize architecture docs")
    parser.add_argument("--map", default=DEFAULT_MAP_PATH, help="Path to plan.map.yml")
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="Suggest a plan.map.yml based on filenames",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Generate .plan layer summaries from the mapping",
    )
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUT_DIR,
        help="Output directory for .plan files",
    )
    parser.add_argument("--max-words", type=int, default=600, help="Max words per layer")
    parser.add_argument("--max-bullets", type=int, default=25, help="Max bullets per layer")
    parser.add_argument(
        "--cite",
        action="store_true",
        help="Append source path to each summary bullet",
    )

    args = parser.parse_args()
    logger = init_logger("map_architecture")

    map_path = Path(args.map)

    if args.suggest:
        mapping = suggest_mapping(Path(".").resolve())
        map_path.write_text(yaml.dump(mapping, sort_keys=False), encoding="utf-8")
        print(f"Suggested mapping written to {map_path}")
        logger.log(
            "info",
            "mapping_suggested",
            "Suggested mapping written",
            {"map_path": str(map_path)},
        )
        if not args.apply:
            return

    if not map_path.exists():
        print(f"Error: mapping file not found: {map_path}", file=sys.stderr)
        logger.log("error", "map_missing", "Mapping file not found", {"map_path": str(map_path)})
        sys.exit(1)

    mapping = load_mapping(map_path)
    root = Path(mapping.get("root", ".")).resolve()
    options = mapping.get("options", {})
    max_words = options.get("max_words", args.max_words)
    max_bullets = options.get("max_bullets", args.max_bullets)
    cite = options.get("cite", args.cite)
    unmapped = mapping.get("unmapped", [])

    out_dir = Path(args.out_dir)
    if not args.apply:
        print("Dry run (use --apply to generate .plan files)")
        logger.log(
            "info",
            "dry_run",
            "Dry run for mapping",
            {"map_path": str(map_path), "layers": list(mapping.get("layers", {}).keys())},
        )
        if mapping.get("unmapped"):
            print(f"Unmapped files: {len(mapping.get('unmapped'))}")

    all_sources: Dict[str, List[Path]] = {}
    for layer, layer_cfg in mapping.get("layers", {}).items():
        sources = normalize_sources(layer_cfg)
        resolved_sources = [(root / src).resolve() for src in sources]
        all_sources[layer] = resolved_sources
        summary = []
        for src in resolved_sources:
            summary.extend(extract_summary_lines_with_source(src, root, cite))
        summary = limit_summary(summary, max_words=max_words, max_bullets=max_bullets)

        if not args.apply:
            print(f"\n{layer} ({len(resolved_sources)} source files)")
            for line in summary[:10]:
                print(f"- {line}")
            continue

        l0_yaml = None
        l5_yaml = None
        if layer == "L0":
            all_lines = load_all_lines(resolved_sources)
            l0_yaml = build_l0_yaml(all_lines)
        if layer == "L5":
            all_lines = load_all_lines(resolved_sources)
            l5_yaml = build_l5_yaml(all_lines)

        write_layer_file(
            out_dir=out_dir,
            layer=layer,
            sources=resolved_sources,
            summary_lines=summary,
            l0_yaml=l0_yaml,
            l5_yaml=l5_yaml,
        )

    if args.apply:
        constraints_file = out_dir / "constraints.yml"
        if not constraints_file.exists():
            # Prefer L1 sources for constraints; fallback to all sources.
            constraint_sources = all_sources.get("L1", [])
            if not constraint_sources:
                constraint_sources = [
                    path for paths in all_sources.values() for path in paths
                ]
            constraints = extract_constraints_from_paths(constraint_sources)
            write_constraints_file(out_dir, constraints)
            print(f"Generated constraints registry in {constraints_file}")
            logger.log(
                "info",
                "constraints_generated",
                "Constraints registry generated",
                {"constraints_file": str(constraints_file), "count": len(constraints)},
            )

    if args.apply:
        print(f"Generated layer summaries in {out_dir}")
        if unmapped:
            print(f"Unmapped files: {len(unmapped)}")
        logger.log(
            "info",
            "mapping_applied",
            "Generated layer summaries",
            {
                "out_dir": str(out_dir),
                "layers": list(mapping.get("layers", {}).keys()),
                "unmapped_count": len(unmapped),
            },
        )


if __name__ == "__main__":
    main()
