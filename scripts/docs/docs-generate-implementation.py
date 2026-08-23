#!/usr/bin/env python3
"""Generate the implementation progress page from reference design + progress.yaml.

Scans docs/reference-design/ for parts marked `tracked: true` (the actionable
build phases) and docs/implementation/progress.yaml (the implementation status
source of truth), then writes the progress chart + table into
docs/implementation/index.md between the generated markers.

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
    "deferred": "⏸️",
}
STATUS_ORDER = list(STATUS_ICON)
DEFAULT = "not-started"


def display_title(index_md: Path) -> str:
    """Return the first H1 of an index.md, else the dir name."""
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
    return frontmatter_order(dir_path / "index.md")


def tracked(dir_path: Path) -> bool:
    """Return whether a part is tracked for implementation progress.

    A part is tracked only if it carries `tracked: true` in its frontmatter.
    Parts that are conceptual/reference (background, failure modes, glossary,
    compact reference, etc.) are intentionally *not* tracked — they describe or
    justify the platform rather than being an actionable build phase.
    """
    text = (dir_path / "index.md").read_text()
    m = re.search(r"^---\n(.*?)\n---", text, flags=re.S)
    if m:
        m2 = re.search(r"(?m)^tracked:\s*(true|yes)\s*$", m.group(1))
        return m2 is not None
    return False


def scan_sections(parent: Path) -> list[dict]:
    """Return [{slug, title, subsections:[...]}] for each dir holding index.md.

    A *section* is a direct child with an index.md. A *sub-section* is any
    further nesting underneath it. This is recursive, so a section may carry
    its own `subsections`. Ordering is by frontmatter `order:`.
    """
    sections = []
    children = [d for d in parent.iterdir() if d.is_dir() and (d / "index.md").exists()]
    for d in sorted(children, key=order_key):
        sections.append({
            "slug": d.name,
            "title": display_title(d / "index.md"),
            "subsections": scan_sections(d),
        })
    return sections


def scan_reference() -> list[dict]:
    """Return parts: [{slug, title, sections:[{slug,title,subsections:[...]}]}].

    Only *tracked* parts (frontmatter `tracked: true`) are returned. Untracked
    parts — conceptual/background/reference chapters — are excluded so they do
    not appear on the implementation progress page.
    """
    parts = []
    children = [d for d in REF.iterdir() if (d / "index.md").exists()]
    for part_dir in sorted(children, key=order_key):
        if not tracked(part_dir):
            continue
        parts.append({"slug": part_dir.name,
                      "title": display_title(part_dir / "index.md"),
                      "sections": scan_sections(part_dir)})
    return parts


def load_runbook() -> dict[str, str]:
    """Load per-phase runbook markdown, keyed by phase path.

    Each runbook file lives under docs/implementation/runbook/ and carries YAML
    frontmatter: `phase: <reference/build/...>` mapping it to a build phase.
    Returns {phase_path: markdown_body}.
    """
    from io import StringIO
    base = REPO / "docs" / "implementation" / "_runbook"
    out: dict[str, str] = {}
    if not base.exists():
        return out
    for f in sorted(base.rglob("*.md")):
        text = f.read_text()
        fm, body = None, text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) == 3:
                fm = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
        phase = (fm or {}).get("phase")
        if phase:
            out[phase] = body
    return out


RUNBOOK = load_runbook()


def load_progress() -> dict:
    if PROGRESS.exists():
        return yaml.safe_load(PROGRESS.read_text()) or {}
    return {}


def status_of(progress: dict, path: str) -> str:
    """Return a section's status, inheriting the nearest ancestor that has one.

    Sub-sections that have no explicit status in progress.yaml inherit their
    parent phase's status (e.g. a doc-only sub-page under a done phase reads
    as done rather than `not-started`).
    """
    parts = path.split("/")
    for i in range(len(parts), 0, -1):
        candidate = "/".join(parts[:i])
        if candidate in progress:
            return progress[candidate]
    return DEFAULT


def bar(pct: float, anim: str = "") -> str:
    """Return an animated gradient bar div (sizing handled by CSS)."""
    fill = (f'<div class="progress-fill{anim}" '
            f'style="--w:{pct:.1f}%"></div>')
    return f'<div class="progress-track">{fill}</div>'


def tooltip(done: list[str], pending: list[str]) -> str:
    """Return a hover tooltip summarizing done vs pending titles."""
    def fmt(items: list[str]) -> str:
        return "\n".join(f"• {t}" for t in items) or "—"
    return ('<div class="tip-box">'
            f'<strong>Done ({len(done)})</strong>\n{fmt(done)}'
            f'\n<hr style="opacity:.3;margin:6px 0;">'
            f'<strong>Pending ({len(pending)})</strong>\n{fmt(pending)}'
            "</div>")


def overall_bar(pct: float) -> str:
    """Return the large animated overall progress bar."""
    return (
        f'<div class="progress-row" style="max-width:720px;padding:8px 0;">'
        f'{bar(pct, " progress-fill--shimmer")}'
        f'<div class="progress-pct">'
        f'{pct:.0f}%</div></div>'
    )


def count_statuses(sections: list[dict], prefix: str, progress: dict,
                   counts: dict) -> None:
    """Recursively tally statuses for every section/sub-section."""
    for s in sections:
        path = f"{prefix}/{s['slug']}"
        st = status_of(progress, path)
        counts[st] += 1
        if s["subsections"]:
            count_statuses(s["subsections"], path, progress, counts)


def collect_statuses(sections: list[dict], prefix: str, progress: dict) -> list:
    """Return [(path, st, title)] flattened, for tooltip purposes."""
    out = []
    for s in sections:
        path = f"{prefix}/{s['slug']}"
        out.append((path, status_of(progress, path), s["title"]))
        if s["subsections"]:
            out.extend(collect_statuses(s["subsections"], path, progress))
    return out


def part_bar(p: dict, progress: dict) -> tuple[str, str]:
    """Return (heading_pct, bar_html) for a part, incl. hover tooltip."""
    counts = {k: 0 for k in STATUS_ORDER}
    done, pending = [], []
    for path, st, title in collect_statuses(p["sections"], p["slug"], progress):
        counts[st] += 1
        (done if st == "done" else pending).append(title)
    total = counts["done"] + sum(counts[k] for k in STATUS_ORDER if k != "done")
    total = total or 1
    pct = round(counts["done"] / total * 100)
    bar_html = (
        f'<div class="tip" style="display:flex;align-items:center;'
        f'gap:8px;max-width:520px;padding:2px 0 10px;">'
        f'{bar(pct)}'
        f'<div class="progress-pct" style="font-size:.85em;">'
        f'{pct}%</div>'
        f'{tooltip(done, pending)}</div>'
    )
    return f"{pct}%", bar_html


def runbook_box(path: str, title: str, icon: str) -> str:
    """Return a collapsible <details> with the phase's runbook body, or ''."""
    body = RUNBOOK.get(path)
    if not body:
        return ""
    return (
        f"<details markdown=\"1\" class=\"runbook\">\n"
        f"<summary>{icon} 📜 Build log — {title}</summary>\n\n"
        f"{body}\n\n"
        f"</details>"
    )


def render_sections(sections: list[dict], prefix: str, progress: dict,
                    lines: list[str], depth: int = 0) -> None:
    """Append a section for each node, recursively; sub-sections are indented.

    Only the bullet line is indented; a runbook `<details>` box must stay at
    column 0 or Markdown would treat it as a code block.
    """
    indent = "  " * depth
    for s in sections:
        path = f"{prefix}/{s['slug']}"
        st = status_of(progress, path)
        icon = STATUS_ICON[st]
        link = f"../reference-design/{path}/index.md"
        lines.append(f"{indent}- {icon} `{st}` — [{s['title']}]({link})")
        rb = runbook_box(path, s["title"], icon)
        if rb:
            lines += ["", rb, ""]
        if s["subsections"]:
            render_sections(s["subsections"], path, progress, lines,
                            depth + 1)


def render(parts: list[dict], progress: dict) -> str:
    counts = {k: 0 for k in STATUS_ORDER}
    total = 0
    for p in parts:
        p_counts = {k: 0 for k in STATUS_ORDER}
        count_statuses(p["sections"], p["slug"], progress, p_counts)
        for k in STATUS_ORDER:
            counts[k] += p_counts[k]
        total += p_counts["done"] + sum(p_counts[k] for k in STATUS_ORDER if k != "done")
    pct = counts["done"] / total * 100 if total else 0

    lines = ["## Overall progress", ""]
    lines.append(f"**{counts['done']} / {total}** phases/sections complete "
                 f"(**{pct:.0f}%**).")
    lines += ["", overall_bar(pct), "", "| Status | Count |", "|--------|-------|"]
    lines += [f"| {STATUS_ICON[st]} {st} | {counts[st]} |" for st in STATUS_ORDER]
    lines += ["", "## Progress by part", ""]

    for p in parts:
        pct_s, bar_html = part_bar(p, progress)
        lines += [f"### {pct_s} — {p['title']}", "", bar_html, ""]
        render_sections(p["sections"], p["slug"], progress, lines)
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