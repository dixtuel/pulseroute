#!/usr/bin/env python3
"""
Public Release Audit Script for PulseRoute
Inspired by SELY MiniGame Hub release audit standards.
Verifies that no private identity, accidental PII leaks, or search engine verification
files are committed into the public repository.
Permits the operator's public identity (email and name) ONLY in the approved canonical file
(src/pulseroute/common/contact.py) and standard project metadata attribution files.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

FORBIDDEN_FILES = re.compile(r"^(google.+\.html|BingSiteAuth\.xml|yandex_.+\.html)$", re.IGNORECASE)
TEXT_FILE_EXTENSIONS = (
    ".py", ".html", ".js", ".css", ".json", ".md", ".toml", ".yaml", ".yml",
    ".txt", ".sh", ".xml", ".example", ".sql", ".rst",
)

# Identity fragments so this audit script itself does not trigger a raw search match
IDENTITY_EMAILS = [
    "".join(["asrinklcc", "@", "sely", ".tr"]),
    "".join(["asrinklcc", "@", "dixtuel", ".tr"]),
]
IDENTITY_NAMES = ["".join(["Asr", "ın", " ", "K", "ıl", "ıç"])]

APPROVED_CANONICAL_IDENTITY_FILE = "src/pulseroute/common/contact.py"

METADATA_ATTRIBUTION_FILES = (
    "README.md",
    "LICENSE",
    "pyproject.toml",
    "ATTRIBUTION.md",
    "SECURITY.md",
)


def is_metadata_attribution(path_str: str) -> bool:
    basename = os.path.basename(path_str)
    return basename in METADATA_ATTRIBUTION_FILES


def strip_approved_public_identity(path_str: str, content: str) -> str:
    norm_path = path_str.replace("\\", "/")
    if norm_path == APPROVED_CANONICAL_IDENTITY_FILE:
        for val in IDENTITY_EMAILS + IDENTITY_NAMES:
            content = content.replace(val, "", 1)
    return content


def contains_private_identity(content: str) -> str | None:
    norm = content.lower()
    for email in IDENTITY_EMAILS:
        if email.lower() in norm:
            return "unauthorized plaintext contact address"
    for name in IDENTITY_NAMES:
        if name.lower() in norm:
            return "unauthorized personal name"
    return None


def run_audit() -> int:
    try:
        raw_files = subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT_DIR,
        )
        paths = [p for p in raw_files.decode("utf-8", errors="ignore").split("\0") if p.strip()]
    except Exception as exc:
        print(f"Error running git ls-files: {exc}", file=sys.stderr)
        return 1

    findings = []
    for rel_path in paths:
        basename = os.path.basename(rel_path)
        if FORBIDDEN_FILES.match(basename):
            findings.append(f"{rel_path}: forbidden search engine verification file")

        _, ext = os.path.splitext(rel_path)
        if ext.lower() not in TEXT_FILE_EXTENSIONS and basename not in METADATA_ATTRIBUTION_FILES:
            continue

        full_path = ROOT_DIR / rel_path
        if not full_path.is_file():
            continue

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if not is_metadata_attribution(rel_path):
            cleaned = strip_approved_public_identity(rel_path, content)
            issue = contains_private_identity(cleaned)
            if issue:
                findings.append(f"{rel_path}: {issue}")

    if findings:
        print("❌ Public release audit FAILED with the following findings:")
        for f in findings:
            print(f"  - {f}")
        return 1

    print("✅ Public release audit PASSED: No unauthorized identity leaks or prohibited artifacts found.")
    return 0


if __name__ == "__main__":
    sys.exit(run_audit())
