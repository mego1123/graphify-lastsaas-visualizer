#!/usr/bin/env python3
"""graphify verify-watch — file watcher that auto-verifies on save.

Watches .go and .ts/.tsx files. When a file changes:
  1. Waits 2s for the write to settle
  2. Runs graphify_verify (Go) or graphify_verify_ts (TypeScript)
  3. Writes results to graphify-out/verify-status.json
  4. Prints a summary

The web app's Verify tab reads verify-status.json to show live results.

Usage:
  python graphify_verify_watch.py [path]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from threading import Thread, Lock
from typing import Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: watchdog not installed. Run: pip install watchdog", file=sys.stderr)
    sys.exit(2)


class VerifyStatus:
    """Thread-safe status store written to graphify-out/verify-status.json."""
    def __init__(self, status_file: Path):
        self.status_file = status_file
        self.lock = Lock()
        self.results: list[dict] = []
        self.last_run: Optional[str] = None
        self.running = False

    def to_dict(self) -> dict:
        with self.lock:
            return {
                "last_run": self.last_run,
                "running": self.running,
                "results": self.results,
                "summary": {
                    "equivalent": sum(1 for r in self.results if r["status"] == "EQUIVALE"),
                    "breaking": sum(1 for r in self.results if r["status"] == "BREAKING"),
                    "inconclusive": sum(1 for r in self.results if r["status"] in ("INCONCLUSIVE", "ERROR")),
                },
            }

    def save(self):
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self.status_file.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def update(self, results: list[dict], running: bool):
        with self.lock:
            self.results = results
            self.last_run = time.strftime("%Y-%m-%d %H:%M:%S")
            self.running = running
        self.save()


class VerifyHandler(FileSystemEventHandler):
    def __init__(self, repo: Path, status: VerifyStatus):
        self.repo = repo
        self.status = status
        self.pending: dict[str, float] = {}  # file_path -> scheduled_time
        self.lock = Lock()
        self.worker = Thread(target=self._worker, daemon=True)
        self.worker.start()

    def on_modified(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if not (path.endswith(".go") or path.endswith((".ts", ".tsx"))):
            return
        # Skip generated files
        if "zz_diffcheck" in path or "graphify-out" in path or "node_modules" in path:
            return
        with self.lock:
            self.pending[path] = time.time() + 2.0  # 2s debounce

    def _worker(self):
        while True:
            time.sleep(0.5)
            now = time.time()
            with self.lock:
                ready = [f for f, t in self.pending.items() if t <= now]
                for f in ready:
                    del self.pending[f]
            if ready:
                self._run_verification(ready)

    def _run_verification(self, changed_files: list[str]):
        """Run verification for the changed files."""
        has_go = any(f.endswith(".go") for f in changed_files)
        has_ts = any(f.endswith((".ts", ".tsx")) for f in changed_files)

        all_results: list[dict] = []
        self.status.update(all_results, running=True)

        scripts_dir = Path(__file__).parent
        env = os.environ.copy()
        env["PATH"] = "/home/z/.local/go/bin:/home/z/.bun/bin:" + env.get("PATH", "")

        if has_go:
            print(f"\n{'='*60}")
            print(f"  Auto-verifying Go changes ({len([f for f in changed_files if f.endswith('.go')])} file(s))")
            print(f"{'='*60}")
            result = subprocess.run(
                ["python3", str(scripts_dir / "graphify_verify.py"), str(self.repo),
                 "--iterations", "100", "--timeout", "30"],
                capture_output=True, text=True, timeout=120, env=env,
            )
            print(result.stdout[-500:] if result.stdout else "")
            if result.stderr:
                print(f"  stderr: {result.stderr[-200:]}")
            # Parse the report
            report_path = self.repo / "graphify-out" / "VERIFY_REPORT.md"
            if report_path.exists():
                all_results.extend(parse_report(report_path, "go"))

        if has_ts:
            print(f"\n{'='*60}")
            print(f"  Auto-verifying TypeScript changes ({len([f for f in changed_files if f.endswith(('.ts', '.tsx'))])} file(s))")
            print(f"{'='*60}")
            result = subprocess.run(
                ["python3", str(scripts_dir / "graphify_verify_ts.py"), str(self.repo),
                 "--iterations", "50", "--timeout", "30"],
                capture_output=True, text=True, timeout=120, env=env,
            )
            print(result.stdout[-500:] if result.stdout else "")
            if result.stderr:
                print(f"  stderr: {result.stderr[-200:]}")
            report_path = self.repo / "graphify-out" / "VERIFY_TS_REPORT.md"
            if report_path.exists():
                all_results.extend(parse_report(report_path, "ts"))

        self.status.update(all_results, running=False)
        summary = self.status.to_dict()["summary"]
        print(f"\n  ✓ Equivalent: {summary['equivalent']}")
        print(f"  ✗ Breaking: {summary['breaking']}")
        print(f"  ? Other: {summary['inconclusive']}")


def parse_report(report_path: Path, lang: str) -> list[dict]:
    """Parse a VERIFY_REPORT.md into structured results."""
    content = report_path.read_text(encoding="utf-8")
    results = []
    # Parse lines like: | ✓ PROVEN EQUIVALENT | 5 | or individual function entries
    # Look for function entries in the "Proven Equivalent" and "Breaking Changes" sections
    for m in __import__("re").finditer(r'### `([^`]+)` in `([^`]+)`', content):
        results.append({
            "function": m.group(1),
            "file": m.group(2),
            "status": "BREAKING",
            "language": lang,
        })
    for m in __import__("re").finditer(r'- `([^`]+)` \(([^)]+)\) — (\d+) inputs tested', content):
        results.append({
            "function": m.group(1),
            "file": m.group(2),
            "status": "EQUIVALE",
            "iterations": int(m.group(3)),
            "language": lang,
        })
    return results


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Watch files and auto-verify on save.")
    ap.add_argument("path", nargs="?", default=".", help="Path to watch (default: .)")
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: {repo} is not a git repository", file=sys.stderr)
        sys.exit(2)

    status_file = repo / "graphify-out" / "verify-status.json"
    status = VerifyStatus(status_file)
    status.update([], running=False)

    handler = VerifyHandler(repo, status)
    observer = Observer()
    observer.schedule(handler, str(repo), recursive=True)
    observer.start()

    print(f"graphify verify-watch — watching {repo}")
    print(f"Status file: {status_file}")
    print(f"Save any .go or .ts/.tsx file to trigger verification.")
    print(f"Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
