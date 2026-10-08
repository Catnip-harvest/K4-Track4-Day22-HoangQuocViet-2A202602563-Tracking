"""Unit test cho module id_switch_frames.

Kiểm tra các hàm thuần: calculate_iou, compute_iou_matrix, match_frame,
và count_id_switches trên dữ liệu giả định nhỏ. Không dùng GPU hay ảnh thật.
"""

from __future__ import annotations

import pytest

from id_switch_frames import (
    calculate_iou,
    compute_iou_matrix,
    count_id_switches,
    match_frame,
)


def test_calculate_iou_identical() -> None:
    """Hai hộp trùng khít nhau có IoU bằng 1.0."""
    box_a = (10.0, 20.0, 30.0, 40.0)
    box_b = (10.0, 20.0, 30.0, 40.0)
    assert calculate_iou(box_a, box_b) == pytest.approx(1.0)


def test_calculate_iou_disjoint() -> None:
    """Hai hộp không giao nhau có IoU bằng 0.0."""
    box_a = (0.0, 0.0, 10.0, 10.0)
    box_b = (20.0, 20.0, 10.0, 10.0)
    assert calculate_iou(box_a, box_b) == pytest.approx(0.0)


def test_calculate_iou_partial_overlap() -> None:
    """Hai hộp giao nhau một phần cho IoU chuẩn xác."""
    # box a: [0, 0, 10, 10] diện tích 100
    # box b: [5, 0, 10, 10] diện tích 100
    # Phần giao: x trong [5, 10], y trong [0, 10] -> diện tích 50
    # Phần hợp: 100 + 100 - 50 = 150 -> IoU = 50 / 150 = 1/3
    box_a = (0.0, 0.0, 10.0, 10.0)
    box_b = (5.0, 0.0, 10.0, 10.0)
    assert calculate_iou(box_a, box_b) == pytest.approx(1.0 / 3.0)


def test_compute_iou_matrix_empty() -> None:
    """Ma trận rỗng khi một trong hai danh sách hộp rỗng."""
    mat = compute_iou_matrix([], [(1, 0.0, 0.0, 10.0, 10.0)])
    assert mat.shape == (0, 1)


def test_compute_iou_matrix_values() -> None:
    """Ma trận IoU tính đúng kích thước và giá trị các ô."""
    gt_boxes = [
        (1, 0.0, 0.0, 10.0, 10.0),
        (2, 50.0, 50.0, 10.0, 10.0),
    ]
    tr_boxes = [
        (101, 0.0, 0.0, 10.0, 10.0),
        (102, 50.0, 50.0, 10.0, 10.0),
    ]
    mat = compute_iou_matrix(gt_boxes, tr_boxes)
    assert mat.shape == (2, 2)
    assert mat[0, 0] == pytest.approx(1.0)
    assert mat[0, 1] == pytest.approx(0.0)
    assert mat[1, 0] == pytest.approx(0.0)
    assert mat[1, 1] == pytest.approx(1.0)


def test_match_frame_success_and_threshold() -> None:
    """Ghép cặp chấp nhận IoU >= 0.5 và loại bỏ cặp có IoU thấp."""
    gt_boxes = [
        (1, 0.0, 0.0, 10.0, 10.0),
        (2, 50.0, 50.0, 10.0, 10.0),
    ]
    tr_boxes = [
        (10, 0.0, 0.0, 10.0, 10.0),    # IoU = 1.0 -> ghép với GT 1
        (20, 56.0, 50.0, 10.0, 10.0),  # Giao 4x10 = 40, hợp 160 -> IoU = 0.25 < 0.5 -> bị loại
    ]
    matches = match_frame(gt_boxes, tr_boxes, iou_thresh=0.5)
    assert matches == [(1, 10)]


def test_match_frame_clear_bias() -> None:
    """Chuẩn CLEAR ưu tiên duy trì ID từ frame trước khi hai hộp gần nhau."""
    gt_boxes = [
        (1, 0.0, 0.0, 10.0, 10.0),
    ]
    # Hai hộp tracker đều có IoU > 0.5 với GT 1 (ví dụ 0.8 và 0.85)
    tr_boxes = [
        (10, 0.0, 0.0, 10.0, 10.0),   # IoU 1.0
        (20, 1.0, 0.0, 10.0, 10.0),   # IoU ~0.82
    ]
    # Nếu frame trước GT 1 đã gắn với ID 20, CLEAR bias (+1000) sẽ giữ ID 20
    prev_matches = {1: 20}
    matches = match_frame(gt_boxes, tr_boxes, prev_matches=prev_matches, use_clear_bias=True)
    assert matches == [(1, 20)]


def test_count_id_switches() -> None:
    """Đếm chính xác số lần đổi ID qua các frame liên tiếp."""
    # Frame 1: GT 1 ghép với Tracker 10
    # Frame 2: GT 1 vẫn ghép với Tracker 10 -> không đổi ID
    # Frame 3: GT 1 ghép với Tracker 20 -> đổi ID (10 -> 20)
    # Frame 4: GT 1 ghép với Tracker 20 -> không đổi ID
    gt_by_frame = {
        1: [(1, 0.0, 0.0, 10.0, 10.0)],
        2: [(1, 0.0, 0.0, 10.0, 10.0)],
        3: [(1, 0.0, 0.0, 10.0, 10.0)],
        4: [(1, 0.0, 0.0, 10.0, 10.0)],
    }
    tr_by_frame = {
        1: [(10, 0.0, 0.0, 10.0, 10.0)],
        2: [(10, 0.0, 0.0, 10.0, 10.0)],
        3: [(20, 0.0, 0.0, 10.0, 10.0)],
        4: [(20, 0.0, 0.0, 10.0, 10.0)],
    }
    switches = count_id_switches(gt_by_frame, tr_by_frame)
    assert len(switches) == 1
    assert switches[0] == (3, 1, 10, 20)
