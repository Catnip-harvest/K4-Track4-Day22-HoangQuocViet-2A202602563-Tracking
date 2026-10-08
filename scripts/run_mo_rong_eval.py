#!/usr/bin/env python
"""Thực hiện chuỗi thử nghiệm mở rộng ngưỡng mở track (min_hits / n_init) trên video_1.

Script chạy 6 cấu hình:
  - ocsort: min_hits = 1 (gốc), 2, 3
  - strongsort: n_init = 1 (gốc), 2, 3
Tất cả chạy tại conf 0.15, iou 0.5, chấm điểm bằng evaluate_practice.py,
và ghi kết quả ra results/mo_rong_video_1.csv.

Ví dụ:
    python scripts/run_mo_rong_eval.py \\
        --lab-data-root "$LAB_DATA" \\
        --trackeval-root TrackEval
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

from sweep import read_trackeval_summary
from track_stats import load_tracks

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
DEFAULT_OUT_ROOT = REPO_ROOT / "runs" / "mo_rong"
DEFAULT_CSV_PATH = REPO_ROOT / "results" / "mo_rong_video_1.csv"

EXPERIMENTS = [
    ("ocsort", "min_hits", 1),
    ("ocsort", "min_hits", 2),
    ("ocsort", "min_hits", 3),
    ("strongsort", "n_init", 1),
    ("strongsort", "n_init", 2),
    ("strongsort", "n_init", 3),
]


def main() -> None:
    """Chạy toàn bộ 6 thử nghiệm mở rộng và lưu kết quả."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--lab-data-root",
        type=Path,
        default=Path(os.environ.get("LAB_DATA", "E:/VinUnni/8-10/lab_data")),
        help="Đường dẫn thư mục lab_data",
    )
    parser.add_argument(
        "--trackeval-root",
        type=Path,
        default=Path("E:/VinUnni/8-10/K4-Track4-Day22-Tracking-VuTienLinh-2A202602657/TrackEval"),
        help="Đường dẫn thư mục TrackEval",
    )
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT, help="Thư mục xuất chạy tracking")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="Đường dẫn file CSV kết quả")
    parser.add_argument("--device", default="cpu", help="Thiết bị chạy ('cpu', 'cuda:0', ...)")
    args = parser.parse_args()

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["tracker", "tham_so", "gia_tri", "HOTA", "MOTA", "IDF1", "IDSW", "So_ID"]
    rows: List[Dict[str, object]] = []

    for tracker, param, val in EXPERIMENTS:
        tag = f"{tracker}_{param}_{val}"
        run_dir = args.out_root / tag
        run_dir.mkdir(parents=True, exist_ok=True)
        mot_txt = run_dir / "video_1.txt"

        print(f"\n=======================================================")
        print(f"Đang chạy {tracker} với {param}={val} (conf 0.15, iou 0.5)...")
        print(f"=======================================================")

        cmd_track = [
            sys.executable,
            str(SCRIPTS / "run_tracking_mo_rong.py"),
            "--source", str(args.lab_data_root / "video_1" / "img1"),
            "--seq-name", "video_1",
            "--tracker", tracker,
            "--conf", "0.15",
            "--iou", "0.5",
            "--override", f"{param}={val}",
            "--out", str(run_dir),
            "--device", args.device,
        ]
        t0 = time.time()
        subprocess.run(cmd_track, check=True)
        t_track = time.time() - t0
        print(f"Tracking xong trong {t_track:.1f}s.")

        tracks = load_tracks(mot_txt)
        so_id = len(tracks)

        run_name = f"morong_{tag}"
        cmd_eval = [
            sys.executable,
            str(SCRIPTS / "evaluate_practice.py"),
            "--trackeval-root", str(args.trackeval_root),
            "--lab-data-root", str(args.lab_data_root),
            "--submission", str(mot_txt),
            "--run-name", run_name,
        ]
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        subprocess.run(cmd_eval, check=True, stdout=subprocess.DEVNULL, env=env)

        summaries = list(
            (args.trackeval_root / "data" / "trackers" / "mot_challenge").glob(f"*/{run_name}/pedestrian_summary.txt")
        )
        if not summaries:
            raise FileNotFoundError(f"Không tìm thấy pedestrian_summary.txt cho {run_name}")

        scores = read_trackeval_summary(summaries[0])
        row_data = {
            "tracker": tracker,
            "tham_so": param,
            "gia_tri": val,
            "HOTA": round(scores.get("HOTA", 0.0), 3),
            "MOTA": round(scores.get("MOTA", 0.0), 3),
            "IDF1": round(scores.get("IDF1", 0.0), 3),
            "IDSW": int(scores.get("IDSW", 0)),
            "So_ID": so_id,
        }
        rows.append(row_data)
        print(f"Kết quả {tag}: HOTA={row_data['HOTA']}, MOTA={row_data['MOTA']}, IDF1={row_data['IDF1']}, IDSW={row_data['IDSW']}, So_ID={so_id}")

    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nĐã ghi toàn bộ kết quả vào {args.csv}")


if __name__ == "__main__":
    main()
