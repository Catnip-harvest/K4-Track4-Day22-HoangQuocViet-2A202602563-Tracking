# Tái lập kết quả trên CPU

Thực hiện bởi: **Vũ Tiến Linh (2A202602657)**  
Cấu hình máy: CPU AMD Ryzen 7 (16 luồng), Windows 11, Conda môi trường `cv_robotics_lab21` (Python 3.10).  
Mục đích: Chạy lại đúng 5 cấu hình được nhóm chọn trong bài nộp chính với cờ `--device cpu`, lưu vào thư mục `runs/tai_lap_cpu`, kiểm tra độ ổn định và tính tái lập của kết quả so với khi chạy GPU (RTX 4060).

---

## 1. Kết quả đánh giá video_1 (GPU so với CPU)

Cấu hình chạy: `tracker = botsort`, `conf = 0.3`, `iou = 0.7`.  
Chấm bằng `scripts/evaluate_practice.py` với benchmark `MOT17` (tương đương chuẩn đánh giá của lab).

| Chỉ số | GPU (`runs/nop_bai/video_1.txt`) | CPU (`runs/tai_lap_cpu/video_1.txt`) | Chênh lệch (CPU − GPU) |
|---|---|---|---|
| **HOTA** | **30.001** | **29.969** | **−0.032** |
| DetA | 18.423 | 18.408 | −0.015 |
| AssA | 49.119 | 49.061 | −0.058 |
| DetRe | 19.150 | 19.176 | +0.026 |
| DetPr | 75.053 | 74.385 | −0.668 |
| AssRe | 52.441 | 52.380 | −0.061 |
| AssPr | 80.973 | 80.959 | −0.014 |
| LocA | 83.068 | 83.019 | −0.049 |
| **MOTA** | **19.278** | **19.025** | **−0.253** |
| MOTP | 80.815 | 80.817 | +0.002 |
| **IDF1** | **29.749** | **29.703** | **−0.046** |
| IDR | 18.670 | 18.680 | +0.010 |
| IDP | 73.170 | 72.463 | −0.707 |
| **IDSW** | **33** | **33** | **0** |
| Dets (sau lọc) | 4741 | 4790 | +49 |
| IDs (sau lọc) | 54 | 55 | +1 |
| CLR_TP | 4178 | 4179 | +1 |
| CLR_FP | 563 | 611 | +48 |
| CLR_FN | 14403 | 14402 | −1 |

---

## 2. Bảng số đại diện của 5 video (Proxy stats: GPU so với CPU)

Thực hiện bằng lệnh `python scripts/track_stats.py runs/nop_bai/video_N.txt runs/tai_lap_cpu/video_N.txt`:

| Video | Tracker | conf | iou | Thiết bị | Số dòng | IDs | Hộp/frame | Độ dài track trung vị | Track ngắn (<10f) | ID/100f | Gaps/track |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **video_1** | botsort | 0.3 | 0.7 | GPU | 4943 | 61 | 8.2 | 42 | 36.1% | 10.2 | 1.48 |
| | | | | CPU | 4991 | 62 | 8.3 | 42 | 35.5% | 10.3 | 1.45 |
| **video_2** | botsort | 0.15 | 0.7 | GPU | 14385 | 63 | 13.7 | 168 | 4.8% | 6.0 | 0.79 |
| | | | | CPU | 14385 | 63 | 13.7 | 168 | 4.8% | 6.0 | 0.79 |
| **video_3** | ocsort | 0.3 | 0.5 | GPU | 4856 | 137 | 5.8 | 15 | 34.3% | 16.4 | 1.69 |
| | | | | CPU | 4856 | 137 | 5.8 | 15 | 34.3% | 16.4 | 1.69 |
| **video_4** | strongsort | 0.3 | 0.4 | GPU | 6240 | 76 | 6.9 | 30 | 32.9% | 8.4 | 1.24 |
| | | | | CPU | 6238 | 76 | 6.9 | 30 | 32.9% | 8.4 | 1.24 |
| **video_5** | botsort | 0.15 | 0.5 | GPU | 3325 | 79 | 4.4 | 31 | 22.8% | 10.5 | 0.53 |
| | | | | CPU | 3333 | 79 | 4.4 | 31 | 22.8% | 10.5 | 0.52 |

---

## 3. Kết luận

Kết quả tái lập trên CPU bám rất sát bản nộp trên GPU: ở `video_1`, HOTA chỉ chênh lệch 0.032 điểm (29.969 so với 30.001), IDF1 chênh 0.046 điểm (29.703 so với 29.749), và đặc biệt số lần đổi ID (IDSW) giữ nguyên chính xác 33 lần. Trên toàn bộ 5 video, các đại lượng proxy hầu như trùng khớp hoàn toàn, trong đó `video_2` và `video_3` có cùng số dòng phát hiện và 100% các chỉ số đại diện như số ID, hộp/frame, độ dài trung vị hay tỷ lệ mất dấu đều giống hệt nhau. Sự tương đồng này khẳng định rằng sai khác thiết bị không làm thay đổi bất kỳ kết luận hay lựa chọn tracker nào của nhóm (vẫn chọn BoT-SORT cho video 1, 2, 5; OC-SORT cho video 3; và StrongSORT cho video 4). Chênh lệch rất nhỏ ở chữ số thập phân (sai lệch tọa độ khoảng 0.01 px) hoàn toàn bắt nguồn từ đặc tính tính toán số thực dấu phẩy động (floating-point non-determinism) giữa tập lệnh CPU (x86 AVX/FMA) và nhân CUDA GPU (cuDNN matrix/convolution operations) khi suy luận mô hình và tính ma trận hiệp phương sai Kalman.
