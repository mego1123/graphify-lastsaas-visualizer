#!/usr/bin/env python3
"""graphify audit — audit logging for all graphify operations.

Records who did what, when, and from where. Supports:
  - File-based audit log (default, no external deps)
  - Structured JSON log entries
  - Log rotation and querying
  - SSO user identity tracking

Usage:
  # As a library (imported by other graphify commands)
  from audit_logger import AuditLogger
  logger = AuditLogger("/data/audit.log")
  logger.log("extract", user="alice", resource="myproject", details={"nodes": 2507})

  # As a CLI (query the audit log)
  python audit_logger.py --log /data/audit.log --tail 20
  python audit_logger.py --log /data/audit.log --user alice
  python audit_logger.py --log /data/audit.log --action extract
  python audit_logger.py --log /data/audit.log --since "2026-08-01"
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class AuditEntry:
    timestamp: str
    action: str          # extract, query, verify, prs, digest, label, update, etc.
    user: str            # username from SSO or "anonymous" / "system"
    resource: str        # file path or project name
    details: dict        # action-specific payload
    source_ip: str = ""  # caller IP (for remote access)
    session_id: str = "" # SSO session ID


class AuditLogger:
    """Thread-safe file-based audit logger."""

    def __init__(self, log_path: str | Path, level: str = "info"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.level = level
        # Get current user from environment or SSO context
        self.default_user = os.environ.get("USER", os.environ.get("USERNAME", "anonymous"))
        # In SSO mode, this would be set by the SSO middleware
        if os.environ.get("GRAPHIFY_SSO_USER"):
            self.default_user = os.environ["GRAPHIFY_SSO_USER"]

    def log(
        self,
        action: str,
        resource: str = "",
        user: Optional[str] = None,
        details: Optional[dict] = None,
        source_ip: str = "",
        session_id: str = "",
    ):
        """Write an audit entry to the log."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            user=user or self.default_user,
            resource=resource,
            details=details or {},
            source_ip=source_ip or self._get_source_ip(),
            session_id=session_id or os.environ.get("GRAPHIFY_SSO_SESSION", ""),
        )

        # Filter by level
        level_priority = {"debug": 0, "info": 1, "warn": 2, "error": 3}
        action_level = {"query": "debug", "extract": "info", "verify": "info",
                        "prs": "info", "digest": "info", "label": "warn",
                        "delete": "warn", "error": "error"}.get(action, "info")
        if level_priority.get(action_level, 1) < level_priority.get(self.level, 1):
            return

        # Append to log file (JSONL format — one JSON object per line)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

    def _get_source_ip(self) -> str:
        """Get the source IP for audit logging."""
        # In a web context, this would come from the request
        # In CLI context, use localhost
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"

    def query(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Query the audit log with filters."""
        if not self.log_path.exists():
            return []

        entries = []
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since)
            except ValueError:
                # Try relative: "7 days ago"
                if "days ago" in since:
                    days = int(since.split()[0])
                    since_dt = datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=days)

        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entry = AuditEntry(**data)
                except (json.JSONDecodeError, TypeError):
                    continue

                # Apply filters
                if user and entry.user != user:
                    continue
                if action and entry.action != action:
                    continue
                if resource and entry.resource != resource:
                    continue
                if since_dt:
                    try:
                        entry_dt = datetime.fromisoformat(entry.timestamp)
                        if entry_dt < since_dt:
                            continue
                    except ValueError:
                        continue

                entries.append(entry)

        return entries[-limit:] if limit > 0 else entries

    def summary(self, since: Optional[str] = None) -> dict:
        """Get a summary of audit activity."""
        entries = self.query(since=since, limit=0)
        from collections import Counter
        return {
            "total_entries": len(entries),
            "by_action": dict(Counter(e.action for e in entries)),
            "by_user": dict(Counter(e.user for e in entries)),
            "first_entry": entries[0].timestamp if entries else None,
            "last_entry": entries[-1].timestamp if entries else None,
        }


# ---------- SSO integration ----------

class SSOConfig:
    """SSO configuration for on-prem deployments.

    Supports OIDC (Google, Okta, Keycloak, etc.) and SAML.
    In production, this would be handled by a reverse proxy (oauth2-proxy, etc.)
    that sets GRAPHIFY_SSO_USER and GRAPHIFY_SSO_SESSION environment variables.
    """

    def __init__(self):
        self.enabled = os.environ.get("GRAPHIFY_SSO_ENABLED", "false").lower() == "true"
        self.provider = os.environ.get("GRAPHIFY_SSO_PROVIDER", "")  # oidc, saml
        self.client_id = os.environ.get("GRAPHIFY_SSO_CLIENT_ID", "")
        self.client_secret = os.environ.get("GRAPHIFY_SSO_CLIENT_SECRET", "")
        self.issuer = os.environ.get("GRAPHIFY_SSO_ISSUER", "")
        self.callback_url = os.environ.get("GRAPHIFY_SSO_CALLBACK_URL", "")

    def get_current_user(self) -> str:
        """Get the current authenticated user.

        In production, this is set by the SSO reverse proxy.
        """
        if not self.enabled:
            return os.environ.get("USER", "anonymous")
        return os.environ.get("GRAPHIFY_SSO_USER", "anonymous")

    def get_session_id(self) -> str:
        """Get the current session ID for audit logging."""
        return os.environ.get("GRAPHIFY_SSO_SESSION", "")


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(
        prog="graphify audit",
        description="Query the audit log.",
    )
    ap.add_argument("--log", "-l", default=os.environ.get("GRAPHIFY_AUDIT_LOG", "graphify-out/audit.log"),
                    help="Path to audit log file")
    ap.add_argument("--tail", "-t", type=int, help="Show last N entries")
    ap.add_argument("--user", "-u", help="Filter by user")
    ap.add_argument("--action", "-a", help="Filter by action")
    ap.add_argument("--resource", "-r", help="Filter by resource")
    ap.add_argument("--since", "-s", help="Filter since date (ISO format or 'N days ago')")
    ap.add_argument("--summary", action="store_true", help="Show summary instead of entries")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    args = ap.parse_args()

    logger = AuditLogger(args.log)

    if args.summary:
        summary = logger.summary(since=args.since)
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"\n📊 Audit Log Summary")
            print(f"   Total entries: {summary['total_entries']}")
            if summary['first_entry']:
                print(f"   First entry:   {summary['first_entry']}")
                print(f"   Last entry:    {summary['last_entry']}")
            if summary['by_action']:
                print(f"\n   By action:")
                for action, count in sorted(summary['by_action'].items(), key=lambda x: -x[1]):
                    print(f"     {action}: {count}")
            if summary['by_user']:
                print(f"\n   By user:")
                for user, count in sorted(summary['by_user'].items(), key=lambda x: -x[1]):
                    print(f"     {user}: {count}")
        return

    entries = logger.query(
        user=args.user,
        action=args.action,
        resource=args.resource,
        since=args.since,
        limit=args.tail or 100,
    )

    if args.json:
        print(json.dumps([asdict(e) for e in entries], indent=2))
    else:
        if not entries:
            print("No audit entries found.")
            return
        print(f"\n{'Timestamp':<26} {'Action':<12} {'User':<15} {'Resource':<30} {'Details'}")
        print("─" * 120)
        for e in entries:
            details_str = json.dumps(e.details) if e.details else ""
            if len(details_str) > 40:
                details_str = details_str[:37] + "..."
            print(f"{e.timestamp:<26} {e.action:<12} {e.user:<15} {(e.resource or '')[:30]:<30} {details_str}")


if __name__ == "__main__":
    from datetime import timedelta
    main()
