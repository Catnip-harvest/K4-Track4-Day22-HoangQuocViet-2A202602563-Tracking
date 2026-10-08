#!/usr/bin/env python
"""Chạy tracking mở rộng với khả năng ghi đè cấu hình nội bộ của tracker.

Script cho phép thử nghiệm các tham số bên trong thuật toán (ví dụ: min_hits của
OC-SORT, n_init của StrongSORT) bằng cách truyền cờ ``--override key=value``.
File cấu hình YAML gốc của tracker được sao chép ra một file tạm, sửa các khóa chỉ định,
rồi khởi tạo tracker với file cấu hình mới.

Tái sử dụng các hàm ``iter_frames``, ``detect``, ``color_for_id`` từ ``run_tracking.py``.

Ví dụ:
    python scripts/run_tracking_mo_rong.py \\
        --source "$LAB_DATA/video_1/img1" \\
        --seq-name video_1 \\
        --tracker ocsort --conf 0.15 --iou 0.5 \\
        --override min_hits=2 \\
        --out runs/mo_rong/ocsort_minhits2
"""

from __future__ import annotations

import argparse
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import cv2
import yaml
from ultralytics import YOLO

from boxmot.tracker_zoo import create_tracker, get_tracker_config

from run_tracking import (
    DETECTOR_WEIGHTS,
    IMG_SIZE,
    PERSON_CLASS_ID,
    REID_WEIGHTS,
    TRACKER_CHOICES,
    USES_APPEARANCE,
    color_for_id,
    detect,
    iter_frames,
)


def parse_override_value(val_str: str) -> Any:
    """Chuyển chuỗi giá trị thành kiểu dữ liệu phù hợp (int, float, bool, hoặc str).

    Args:
        val_str: Chuỗi giá trị cần ép kiểu.

    Returns:
        Giá trị tương ứng đã ép kiểu.
    """
    val_lower = val_str.lower()
    if val_lower in ("true", "yes"):
        return True
    if val_lower in ("false", "no"):
        return False
    try:
        return int(val_str)
    except ValueError:
        pass
    try:
        return float(val_str)
    except ValueError:
        pass
    return val_str


def parse_override(override_str: str) -> Tuple[str, Any]:
    """Tách một chuỗi key=value thành cặp (khóa, giá trị đã ép kiểu).

    Args:
        override_str: Chuỗi định dạng 'key=value'.

    Returns:
        Cặp (key, value) đã được ép kiểu.

    Raises:
        ValueError: Khi chuỗi thiếu dấu '=' hoặc khóa bị rỗng.
    """
    if "=" not in override_str:
        raise ValueError(f"Định dạng override phải là key=value, nhận được: {override_str}")
    parts = override_str.split("=", 1)
    key = parts[0].strip()
    val = parts[1].strip()
    if not key:
        raise ValueError(f"Khóa trong override không được để trống: {override_str}")
    return key, parse_override_value(val)


def parse_overrides(override_list: Optional[Sequence[str]]) -> Dict[str, Any]:
    """Chuyển danh sách các chuỗi override dạng key=value thành từ điển.

    Args:
        override_list: Danh sách chuỗi override hoặc None.

    Returns:
        Dict {key: value}.
    """
    res: Dict[str, Any] = {}
    if not override_list:
        return res
    for item in override_list:
        k, v = parse_override(item)
        res[k] = v
    return res


def create_custom_tracker_config(
    tracker_type: str,
    overrides: Dict[str, Any],
    temp_dir: Optional[Path] = None,
) -> Path:
    """Tạo file YAML cấu hình tạm thời với các tham số đã ghi đè.

    Args:
        tracker_type: Tên tracker ('ocsort', 'strongsort', ...).
        overrides: Dict chứa các tham số cần sửa đổi.
        temp_dir: Thư mục tạm tùy chọn. Nếu None sẽ dùng tempfile của hệ thống.

    Returns:
        Đường dẫn Path tới file YAML tạm.
    """
    orig_path = get_tracker_config(tracker_type)
    with open(orig_path, "r", encoding="utf-8") as f:
        cfg_dict = yaml.safe_load(f)

    cfg_dict.update(overrides)

    if temp_dir is None:
        fd, temp_path_str = tempfile.mkstemp(suffix=f"_{tracker_type}.yaml", prefix="custom_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg_dict, f)
        return Path(temp_path_str)

    temp_dir.mkdir(parents=True, exist_ok=True)
    custom_path = temp_dir / f"{tracker_type}_custom_{int(time.time()*1000)}.yaml"
    with open(custom_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg_dict, f)
    return custom_path


def run(args: argparse.Namespace) -> None:
    """Chạy quy trình phát hiện và tracking với cấu hình ghi đè.

    Args:
        args: Namespace các tham số dòng lệnh.
    """
    source = Path(args.source)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    mot_txt = out_dir / f"{args.seq_name}.txt"

    overrides = parse_overrides(args.override)
    temp_cfg = create_custom_tracker_config(args.tracker, overrides)

    try:
        print(f"[nạp mô hình] detector={DETECTOR_WEIGHTS} imgsz={IMG_SIZE} tracker={args.tracker}")
        if overrides:
            print(f"              tham số ghi đè: {overrides}")
        if args.tracker in USES_APPEARANCE:
            print(f"              tracker này dùng Re-ID: {REID_WEIGHTS.name} (tự tải nếu chưa có)")

        detector = YOLO(DETECTOR_WEIGHTS)
        tracker = create_tracker(
            tracker_type=args.tracker,
            tracker_config=temp_cfg,
            reid_weights=REID_WEIGHTS,
            device=args.device,
            half=False,
            per_class=False,
        )

        rows: List[str] = []
        n_frames = 0
        t0 = time.time()

        for frame_idx, frame in iter_frames(source):
            if frame is None:
                continue
            n_frames += 1

            dets = detect(detector, frame, conf=args.conf, iou=args.iou)
            tracks = tracker.update(dets, frame)

            for track in tracks:
                x1, y1, x2, y2, tid = track[0], track[1], track[2], track[3], track[4]
                tconf = track[5]
                rows.append(
                    f"{frame_idx + 1},{int(tid)},{x1:.2f},{y1:.2f},{x2 - x1:.2f},"
                    f"{y2 - y1:.2f},{tconf:.4f},-1,-1,-1"
                )

            if args.max_frames and n_frames >= args.max_frames:
                break

        mot_txt.write_text("\n".join(rows) + ("\n" if rows else ""))

        dt = time.time() - t0
        fps = n_frames / dt if dt > 0 else 0.0
        print(
            f"\n[{args.seq_name}] tracker={args.tracker} conf={args.conf} iou={args.iou} overrides={overrides} "
            f"-> {n_frames} frame trong {dt:.1f}s ({fps:.1f} FPS)"
        )
        print(f"  File kết quả: {mot_txt}")
    finally:
        if temp_cfg.exists():
            try:
                temp_cfg.unlink()
            except OSError:
                pass


def parse_args() -> argparse.Namespace:
    """Khai báo tham số dòng lệnh.

    Returns:
        Namespace chứa các tham số đã parse.
    """
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, help="Thư mục img1/ hoặc file .mp4")
    parser.add_argument("--seq-name", required=True, help="Tên video (ví dụ: video_1)")
    parser.add_argument("--tracker", required=True, choices=TRACKER_CHOICES)
    parser.add_argument("--conf", type=float, default=0.15, help="Ngưỡng confidence của detector")
    parser.add_argument("--iou", type=float, default=0.5, help="Ngưỡng IoU NMS của detector")
    parser.add_argument("--device", default="cpu", help="'cpu', 'cuda:0', ...")
    parser.add_argument("--out", default="runs/mo_rong", help="Thư mục xuất kết quả")
    parser.add_argument(
        "--override", action="append", default=[],
        help="Ghi đè tham số tracker (dạng key=value, có thể gọi nhiều lần)",
    )
    parser.add_argument(
        "--max-frames", type=int, default=0,
        help="Giới hạn số frame (0 = toàn bộ)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
