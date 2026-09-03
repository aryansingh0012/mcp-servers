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

from sdlc_harness.loopback import REVIEW_MARKER, record_loopback


def test_record_loopback_marks_artifact_and_appends_log(tmp_path) -> None:
    artifact = tmp_path / "ISSUE-1" / "02-specification.md"
    artifact.parent.mkdir()
    artifact.write_text("# Specification\n", encoding="utf-8")

    result = record_loopback(
        "ISSUE-1",
        "Missing error state",
        "specification",
        "02-specification.md",
        str(tmp_path),
    )

    assert REVIEW_MARKER in artifact.read_text(encoding="utf-8")
    assert "Missing error state" in (
        tmp_path / "ISSUE-1" / "08-loopback-log.md"
    ).read_text(encoding="utf-8")
    assert result["log_path"].endswith("08-loopback-log.md")
