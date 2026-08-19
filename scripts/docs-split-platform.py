#!/usr/bin/env python3
"""Split ubuntu-26.04-rke2-platform-proper-stack.md into a phase-based docs tree.

Output layout under docs/platform/:

    docs/platform/
        index.md                    <- overview page
        <NN>-<part-slug>/           <- one folder per "Part"
            index.md                <- part landing page
            <NN>-<section-slug>/
                index.md            <- one folder per Phase / section

The document is internally inconsistent: Part titles are H1, but phases are
sometimes H1 and sometimes H2. This script treats any H1/H2 heading inside a
part as a phase boundary, so the split is robust to that inconsistency.

It also regenerates the nav block in mkdocs.yml between the
`# >>> nav-autogen (generated) >>>` markers.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources" / "ubuntu-26.04-rke2-platform-proper-stack.md"
OUT = REPO / "docs" / "platform"

TITLE = "Ubuntu 26.04 LTS Production-Like Hosting Platform"
PART_RE = re.compile(r"^Part\s+(\S+)\s*[—-]?\s*(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def slugify(name: str) -> str:
    name = name.strip().lower()
    name = name.replace("—", "-").replace("–", "-")
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "untitled"


def roman_to_int(roman: str) -> int:
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    total = 0
    prev = 0
    for ch in reversed(roman.upper()):
        cur = vals.get(ch, 0)
        total += -cur if cur < prev else cur
        prev = cur
    return total


def is_part(text: str) -> bool:
    return bool(PART_RE.match(text))


FENCE_RE = re.compile(r"^\s*(```+|~~~+)")


def split_blocks(lines):
    """Return list of [start, end, level, text] for real headings, ignoring
    heading-looking lines that appear inside fenced code blocks."""
    blocks = []
    in_fence = False
    for i, ln in enumerate(lines):
        if FENCE_RE.match(ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(ln)
        if m:
            blocks.append([i, len(lines), len(m.group(1)), m.group(2).strip()])
    for j in range(len(blocks) - 1):
        blocks[j][1] = blocks[j + 1][0]
    return blocks


def main() -> int:
    if not SRC.exists():
        print(f"Missing source: {SRC}", file=sys.stderr)
        return 1

    lines = SRC.read_text().split("\n")
    blocks = split_blocks(lines)
    part_idxs = [i for i, b in enumerate(blocks) if is_part(b[3])]

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    first_part_line = blocks[part_idxs[0]][0]
    overview = "\n".join(lines[:first_part_line]).strip()
    overview = re.sub(r"^# .*$", f"# {TITLE}", overview, count=1, flags=re.M)
    (OUT / "index.md").write_text(overview + "\n")

    nav = [{"Platform Overview": "platform/index.md"}]
    part_summary: list[tuple[str, str, str]] = []  # (roman, title, slug)

    for p_idx, b in enumerate(part_idxs):
        part_line = blocks[b][0]
        part_end = blocks[part_idxs[p_idx + 1]][0] if p_idx + 1 < len(part_idxs) else len(lines)
        m = PART_RE.match(blocks[b][3])
        roman = m.group(1)
        part_title = (m.group(2) or "").strip()
        part_num = roman_to_int(roman)

        part_slug = f"{part_num:02d}-{slugify(part_title)}"
        part_dir = OUT / part_slug
        part_dir.mkdir()

        secs = [
            s for s in range(len(blocks))
            if blocks[s][0] > part_line and blocks[s][0] < part_end
            and blocks[s][2] <= 2
        ]

        first_sec = secs[0] if secs else None
        landing_end = blocks[first_sec][0] if first_sec is not None else part_end
        part_intro = "\n".join(lines[part_line:landing_end]).strip()
        if not part_intro:
            part_intro = f"# Part {roman}"
        (part_dir / "index.md").write_text(part_intro + "\n")

        part_nav = [{"Overview": f"platform/{part_slug}/index.md"}]

        # Precompute section display titles for the TOC
        sec_display: list[tuple[str, str]] = []
        for s in secs:
            s_text = blocks[s][3]
            num_match = re.match(r"^(\d+(?:\.\d+)?|[A-I])\b\.?\s*(.*)$", s_text)
            display = (
                num_match.group(2).strip() if num_match and num_match.group(2) else s_text
            )
            sec_display.append((s, display))

        for s_idx, s in enumerate(secs):
            s_line = blocks[s][0]
            s_end = blocks[secs[s_idx + 1]][0] if s_idx + 1 < len(secs) else part_end
            s_text = blocks[s][3]
            s_level = blocks[s][2]

            body_lines = lines[s_line + 1 : s_end]
            body = "\n".join(body_lines).strip()
            body = re.sub(
                r"(?m)^(#{3,6})\s+",
                lambda mm: "#" * (int(len(mm.group(1))) - 1) + " ",
                body,
            )

            num_match = re.match(r"^(\d+(?:\.\d+)?|[A-I])\b\.?\s*(.*)$", s_text)
            display_title = (
                num_match.group(2).strip() if num_match and num_match.group(2) else s_text
            )

            sec_slug = f"{s_idx:02d}-{slugify(s_text)}"
            sec_dir = part_dir / sec_slug
            sec_dir.mkdir()
            (sec_dir / "index.md").write_text(f"# {display_title}\n\n{body}\n")

            part_nav.append({display_title: f"platform/{part_slug}/{sec_slug}/index.md"})

        # Append a generated table of contents to the part landing page
        if sec_display:
            toc_lines = ["", "---", "", "## Contents", ""]
            for s_idx, (s, display) in enumerate(sec_display):
                sec_slug = f"{s_idx:02d}-{slugify(blocks[s][3])}"
                toc_lines.append(f"- [{display}]({sec_slug}/index.md)")
            with (part_dir / "index.md").open("a") as fh:
                fh.write("\n".join(toc_lines) + "\n")

        nav.append({f"{roman} — {part_title}": part_nav})
        part_summary.append((roman, part_title, part_slug))

    # Append a platform map to the overview page
    with (OUT / "index.md").open("a") as fh:
        fh.write("\n---\n\n## Platform Map\n\n")
        for roman, part_title, part_slug in part_summary:
            fh.write(f"- [{roman} — {part_title}]({part_slug}/index.md)\n")

    # Regenerate the "Platform" section in mkdocs.yml between markers
    _write_mkdocs_platform(REPO / "mkdocs.yml", nav)
    print(f"Split {len(lines)} lines into {len(nav)} top-level entries under {OUT}")
    return 0


def _dump_nav(node, level: int, lines: list, indent: int = 2) -> None:
    """Render a dict subtree as mkdocs nav text."""
    pad = " " * (level * indent)
    for key, val in node.items():
        display = _yaml_scalar(key)
        if isinstance(val, str):
            lines.append(f"{pad}- {display}: {val}")
        elif isinstance(val, list):
            lines.append(f"{pad}- {display}:")
            for item in val:
                if isinstance(item, dict):
                    _dump_nav(item, level + 1, lines)
                elif isinstance(item, str):
                    lines.append(f"{' ' * ((level + 1) * indent)}- {_yaml_scalar(item)}")


def _yaml_scalar(s: str) -> str:
    """Quote a scalar if it contains characters that would break YAML."""
    if re.search(r":\s|^[#\-*&!?|>\[\]{}]|^\s", s) or s == "" or '"' in s:
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _write_mkdocs_platform(mkdocs_yml: Path, platform_nav: list) -> None:
    if not mkdocs_yml.exists():
        return
    static = [
        {"Home": "index.md"},
        {
            "Setup": [
                {"Server Setup Guide": "setup/server-setup-guide.md"},
            ]
        },
        {
            "Guides": [
                {"Getting Started": "guides/getting-started.md"},
                {"SSH Connection": "guides/ssh-connection-guide.md"},
                {"GPU Power Limiting": "guides/gpu-power-limit-guide.md"},
                {"System Stress Test": "guides/stress-test-guide.md"},
            ]
        },
        {"Platform": platform_nav},
    ]
    lines: list[str] = ["nav:"]
    for entry in static:
        _dump_nav(entry, 0, lines)
    block = "\n".join(lines)
    start = "# >>> nav-autogen (generated) >>>"
    end = "# <<< nav-autogen (generated) <<<"
    replacement = f"{start}\n{block}\n{end}"
    content = mkdocs_yml.read_text()
    if start in content and end in content:
        content = re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            replacement,
            content,
            flags=re.S,
        )
    else:
        content = content.rstrip() + "\n\n" + replacement + "\n"
    mkdocs_yml.write_text(content)


if __name__ == "__main__":
    sys.exit(main())