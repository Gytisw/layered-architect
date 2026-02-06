#!/usr/bin/env python3
"""
Structured logging utility for layered-architect scripts.
Writes JSONL to .plan/logs by default.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _default_log_path(script_name: str) -> Path:
    base = Path(".plan") / "logs"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{script_name}.jsonl"


class JsonlLogger:
    def __init__(
        self,
        script_name: str,
        log_path: Optional[Path] = None,
        enabled: bool = True,
    ):
        self.script_name = script_name
        self.log_path = log_path or _default_log_path(script_name)
        self.enabled = enabled
        self.run_id = str(uuid.uuid4())

    def log(self, level: str, event: str, message: str, data: Optional[Dict[str, Any]] = None):
        if not self.enabled:
            return
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "script": self.script_name,
            "level": level,
            "event": event,
            "message": message,
            "data": data or {},
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            # Logging must never break the main script
            return


def init_logger(script_name: str, log_path: Optional[str] = None, enabled: bool = True) -> JsonlLogger:
    path = Path(log_path) if log_path else None
    return JsonlLogger(script_name=script_name, log_path=path, enabled=enabled)
