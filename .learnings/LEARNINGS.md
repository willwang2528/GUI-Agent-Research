# Learnings

## [LRN-20260721-001] correction

**Logged**: 2026-07-21T16:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: docs

### Summary
For this research map, “the latest three years” means a strict 2024–2026 core paper window, not 2023–2025.

### Details
The first report over-weighted foundational 2023 papers. The user requires every core paper and all principal conclusions to be grounded in 2024, 2025, or 2026 work. Older papers may appear only as clearly separated historical foundations and must not occupy the core paper pool. Paper analysis must also start from the necessary conditions of successful long-horizon GUI control rather than paraphrasing each method's stated motivation.

### Suggested Action
Before finalizing, mechanically audit all core-table and paper-card years; require them to match `2024|2025|2026`. Use a first-principles template: required capability → information/state bottleneck → intervention → remaining impossibility → falsifiable opportunity.

### Metadata
- Source: user_feedback
- Related Files: memory_context_gui_agent_research_map.md
- Tags: literature-review, year-window, first-principles

### Resolution
- **Resolved**: 2026-07-21T16:45:00+08:00
- **Notes**: Rebuilt the core paper pool to 5 papers from 2024, 5 from 2025, and 7 from 2026. Added a first-principles diagnosis to every core paper and mechanically verified all required fields and years.

---

## [LRN-20260721-002] correction

**Logged**: 2026-07-21T18:10:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: docs

### Summary
Use `$...$` and `$$...$$` consistently for math in workspace Markdown; do not emit `\(...\)` or `\[...\]` delimiters, and do not place LaTeX expressions inside ordinary parentheses.

### Details
The generated battle report mixed `\[...\]` display formulas with expressions such as `(\eta)` and `(EVSI(q)>c_q)`. The target Markdown renderer does not reliably render those forms. A full audit also needs to detect raw LaTeX commands outside code or math delimiters, not merely replace display-block markers.

### Suggested Action
Before handing off research Markdown, scan all `.md` files for `\[`, `\]`, `\(`, `\)`, raw LaTeX commands outside math blocks, unmatched `$`/`$$`, unbalanced code fences, malformed tables, and source/rendered link-count mismatches.

### Metadata
- Source: user_feedback
- Related Files: gui_epistemic_commit_control_battle_report.md, memory_context_gui_agent_research_map.md
- Tags: markdown, latex, math-rendering, documentation

### Resolution
- **Resolved**: 2026-07-21T18:20:00+08:00
- **Notes**: Converted 18 display equations to `$$...$$`, corrected all malformed inline variables to `$...$`, and passed delimiter, fence, table, heading, and link-count checks across both reports.

---
