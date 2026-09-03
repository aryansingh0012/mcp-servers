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

import pytest
from sdlc_harness.artifact_writer import (
    assess_sdlc_issue,
    bootstrap_sdlc_issue,
    check_stage_completeness,
    write_stage_artifact,
)


def test_writes_numbered_artifacts_and_reports_missing_prerequisites(tmp_path) -> None:
    result = write_stage_artifact(
        "ISSUE-1",
        "requirement",
        "Login",
        "A user can sign in.",
        {"satisfies": "REQ-1"},
        str(tmp_path),
    )

    artifact = tmp_path / "ISSUE-1" / "01-requirement.md"
    assert result["path"] == str(artifact)
    assert "SPDX-License-Identifier: Apache-2.0" in artifact.read_text(encoding="utf-8")
    assert check_stage_completeness("ISSUE-1", "architecture", str(tmp_path))[
        "missing"
    ] == ["02-specification.md"]


def test_writes_incrementing_task_artifacts(tmp_path) -> None:
    first = write_stage_artifact(
        "ISSUE-1", "task", "First", "Do this.", stage_dir=str(tmp_path)
    )
    second = write_stage_artifact(
        "ISSUE-1", "task", "Second", "Then this.", stage_dir=str(tmp_path)
    )

    assert first["path"].endswith("task-001.md")
    assert second["path"].endswith("task-002.md")


def test_bootstrap_creates_complete_reviewable_draft(tmp_path) -> None:
    result = bootstrap_sdlc_issue(
        "COMM-2",
        "Connection recovery",
        "The client shall recover from a peer disconnect.",
        str(tmp_path),
    )

    issue_dir = tmp_path / "COMM-2"
    assert result["ok"] is True
    assert len(result["paths"]) == 7
    assert "[DRAFT]" in (issue_dir / "02-specification.md").read_text(encoding="utf-8")
    assert check_stage_completeness("COMM-2", "implementation", str(tmp_path))["ok"]

    with pytest.raises(ValueError, match="not empty"):
        bootstrap_sdlc_issue("COMM-2", "Duplicate", "Duplicate", str(tmp_path))


def test_assessment_flags_drafts_missing_evidence_and_dependency_analysis(
    tmp_path,
) -> None:
    bootstrap_sdlc_issue(
        "COMM-181",
        "GenericSkeletonField",
        "Add GenericSkeletonField support. Depends on: #179.",
        str(tmp_path),
    )

    assessment = assess_sdlc_issue("COMM-181", str(tmp_path))

    assert assessment["ok"] is False
    assert assessment["assessment"] == {
        "requirement": "complete",
        "specification": "mostly_placeholder",
        "architecture": "mostly_placeholder",
        "dependency_analysis": "missing",
        "repository_evidence": "missing",
        "implementation_plan": "mostly_placeholder",
        "tasks": "mostly_placeholder",
    }
    assert assessment["dependencies"] == ["#179"]
    assert any("#179" in finding for finding in assessment["findings"])
