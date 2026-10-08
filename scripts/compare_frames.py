#!/usr/bin/env python
"""Vẽ lại ID từ nhiều file kết quả thành một ảnh lưới để so sánh bằng mắt.

Mỗi hàng là một cấu hình (một file ``video_N.txt``), mỗi cột là một frame. Ảnh
được vẽ lại từ thư mục ``img1/`` với chữ ID to, nên vẫn đọc được sau khi cắt và
thu nhỏ — dễ thấy một người giữ hay đổi ID giữa các thời điểm.

Ví dụ:
    python scripts/compare_frames.py --img-dir "$LAB_DATA/video_2/img1" \\
        --tracks runs/sweep/video_2/bytetrack_c0.30_i0.50/video_2.txt \\
                 runs/sweep/video_2/botsort_c0.30_i0.50/video_2.txt \\
        --labels bytetrack botsort --frames 100 300 500 --crop 0 0 0.5 0.6 \\
        --out submission_template/hinh/video_2_so_sanh.jpg
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np

Box = Tuple[int, float, float, float, float]  # (id, x, y, w, h)


def color_for_id(track_id: int) -> Tuple[int, int, int]:
    """Màu BGR ổn định cho mỗi ID, cùng công thức với ``run_tracking.color_for_id``.

    Chép lại ở đây để script không phải nạp ultralytics / boxmot chỉ để lấy màu.

    Args:
        track_id: Định danh track.

    Returns:
        Bộ ba ``(B, G, R)``, mỗi kênh trong khoảng 64–254.
    """
    rng = np.random.default_rng(track_id * 9973 + 17)
    return tuple(int(c) for c in rng.integers(64, 255, size=3))


def crop_box(width: int, height: int, crop: Optional[Sequence[float]]) -> Tuple[int, int, int, int]:
    """Đổi vùng cắt dạng tỉ lệ sang pixel.

    Args:
        width: Chiều rộng frame.
        height: Chiều cao frame.
        crop: ``(x0, y0, x1, y1)`` trong khoảng 0–1, hoặc ``None`` để lấy cả frame.

    Returns:
        ``(x0, y0, x1, y1)`` theo pixel.

    Raises:
        ValueError: Khi vùng cắt rỗng hoặc ra ngoài khoảng 0–1.
    """
    if crop is None:
        return 0, 0, width, height
    x0, y0, x1, y1 = crop
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError(f"Vùng cắt không hợp lệ: {crop}")
    return int(x0 * width), int(y0 * height), int(x1 * width), int(y1 * height)


def boxes_by_frame(mot_txt: Path) -> Dict[int, List[Box]]:
    """Đọc file MOT và gom hộp theo frame (frame đánh số từ 1).

    Args:
        mot_txt: File kết quả ``frame,id,x,y,w,h,conf,...``.

    Returns:
        Dict ``{frame: [(id, x, y, w, h), ...]}``.
    """
    frames: Dict[int, List[Box]] = defaultdict(list)
    for line in mot_txt.read_text().splitlines():
        if not line.strip():
            continue
        p = line.split(",")
        frames[int(float(p[0]))].append((int(float(p[1])), float(p[2]), float(p[3]), float(p[4]), float(p[5])))
    return frames


def draw_tile(image: np.ndarray, boxes: List[Box], crop: Tuple[int, int, int, int], tile_width: int,
              title: str) -> np.ndarray:
    """Cắt, thu nhỏ một frame rồi vẽ hộp và ID cỡ chữ lớn.

    Args:
        image: Ảnh BGR gốc.
        boxes: Hộp của frame này.
        crop: Vùng cắt theo pixel.
        tile_width: Chiều rộng ô sau khi thu nhỏ.
        title: Dòng tiêu đề vẽ ở mép trên.

    Returns:
        Ảnh ô đã vẽ.
    """
    x0, y0, x1, y1 = crop
    scale = tile_width / (x1 - x0)
    tile = cv2.resize(image[y0:y1, x0:x1], (tile_width, int((y1 - y0) * scale)))
    for tid, x, y, w, h in boxes:
        a = (int((x - x0) * scale), int((y - y0) * scale))
        b = (int((x + w - x0) * scale), int((y + h - y0) * scale))
        if b[0] < 0 or b[1] < 0 or a[0] > tile.shape[1] or a[1] > tile.shape[0]:
            continue
        color = color_for_id(tid)
        cv2.rectangle(tile, a, b, color, 2)
        label = str(tid)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        top = max(th + 4, a[1])
        cv2.rectangle(tile, (a[0], top - th - 4), (a[0] + tw + 4, top), color, -1)
        cv2.putText(tile, label, (a[0] + 2, top - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.rectangle(tile, (0, 0), (tile_width, 24), (0, 0, 0), -1)
    cv2.putText(tile, title, (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return tile


def main() -> None:
    """Tạo ảnh lưới hàng = cấu hình, cột = frame."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--img-dir", type=Path, required=True, help="Thư mục img1/ của video")
    parser.add_argument("--tracks", nargs="+", type=Path, required=True, help="Các file video_N.txt")
    parser.add_argument("--labels", nargs="+", required=True)
    parser.add_argument("--frames", nargs="+", type=int, required=True, help="Số frame, đánh số từ 1")
    parser.add_argument("--crop", nargs=4, type=float, default=None, help="x0 y0 x1 y1 theo tỉ lệ 0–1")
    parser.add_argument("--tile-width", type=int, default=480)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if len(args.labels) != len(args.tracks):
        raise SystemExit("Số nhãn phải bằng số file kết quả")

    images = sorted(args.img_dir.glob("*.jpg"))
    rows = []
    for mot_txt, label in zip(args.tracks, args.labels):
        frames = boxes_by_frame(mot_txt)
        tiles = []
        for number in args.frames:
            image = cv2.imread(str(images[number - 1]))
            box = crop_box(image.shape[1], image.shape[0], args.crop)
            tiles.append(draw_tile(image, frames.get(number, []), box, args.tile_width, f"{label} | frame {number}"))
        rows.append(np.hstack(tiles))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.out), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"Đã ghi {args.out}")


if __name__ == "__main__":
    main()
