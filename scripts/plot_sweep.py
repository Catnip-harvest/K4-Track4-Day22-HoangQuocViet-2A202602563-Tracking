#!/usr/bin/env python
"""Vẽ biểu đồ HOTA / IDF1 / MOTA của video_1 cho từng tracker và từng lượt đổi tham số.

Đọc các CSV do ``sweep.py`` ghi (lượt gốc conf 0.3 / iou 0.5 và các lượt đổi
một tham số), rồi vẽ ba biểu đồ cột nhóm theo tracker.

Ví dụ:
    python scripts/plot_sweep.py results/stageA_video_1.csv results/stageB_video_1.csv \\
        --out submission_template/hinh/video_1_sweep.png
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

TRACKERS = ["bytetrack", "ocsort", "botsort", "strongsort", "deepocsort"]
VARIANTS = [(0.3, 0.5, "gốc 0.3/0.5"), (0.15, 0.5, "conf 0.15"), (0.5, 0.5, "conf 0.5"),
            (0.3, 0.4, "iou 0.4"), (0.3, 0.7, "iou 0.7")]
COLORS = ["#4C566A", "#5E81AC", "#88C0D0", "#D08770", "#EBCB8B"]


def main() -> None:
    """Đọc CSV và ghi ảnh biểu đồ."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    scores = {}
    for path in args.csv_files:
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row["HOTA"]:
                    scores[(row["tracker"], float(row["conf"]), float(row["iou"]))] = row

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6), sharey=False)
    width = 0.16
    for ax, metric in zip(axes, ["HOTA", "IDF1", "MOTA"]):
        for j, (conf, iou, label) in enumerate(VARIANTS):
            xs, ys = [], []
            for i, tracker in enumerate(TRACKERS):
                row = scores.get((tracker, conf, iou))
                if row:
                    xs.append(i + (j - 2) * width)
                    ys.append(float(row[metric]))
            ax.bar(xs, ys, width=width, color=COLORS[j], label=label)
        ax.set_xticks(range(len(TRACKERS)), TRACKERS)
        ax.set_title(f"video_1 — {metric}")
        ax.grid(axis="y", alpha=0.3)
        ax.set_axisbelow(True)
        values = [float(r[metric]) for r in scores.values()]
        ax.set_ylim(min(values) - 3, max(values) + 2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(VARIANTS), fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=110)
    print(f"Đã ghi {args.out}")


if __name__ == "__main__":
    main()
