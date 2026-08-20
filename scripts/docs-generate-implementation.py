#!/usr/bin/env python3
"""Generate the implementation progress page from reference design + progress.yaml.

Scans docs/reference-design/ (the reference spec) and docs/implementation/progress.yaml
(the implementation status source of truth), then writes the progress chart +
table into docs/implementation/index.md between the generated markers.

Run:
    python3 scripts/docs-generate-implementation.py

The generated region is delimited by:
    <!-- BEGIN_GENERATED_IMPLEMENTATION --> ... <!-- END_GENERATED_IMPLEMENTATION -->
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install with: uv add pyyaml (in projects/)", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parent.parent
REF = REPO / "docs" / "reference-design"
PROGRESS = REPO / "docs" / "implementation" / "progress.yaml"
OUT = REPO / "docs" / "implementation" / "index.md"

STATUS_ICON = {
    "done": "✅",
    "in-progress": "🔶",
    "not-started": "⬜",
    "blocked": "❌",
}
STATUS_ORDER = ["done", "in-progress", "not-started", "blocked"]


def display_title(index_md: Path) -> str:
    """Extract the first H1 from an index.md as the display title."""
    text = index_md.read_text()
    m = re.search(r"^#\s+(.*)$", text, flags=re.M)
    return m.group(1).strip() if m else index_md.parent.name


def scan_reference() -> list[dict]:
    """Return list of parts: [{slug, title, sections:[{slug,title}]}]."""
    parts = []
    for part_dir in sorted(REF.iterdir()):
        if not part_dir.is_dir():
            continue
        part_index = part_dir / "index.md"
        if not part_index.exists():
            continue
        sections = []
        for sec_dir in sorted(part_dir.iterdir()):
            sec_index = sec_dir / "index.md"
            if sec_dir.is_dir() and sec_index.exists():
                sections.append(
                    {"slug": sec_dir.name, "title": display_title(sec_index)}
                )
        parts.append(
            {
                "slug": part_dir.name,
                "title": display_title(part_index),
                "sections": sections,
            }
        )
    return parts


def load_progress() -> dict:
    if PROGRESS.exists():
        return yaml.safe_load(PROGRESS.read_text()) or {}
    return {}


def render(parts: list[dict], progress: dict) -> str:
    # Overall counts
    all_slugs = [
        (f"{p['slug']}/{s['slug']}", s)
        for p in parts
        for s in p["sections"]
    ]
    total = len(all_slugs)
    counts = {k: 0 for k in STATUS_ORDER}
    for path, _ in all_slugs:
        counts[progress.get(path, "not-started")] += 1
    pct = (counts["done"] / total * 100) if total else 0

    lines = []
    lines.append("## Overall progress")
    lines.append("")
    lines.append(
        f"**{counts['done']} / {total}** phases/sections complete "
        f"(**{pct:.0f}%**)."
    )
    lines.append("")

    # Bar (text-based, renders reliably)
    bar_width = 40
    done_ch = round(bar_width * counts["done"] / total) if total else 0
    bar = "█" * done_ch + "░" * (bar_width - done_ch)
    lines.append(f"```text\n{bar} {pct:.0f}%\n```")
    lines.append("")

    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    for st in STATUS_ORDER:
        lines.append(f"| {STATUS_ICON[st]} {st} | {counts[st]} |")
    lines.append("")

    # Per-part tables
    lines.append("## Progress by part")
    lines.append("")
    for p in parts:
        sec_counts = {k: 0 for k in STATUS_ORDER}
        for s in p["sections"]:
            path = f"{p['slug']}/{s['slug']}"
            sec_counts[progress.get(path, "not-started")] += 1
        part_total = len(p["sections"]) or 1
        part_pct = round(sec_counts["done"] / part_total * 100)
        lines.append(f"### {part_pct}% — {p['title']}")
        lines.append("")
        lines.append("| Status | Phase |")
        lines.append("|--------|-------|")
        for s in p["sections"]:
            path = f"{p['slug']}/{s['slug']}"
            status = progress.get(path, "not-started")
            icon = STATUS_ICON[status]
            link = f"../reference-design/{path}/index.md"
            lines.append(f"| {icon} `{status}` | [{s['title']}]({link}) |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parts = scan_reference()
    progress = load_progress()
    block = render(parts, progress)

    content = OUT.read_text()
    start = "<!-- BEGIN_GENERATED_IMPLEMENTATION -->"
    end = "<!-- END_GENERATED_IMPLEMENTATION -->"
    replacement = f"{start}\n\n{block}\n{end}"
    if start in content and end in content:
        content = re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            replacement,
            content,
            flags=re.S,
        )
    else:
        content = content.rstrip() + "\n\n" + replacement + "\n"
    OUT.write_text(content)
    print(f"Generated implementation progress: {len(parts)} parts, {len(parts) and sum(len(p['sections']) for p in parts)} sections -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())