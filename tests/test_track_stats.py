"""Tests for track_stats without lab images or a network."""

from pathlib import Path

import pytest

from track_stats import load_tracks, summarize


def test_load_tracks_groups_and_sorts(tmp_path: Path) -> None:
    mot = tmp_path / "video_x.txt"
    mot.write_text("2,1,0,0,5,5,0.9,-1,-1,-1\n1,1,0,0,5,5,0.9,-1,-1,-1\n1,7,1,1,5,5,0.8,-1,-1,-1\n\n")
    assert load_tracks(mot) == {1: [1, 2], 7: [1]}


def test_summarize_counts_gaps_and_short_tracks() -> None:
    tracks = {1: list(range(1, 21)), 2: [1, 2, 5, 6], 3: [10]}
    s = summarize(tracks, n_frames=20, short_len=10)
    assert s["n_ids"] == 3
    assert s["boxes_per_frame"] == pytest.approx(25 / 20)
    assert s["median_len"] == 4
    assert s["short_frac"] == pytest.approx(2 / 3)
    assert s["ids_per_100f"] == pytest.approx(15.0)
    assert s["gaps_per_track"] == pytest.approx(1 / 3)


def test_summarize_even_count_median() -> None:
    s = summarize({1: [1, 2], 2: [1, 2, 3, 4]}, n_frames=4)
    assert s["median_len"] == 3


def test_summarize_empty_and_invalid() -> None:
    assert summarize({}, n_frames=5)["n_ids"] == 0
    with pytest.raises(ValueError):
        summarize({1: [1]}, n_frames=0)
