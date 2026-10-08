"""Tests for compare_frames.crop_box without video files."""

import pytest

from compare_frames import crop_box


def test_crop_box_full_frame() -> None:
    assert crop_box(1920, 1080, None) == (0, 0, 1920, 1080)


def test_crop_box_fraction() -> None:
    assert crop_box(1000, 500, (0.1, 0.2, 0.5, 1.0)) == (100, 100, 500, 500)


@pytest.mark.parametrize("crop", [(0.5, 0.0, 0.5, 1.0), (0.0, 0.0, 1.2, 1.0)])
def test_crop_box_rejects_bad_crop(crop: tuple) -> None:
    with pytest.raises(ValueError):
        crop_box(100, 100, crop)


def test_boxes_by_frame_groups(tmp_path) -> None:
    from compare_frames import boxes_by_frame

    mot = tmp_path / "video_x.txt"
    mot.write_text("1,4,10,20,5,6,0.9,-1,-1,-1\n2,4,11,20,5,6,0.9,-1,-1,-1\n1,9,0,0,1,1,0.5,-1,-1,-1\n")
    frames = boxes_by_frame(mot)
    assert frames[1] == [(4, 10.0, 20.0, 5.0, 6.0), (9, 0.0, 0.0, 1.0, 1.0)]
    assert frames[2] == [(4, 11.0, 20.0, 5.0, 6.0)]


def test_color_matches_run_tracking_formula() -> None:
    import numpy as np

    from compare_frames import color_for_id

    rng = np.random.default_rng(7 * 9973 + 17)
    assert color_for_id(7) == tuple(int(c) for c in rng.integers(64, 255, size=3))
