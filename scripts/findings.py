#!/usr/bin/env python3
"""
Shared finding model for architecture validators.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


VALID_SEVERITIES = {"error", "warning", "info"}


@dataclass
class Finding:
    id: str
    severity: str
    layer: str
    file: str
    section: str
    line: Optional[int]
    message: str
    why_blocking: str
    fix_hint: str
    fix_command: str

    def to_dict(self) -> Dict:
        return asdict(self)


def make_finding(
    *,
    finding_id: str,
    severity: str,
    layer: str,
    file: str,
    section: str,
    message: str,
    why_blocking: str,
    fix_hint: str,
    fix_command: str,
    line: Optional[int] = None,
) -> Dict:
    sev = severity.strip().lower()
    if sev not in VALID_SEVERITIES:
        raise ValueError(f"Invalid finding severity: {severity}")
    return Finding(
        id=finding_id,
        severity=sev,
        layer=layer,
        file=file,
        section=section,
        line=line,
        message=message,
        why_blocking=why_blocking,
        fix_hint=fix_hint,
        fix_command=fix_command,
    ).to_dict()


def split_by_severity(findings: List[Dict]) -> Dict[str, List[Dict]]:
    errors = [f for f in findings if f.get("severity") == "error"]
    warnings = [f for f in findings if f.get("severity") == "warning"]
    infos = [f for f in findings if f.get("severity") == "info"]
    return {"errors": errors, "warnings": warnings, "infos": infos}


def blocking_findings(findings: List[Dict], strict: bool) -> List[Dict]:
    if strict:
        return [f for f in findings if f.get("severity") in {"error", "warning"}]
    return [f for f in findings if f.get("severity") == "error"]


def next_fix_command(findings: List[Dict], strict: bool) -> str:
    blockers = blocking_findings(findings, strict=strict)
    if not blockers:
        return ""
    for finding in blockers:
        cmd = str(finding.get("fix_command", "")).strip()
        if cmd:
            return cmd
    return "python scripts/arch.py next --path .plan"
