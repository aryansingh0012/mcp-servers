---
description: "Use when: a user gives a new requirement, asks to create SDLC artifacts, or asks to implement a staged change."
applyTo: "**"
---

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# SDLC Lifecycle Stages

Use `.stage/ISSUE-N/` to make the decision trail for a change inspectable. When the user supplies a new requirement, call `bootstrap_sdlc_issue` once. It creates a complete review-marked draft: requirement, specification, architecture, plan, and three tasks.

Then inspect the repository and replace every `[DRAFT]` section with evidence-based content before changing production code. The MCP server creates files; it does not contain an LLM and cannot make repository-specific design decisions itself.

1. Turn the requirement into verifiable behavior in `02-specification.md`.
2. Explain system boundaries and significant technical choices in `03-architecture.md`.
3. Convert the architecture into ordered work in `04-plan.yaml` and `05-tasks/`.
4. Remove draft/review markers only after the artifacts are consistent and reviewed.
5. Store actual implementation evidence in `harness/run.json` before review.

Call `assess_sdlc_issue` after filling the draft artifacts. Address every finding before production changes: it detects unresolved `[DRAFT]` content, requirement dependencies such as `#179` that lack a `## Dependency analysis` section, and missing `## Repository evidence` sections. Repository evidence must name inspected files, symbols, and test targets.

After each implementation task, call `record_implementation_evidence` with the task filename, requirement/need IDs, changed source files, actual test commands, test statuses, and an honest task status. Call `assess_implementation_progress` before review to check completed-task percentage and unverified work. For Sphinx documentation, call `write_sphinx_progress_report` into the documentation source tree and add the generated RST file to a toctree; its `needflow` diagram renders when sphinx-needs is enabled.

Call `check_stage_completeness` before entering a later stage. It validates file presence only; it does not validate semantic consistency. Never treat a passing completeness check as proof that an agent followed the plan.