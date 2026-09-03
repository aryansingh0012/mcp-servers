# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

import json

from sdlc_harness.needs_reader import NeedsReader


def test_trace_uses_latest_version_and_returns_reverse_links(tmp_path) -> None:
    needs_path = tmp_path / "needs.json"
    needs_path.write_text(
        json.dumps(
            {
                "versions": {
                    "1.0": {"needs": {}},
                    "2.0": {
                        "needs": {
                            "REQ-1": {
                                "title": "Requirement",
                                "type": "req",
                                "status": "open",
                                "links": ["SPEC-1"],
                                "docname": "requirements",
                            },
                            "SPEC-1": {
                                "title": "Specification",
                                "type": "spec",
                                "status": "open",
                                "links_back": ["REQ-1"],
                                "docname": "specification",
                            },
                        }
                    },
                }
            }
        ),
        encoding="utf-8-sig",
    )

    trace = NeedsReader(str(needs_path)).trace("REQ-1")

    assert trace["links_forward"] == [
        {
            "id": "SPEC-1",
            "title": "Specification",
            "type": "spec",
            "status": "open",
            "docname": "specification",
        }
    ]
    assert trace["all_linked_by"] == []
