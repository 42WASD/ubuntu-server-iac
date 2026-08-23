# Docs refactor — SSOT sequence manifest replaces `order:` frontmatter

**Intent:** eliminate the hardcoded numbering that caused drift. Phase/part
numbers (Roman numerals I–XXV, build phases 0–70) are now DERIVED from a single
manifest position rather than stored per-page, so collisions and stale numbers
are impossible by construction.

**What changed:**
1. **New SSOT manifest** `docs/reference-design/_sequence.yaml` — a deep tree:
   `parts:` ordered list; each `{slug: {tracked: bool, sections: [...]}}`;
   sections are strings or `{slug: {subsections: [...]}}`. This is the ONLY
   place reading order is defined.
2. **Removed `order:` and `tracked:` frontmatter** from every part/section
   `index.md` (`docs-strip-sequence-number.py`, 169 files). Stripped `Part N —`
   / `Phase N —` H1 prefixes; `tracked:` moved into the manifest.
3. **Stripped phase prefixes from Contents-list link text**
   (`docs-strip-toc-numbers.py`, 16 files).
4. **Shared loader** `scripts/docs/docs_manifest.py`:
   - `load_sequence()` → parts with `numeral` (Roman) derived from position.
   - `assign_phase_numbers()` → sets `s["phase"]` = GLOBAL contiguous counter
     0→70 across all tracked parts' top-level sections.
   - `phase_by_slug()` for lookups.
5. **Both generators** (`docs-generate-nav.py`, `docs-generate-implementation.py`)
   import `docs_manifest`. Nav labels `"{numeral} — {title}"`; tracked top-level
   bullets `"Phase {N} — {title}"`.

**Commands run:**
```bash
# Strip order:/tracked: frontmatter + H1 part/phase prefixes (169 files)
python3 scripts/docs/docs-strip-sequence-number.py
# Strip phase prefixes from Contents link text (16 files)
python3 scripts/docs/docs-strip-toc-numbers.py

# Regenerate nav + implementation from the manifest
python3 scripts/docs/docs-generate-implementation.py
python3 scripts/docs/docs-generate-nav.py

# Build (strict validates all links)
cd projects && uv run mkdocs build --strict -f ../mkdocs.yml
```

**Verified:**
- Generator reports `15 parts, 71 sections`.
- Implementation page headings: `### 90% — Part III — Build the host`.
- Tracked top-level bullets show derived `Phase N — ` prefixes.
- Global phase sequence is contiguous `0–70` (71 unique, no gaps/collisions):
  `grep -E '^- .*\[Phase [0-9]+ —' implementation/index.md | grep -oE '[0-9]+'`
  → first 0, last 70, 71 unique.
- `mkdocs build --strict` passes with no warnings.

## Migration rule (for future changes)
- **Never** re-add `order:`/`tracked:` frontmatter or numeric prefixes to page
  files. To reorder/restructure, edit `_sequence.yaml`, then re-run both
  generators and the strict build. Numbers always follow the manifest position.