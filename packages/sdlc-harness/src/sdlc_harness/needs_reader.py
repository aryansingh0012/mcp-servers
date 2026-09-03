#!/usr/bin/env python3
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

"""Read sphinx-needs ``needs.json`` exports and query traceability links."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class NeedNode:
    """A single requirement, decision, or other sphinx-needs node."""

    id: str
    title: str
    type: str
    status: str
    links: list[str] = field(default_factory=list)
    links_back: list[str] = field(default_factory=list)
    docname: str = ""
    description: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class NeedsReader:
    """Load a versioned sphinx-needs export and expose traceability queries."""

    def __init__(self, needs_json_path: str) -> None:
        path = Path(needs_json_path)
        if not path.exists():
            raise FileNotFoundError(
                f"needs.json not found at {needs_json_path}. "
                "Run: sphinx-build docs/ docs/_build in eclipse-score/score"
            )

        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        versions = raw.get("versions", {})
        if not versions:
            raise ValueError("needs.json has no versions")

        latest = max(versions)
        raw_needs = versions[latest].get("needs", {})
        self._needs: dict[str, NeedNode] = {}
        for need_id, need in raw_needs.items():
            self._needs[need_id] = NeedNode(
                id=need_id,
                title=need.get("title", ""),
                type=need.get("type", ""),
                status=need.get("status", ""),
                links=need.get("links", []),
                links_back=need.get("links_back", []),
                docname=need.get("docname", ""),
                description=need.get("description", ""),
                extra={
                    key: value
                    for key, value in need.items()
                    if key
                    not in {
                        "title",
                        "type",
                        "status",
                        "links",
                        "links_back",
                        "docname",
                        "description",
                    }
                },
            )

    def get(self, need_id: str) -> NeedNode | None:
        """Return a need by ID, or ``None`` when it is not present."""
        return self._needs.get(need_id)

    def trace(self, need_id: str) -> dict[str, Any]:
        """Return the declared and inferred forward and reverse trace links."""
        node = self.get(need_id)
        if node is None:
            return {"error": f"Need '{need_id}' not found in needs.json"}

        return {
            "id": node.id,
            "title": node.title,
            "type": node.type,
            "status": node.status,
            "docname": node.docname,
            "links_forward": [
                self._node_summary(self._needs[linked_id])
                for linked_id in node.links
                if linked_id in self._needs
            ],
            "links_back": [
                self._node_summary(self._needs[linked_id])
                for linked_id in node.links_back
                if linked_id in self._needs
            ],
            "all_linked_by": [
                self._node_summary(linked_node)
                for linked_node in self._needs.values()
                if need_id in linked_node.links and linked_node.id != need_id
            ],
        }

    @staticmethod
    def _node_summary(node: NeedNode) -> dict[str, str]:
        return {
            "id": node.id,
            "title": node.title,
            "type": node.type,
            "status": node.status,
            "docname": node.docname,
        }
