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

from sdlc_harness.artifact_writer import bootstrap_sdlc_issue
from sdlc_harness.implementation_tracking import (
    assess_implementation_progress,
    record_implementation_evidence,
    write_sphinx_progress_report,
)


def test_tracks_task_progress_and_writes_sphinx_report(tmp_path) -> None:
    bootstrap_sdlc_issue("ISSUE-181", "Field support", "Support fields.", str(tmp_path))
    record_implementation_evidence(
        "ISSUE-181",
        "task-001.md",
        ["REQ-181"],
        ["score/generic_skeleton_field.cpp"],
        [{"command": "bazel test //score:field_test", "status": "passed"}],
        "completed",
        "Added GenericSkeletonField support.",
        str(tmp_path),
    )

    progress = assess_implementation_progress("ISSUE-181", str(tmp_path))
    report_path = tmp_path / "docs" / "implementation-progress.rst"
    report = write_sphinx_progress_report("ISSUE-181", str(report_path), str(tmp_path))

    assert progress["tasks"] == {
        "total": 3,
        "completed": 1,
        "percentage": 33,
        "without_evidence": ["task-002.md", "task-003.md"],
    }
    assert progress["requirements"]["linked"] == ["REQ-181"]
    assert progress["source_files"]["linked"] == ["score/generic_skeleton_field.cpp"]
    assert progress["tests"]["passed"] == 1
    assert report["path"] == str(report_path)
    text = report_path.read_text(encoding="utf-8")
    assert ".. needflow:: Requirement implementation trace" in text
    assert "REQ-181" in text
