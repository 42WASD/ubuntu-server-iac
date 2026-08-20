#!/usr/bin/env python3
"""Generate the implementation progress page from reference design + progress.yaml.

Scans docs/reference-design/ (the reference spec) and docs/implementation/progress.yaml
(the implementation status source of truth), then writes the progress chart +
table into docs/implementation/index.md between the generated markers.

Run:
    python3 scripts/docs/docs-generate-implementation.py

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

REPO = Path(__file__).resolve().parent.parent.parent
REF = REPO / "docs" / "reference-design"
PROGRESS = REPO / "docs" / "implementation" / "progress.yaml"
OUT = REPO / "docs" / "implementation" / "index.md"

STATUS_ICON = {
    "done": "✅",
    "in-progress": "🔶",
    "not-started": "⬜",
    "blocked": "❌",
}
STATUS_ORDER = list(STATUS_ICON)
DEFAULT = "not-started"

GRADIENT = ("background:linear-gradient(90deg,#38bdf8,#818cf8,#c084fc,#34d399);"
            "background-size:200% 100%;")

CSS = """
<style>
@keyframes imp-fill { from { width: 0; } to { width: var(--imp-w); } }
@keyframes imp-shimmer { from { background-position: 0 0; } to { background-position: 200% 0; } }
.imp-progress-fill { animation: imp-fill 1.6s cubic-bezier(.22,1,.36,1) forwards; }
.imp-part-fill { animation: imp-fill 1.2s cubic-bezier(.22,1,.36,1) forwards; }
.imp-progress-fill.imp-shimmer { animation: imp-fill 1.6s cubic-bezier(.22,1,.36,1) forwards, imp-shimmer 2s linear infinite; }
.imp-tip { position: relative; }
.imp-tooltip {
  visibility: hidden; opacity: 0; position: absolute; z-index: 30;
  left: 0; top: calc(100% + 8px); width: 320px; max-height: 260px;
  overflow: auto; background: var(--md-default-bg-color);
  color: var(--md-default-fg-color);
  border: 1px solid var(--md-default-fg-color--lightest);
  border-radius: 8px; box-shadow: 0 6px 24px rgba(0,0,0,.25);
  padding: 10px 12px; font-size: .8em; line-height: 1.5;
  transition: opacity .15s ease, visibility .15s ease; white-space: pre-wrap;
}
.imp-tip:hover .imp-tooltip, .imp-tip:focus-within .imp-tooltip {
  visibility: visible; opacity: 1;
}
</style>
"""


def display_title(index_md: Path) -> str:
    """Return the first H1 of an index.md, else the dir name."""
    text = index_md.read_text()
    m = re.search(r"^#\s+(.*)$", text, flags=re.M)
    return m.group(1).strip() if m else index_md.parent.name


def scan_reference() -> list[dict]:
    """Return parts: [{slug, title, sections:[{slug,title}]}]."""
    parts = []
    for part_dir in sorted(REF.iterdir()):
        if not (part_dir / "index.md").exists():
            continue
        sections = [
            {"slug": d.name, "title": display_title(d / "index.md")}
            for d in sorted(part_dir.iterdir())
            if d.is_dir() and (d / "index.md").exists()
        ]
        parts.append({"slug": part_dir.name,
                      "title": display_title(part_dir / "index.md"),
                      "sections": sections})
    return parts


def load_progress() -> dict:
    if PROGRESS.exists():
        return yaml.safe_load(PROGRESS.read_text()) or {}
    return {}


def status_of(progress: dict, path: str) -> str:
    return progress.get(path, DEFAULT)


def bar(pct: float, height: str, anim: str) -> str:
    """Return an animated gradient bar div."""
    return (f'<div style="flex:1;height:{height};'
            f'background:rgba(127,127,127,0.15);border-radius:999px;'
            f'overflow:hidden;"><div class="{anim}" style="--imp-w:{pct}%;'
            f'width:0%;height:100%;border-radius:999px;{GRADIENT}"></div></div>')


def tooltip(done: list[str], pending: list[str]) -> str:
    """Return a hover tooltip summarizing done vs pending titles."""
    def fmt(items: list[str]) -> str:
        return "\n".join(f"• {t}" for t in items) or "—"
    return ('<div class="imp-tooltip">'
            f'<strong>Done ({len(done)})</strong>\n{fmt(done)}'
            f'\n<hr style="opacity:.3;margin:6px 0;">'
            f'<strong>Pending ({len(pending)})</strong>\n{fmt(pending)}'
            "</div>")


def overall_bar(pct: float) -> str:
    """Return the large animated overall progress bar."""
    return (
        f'<div style="display:flex;align-items:center;gap:12px;'
        f'max-width:720px;padding:8px 0;">'
        f'{bar(f"{pct:.1f}", "22px", "imp-progress-fill imp-shimmer")}'
        f'<div style="font-weight:700;min-width:52px;text-align:right;">'
        f'{pct:.0f}%</div></div>'
    )


def part_bar(p: dict, progress: dict) -> tuple[str, str]:
    """Return (heading_pct, bar_html) for a part, incl. hover tooltip."""
    counts = {k: 0 for k in STATUS_ORDER}
    done, pending = [], []
    for s in p["sections"]:
        st = status_of(progress, f"{p['slug']}/{s['slug']}")
        counts[st] += 1
        (done if st == "done" else pending).append(s["title"])
    total = len(p["sections"]) or 1
    pct = round(counts["done"] / total * 100)
    bar_html = (
        f'<div class="imp-tip" style="display:flex;align-items:center;'
        f'gap:8px;max-width:520px;padding:2px 0 10px;cursor:help;">'
        f'<div style="display:flex;align-items:center;gap:8px;flex:1;">'
        f'{bar(f"{pct:.1f}", "8px", "imp-part-fill")}'
        f'<div style="font-size:.85em;font-weight:600;min-width:36px;'
        f'text-align:right;">{pct}%</div></div>'
        f'{tooltip(done, pending)}</div>'
    )
    return f"{pct}%", bar_html


def render(parts: list[dict], progress: dict) -> str:
    counts = {k: 0 for k in STATUS_ORDER}
    total = sum(len(p["sections"]) for p in parts)
    for p in parts:
        for s in p["sections"]:
            counts[status_of(progress, f"{p['slug']}/{s['slug']}")] += 1
    pct = counts["done"] / total * 100 if total else 0

    lines = ["## Overall progress", ""]
    lines.append(f"**{counts['done']} / {total}** phases/sections complete "
                 f"(**{pct:.0f}%**).")
    lines += ["", overall_bar(pct), "", "| Status | Count |", "|--------|-------|"]
    lines += [f"| {STATUS_ICON[st]} {st} | {counts[st]} |" for st in STATUS_ORDER]
    lines += ["", "## Progress by part", ""]

    for p in parts:
        pct_s, bar_html = part_bar(p, progress)
        lines += [f"### {pct_s} — {p['title']}", "", bar_html, "",
                  "| Status | Phase |", "|--------|-------|"]
        for s in p["sections"]:
            path = f"{p['slug']}/{s['slug']}"
            st = status_of(progress, path)
            icon = STATUS_ICON[st]
            link = f"../reference-design/{path}/index.md"
            lines.append(f"| {icon} `{st}` | [{s['title']}]({link}) |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n" + CSS


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