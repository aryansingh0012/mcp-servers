<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# SDLC Harness Implementation Guide

## Purpose

`sdlc-harness` is a local MCP server that gives an AI coding agent a durable SDLC trail. It provides lifecycle artifacts, content assessment, traceability, and implementation-progress evidence.

1. Read a sphinx-needs `needs.json` export and trace one requirement or decision.
2. Write SDLC artifacts to a deterministic `.stage/ISSUE-N/` location.
3. Check that prerequisite artifacts exist before entering a lifecycle stage.
4. Record a loopback when implementation reveals a gap in an earlier decision.

The package does not call a cloud service, modify source requirements, or build Sphinx documentation. Its inputs and outputs are local files. It can generate Sphinx-ready RST progress reports, which a target Sphinx project renders after including the file in a toctree and enabling `sphinx_needs`.

## Package Layout

```text
packages/sdlc-harness/
  apm.yml                         Package manifest and MCP process declaration
  mcp.yml                         Tool schema for APM consumers
  README.md                       Concise user guide
  IMPLEMENTATION.md               This detailed guide
  src/sdlc_harness/
    __init__.py                   Python package marker
    serve.py                      JSON-RPC over stdio MCP entry point
    needs_reader.py               sphinx-needs export reader and trace query
    artifact_writer.py            Stage artifact writer and readiness gates
    loopback.py                   Loopback logger and review marker
  tests/
    test_needs_reader.py
    test_artifact_writer.py
    test_loopback.py
  .apm/
    instructions/                 Agent behavioral guidance
    skills/                       Agent task workflows
```

The root marketplace manifest, [../../apm.yml](../../apm.yml), registers the package as `sdlc-harness` at version `0.1.0` in the `Productivity` category.

## Installation Metadata

The package manifest declares the six agent targets supported by the repository: Copilot, Claude, Cursor, Codex, Gemini, and OpenCode. It has APM dependencies on `context-discipline` and `graphify-codegraph` so an installed environment includes the complementary working-memory and code-navigation guidance.

The MCP declaration uses stdio and starts:

```text
python3 apm_modules/eclipse-score/mcp-servers/packages/sdlc-harness/src/sdlc_harness/serve.py
```

`serve.py` deliberately supports both direct-script execution and `python -m sdlc_harness.serve`. When launched as a file, it adds the package source parent to `sys.path` and imports through `sdlc_harness.*`; when imported as a module, it uses normal relative imports. This matters because a Python file executed by path otherwise has no package context for relative imports.

## MCP Server Protocol

The server accepts one JSON-RPC request per standard-input line and writes one JSON-RPC response per standard-output line. Empty input lines are ignored. `notifications/initialized` produces no response, as required for a notification.

Supported protocol methods are:

| Method | Result |
| --- | --- |
| `initialize` | Reports protocol version `2024-11-05`, empty tools capabilities, and server name/version. |
| `tools/list` | Returns four available tool definitions. |
| `tools/call` | Dispatches the named tool and wraps JSON output in MCP text content. |
| Any other method | Returns JSON-RPC error code `-32601`. |

An argument, filesystem, or tool validation error is returned with code `-32000`. The server catches `KeyError`, `OSError`, and `ValueError` from a tool invocation. Clients should include all required tool arguments and handle an MCP error response rather than expecting a process crash.

Example initialization request:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
```

Example response shape:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}},
    "serverInfo": {"name": "sdlc-harness", "version": "0.1.0"}
  }
}
```

## `trace_need`

### Inputs

| Field | Required | Meaning |
| --- | --- | --- |
| `need_id` | Yes | Exact sphinx-needs identifier, such as `stkh_req__communication__safe`. |
| `needs_json_path` | Yes | Path to a generated Sphinx `needs.json` file. |

### Data Loading

`NeedsReader` expects the sphinx-needs versioned export structure:

```json
{
  "versions": {
    "version-name": {
      "needs": {
        "NEED-ID": {"title": "...", "links": []}
      }
    }
  }
}
```

It selects the greatest version key using Python string ordering, then loads the corresponding `needs` mapping. The reader uses `utf-8-sig`, so it accepts both standard UTF-8 exports and UTF-8 files with a byte-order mark, which are commonly created by Windows tooling. If the path is missing, it raises a `FileNotFoundError` explaining how to run `sphinx-build docs/ docs/_build` in the S-CORE repository. An export with no `versions` value raises `ValueError`.

Each loaded need is represented as `NeedNode`. Common fields (`title`, `type`, `status`, `links`, `links_back`, `docname`, and `description`) are exposed directly; all remaining original fields are retained in `extra`.

### Trace Result

For a known need, the tool returns its identity fields plus three relationship lists:

| Field | Meaning |
| --- | --- |
| `links_forward` | Nodes named in the queried need's `links` field. Missing IDs are ignored. |
| `links_back` | Nodes named in the queried need's explicit `links_back` field. Missing IDs are ignored. |
| `all_linked_by` | Every other loaded node whose `links` list contains the queried ID. This is an inferred reverse relationship. |

Nodes in relationship lists contain `id`, `title`, `type`, `status`, and `docname`. A missing ID returns a normal tool result containing `{"error": "Need 'ID' not found in needs.json"}`; it is not an MCP protocol error.

## `write_stage_artifact`

### Inputs

| Field | Required | Meaning |
| --- | --- | --- |
| `issue_id` | Yes | A single issue directory name, such as `ISSUE-SDLC`. Path separators and `.`/`..` are rejected. |
| `artifact_type` | Yes | `requirement`, `specification`, `architecture`, `plan`, or `task`. |
| `title` | Yes | Human-readable artifact title. |
| `content` | Yes | Artifact body. Markdown for every type except `plan`. |
| `links` | No | Mapping of traceability link names to identifiers. |
| `stage_dir` | No | Stage root; defaults to `.stage`. |

### Deterministic Paths

The writer creates parent directories as necessary. Non-task artifact types use fixed filenames:

| Artifact type | Relative path |
| --- | --- |
| `requirement` | `01-requirement.md` |
| `specification` | `02-specification.md` |
| `architecture` | `03-architecture.md` |
| `plan` | `04-plan.yaml` |
| `task` | `05-tasks/task-NNN.md` |

Tasks count existing `task-*.md` files and assign the next three-digit number. For example, the first task is `task-001.md` and the second is `task-002.md`.

Markdown artifacts start with an Apache-2.0 SPDX comment, then YAML frontmatter containing `title` and `links`, followed by a Markdown level-one title and the supplied body. Plans use YAML comments and YAML fields (`title`, `links`, and block-scalar `content`) instead of Markdown frontmatter.

The successful result is:

```json
{"ok": "true", "path": ".stage/ISSUE-SDLC/02-specification.md"}
```

`ok` is currently the string value `"true"` for write and loopback operations. Completeness checks use boolean `ok` and `complete` fields.

## `check_stage_completeness`

This tool performs a presence check for an issue directory. It does not inspect the semantic quality or contents of artifacts.

| Target stage | Required files or directories |
| --- | --- |
| `specification` | `01-requirement.md` |
| `architecture` | Requirement and `02-specification.md` |
| `plan` | Requirement, specification, and `03-architecture.md` |
| `implementation` | Prior artifacts, `04-plan.yaml`, and a non-empty `05-tasks/` directory |
| `review` | Implementation prerequisites and `harness/run.json` |

The response has this form:

```json
{"ok": false, "complete": false, "missing": ["02-specification.md"]}
```

An unknown stage is rejected as an MCP tool error. A task directory only counts as present when it exists and contains at least one entry.

## `record_loopback`

### When to Use It

Call `record_loopback` when later work discovers that an earlier lifecycle decision is incomplete or invalid. Typical triggers include an absent error-handling requirement, an ambiguous acceptance criterion, or an architecture that cannot meet a requirement. The tool makes the return to an earlier stage explicit instead of leaving an undocumented implementation workaround.

### Inputs and Effects

The tool requires `issue_id`, a one-sentence `trigger`, `stage_returned_to`, and `affected_artifact`. Valid return stages are `requirement`, `specification`, `architecture`, `plan`, and `task`. `stage_dir` defaults to `.stage`.

For a relative `affected_artifact`, the path is resolved beneath the issue directory. If that file exists, the writer prepends this marker once:

```html
<!-- SDLC-HARNESS: review required -->
```

The tool then creates or appends to `08-loopback-log.md`. A new log gets an Apache-2.0 SPDX header and `# Loopback Log` heading. Each event includes an ISO 8601 UTC timestamp, trigger, return stage, and resolved affected-artifact path.

The affected artifact may be absent. The loopback event is still recorded, but no file is marked because there is no existing file to update.

## Implementation Tracking

`record_implementation_evidence` creates `.stage/ISSUE-N/harness/implementation-evidence.json`. Each entry is tied to one task artifact and records the linked requirement or sphinx-needs IDs, repository-relative source files, test commands/results, status, and a short factual summary.

Valid task statuses are `completed`, `in_progress`, `blocked`, and `failed`. An evidence entry replaces the prior entry for the same task, so the current task state is deterministic.

`assess_implementation_progress` reports:

- Total, completed, and percentage-complete task counts.
- Task artifacts without evidence and tasks not marked complete.
- Source files linked to implementation work.
- Requirement or sphinx-needs IDs linked to implementation work.
- Total and passed test evidence, plus any failed or blocked tests.

`write_sphinx_progress_report` writes an RST file with a task-evidence table and a sphinx-needs `needflow` directive filtered to the recorded need IDs. Add the report to the target documentation's toctree and build with `sphinx_needs` enabled. The harness cannot enable Sphinx extensions or modify source need/link configuration in another repository; that remains an explicit project integration decision.

## Agent Guidance

The `.apm/instructions/` files explain the expected lifecycle behavior:

- `sdlc-lifecycle-stages.instructions.md` defines the requirement-to-review progression.
- `sphinx-needs-traceability.instructions.md` requires exact need IDs and current Sphinx exports.
- `loopback-detection.instructions.md` defines when implementation must return to an earlier stage.

The `.apm/skills/` directories turn these into focused workflows: trace a need before linking it, let the writer choose artifact paths, and log a loopback before proceeding with dependent work.

## Validation

Run these commands from the repository root:

```powershell
$env:PYTHONPATH = "$PWD\packages\sdlc-harness\src"
uv run pytest packages/sdlc-harness/tests -q
uv run ruff check packages/sdlc-harness
uv run python -m compileall -q packages/sdlc-harness/src
apm marketplace check --offline
```

To test the stdio entry point directly:

```powershell
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' |
  uv run python packages/sdlc-harness/src/sdlc_harness/serve.py
```

The implementation has focused tests for the latest-version needs selection and trace direction, stage path generation and prerequisites, task numbering, loopback logging, and review markers.