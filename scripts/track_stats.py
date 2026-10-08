#!/usr/bin/env python
"""Thống kê "đại diện" (proxy) cho file kết quả tracking không có nhãn.

video_2–video_5 không có nhãn nên không tính được HOTA / MOTA / IDF1. Các số
dưới đây chỉ đọc từ chính file kết quả, KHÔNG phải điểm chất lượng. Chúng giúp
chỉ ra chỗ cần xem kỹ bằng mắt:

- ``ids_per_100f``: số ID mới xuất hiện trên mỗi 100 frame. Cảnh có số người ổn
  định mà con số này cao thường là dấu hiệu đổi ID / phân mảnh track.
- ``short_frac``: tỉ lệ track ngắn hơn ``short_len`` frame — hay là hộp giả
  nhấp nháy hoặc mảnh vỡ của một track dài bị cắt.
- ``gaps_per_track``: số lần một ID biến mất rồi xuất hiện lại. Cao nghĩa là
  tracker giữ được ID qua che khuất (tốt) hoặc nối nhầm (cần xem video).

Ví dụ:
    python scripts/track_stats.py runs/nop_bai/video_2.txt runs/nop_bai/video_3.txt
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def load_tracks(mot_txt: Path) -> Dict[int, List[int]]:
    """Đọc file MOT và gom các frame theo track ID.

    Args:
        mot_txt: File ``video_N.txt`` dạng MOTChallenge
            (``frame,id,x,y,w,h,conf,-1,-1,-1``).

    Returns:
        Dict ``{track_id: [frame, ...]}`` với danh sách frame đã sắp xếp tăng dần.
    """
    tracks: Dict[int, List[int]] = defaultdict(list)
    for line in mot_txt.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split(",")
        tracks[int(float(parts[1]))].append(int(float(parts[0])))
    return {tid: sorted(frames) for tid, frames in tracks.items()}


def summarize(tracks: Dict[int, List[int]], n_frames: int, short_len: int = 10) -> Dict[str, float]:
    """Tính các số proxy từ track đã gom.

    Args:
        tracks: Kết quả của ``load_tracks``.
        n_frames: Tổng số frame của video (để chuẩn hóa theo độ dài).
        short_len: Track có ít hơn số frame này bị coi là track ngắn.

    Returns:
        Dict gồm ``n_ids``, ``boxes_per_frame``, ``median_len``, ``short_frac``,
        ``ids_per_100f`` và ``gaps_per_track``. Mọi giá trị là 0 khi không có track.

    Raises:
        ValueError: Khi ``n_frames`` không dương.
    """
    if n_frames <= 0:
        raise ValueError("n_frames phải dương")
    if not tracks:
        return {
            "n_ids": 0, "boxes_per_frame": 0.0, "median_len": 0.0,
            "short_frac": 0.0, "ids_per_100f": 0.0, "gaps_per_track": 0.0,
        }
    lengths = sorted(len(frames) for frames in tracks.values())
    mid = len(lengths) // 2
    median = lengths[mid] if len(lengths) % 2 else (lengths[mid - 1] + lengths[mid]) / 2
    gaps = sum(
        sum(1 for a, b in zip(frames, frames[1:]) if b - a > 1)
        for frames in tracks.values()
    )
    return {
        "n_ids": len(tracks),
        "boxes_per_frame": sum(lengths) / n_frames,
        "median_len": float(median),
        "short_frac": sum(1 for n in lengths if n < short_len) / len(lengths),
        "ids_per_100f": 100.0 * len(tracks) / n_frames,
        "gaps_per_track": gaps / len(tracks),
    }


def count_frames(img_dir: Path) -> int:
    """Đếm ảnh ``.jpg`` trong thư mục ``img1/``.

    Args:
        img_dir: Thư mục ảnh của một video.

    Returns:
        Số file ``.jpg``.
    """
    return len(list(img_dir.glob("*.jpg")))


def main() -> None:
    """In bảng proxy cho từng file kết quả được truyền vào."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mot_files", nargs="+", type=Path)
    parser.add_argument("--n-frames", type=int, default=0,
                        help="Tổng frame; 0 = lấy frame lớn nhất trong file")
    args = parser.parse_args()
    print(f"{'file':28} {'IDs':>5} {'hộp/f':>6} {'len~':>6} {'ngắn%':>6} {'ID/100f':>8} {'gap/ID':>7}")
    for path in args.mot_files:
        tracks = load_tracks(path)
        n = args.n_frames or max((f[-1] for f in tracks.values()), default=1)
        s = summarize(tracks, n)
        print(f"{str(path)[-28:]:28} {s['n_ids']:5d} {s['boxes_per_frame']:6.1f} {s['median_len']:6.0f} "
              f"{100 * s['short_frac']:6.1f} {s['ids_per_100f']:8.1f} {s['gaps_per_track']:7.2f}")


if __name__ == "__main__":
    main()
