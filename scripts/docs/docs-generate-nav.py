#!/usr/bin/env python3
"""Rewrite the MkDocs nav for docs/reference-design based on the live folder tree.

The reference design is organized into three groups (background/build/reference)
under docs/reference-design/. This script walks that tree and rewrites the nav
block in mkdocs.yml between the nav-autogen markers, mapping:

    reference-design/
        <group>/<part>/index.md        -> group nav section, part landing page
        <group>/<part>/<section>/index.md -> section under that part

Run:
    python3 scripts/docs/docs-generate-nav.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
MKDOCS = REPO / "mkdocs.yml"
REF = REPO / "docs" / "reference-design"

GROUP_LABELS = {
    "background": "Concepts & Design",
    "build": "Build (Implementation Phases)",
    "reference": "Reference Material",
}
GROUP_ORDER = ["background", "build", "reference"]


def display_title(index_md: Path) -> str:
    text = index_md.read_text()
    m = re.search(r"^#\s+(.*)$", text, flags=re.M)
    return m.group(1).strip() if m else index_md.parent.name


def build_nav() -> list:
    nav = []
    for group in GROUP_ORDER:
        gdir = REF / group
        if not gdir.is_dir():
            continue
        label = GROUP_LABELS.get(group, group)
        parts = []
        for part_dir in sorted(gdir.iterdir()):
            if part_dir.is_dir() and (part_dir / "index.md").exists():
                title = display_title(part_dir / "index.md")
                rel = f"reference-design/{group}/{part_dir.name}"
                part_nav_entries = [{"Overview": f"{rel}/index.md"}]
                for sec_dir in sorted(part_dir.iterdir()):
                    if sec_dir.is_dir() and (sec_dir / "index.md").exists():
                        part_nav_entries.append({
                            display_title(sec_dir / "index.md"):
                                f"{rel}/{sec_dir.name}/index.md"
                        })
                parts.append({title: part_nav_entries})
        nav.append({label: parts})
    return nav


def dump(node, level: int, lines: list, indent: int = 2) -> None:
    pad = " " * (level * indent)
    for key, val in node.items():
        display = yaml_scalar(key)
        if isinstance(val, str):
            lines.append(f"{pad}- {display}: {val}")
        elif isinstance(val, list):
            lines.append(f"{pad}- {display}:")
            for item in val:
                if isinstance(item, dict):
                    dump(item, level + 1, lines)
                elif isinstance(item, str):
                    lines.append(f"{' ' * ((level + 1) * indent)}- {item}")


def yaml_scalar(s: str) -> str:
    if re.search(r":\s|^[#\-*&!?|>\[\]{}]|^\s", s) or s == "" or '"' in s:
        return '"' + s.replace('"', '\\"') + '"'
    return s


def main() -> int:
    static = [
        {"Home": "index.md"},
        {
            "Setup": [
                {"Getting Started": "setup/getting-started.md"},
                {"Server Setup Guide": "setup/server-setup-guide.md"},
            ]
        },
        {
            "Guides": [
                {
                    "Connectivity": [
                        {"Overview": "guides/connectivity/index.md"},
                        {"SSH Connection": "guides/connectivity/ssh-connection-guide.md"},
                        {"Tailscale Setup": "guides/connectivity/tailscale-setup-guide.md"},
                        {"VPN Connection": "guides/connectivity/vpn-guide.md"},
                    ]
                },
                {
                    "Hardware": [
                        {"Overview": "guides/hardware/index.md"},
                        {"GPU Power Limiting": "guides/hardware/gpu-power-limit-guide.md"},
                        {"Beta GPU Driver": "guides/hardware/beta-gpu-driver-guide.md"},
                    ]
                },
                {
                    "Operations & Testing": [
                        {"Overview": "guides/operations/index.md"},
                        {"System Stress Test": "guides/operations/stress-test-guide.md"},
                        {"System Performance": "guides/operations/system-performance.md"},
                        {"System Test Results": "guides/operations/system-test-results.md"},
                    ]
                },
            ]
        },
        {"Reference Design": [{"Overview": "reference-design/index.md"}, *build_nav()]},
        {"Implementation": [
            {"Progress": "implementation/index.md"},
            {"Build Runbook (Command Log)": "implementation/runbook.md"},
        ]},
    ]

    lines = ["nav:"]
    for entry in static:
        dump(entry, 0, lines)

    block = "\n".join(lines)
    start = "# >>> nav-autogen (generated) >>>"
    end = "# <<< nav-autogen (generated) <<<"
    replacement = f"{start}\n{block}\n{end}"
    content = MKDOCS.read_text()
    if start in content and end in content:
        content = re.sub(re.escape(start) + r".*?" + re.escape(end),
                         replacement, content, flags=re.S)
    else:
        content = content.rstrip() + "\n\n" + replacement + "\n"
    MKDOCS.write_text(content)
    print(f"Rewrote nav in {MKDOCS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())