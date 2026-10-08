#!/usr/bin/env python
"""Chạy nhiều cấu hình (tracker / conf / iou) cho một video và gom kết quả vào CSV.

Script chỉ gọi lại ``run_tracking.py`` (detector và Re-ID vẫn cố định), mỗi cấu
hình ghi vào một thư mục riêng để không đè nhau. Với ``video_1`` script gọi thêm
``evaluate_practice.py`` và đọc HOTA / MOTA / IDF1; với video khác chỉ ghi số
proxy của ``track_stats.py`` (không phải điểm chất lượng).

Ví dụ (đổi tracker trước, rồi quét conf, rồi quét iou — mỗi lượt một tham số):
    python scripts/sweep.py --lab-data-root "$LAB_DATA" --video video_1 \\
        --configs bytetrack:0.3:0.5 botsort:0.3:0.5 --device cuda:0 \\
        --trackeval-root TrackEval --csv results/sweep_video_1.csv
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

from track_stats import count_frames, load_tracks, summarize

SCRIPTS = Path(__file__).resolve().parent
PRACTICE_VIDEO = "video_1"


def parse_config(text: str) -> Tuple[str, float, float]:
    """Tách chuỗi ``tracker:conf:iou``.

    Args:
        text: Ví dụ ``"botsort:0.3:0.5"``.

    Returns:
        Bộ ``(tracker, conf, iou)``.

    Raises:
        ValueError: Khi chuỗi không đủ ba phần hoặc conf / iou ngoài (0, 1).
    """
    parts = text.split(":")
    if len(parts) != 3:
        raise ValueError(f"Cấu hình phải có dạng tracker:conf:iou, nhận '{text}'")
    tracker, conf, iou = parts[0], float(parts[1]), float(parts[2])
    if not (0 < conf < 1 and 0 < iou < 1):
        raise ValueError(f"conf và iou phải trong (0, 1), nhận '{text}'")
    return tracker, conf, iou


def run_tag(tracker: str, conf: float, iou: float) -> str:
    """Tên thư mục cho một cấu hình, ví dụ ``botsort_c0.30_i0.50``.

    Args:
        tracker: Tên tracker.
        conf: Ngưỡng confidence của detector.
        iou: Ngưỡng IoU NMS của detector.

    Returns:
        Chuỗi dùng làm tên thư mục và tên lần chấm.
    """
    return f"{tracker}_c{conf:.2f}_i{iou:.2f}"


def read_trackeval_summary(summary_txt: Path) -> Dict[str, float]:
    """Đọc ``pedestrian_summary.txt`` mà TrackEval ghi ra.

    Args:
        summary_txt: File hai dòng: dòng tên cột và dòng giá trị, cách nhau bằng dấu cách.

    Returns:
        Dict tên cột -> giá trị số.
    """
    header, values = summary_txt.read_text().strip().splitlines()[:2]
    return {k: float(v) for k, v in zip(header.split(), values.split())}


def main() -> None:
    """Chạy từng cấu hình, chấm (nếu là video_1) và nối thêm dòng vào CSV."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lab-data-root", required=True, type=Path)
    parser.add_argument("--video", required=True)
    parser.add_argument("--configs", nargs="+", required=True, help="Danh sách tracker:conf:iou")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--out-root", type=Path, default=Path("runs/sweep"))
    parser.add_argument("--trackeval-root", type=Path, default=Path("TrackEval"))
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--save-video", action="store_true")
    args = parser.parse_args()

    img_dir = args.lab_data_root / args.video / "img1"
    n_total = count_frames(img_dir)
    n_frames = min(n_total, args.max_frames) if args.max_frames else n_total
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    new_file = not args.csv.exists()
    fields = ["video", "tracker", "conf", "iou", "frames", "seconds", "HOTA", "DetA", "AssA",
              "MOTA", "IDF1", "IDSW", "n_ids", "boxes_per_frame", "median_len", "short_frac",
              "ids_per_100f", "gaps_per_track"]

    with args.csv.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if new_file:
            writer.writeheader()
        for text in args.configs:
            tracker, conf, iou = parse_config(text)
            tag = run_tag(tracker, conf, iou)
            out_dir = args.out_root / args.video / tag
            cmd = [sys.executable, str(SCRIPTS / "run_tracking.py"), "--source", str(img_dir),
                   "--seq-name", args.video, "--tracker", tracker, "--conf", str(conf),
                   "--iou", str(iou), "--out", str(out_dir), "--device", args.device]
            if args.max_frames:
                cmd += ["--max-frames", str(args.max_frames)]
            if args.save_video:
                cmd.append("--save-video")
            t0 = time.time()
            subprocess.run(cmd, check=True)
            row: Dict[str, object] = {"video": args.video, "tracker": tracker, "conf": conf, "iou": iou,
                                      "frames": n_frames, "seconds": round(time.time() - t0, 1)}
            mot_txt = out_dir / f"{args.video}.txt"
            row.update({k: round(v, 4) for k, v in summarize(load_tracks(mot_txt), n_frames).items()})

            if args.video == PRACTICE_VIDEO and not args.max_frames:
                run_name = f"sweep_{tag}"
                subprocess.run([sys.executable, str(SCRIPTS / "evaluate_practice.py"),
                                "--trackeval-root", str(args.trackeval_root),
                                "--lab-data-root", str(args.lab_data_root),
                                "--submission", str(mot_txt), "--run-name", run_name],
                               check=True, stdout=subprocess.DEVNULL)
                summaries = list((args.trackeval_root / "data" / "trackers" / "mot_challenge")
                                 .glob(f"*/{run_name}/pedestrian_summary.txt"))
                scores = read_trackeval_summary(summaries[0])
                row.update({k: scores.get(k) for k in ("HOTA", "DetA", "AssA", "MOTA", "IDF1", "IDSW")})
            writer.writerow(row)
            handle.flush()
            print(f"==> {args.video} {tag}: {row}")


if __name__ == "__main__":
    main()
