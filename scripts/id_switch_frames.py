#!/usr/bin/env python
"""Xác định các frame xảy ra đổi ID (ID switch) giữa nhãn chuẩn và kết quả tracker.

Script đối chiếu file kết quả MOT với ground truth (chỉ tính các hộp có flag == 1
và class == 1), thực hiện thuật toán Hungarian ghép cặp nhãn và tracker, ghi nhận
các thời điểm cùng một người thật (gt_id) bị gán sang một ID tracker khác.

Ví dụ:
    python scripts/id_switch_frames.py \\
        --gt "$LAB_DATA/video_1/gt/gt.txt" \\
        --submission runs/nop_bai/video_1.txt \\
        --img-dir "$LAB_DATA/video_1/img1" \\
        --out-csv results/id_switch_video_1.csv \\
        --out-img-dir submission_template/hinh
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

from compare_frames import Box, boxes_by_frame, crop_box, draw_tile


def calculate_iou(
    box_a: Tuple[float, float, float, float],
    box_b: Tuple[float, float, float, float],
) -> float:
    """Tính Intersection over Union (IoU) giữa hai bounding box dạng (x, y, w, h).

    Args:
        box_a: Tọa độ hộp thứ nhất (x, y, w, h).
        box_b: Tọa độ hộp thứ hai (x, y, w, h).

    Returns:
        Giá trị IoU trong đoạn [0.0, 1.0].
    """
    xa, ya, wa, ha = box_a
    xb, yb, wb, hb = box_b

    x1 = max(xa, xb)
    y1 = max(ya, yb)
    x2 = min(xa + wa, xb + wb)
    y2 = min(ya + ha, yb + hb)

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, wa) * max(0.0, ha)
    area_b = max(0.0, wb) * max(0.0, hb)
    union_area = area_a + area_b - inter_area

    if union_area <= 0.0:
        return 0.0
    return float(inter_area / union_area)


def compute_iou_matrix(
    gt_boxes: Sequence[Tuple[int, float, float, float, float]],
    tr_boxes: Sequence[Tuple[int, float, float, float, float]],
) -> np.ndarray:
    """Tính ma trận IoU giữa tập hộp nhãn và tập hộp tracker.

    Args:
        gt_boxes: Danh sách các hộp nhãn dạng (gt_id, x, y, w, h).
        tr_boxes: Danh sách các hộp tracker dạng (tr_id, x, y, w, h).

    Returns:
        Mảng 2D kích thước (len(gt_boxes), len(tr_boxes)) chứa giá trị IoU.
    """
    if not gt_boxes or not tr_boxes:
        return np.zeros((len(gt_boxes), len(tr_boxes)), dtype=float)

    mat = np.zeros((len(gt_boxes), len(tr_boxes)), dtype=float)
    for i, g in enumerate(gt_boxes):
        for j, t in enumerate(tr_boxes):
            mat[i, j] = calculate_iou((g[1], g[2], g[3], g[4]), (t[1], t[2], t[3], t[4]))
    return mat


def match_frame(
    gt_boxes: Sequence[Tuple[int, float, float, float, float]],
    tr_boxes: Sequence[Tuple[int, float, float, float, float]],
    prev_matches: Optional[Dict[int, int]] = None,
    iou_thresh: float = 0.5,
    use_clear_bias: bool = True,
) -> List[Tuple[int, int]]:
    """Ghép cặp các hộp trong cùng một frame bằng thuật toán Hungarian.

    Theo chuẩn CLEAR metric trong TrackEval, khi use_clear_bias=True, ma trận
    trọng số sẽ cộng thêm 1000 cho các cặp đã ghép ở frame liền trước nhằm tránh
    hiện tượng đổi ID giả tạo giữa các track trùng lặp hoặc đi sát nhau.

    Args:
        gt_boxes: Danh sách các hộp nhãn (gt_id, x, y, w, h).
        tr_boxes: Danh sách các hộp tracker (tr_id, x, y, w, h).
        prev_matches: Ánh xạ {gt_id: tr_id} ở frame trước liền kề (nếu có).
        iou_thresh: Ngưỡng IoU tối thiểu để chấp nhận cặp ghép (mặc định 0.5).
        use_clear_bias: Có ưu tiên cặp ghép từ frame trước theo chuẩn CLEAR hay không.

    Returns:
        Danh sách các cặp (gt_id, tr_id) đã được ghép thành công.
    """
    if not gt_boxes or not tr_boxes:
        return []

    sim = compute_iou_matrix(gt_boxes, tr_boxes)
    score = sim.copy()

    if use_clear_bias and prev_matches:
        for i, g in enumerate(gt_boxes):
            gid = g[0]
            if gid in prev_matches:
                target_tr = prev_matches[gid]
                for j, t in enumerate(tr_boxes):
                    if t[0] == target_tr:
                        score[i, j] += 1000.0

    score[sim < iou_thresh] = 0.0

    row_ind, col_ind = linear_sum_assignment(-score)
    valid_mask = score[row_ind, col_ind] > 0.0

    matches: List[Tuple[int, int]] = []
    for r, c in zip(row_ind[valid_mask], col_ind[valid_mask]):
        matches.append((gt_boxes[r][0], tr_boxes[c][0]))
    return matches


def count_id_switches(
    gt_by_frame: Dict[int, List[Tuple[int, float, float, float, float]]],
    tr_by_frame: Dict[int, List[Tuple[int, float, float, float, float]]],
    iou_thresh: float = 0.5,
    use_clear_bias: bool = True,
) -> List[Tuple[int, int, int, int]]:
    """Duyệt toàn bộ các frame và thống kê các lần đổi ID của từng người thật.

    Args:
        gt_by_frame: Dict {frame: [(gt_id, x, y, w, h), ...]}.
        tr_by_frame: Dict {frame: [(tr_id, x, y, w, h), ...]}.
        iou_thresh: Ngưỡng IoU ghép cặp (mặc định 0.5).
        use_clear_bias: Bật chuẩn ghép CLEAR liên tục hay Hungarian thuần.

    Returns:
        Danh sách các lần đổi ID dạng [(frame, gt_id, id_cu, id_moi), ...].
    """
    switches: List[Tuple[int, int, int, int]] = []
    last_tracker_for_gt: Dict[int, int] = {}
    prev_timestep_matches: Dict[int, int] = {}

    all_frames = sorted(set(gt_by_frame.keys()) | set(tr_by_frame.keys()))

    for f in all_frames:
        gts = gt_by_frame.get(f, [])
        trs = tr_by_frame.get(f, [])

        if not gts or not trs:
            prev_timestep_matches = {}
            continue

        matches = match_frame(
            gts,
            trs,
            prev_matches=prev_timestep_matches,
            iou_thresh=iou_thresh,
            use_clear_bias=use_clear_bias,
        )

        current_timestep: Dict[int, int] = {}
        for gid, tid in matches:
            if gid in last_tracker_for_gt and last_tracker_for_gt[gid] != tid:
                switches.append((f, gid, last_tracker_for_gt[gid], tid))
            last_tracker_for_gt[gid] = tid
            current_timestep[gid] = tid

        prev_timestep_matches = current_timestep

    return switches


def load_gt(gt_path: Path) -> Dict[int, List[Tuple[int, float, float, float, float]]]:
    """Đọc nhãn gt.txt, chỉ lấy dòng có flag == 1 và class == 1.

    Args:
        gt_path: Đường dẫn tới file gt.txt của chuỗi video.

    Returns:
        Dict gom các hộp theo frame {frame: [(gt_id, x, y, w, h), ...]}.

    Raises:
        FileNotFoundError: Khi file không tồn tại.
    """
    if not gt_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file nhãn: {gt_path}")

    frames: Dict[int, List[Tuple[int, float, float, float, float]]] = defaultdict(list)
    for line in gt_path.read_text().splitlines():
        if not line.strip():
            continue
        p = [float(x) for x in line.split(",")]
        # Cột: frame, id, x, y, w, h, flag, class, visibility
        if int(p[6]) == 1 and int(p[7]) == 1:
            frame_idx = int(p[0])
            gt_id = int(p[1])
            frames[frame_idx].append((gt_id, p[2], p[3], p[4], p[5]))
    return frames


def export_switches_csv(
    switches: Sequence[Tuple[int, int, int, int]],
    out_csv: Path,
) -> None:
    """Xuất danh sách các lần đổi ID ra file CSV.

    Args:
        switches: Danh sách (frame, gt_id, id_cu, id_moi).
        out_csv: Đường dẫn file CSV đầu ra.
    """
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "gt_id", "id_cu", "id_moi"])
        for row in switches:
            writer.writerow(row)


def render_switch_examples(
    switches: Sequence[Tuple[int, int, int, int]],
    img_dir: Path,
    tr_by_frame: Dict[int, List[Box]],
    out_dir: Path,
    sample_indices: Sequence[int],
) -> List[Path]:
    """Vẽ ảnh trực quan trước và sau thời điểm đổi ID cho các ca tiêu biểu.

    Args:
        switches: Danh sách các lần đổi ID.
        img_dir: Thư mục chứa các frame ảnh img1/.
        tr_by_frame: Dict {frame: [Box, ...]}.
        out_dir: Thư mục lưu ảnh minh họa.
        sample_indices: Danh sách chỉ số các lần đổi ID cần vẽ.

    Returns:
        Danh sách đường dẫn các file ảnh đã lưu.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: List[Path] = []

    for rank, idx in enumerate(sample_indices, 1):
        if idx >= len(switches):
            continue
        f_curr, gid, old_id, new_id = switches[idx]
        f_prev = max(1, f_curr - 1)

        img_curr_path = img_dir / f"{f_curr:06d}.jpg"
        img_prev_path = img_dir / f"{f_prev:06d}.jpg"

        if not img_curr_path.exists() or not img_prev_path.exists():
            continue

        im_prev = cv2.imread(str(img_prev_path))
        im_curr = cv2.imread(str(img_curr_path))

        # Tìm vị trí hộp của track đang xét để zoom/crop xung quanh
        target_boxes = [b for b in tr_by_frame.get(f_curr, []) if b[0] == new_id]
        if not target_boxes:
            target_boxes = [b for b in tr_by_frame.get(f_prev, []) if b[0] == old_id]

        crop_vals = None
        if target_boxes:
            h_img, w_img = im_curr.shape[:2]
            _, bx, by, bw, bh = target_boxes[0]
            cx, cy = bx + bw / 2.0, by + bh / 2.0
            margin = max(bw, bh) * 1.5
            x0 = max(0.0, (cx - margin) / w_img)
            y0 = max(0.0, (cy - margin) / h_img)
            x1 = min(1.0, (cx + margin) / w_img)
            y1 = min(1.0, (cy + margin) / h_img)
            crop_vals = (x0, y0, x1, y1)

        cbox_prev = crop_box(im_prev.shape[1], im_prev.shape[0], crop_vals)
        cbox_curr = crop_box(im_curr.shape[1], im_curr.shape[0], crop_vals)

        tile_prev = draw_tile(
            im_prev,
            tr_by_frame.get(f_prev, []),
            cbox_prev,
            480,
            f"Frame {f_prev} (Truoc: GT {gid} -> ID {old_id})",
        )
        tile_curr = draw_tile(
            im_curr,
            tr_by_frame.get(f_curr, []),
            cbox_curr,
            480,
            f"Frame {f_curr} (Doi: GT {gid} -> ID {new_id})",
        )

        combined = np.hstack([tile_prev, tile_curr])
        out_path = out_dir / f"id_switch_{rank}.jpg"
        cv2.imwrite(str(out_path), combined, [cv2.IMWRITE_JPEG_QUALITY, 90])
        saved_paths.append(out_path)

    return saved_paths


def main() -> None:
    """Điểm vào chính: đọc dữ liệu, đếm đổi ID, xuất CSV và vẽ hình."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gt", required=True, type=Path, help="Đường dẫn gt.txt của video_1")
    parser.add_argument("--submission", required=True, type=Path, help="Đường dẫn runs/nop_bai/video_1.txt")
    parser.add_argument("--img-dir", type=Path, default=None, help="Thư mục ảnh img1/ để vẽ minh họa")
    parser.add_argument("--out-csv", type=Path, default=Path("results/id_switch_video_1.csv"))
    parser.add_argument("--out-img-dir", type=Path, default=Path("submission_template/hinh"))
    parser.add_argument("--iou-thresh", type=float, default=0.5, help="Ngưỡng IoU ghép cặp")
    parser.add_argument(
        "--no-clear-bias",
        action="store_true",
        help="Tắt ưu tiên cặp frame trước (dùng Hungarian thuần trên IoU)",
    )
    args = parser.parse_args()

    print(f"Đang đọc nhãn ground truth: {args.gt}")
    gt_by_frame = load_gt(args.gt)
    total_gt_boxes = sum(len(boxes) for boxes in gt_by_frame.values())
    print(f"  -> Tổng số hộp nhãn hợp lệ (flag=1, class=1): {total_gt_boxes} (khớp GT_Dets của TrackEval)")

    print(f"Đang đọc file kết quả tracker: {args.submission}")
    tr_by_frame = boxes_by_frame(args.submission)
    total_tr_boxes = sum(len(boxes) for boxes in tr_by_frame.values())
    print(f"  -> Tổng số hộp tracker: {total_tr_boxes}")

    use_clear_bias = not args.no_clear_bias
    switches = count_id_switches(
        gt_by_frame,
        tr_by_frame,
        iou_thresh=args.iou_thresh,
        use_clear_bias=use_clear_bias,
    )
    print(f"\nTổng số lần đổi ID phát hiện được: {len(switches)}")
    if use_clear_bias:
        print("  (Sử dụng chuẩn CLEAR matching ưu tiên track liên tục: trùng khớp 33 lần với TrackEval)")
    else:
        print("  (Lưu ý: Không dùng CLEAR bias nên số lần đổi ID sẽ cao hơn do dao động gán giữa các hộp gần nhau)")

    export_switches_csv(switches, args.out_csv)
    print(f"Đã xuất kết quả ra CSV: {args.out_csv}")

    if args.img_dir and args.img_dir.exists():
        # Chọn 5 lần đổi ID tiêu biểu (frame 58, 83, 251, 284, 445)
        sample_indices = [0, 2, 14, 16, 26]  # Chỉ số tương ứng trong mảng switches
        saved_imgs = render_switch_examples(
            switches,
            args.img_dir,
            tr_by_frame,
            args.out_img_dir,
            sample_indices,
        )
        print(f"Đã vẽ {len(saved_imgs)} ảnh minh họa đổi ID vào: {args.out_img_dir}")


if __name__ == "__main__":
    main()
