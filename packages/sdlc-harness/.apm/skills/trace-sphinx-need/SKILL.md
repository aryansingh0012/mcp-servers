<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# Trace Sphinx Need

## Prerequisites

- A current sphinx-needs `needs.json` export from the S-CORE documentation build.
- The exact need ID or a source reference containing it.

## Workflow

1. Call `trace_need` with `need_id` and `needs_json_path`.
2. Inspect `links_forward`, `links_back`, and `all_linked_by`.
3. Add the applicable need IDs to the stage artifact's `links` when documenting the change.
4. Return the not-found response to the user when the ID is absent instead of guessing a replacement.