#!/usr/bin/env python3
"""Rewrite the MkDocs nav for docs/reference-design from the sequence manifest.

The reading order is defined in ONE place — docs/reference-design/_sequence.yaml
(the SSOT manifest). This generator reads it and derives the display numbering:

  - Part numeral (I, II, III ...) from a part's position in the manifest
  - Phase number from a tracked section's global position
  - Nav labels are built as "Part N — <title>" / "Phase N — <title>"

Because numbers are DERIVED (never stored in page frontmatter or H1s), they can
never drift or collide.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docs_manifest import assign_phase_numbers, load_sequence, phase_by_slug  # noqa: E402


def display_title(index_md: Path) -> str:
    text = index_md.read_text()
    m = re.search(r"^#\s+(.*)$", text, flags=re.M)
    return m.group(1).strip() if m else index_md.parent.name


def build_subnav(dir_path: Path, rel: str, nodes: list[dict], part_slug: str = "",
                 tracked: bool = False, section_path: list[str] | None = None,
                 parts: list[dict] | None = None) -> list:
    """Recursively build a nav list from the manifest's section tree.

    For a tracked part's top-level sections, the nav label is prefixed with the
    derived phase number (e.g. "Phase 13 — ..."). Deeper sub-sections get their
    clean title only.
    """
    entries = []
    section_path = section_path or []
    for node in nodes:
        slug = node["slug"]
        child_rel = f"{rel}/{slug}"
        title = display_title(dir_path / slug / "index.md")
        # Phase-prefix only top-level sections of tracked parts.
        if tracked and not section_path:
            ph = phase_by_slug(parts or [], part_slug, slug)
            if ph is not None:
                title = f"Phase {ph} — {title}"
        sub = build_subnav(dir_path / slug, child_rel, node["subsections"],
                           part_slug, tracked, section_path + [slug], parts)
        if sub:
            entries.append({title: [f"{child_rel}/index.md", *sub]})
        else:
            entries.append({title: f"{child_rel}/index.md"})
    return entries


def build_nav(parts: list[dict]) -> list:
    part_list = []
    for i, part in enumerate(parts, start=1):
        numeral = _roman(i)
        title = display_title(REF / part["slug"] / "index.md")
        rel = f"reference-design/{part['slug']}"
        part_entries = [{"Overview": f"{rel}/index.md"}]
        part_entries.extend(build_subnav(REF / part["slug"], rel, part["sections"],
                                         part_slug=part["slug"], tracked=part["tracked"],
                                         parts=parts))
        part_list.append({f"{numeral} — {title}": part_entries})
    return part_list


def _roman(n: int) -> str:
    vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
            (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
            (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for value, sym in vals:
        while n >= value:
            out += sym
            n -= value
    return out


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
    parts = load_sequence()
    assign_phase_numbers(parts)
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
        {"Reference Design": [{"Overview": "reference-design/index.md"}, *build_nav(parts)]},
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