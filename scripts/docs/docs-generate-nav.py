#!/usr/bin/env python3
"""Rewrite the MkDocs nav for docs/reference-design based on the live folder tree.

The reference design is a single linear, chronological sequence. Part folders
live directly under docs/reference-design/ (NN-slug, sorted by Roman numeral),
and each part contains section folders named by semantic slug. Ordering is
driven by the `order:` frontmatter key on each part/section index.md.

    reference-design/
        <NN-part-slug>/index.md          -> part landing page
        <NN-part-slug>/<section-slug>/index.md -> section under that part

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


def display_title(index_md: Path) -> str:
    text = index_md.read_text()
    m = re.search(r"^#\s+(.*)$", text, flags=re.M)
    return m.group(1).strip() if m else index_md.parent.name


def frontmatter_order(index_md: Path) -> float:
    """Return the `order:` value from a page's frontmatter, else Infinity."""
    text = index_md.read_text()
    m = re.search(r"^---\n(.*?)\n---", text, flags=re.S)
    if m:
        m2 = re.search(r"(?m)^order:\s*([\d.]+)\s*$", m.group(1))
        if m2:
            return float(m2.group(1))
    return float("inf")


def order_key(dir_path: Path) -> float:
    """Sort key for a dir based on its index.md `order:` frontmatter."""
    return frontmatter_order(dir_path / "index.md")


def build_subnav(dir_path: Path, rel: str) -> list:
    """Recursively build a nav list for a directory's child sections."""
    entries = []
    children = [d for d in dir_path.iterdir()
                if d.is_dir() and (d / "index.md").exists()]
    for sec_dir in sorted(children, key=order_key):
        child_rel = f"{rel}/{sec_dir.name}"
        sub = build_subnav(sec_dir, child_rel)
        title = display_title(sec_dir / "index.md")
        if sub:
            entries.append({title: [f"{child_rel}/index.md", *sub]})
        else:
            entries.append({title: f"{child_rel}/index.md"})
    return entries


def build_nav() -> list:
    parts = [d for d in REF.iterdir() if d.is_dir() and (d / "index.md").exists()]
    part_list = []
    for part_dir in sorted(parts, key=order_key):
        title = display_title(part_dir / "index.md")
        rel = f"reference-design/{part_dir.name}"
        part_entries = [{"Overview": f"{rel}/index.md"}]
        part_entries.extend(build_subnav(part_dir, rel))
        part_list.append({title: part_entries})
    return part_list


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