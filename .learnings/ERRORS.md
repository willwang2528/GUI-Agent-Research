# Errors

## [ERR-20260722-014] repeated_jq_array_pipe_scope

**Logged**: 2026-07-22T23:12:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The already documented unparenthesized `jq` array-pipe mistake from ERR-20260722-012 recurred while validating the newly saved OSWorld raw API snapshots.

### Error
```text
jq: error: Cannot index array with string "tasks"
```

### Context
- The expression again began an array element with `.tasks|length`, which changed the input for later comma-separated expressions.
- No data files were modified and no scientific result depended on the failed command.

### Resolution
- **Resolved**: 2026-07-22T23:12:00+08:00
- **Notes**: Bound `.tasks as $tasks` once and parenthesized all piped array elements; six snapshots then each validated as 108 tasks, 108 unique IDs and 8 Block A task IDs.

---

## [ERR-20260728-041] stage0f_unittest_selector_typo

**Logged**: 2026-07-28T18:45:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
An initial targeted unittest command used two guessed method names that do not
exist in `ValidatorTests`.

### Error
```text
AttributeError: type object 'ValidatorTests' has no attribute
'test_full_synthetic_block_mechanics_pass'
```

### Context
- No implementation code ran in the failed selection.
- `rg` identified the actual methods as
  `test_synthetic_full_block_two_event_mechanics_pass` and
  `test_e10_empty_submissions_no_event_location`.

### Suggested Fix
Resolve exact unittest selectors from source before running targeted methods.

### Metadata
- Reproducible: yes
- Related Files: tests/test_stage0f_stage_a_validator.py

### Resolution
- **Resolved**: 2026-07-28T18:46:00+08:00
- **Notes**: Re-ran both exact methods successfully.

---

## [ERR-20260722-013] github_git_transport_empty_checkout

**Logged**: 2026-07-22T22:45:00+08:00
**Priority**: medium
**Status**: mitigated
**Area**: infra

### Summary
Cloning the ARIS GitHub repository through the local Git transport repeatedly produced an empty temporary checkout with no usable `HEAD` or refs, although GitHub showed a non-empty `main` branch.

### Error
```text
git clone returned without a usable working tree; git ls-remote produced no refs
```

### Context
- Operation: retrieve `wanshuiyin/Auto-claude-code-research-in-sleep` into the GUI-agent-memory workspace.
- Both HTTP and HTTPS clone attempts failed to produce a valid checkout.
- The official GitHub codeload archive for `refs/heads/main` downloaded and passed ZIP integrity validation.

### Suggested Fix
Use the official GitHub codeload snapshot as a transparent fallback, record the upstream commit SHA and archive checksum, and do not represent the snapshot as a full Git clone with history.

### Metadata
- Reproducible: yes
- Related Files: external/Auto-claude-code-research-in-sleep

### Resolution
- **Mitigated**: 2026-07-22T22:45:00+08:00
- **Notes**: Extracted the validated `main` snapshot at upstream commit `53562a7c64cc1d55946cba1fb8a8416137143d14`; SHA-256 of the downloaded archive is `2a91d6e293777cab3b4967d0031569dfd1168fb62c599eab3fc494debb7d44c5`.

---

## [ERR-20260722-012] jq_array_pipe_scope_in_catalog_audit

**Logged**: 2026-07-22T23:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
An unparenthesized `jq` pipe inside an array constructor changed the input context and made six valid OSWorld catalog responses look structurally invalid.

### Error
```
jq: error (at <stdin>:1): Cannot index array with string "tasks"
```

### Context
- Operation: aggregate task count, unique IDs, and terminal-status counts from six official `/api/tasks/brief` responses.
- Expression began with `.tasks|length` inside `[...]`; the pipe applied to the following comma-separated expressions, so later `.tasks` lookups ran against the array.
- Earlier inspection confirmed the response root is an object with a `tasks` array.

### Suggested Fix
Parenthesize every array element that contains a pipe, for example `[(.tasks|length), ([.tasks[].id]|unique|length), ...]`, or bind `.tasks as $tasks` once and aggregate from `$tasks`.

### Metadata
- Reproducible: yes
- Related Files: stage0f_osworld2_natural_burden_preregistration.md

### Resolution
- **Resolved**: 2026-07-22T23:11:00+08:00
- **Notes**: Re-ran the aggregation with `.tasks as $tasks` and explicit parentheses.

---

## [ERR-20260722-011] interruptbench_full_repo_ast_parse

**Logged**: 2026-07-22T17:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Whole-repository Python AST validation is invalid for InterruptBench because a `.py`-named config helper contains bare natural-language task text.

### Error
```
File "external/InterruptBench/Eval/config_files/wa/get_train_webarena_lite_raw.py", line 32
    Find a recipe for a vegetarian lasagna that has at least a four-star rating and uses zucchini.
         ^
SyntaxError: invalid syntax
```

### Context
- Operation: perform a read-only offline dry-run before assessing the InterruptBench task-3 replay path.
- The attempted validation parsed every `.py` file, including dataset/config artifacts that are not imported by the task-3 replay workflow.
- Raw interruption JSON and the 60-percent interrupt spec had already passed their independent schema and consistency assertions.

### Suggested Fix
Parse only executable scripts on the intended path (`run.py`, the raw-to-spec converter, metrics scripts), and validate data/config files with their own format-specific checks. Do not use a whole-repository AST pass as an environment readiness criterion.

### Metadata
- Reproducible: yes
- Related Files: external/InterruptBench/Eval/config_files/wa/get_train_webarena_lite_raw.py, external/InterruptBench/Eval/run.py

### Resolution
- **Resolved**: 2026-07-22T17:21:00+08:00
- **Notes**: Replaced the broad AST scan with targeted syntax checks and separate JSON integrity assertions.

---

## [ERR-20260722-010] docker_unavailable_for_gui_benchmarks

**Logged**: 2026-07-22T03:00:00+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
The current macOS workspace has no Docker CLI, so the released WebArena-based InterruptBench environment cannot be executed locally as documented.

### Error
```
zsh:1: command not found: docker
```

### Context
- Operation: assess whether Step 2 frozen checkpoint interventions can run on the current machine.
- InterruptBench requires multiple WebArena containers and a reset server.
- OSWorld 2.0 also requires provider images and gated task assets; only 59 GiB is currently available, while the full trajectory dataset is about 250 GB.

### Suggested Fix
Use a Linux host with Docker and sufficient storage, or acquire only a single task family with its exact checkpoint, task class, assets, evaluator, and trajectory. Do not claim a causal replay from the current observational evidence.

### Metadata
- Reproducible: yes
- Related Files: external/InterruptBench/Eval/RUN_PARALLEL_EVAL.md, stage0c_action_state_failure_evidence.md

---

## [ERR-20260722-009] interruptbench_wrong_repository_url

**Logged**: 2026-07-22T02:35:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The first InterruptBench clone used an inferred GitHub organization and returned repository not found.

### Error
```
remote: Repository not found.
fatal: repository 'https://github.com/OS-Agent-Survey/InterruptBench.git/' not found
```

### Context
- Operation: obtain the official public code and interruption data for read-only audit.
- The repository URL was guessed instead of opened from the paper's official code link.

### Suggested Fix
Resolve repository URLs from the primary paper page before cloning.

### Metadata
- Reproducible: yes
- Related Files: external/InterruptBench

### Resolution
- **Resolved**: 2026-07-22T02:35:00+08:00
- **Notes**: Opened the official arXiv code link and identified https://github.com/HenryPengZou/InterruptBench.

---

## [ERR-20260722-008] tavily_tls_eof

**Logged**: 2026-07-22T02:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
One of three parallel Tavily searches ended during the TLS handshake, while the other two searches completed.

### Error
```
urllib.error.URLError: <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>
```

### Context
- Operation: search for 2024–2026 long-horizon GUI state-tracking evidence.
- The failure was limited to one query and did not affect the completed results.

### Suggested Fix
Retry the failed query independently or use the built-in web retriever for official primary sources.

### Metadata
- Reproducible: intermittent
- Related Files: stage0_step1_natural_failure_audit.md

### Resolution
- **Resolved**: 2026-07-22T02:20:00+08:00
- **Notes**: Continued with two successful Tavily results and official arXiv pages.

---

## [ERR-20260722-007] git_status_non_repository

**Logged**: 2026-07-22T02:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The workspace root is a plain research directory rather than a Git repository, so a Git status check failed before the file audit ran.

### Error
```
fatal: not a git repository (or any of the parent directories): .git
```

### Context
- Operation: inspect current workspace state before continuing the seven-step topic-validity audit.
- The command used a Git assumption that is not valid for this workspace.
- No file changes occurred from the failed command.

### Suggested Fix
Treat the workspace files themselves as authoritative and use direct file enumeration, hashes, and content validation instead of Git status.

### Metadata
- Reproducible: yes
- Related Files: stage0_step1_natural_failure_audit.md, stage0b_mads_observational_pilot.md

### Resolution
- **Resolved**: 2026-07-22T02:00:00+08:00
- **Notes**: Switched to direct file-level inspection.

---

## [ERR-20260722-006] tavily_cli_missing_query_flag

**Logged**: 2026-07-22T01:35:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The Tavily helper requires `--query`; passing the search text positionally caused argument parsing to fail.

### Error
```
tavily_search.py: error: the following arguments are required: --query
```

### Context
- Operation: locate official 2024–2026 GUI benchmark trajectory releases.
- Three read-only searches failed before any network request was made.

### Suggested Fix
Always invoke the helper as `tavily_search.py --query "..."` and keep the remaining flags unchanged.

### Metadata
- Reproducible: yes
- Related Files: none

### Resolution
- **Resolved**: 2026-07-22T01:36:00+08:00
- **Notes**: Corrected the argument form and reran the searches.

---

## [ERR-20260722-005] py_compile_cache_permission

**Logged**: 2026-07-22T01:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
`py_compile` attempted to create its default bytecode cache under a macOS user cache directory that is outside the writable sandbox.

### Error
```
PermissionError: [Errno 1] Operation not permitted: '/Users/will/Library/Caches/com.apple.python/Users/will/research'
```

### Context
- Operation: syntax-check the read-only MaDS audit script.
- The script itself ran successfully and did not require a bytecode cache.

### Suggested Fix
Use `ast.parse` for read-only syntax validation in this sandbox, or direct bytecode output to a task-owned temporary directory when compilation artifacts are required.

### Metadata
- Reproducible: yes
- Related Files: stage0_mads_pilot_audit.py

### Resolution
- **Resolved**: 2026-07-22T01:21:00+08:00
- **Notes**: Replaced `py_compile` with a read-only `ast.parse` check and retained the successful script execution as the functional validation.

---

## [ERR-20260722-004] github_mads_clone

**Logged**: 2026-07-22T01:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The direct network clone of the MaDS public repository failed after connection setup with an empty HTTP response.

### Error
```
fatal: unable to access 'https://github.com/PcCin37/MaDS/': Empty reply from server
```

### Context
- Operation: persist the MaDS audit data from the official GitHub repository into the workspace.
- A verified shallow clone at commit `99c1bffc0df85f12bc236b1793d05791934dbda5` already existed in the task-owned temporary directory.

### Suggested Fix
When the remote clone is transiently unavailable, clone the already verified local repository into the workspace and recheck its commit and file counts.

### Metadata
- Reproducible: unknown
- Related Files: external/MaDS

### Resolution
- **Resolved**: 2026-07-22T01:02:00+08:00
- **Notes**: Cloned the verified local repository into `external/MaDS`; confirmed the exact commit, 127 analysis records, and a 75 MiB workspace footprint.

---

## [ERR-20260722-003] huggingface_trajectory_probe

**Logged**: 2026-07-22T00:40:00+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Both sandboxed and approved external HEAD requests failed to reach the public Hugging Face trajectory bundle, preventing a lightweight size check.

### Error
```
curl: (6) Could not resolve host: huggingface.co
curl: (28) Failed to connect to huggingface.co port 443 after 75217 ms
```

### Context
- Operation: inspect the size of `site/trajs/m3a.json.gz` before deciding whether to download replayable trajectories.
- Recurrence: later read-only requests for OSWorld-Verified's 16.4 kB `all_result.json` failed through both `huggingface.co` and `hf-mirror.com`, although the browser search layer could inspect the Hugging Face page.
- The official benchmark repository and project page remained available through other search paths.
- No trajectory files were downloaded or modified.

### Suggested Fix
Use an accessible Hugging Face mirror, the browser-served static trajectory viewer, or obtain the preview bundle from the authors; do not download the 21–43 GB raw archives merely to bypass this metadata failure.

### Metadata
- Reproducible: yes
- Related Files: external/MemGUI-Bench/docs/README.md, external/OSWorld/mm_agents/kimi/README.md
- Recurrence-Count: 3
- Last-Seen: 2026-07-22

---

## [ERR-20260722-002] markdown_audit_validation

**Logged**: 2026-07-22T00:30:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
The first validation command used an over-escaped ripgrep expression and attempted `git diff` in a workspace without a Git repository.

### Error
```
rg: regex parse error: unrecognized escape sequence
warning: Not a git repository
```

### Context
- Operation: read-only structural validation of the new Stage-0A Markdown report.
- The report had already been written successfully; neither failure modified files.

### Suggested Fix
Use a small read-only parser to count table columns, code fences, and math delimiters without relying on complex regexes or repository state.

### Metadata
- Reproducible: yes
- Related Files: stage0a_natural_memory_failure_audit.md

### Resolution
- **Resolved**: 2026-07-22T00:31:00+08:00
- **Notes**: Replaced the failed checks with a Python line parser; all three Markdown tables have consistent column counts and no unmatched fences or dollar delimiters.

---

## [ERR-20260722-001] csv_readonly_stats

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
The first read-only CSV statistics command embedded escaped newlines in a Python `-c` string, so Python parsed the literal backslash sequence instead of a loop body.

### Error
```
SyntaxError: unexpected character after line continuation character
```

### Context
- Operation: count long-horizon and potentially effectful tasks in MemGUI-Bench.
- The command was read-only; no dataset or report files were modified.

### Suggested Fix
For short shell-driven analysis, replace multiline loops with comprehensions and keep the `python3 -c` body on one logical line.

### Metadata
- Reproducible: yes
- Related Files: external/MemGUI-Bench/data/memgui-tasks-all.csv
- Recurrence-Count: 2
- Last-Seen: 2026-07-22

### Resolution
- **Resolved**: 2026-07-22T00:01:00+08:00
- **Notes**: Replaced the multiline loop with a list comprehension before rerunning the statistics. The same mistake recurred during Markdown validation; future `python3 -c` checks in this workspace must use a single expression or a temporary checked-in helper rather than escaped newlines.

---

## [ERR-20260721-001] tavily_search

**Logged**: 2026-07-21T14:30:00+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Tavily search intermittently failed during literature discovery because the TLS connection closed during the handshake.

### Error
```
urllib.error.URLError: <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>
```

### Context
- Operation: targeted searches restricted to OpenReview and ACL Anthology.
- Environment: macOS system Python 3.9, Tavily search helper.
- Other Tavily queries in the same run succeeded, so the failure appears intermittent.

### Suggested Fix
Retry once with external-network permission, then use the built-in web search path and official venue pages as the fallback.

### Metadata
- Reproducible: unknown
- Related Files: none

---

## [ERR-20260721-005] markdown_validation_script

**Logged**: 2026-07-21T18:22:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
The first read-only Markdown validation script used a raw-regex expression directly inside a Python f-string expression and failed to parse.

### Error
```
SyntaxError: f-string expression part cannot include a backslash
```

### Context
- Operation: report paired math fences and parsed Markdown structure.
- No file writes occurred.

### Suggested Fix
Compute regex-derived counts in local variables before interpolating them into f-strings.

### Metadata
- Reproducible: yes
- Related Files: gui_epistemic_commit_control_battle_report.md, memory_context_gui_agent_research_map.md

### Resolution
- **Resolved**: 2026-07-21T18:23:00+08:00
- **Notes**: Moved all regex counts outside the f-string; both reports passed the final validation.

---

## [ERR-20260721-004] apply_patch_markdown_math

**Logged**: 2026-07-21T18:15:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
A single large Markdown-formatting patch was rejected because one malformed inline expression contained an extra escaping backslash not represented in the patch context.

### Error
```
apply_patch verification failed: Failed to find expected lines:
- 自然轨迹中可利用机会 (\rho<10\%)；
```

### Context
- Operation: convert all display and inline LaTeX delimiters in the battle report.
- The actual source ended the expression as `(\rho<10\%\)`, so the exact context did not match.
- `apply_patch` rejected the entire patch; no partial edit occurred.

### Suggested Fix
Inspect escaped source with a literal-output view, split large formatting patches into bounded sections, and rerun structural scans after each section.

### Metadata
- Reproducible: yes
- Related Files: gui_epistemic_commit_control_battle_report.md

### Resolution
- **Resolved**: 2026-07-21T18:20:00+08:00
- **Notes**: Applied four smaller patches and verified that no raw LaTeX delimiters or commands remain outside valid math blocks.

---

## [ERR-20260721-003] pdf_text_extraction

**Logged**: 2026-07-21T17:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The local shell environment does not provide `pdftotext` for extracting tables from downloaded conference PDFs.

### Error
```
zsh: command not found: pdftotext
```

### Context
- Operation: extract UI-Copilot ACL 2026 ablation tables from the official PDF.
- The PDF itself downloaded successfully.

### Suggested Fix
Use the bundled workspace document/PDF Python runtime or official HTML/arXiv pages when available.

### Metadata
- Reproducible: yes
- Related Files: memory_context_gui_agent_research_map.md

### Resolution
- **Resolved**: 2026-07-21T17:21:00+08:00
- **Notes**: Switched to the bundled workspace dependency runtime and official HTML sources.

---

## [ERR-20260721-002] scholar_citation_lookup

**Logged**: 2026-07-21T15:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
Automated citation lookup could not be used consistently: Google Scholar returned an anti-automation page and the Semantic Scholar Graph API returned HTTP 429.

### Error
```
Google Scholar: anti-automation interstitial
Semantic Scholar Graph API: HTTP 429 Too Many Requests
```

### Context
- Operation: verify citation counts for the selected core paper pool.
- Venue, author, method, and experiment claims were not taken from these blocked endpoints.

### Resolution
Use official venue pages and PDFs for stable bibliographic and method evidence. Record citation counts only when an exact Semantic Scholar paper page is accessible; otherwise mark the count as unavailable instead of inferring it from search snippets.

### Metadata
- Reproducible: intermittent
- Related Files: memory_context_gui_agent_research_map.md

---
## [ERR-20260722-007] git_status_non_repository

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The workspace root is a plain research directory rather than a Git repository, so a Git status check failed before the file audit ran.

### Error
```
fatal: not a git repository (or any of the parent directories): .git
```

### Context
- Operation: inspect current workspace state before continuing the seven-step topic-validity audit.
- The command used a Git assumption that is not valid for this workspace.
- No file changes occurred from the failed command.

### Suggested Fix
Treat the workspace files themselves as authoritative and use direct file enumeration, hashes, and content validation instead of Git status.

### Metadata
- Reproducible: yes
- Related Files: stage0_step1_natural_failure_audit.md, stage0b_mads_observational_pilot.md

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Switched to direct file-level inspection.

---

## [ERR-20260722-011] interrupt_spec_jq_path

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: data-audit

### Summary
The first InterruptBench spec audit queried `.tasks[]` after constructing an array, so jq evaluated the path against the array and returned a null-iteration error.

### Error
```text
jq: error: Cannot iterate over null (null)
```

### Context
- Operation: verify that the 20/40/60/80-percent interrupt specifications cover the same task set and use a uniform update mode.
- The JSON files were intact; only the audit query was wrong.
- No source or data files were changed.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Query `.tasks` once, bind it to a variable, and compute all counts and unique values from that object.

---

## [ERR-20260722-012] huggingface_tree_safe_open

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: pending
**Area**: web-access

### Summary
The browser research tool rejected a direct Hugging Face dataset tree URL as unsafe, so it could not enumerate the OSWorld 2.0 `website_demo` directory through that route.

### Error
```text
URL https://huggingface.co/datasets/xlangai/osworld2.0-trajectory/tree/main/website_demo is not safe to open
```

### Context
- Operation: locate only the public Task 035 trajectory instead of downloading the full OSWorld 2.0 trajectory dataset.
- No local files or remote resources were changed.

### Suggested Fix
Discover the path through an indexed official page or use the Hugging Face dataset API from an approved network path, then pin the dataset revision and file checksums.

---

## [ERR-20260722-013] web_query_js_quote

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
A JavaScript string for an exact web-search query contained unescaped nested double quotes and failed before the web request was sent.

### Error
```text
SyntaxError: Unexpected string
```

### Context
- Operation: search indexed Hugging Face paths for the OSWorld 2.0 MiniMax Task 035 demo trajectory.
- No network request or file mutation occurred.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Use single-quoted JavaScript strings around queries that contain exact double-quoted search terms.

---

## [ERR-20260722-014] huggingface_api_empty_response

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: medium
**Status**: pending
**Area**: web-access

### Summary
Two read-only requests to the official Hugging Face dataset tree API completed without response headers or body, so the Task 035 file list could not be pinned or downloaded in this environment.

### Context
- Operation: enumerate `website_demo/MiniMax-M3/tasks/035` in the OSWorld 2.0 trajectory dataset.
- The indexed official dataset page independently confirms the directory layout and website-demo commit, but not individual files or checksums.
- No local or remote data was changed.

### Suggested Fix
Retry from a network path with a functioning Hugging Face API client, then record the dataset revision, exact file list, sizes, ETags, and SHA-256 values before audit.

---

## [ERR-20260722-015] stage0d_minor_fix_patch_context

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: editing

### Summary
A multi-hunk patch for the final Stage 0D minor fixes included a sentence that had not yet been added to the file, so patch verification rejected the whole edit.

### Error
```text
apply_patch verification failed: Failed to find expected lines
```

### Context
- Operation: tighten the Memory retention and rename criteria after the eighth-round causal review.
- No partial edit was applied.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Re-read the exact section and applied a smaller patch against current text.

---

## [ERR-20260722-016] preregistration_atom_text_normalization

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: validation

### Summary
The first preregistration validation rejected all flat-state atoms because canonical underscore identifiers were compared literally against natural-language spaces.

### Error
```text
flat text does not explicitly encode atom origin_value
flat text does not explicitly encode atom destination_value
flat text does not explicitly encode atom travel_modes
flat text does not explicitly encode atom requested_output
```

### Context
- Operation: validate information equivalence between flat and structured Task 3 state inputs.
- Official asset checks and negative self-tests otherwise ran successfully.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Normalize underscores and whitespace before semantic-atom membership checks, and use the exact canonical requested-output wording in both inputs.

---

## [ERR-20260722-017] subagent_false_positive_security_filter

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: pending
**Area**: collaboration

### Summary
The reproduction reviewer could not complete a benign local JSON-validator audit because its turn was flagged as possible cybersecurity content.

### Context
- Requested work was limited to running a local preregistration validator, checking public benchmark checksums, and finding validation mutations.
- No security testing, exploitation, credential handling, or external mutation was requested.
- The causal and adversarial reviewers remained available.

### Suggested Fix
Retry with a narrower prompt that asks only for local reproducibility and manifest consistency, or complete the checksum and exit-code audit in the primary agent.

---

## [ERR-20260722-018] overlapping_line_range_false_duplicate

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: validation

### Summary
Two adjacent source-view ranges both included line 240, making one JSON key appear duplicated and causing a patch against a nonexistent duplicate to fail.

### Error
```text
apply_patch verification failed: Failed to find expected lines
```

### Context
- The first range ended at line 240 and the second range started at line 240.
- The protocol itself contained only one `U_REPEAT_P0` id key.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Re-read a non-overlapping range, confirmed the file was valid, and added an explicit duplicate-key rejection test to the JSON loader as a separate hardening measure.

---

## [ERR-20260722-019] backtick_shell_substitution_in_search

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: validation

### Summary
A search pattern containing Markdown backticks was placed inside a shell double-quoted command, so the shell attempted to execute `S_P1` as command substitution.

### Error
```text
zsh:1: command not found: S_P1
```

### Context
- Operation: scan the Stage 0D report for stale labels after v0.3 synchronization.
- No file mutation occurred, but the combined search output was not authoritative.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Re-ran searches using fixed-string patterns without shell-active backticks and kept future command patterns free of command-substitution syntax.

---

## [ERR-20260722-020] hosted_monitor_api_path_assumption

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: research-data

### Summary
The first direct request to the OSWorld 2.0 hosted monitor used an endpoint inferred from a local monitor implementation and returned HTTP 405.

### Error
```text
curl: (56) The requested URL returned error: 405
```

### Context
- Operation: read the official hosted trajectory catalog configuration without downloading the large trajectory archives.
- The public host may use a different static catalog implementation or HTTP method than the cloned repository monitor.
- No local or remote data was modified.

### Suggested Fix
Inspect the hosted page assets or documented links to recover its actual read-only endpoints; do not treat the 405 as evidence that trajectories are absent.

### Metadata
- Reproducible: yes
- Related Files: external/OSWorld-V2/monitor/main.py

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Read the cloned official monitor routes and used `/api/available-configs`, `/api/tasks/brief`, and `/api/task/tasks/<id>`; the hosted catalog then returned six model configurations and 108 task entries per model.

---

## [ERR-20260722-021] workspace_root_not_git_repository

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backup

### Summary
The backup audit attempted to record a workspace Git status, but the research workspace root is not a Git repository.

### Error
```text
fatal: not a git repository (or any of the parent directories): .git
```

### Context
- Operation: create a resumable checkpoint for the active research goal.
- Upstream projects under `external/` are separate Git repositories, but `/Users/will/research/gui_agent_memory` itself has no `.git` repository.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Use absolute paths and SHA-256 hashes for workspace artifacts, plus individual upstream repository commit hashes, as the backup anchors.

---

## [ERR-20260722-022] pdftotext_unavailable

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: research-data

### Summary
The OSWorld 2.0 paper metadata was readable with `pdfinfo`, but the expected `pdftotext` executable was not installed on the shell path.

### Error
```text
zsh:1: command not found: pdftotext
```

### Context
- Operation: search the official 68-page paper for run selection, retry, exclusion, seed, and trajectory-release details.
- Source PDF: `external/OSWorld-V2/OSWorld2.0.pdf`.
- No source or workspace research artifact was modified by the failed extraction.

### Suggested Fix
Use the bundled PDF Python runtime (`pdfplumber` or `pypdf`) for text extraction, and visually inspect any relevant pages before relying on tables or layout-sensitive evidence.

### Metadata
- Reproducible: yes
- Related Files: external/OSWorld-V2/OSWorld2.0.pdf

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Used the bundled Python runtime with `pdfplumber`; the extraction recovered page markers and the relevant evaluation, one-run, behavior-annotation, and exposure-attribution text.

---

## [ERR-20260722-023] mixed_pdf_binary_probe

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: research-data

### Summary
A single `ls` probe checked both override and fallback Poppler paths; the existing override binary was found, but the missing fallback path made the command exit non-zero.

### Error
```text
ls: .../dependencies/bin/fallback/pdftoppm: No such file or directory
```

### Context
- The override executable exists at `/Users/will/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm`.
- The fallback location does not exist and is not needed.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Use the confirmed override executable directly for relevant-page rendering.

---

## [ERR-20260722-024] pdf_render_parallel_script_syntax

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: research-data

### Summary
The first JavaScript orchestration attempt for three parallel PDF page renders failed at parse time before invoking Poppler.

### Error
```text
SyntaxError: Invalid or unexpected token
```

### Context
- Intended pages: OSWorld 2.0 paper pages 11, 36, and 39.
- The output directory already existed; no render command ran and no evidence artifact was changed.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Replace the generated template commands with explicit independent Poppler calls.

---

## [ERR-20260722-025] osworld_helper_module_path_assumption

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: research-data

### Summary
The first result-persistence audit looked for `lib_run_single.py` and `lib_results_logger.py` under `scripts/python/`, but both modules live at the OSWorld-V2 repository root.

### Error
```text
rg: scripts/python/lib_run_single.py: No such file or directory
nl: scripts/python/lib_run_single.py: No such file or directory
```

### Context
- Operation: determine whether incomplete task attempts can be erased and rerun before publication.
- The runner imports the helper modules from the repository root; no files were modified by the failed lookup.

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Located the modules with a repository file search, then inspected the root-level files directly.

---

## [ERR-20260722-026] learning_log_wrong_workdir

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: validation

### Summary
The first learning-log read was issued from the nested `external/OSWorld-V2` checkout, but `.learnings/ERRORS.md` belongs to the research workspace root.

### Error
```text
ls: .learnings: No such file or directory
sed: .learnings/ERRORS.md: No such file or directory
```

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Re-ran the read from `/Users/will/research/gui_agent_memory` and recorded subsequent entries there.

---

## [ERR-20260722-027] hosted_api_direct_web_open_and_sandbox_dns

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: research-data

### Summary
The browser retriever rejected direct OSWorld monitor API URLs as unsafe, and the sandboxed shell could not resolve the host.

### Error
```text
URL https://osworld-v2-monitor.xlang.ai/api/tasks/brief is not safe to open
curl: (6) Could not resolve host: osworld-v2-monitor.xlang.ai
```

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Re-ran the same read-only API requests with approved external network access and froze six config snapshots plus SHA-256 values.

---

## [ERR-20260722-028] collaboration_wait_timeout_below_minimum

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: collaboration

### Summary
A mailbox poll used `timeout_ms=1000`, below the tool's 10000 ms minimum.

### Error
```text
timeout_ms must be at least 10000
```

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Used 10000 ms or more for later collaboration waits.

---

## [ERR-20260722-029] jq_pipeline_precedence_probe

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: research-data

### Summary
A compact jq expression piped the output of `type` and `length` into `keys`, so it attempted to apply `keys` to a string instead of the root object.

### Error
```text
jq: string ("object") has no keys
```

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Split the root-key, entry-type, and first-record probes into explicit jq expressions.

---

## [ERR-20260722-030] gated_task_raw_fetch_no_artifact

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: medium
**Status**: pending
**Area**: research-data

### Summary
Read-only curl attempts against the gated OSWorld V2 task source returned no usable output and created no local file, even though the command session ended without diagnostic text.

### Context
- Target: `osworld_v2_tasks/task_035.py`.
- The official dataset page later confirmed that task implementations and evaluator details require accepting gated access conditions.
- Public trajectory APIs remain accessible, but normative evaluator truth cannot be independently reproduced from the ungated artifacts alone.

### Suggested Fix
Authenticate to the official gated task dataset, fetch the immutable `v2026.06.24` tag and task hash manifest, and verify every task class against the release manifest. Do not use floating `main` or silently replace evaluator truth with the final catalog score.

### Metadata
- Reproducible: yes
- Related Files: stage0f_public_trace_feasibility_audit.md

---

## [ERR-20260722-031] formula_patch_whitespace_mismatch

**Logged**: 2026-07-22T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
A cleanup patch expected pseudo-formula lines beginning with `+=`, but the actual Markdown contained a line break followed by `=`; patch verification failed.

### Error
```text
apply_patch verification failed: Failed to find expected lines
```

### Resolution
- **Resolved**: 2026-07-22T00:00:00+08:00
- **Notes**: Re-read the exact block and applied a smaller patch that converted it to aligned plain-text formulas inside a fenced block.

---

## [ERR-20260728-032] python314_venv_ensurepip_failure

**Logged**: 2026-07-28T10:20:00+08:00
**Priority**: medium
**Status**: in_progress
**Area**: tests

### Summary
The system Python 3.14.6 could not bootstrap pip while creating the project-local Stage 0F validation environment.

### Error
```text
Error: Command '['/Users/will/research/gui_agent_memory/.venv-stage0f/bin/python3.14', '-m', 'ensurepip', '--upgrade', '--default-pip']' returned non-zero exit status 1.
```

### Context
- Command: `python3 -m venv .venv-stage0f`
- Purpose: install the pinned Draft 2020-12 JSON Schema validation dependencies without modifying system Python.
- The partially created environment must not be treated as a valid dependency lock or test environment.
- Direct reproduction showed that Homebrew Python 3.14 loads `pyexpat` against an incompatible system `libexpat` and fails on the missing symbol `_XML_SetAllocTrackerActivationThreshold`.
- `/usr/bin/python3` 3.9.6 can create a venv, but sandboxed pip could not resolve the package index.
- The required escalated install request was rejected by the automatic approval path with an internal `Unknown parameter: input[13].namespace` error; it was not retried.
- The two incomplete workspace environments were moved to explicit `/private/tmp/gui_agent_memory_*_20260728` paths so they cannot be mistaken for the frozen validator environment.
- A separately approved ephemeral Python 3.9 environment at `/private/tmp/stage0f-jsonschema-py39` currently supplies the exact pinned packages for mechanical tests; it is not a project-local freeze artifact.

### Suggested Fix
Use a verified alternate Python runtime and an explicitly approved dependency installation, then recreate the local environment from `requirements-stage0f.txt`. The already installed global Ajv 8.20.0 may be used only as an interim second implementation check; it does not close the project-local dependency-lock gate.

### Metadata
- Reproducible: unknown
- Related Files: requirements-stage0f.txt, tools/validate_stage0f_stage_a_packet.py

---

## [ERR-20260728-033] local_git_init_sandbox_and_approval_failure

**Logged**: 2026-07-28T10:55:00+08:00
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
The user-requested local `.git` repository could not be initialized because direct creation was denied and the required escalation path failed internally.

### Error
```text
/Users/will/research/gui_agent_memory/.git: Operation not permitted

Automatic approval review failed:
Unknown parameter: 'input[13].namespace'
```

### Context
- User explicitly requested a local-only Git repository and a directory tracking the seven research steps.
- `research-ledger/` and `.gitignore` were created successfully.
- `git init -b main` was attempted once normally and once through the required approval path.
- No remote was created and no upload was attempted.
- The rejected action was not retried through an alternate git-dir, symlink, or other bypass.

### Suggested Fix
After the user has been informed, obtain a functioning explicit approval for `git init -b main`, then verify `git remote -v` is empty before the first commit.

### Metadata
- Reproducible: yes
- Related Files: .gitignore, research-ledger/

### Resolution
- **Resolved**: 2026-07-28T10:58:00+08:00
- **Notes**: Superseded by the user's later instruction to use `willwang2528/GUI-Agent-Research` as the canonical history repository instead of creating `.git` in the source workspace. No local-repository bypass was attempted.

---

## [ERR-20260728-034] github_ssh_port22_clone_failure

**Logged**: 2026-07-28T11:00:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
Cloning the newly specified GitHub repository over the default SSH port failed because the connection was closed on port 22.

### Error
```text
Connection closed by 198.18.0.20 port 22
fatal: Could not read from remote repository.
```

### Context
- Remote: `git@github.com:willwang2528/GUI-Agent-Research.git`
- Intended local path: `/Users/will/research/GUI-Agent-Research`
- The user explicitly authorized using this new GitHub repository as the research-history destination.

### Suggested Fix
Retry GitHub SSH through the official `ssh.github.com:443` endpoint with the same repository and identity, then verify the resolved origin before copying or pushing any files.

### Metadata
- Reproducible: yes
- Related Files: .gitignore, research-ledger/

### Resolution
- **Resolved**: 2026-07-28T10:58:00+08:00
- **Notes**: Cloned successfully through `ssh://git@ssh.github.com:443/willwang2528/GUI-Agent-Research.git`; the resulting `origin` uses the same SSH-over-443 URL and the checked-out branch is `main`.

---

## [ERR-20260728-035] python_compileall_cache_permission

**Logged**: 2026-07-28T11:01:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The first Python compilation audit could not write bytecode to the macOS user cache path permitted by that interpreter configuration.

### Error
```text
PermissionError: [Errno 1] Operation not permitted: '/Users/will/Library/Caches/com.apple.python/Users/will/research'
```

### Context
- Operation: compile the selected root scripts, tools, and tests before the GitHub checkpoint.
- The failure occurred while writing cache artifacts, before it could serve as a complete syntax-audit result.
- No source file was modified.

### Suggested Fix
Use Python's explicit `-X pycache_prefix` option with a task-specific path under `/private/tmp` for sandboxed compilation audits.

### Metadata
- Reproducible: yes
- Related Files: stage0_mads_pilot_audit.py, stage0d_contract_evaluator.py, tools/, tests/

### Resolution
- **Resolved**: 2026-07-28T11:01:00+08:00
- **Notes**: Re-ran the same compile set with `-X pycache_prefix=/private/tmp/gui_agent_memory_pycache`; the command completed successfully.

---

## [ERR-20260728-036] osworld_detail_audit_wrong_directory

**Logged**: 2026-07-28T11:03:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The first live OSWorld detail audit passed the parent raw directory instead of the exact `detail_pages` directory, so the auditor correctly reported zero expected HTML files.

### Error
```text
detail_dir = source_provenance/osworld2/raw
audit_complete = false
file_count = 0
```

### Context
- The raw snapshot was present under the nested path recorded in `source_provenance/osworld2/manifest.json`.
- The failed invocation did not modify the stored audit or manifest.
- Its zero-page result is an operator path error and must not replace the frozen audit.

### Suggested Fix
Read `source_directory` from the manifest and pass that exact directory to the auditor.

### Metadata
- Reproducible: yes
- Related Files: source_provenance/osworld2/manifest.json, tools/audit_stage0f_detail_pages.py

### Resolution
- **Resolved**: 2026-07-28T11:03:00+08:00
- **Notes**: Re-ran with `source_provenance/osworld2/raw/detail_pages`; the audit reproduced 48/48 files, tree hash `7aada049e5711fc10f13162660d8e24670ac4cc694f4a01e1ece19f05e8b6d56`, 47 replay pages, one explicit no-step page, and 9,138 steps.

---

## [ERR-20260728-037] canonical_clone_sync_approval_failure

**Logged**: 2026-07-28T11:07:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
Synchronizing selected research artifacts into the canonical clone at `/Users/will/research/GUI-Agent-Research` required an escalation, but the automatic approval service failed internally.

### Error
```text
Automatic approval review failed:
Unknown parameter: 'input[13].namespace'
```

### Context
- The user had explicitly authorized committing the current goal data and conclusions directly to `main`.
- The selected file set had already excluded external repositories, raw detail pages, PDFs, backups, caches, and large files.
- No write to the canonical clone occurred after the rejection.

### Suggested Fix
Use a new publishing clone inside a sandbox-authorized temporary directory, then preserve the canonical clone unchanged.

### Metadata
- Reproducible: yes
- Related Files: .gitignore, research-ledger/

### Resolution
- **Resolved**: 2026-07-28T11:08:00+08:00
- **Notes**: Created `/private/tmp/gui-agent-research-publish.Uj54FM/repo`, cloned the same SSH-over-443 origin, synchronized the audited file set there, and completed all pre-commit checks without writing to the rejected path.

---

## [ERR-20260728-038] github_main_push_approval_failure

**Logged**: 2026-07-28T11:10:00+08:00
**Priority**: high
**Status**: in_progress
**Area**: infra

### Summary
The audited `main` commit exists in the temporary publishing clone, but network-sandbox push failed and the required escalation was rejected by the same internal approval-service error.

### Error
```text
ssh: connect to host ssh.github.com port 443: Operation not permitted

Automatic approval review failed:
Unknown parameter: 'input[13].namespace'
```

### Context
- Repository: `willwang2528/GUI-Agent-Research`
- Branch: `main`
- The failure happened before any remote update.
- The local commit is not evidence that GitHub `main` changed.
- Safety rules prohibit switching to another write channel after this rejection without renewed explicit user approval after disclosure.
- The user then gave renewed explicit authorization for exact commit `ad3a3349d42f0bedbd142ae8c4d160c16ef1a7f6`; the approval service still failed with the same internal parameter error before `git push` executed.

### Suggested Fix
Obtain renewed explicit user authorization after reporting this exact blocker, then retry only `git push origin main` from the audited temporary publishing clone and verify local HEAD against the remote ref.

### Metadata
- Reproducible: yes
- Related Files: README.md, research-ledger/, refine-logs/
- Recurrence-Count: 2

---

## [ERR-20260728-039] python312_homebrew_and_dependency_approval_failure

**Logged**: 2026-07-28T11:27:00+08:00
**Priority**: medium
**Status**: in_progress
**Area**: infra

### Summary
The user requested Python 3.12 for future experiments. Homebrew identified `python@3.12` version 3.12.13, but installation and the later locked-dependency installation could not pass the broken escalation service.

### Error
```text
Homebrew cache:
Operation not permitted @ dir_s_mkdir - /Users/will/Library/Caches/Homebrew/api/formula

Sandboxed pip:
Failed to establish a new connection: [Errno 8] nodename nor servname provided

Escalation:
Unknown parameter: 'input[13].namespace'
```

### Context
- A bundled Python 3.12.13 interpreter was already available in the Codex runtime.
- `.venv-stage0f-py312` was created successfully from that interpreter.
- The project venv currently has Python 3.12.13 and pip 25.0.1, but not the locked Stage 0F packages.
- Python 3.9 native extensions must not be copied into the 3.12 environment.
- A later `uv pip install --offline` attempt was deliberately limited to the existing local cache, but the same approval-service `input[13].namespace` failure occurred before `uv` could run outside the sandbox.
- After the user explicitly authorized obtaining Python 3.12, a direct
  `.venv-stage0f-py312/bin/python -m pip install --only-binary=:all:` request
  was rejected before execution by the same approval-service parameter error.
- Read-only inspection found only `typing-extensions==4.16.0` in the bundled
  Python 3.12 runtime and no matching local pip/uv artifacts for the other
  five locked distributions, so no local exact-dependency path exists.

### Suggested Fix
When the approval service is functional, install the exact lock into `.venv-stage0f-py312`, run `pip check`, run the full suite and both schema validators, recompute the environment fingerprint, and then make 3.12 the default.

### Metadata
- Reproducible: yes
- Related Files: requirements-stage0f.txt, source_provenance/stage0f_python312_target.json
- Recurrence-Count: 3
- Last-Seen: 2026-07-28

---

## [ERR-20260728-040] python39_py_compile_cache_permission

**Logged**: 2026-07-28T18:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
`py_compile` tried to create its cache under a sandbox-blocked macOS user cache path.

### Error
```
PermissionError: [Errno 1] Operation not permitted:
'/Users/will/Library/Caches/com.apple.python/Users/will/research'
```

### Context
- Command: `.venv-stage0f/bin/python -m py_compile tools/validate_stage0f_stage_a_packet.py`
- Python: 3.9.6 in the project Stage-0F environment.
- Direct module import and all 20 Draft 2020-12 schema meta-checks succeeded, so this was a bytecode-cache destination failure rather than a source syntax failure.

### Suggested Fix
Set `PYTHONPYCACHEPREFIX` to a writable `/private/tmp` directory, or use direct import/unittest when bytecode output is unnecessary.

### Metadata
- Reproducible: yes
- Related Files: tools/validate_stage0f_stage_a_packet.py, tools/stage0f_bounds_mechanics.py, tests/test_stage0f_bounds_mechanics.py
- Recurrence-Count: 2
- Last-Seen: 2026-07-28

### Resolution
- **Resolved**: 2026-07-28T18:10:00+08:00
- **Notes**: Continued with direct module import; future compile checks use a writable cache prefix. Recurrence during the bounds-mechanics audit was resolved with `PYTHONPYCACHEPREFIX=/private/tmp/stage0f-pycache`.

---

## [ERR-20260728-042] cross_file_patch_context_mismatch

**Logged**: 2026-07-28T19:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
One `apply_patch` attempted to remove a test-file line while still inside a
fixture-file update hunk, so context verification failed without changing
files.

### Error
```text
apply_patch verification failed: Failed to find expected lines
```

### Suggested Fix
Use an explicit `*** Update File` boundary for every file in a multi-file
patch.

### Resolution
- **Resolved**: 2026-07-28T19:05:00+08:00
- **Notes**: Reissued the patch with separate file headers; tests passed.

---

## [ERR-20260728-043] unittest_class_name_mismatch

**Logged**: 2026-07-28T20:15:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A targeted unittest invocation used an assumed class name instead of the
test module's declared class name.

### Error
```text
AttributeError: module 'tests.test_stage0f_bounds_mechanics' has no
attribute 'BoundsMechanicsTest'
```

### Suggested Fix
Resolve the class with `rg '^class .*Test'` before constructing a dotted
target.

### Metadata
- Reproducible: yes
- Related Files: tests/test_stage0f_bounds_mechanics.py

### Resolution
- **Resolved**: 2026-07-28T20:16:00+08:00
- **Notes**: Reran the X61 target with `Stage0FBoundsMechanicsTests`; it passed.

---

## [ERR-20260728-044] frozen_authority_test_sequence_type

**Logged**: 2026-07-28T20:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Two legacy assertions expected mutable lists after X53 made trusted authority
sequences recursively immutable tuples.

### Error
```text
AssertionError: (...) != [...]
```

### Suggested Fix
Assert the frozen tuple contract for authority-owned sequences; thaw only at
the JSON packet/output boundary.

### Metadata
- Reproducible: yes
- Related Files: tests/test_stage0f_bounds_mechanics.py, tools/stage0f_bounds_mechanics.py

### Resolution
- **Resolved**: 2026-07-28T20:22:00+08:00
- **Notes**: Updated X38 and X44 to assert immutable tuple values.

---
