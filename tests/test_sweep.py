"""Tests for sweep helpers without running a detector."""

from pathlib import Path

import pytest

from sweep import parse_config, read_trackeval_summary, run_tag


def test_parse_config_ok() -> None:
    assert parse_config("botsort:0.3:0.5") == ("botsort", 0.3, 0.5)


@pytest.mark.parametrize("text", ["botsort:0.3", "botsort:1.5:0.5", "botsort:0.3:0"])
def test_parse_config_rejects_bad_input(text: str) -> None:
    with pytest.raises(ValueError):
        parse_config(text)


def test_run_tag_is_stable() -> None:
    assert run_tag("ocsort", 0.15, 0.7) == "ocsort_c0.15_i0.70"


def test_read_trackeval_summary(tmp_path: Path) -> None:
    summary = tmp_path / "pedestrian_summary.txt"
    summary.write_text("HOTA DetA AssA MOTA IDF1 IDSW\n55.1 50.2 60.3 62.0 70.5 12\n")
    scores = read_trackeval_summary(summary)
    assert scores["HOTA"] == pytest.approx(55.1)
    assert scores["IDSW"] == 12
