---
description: "Use when: tracing S-CORE requirements, decisions, or a sphinx-needs needs.json export."
applyTo: "**/needs.json"
---

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# Sphinx-Needs Traceability

When a task refers to a S-CORE requirement or decision, call `trace_need` with the exact ID and the documentation build's `needs.json`. Use the returned forward links, explicit `links_back`, and inferred `all_linked_by` references to identify related decisions.

Record the governing need ID in artifact `links` frontmatter. Do not invent a need ID or infer a relationship from a title alone. Rebuild documentation after source need changes so the exported graph remains current.