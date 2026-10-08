# Báo cáo lab: chọn tracker cho 5 video

**Nhóm:** Việt – Linh **Thành viên:** Hoàng Quốc Việt (2A202602563), Vũ Tiến Linh (2A202602657)

Detector cố định: `yolo26n.pt`, ảnh 640 px, Re-ID `osnet_x0_25_msmt17`. Không đổi các mục này trong bài nộp chính.

File nộp: [`runs/nop_bai/video_1.txt`](../runs/nop_bai/video_1.txt) … [`video_5.txt`](../runs/nop_bai/video_5.txt), chạy đủ frame (600 / 1050 / 837 / 900 / 750), không dùng `--max-frames`. Mỗi file trùng từng byte với lượt quét cùng cấu hình (đã `cmp`), nên kết quả lặp lại được.

## 1. Cấu hình đã chọn

| Video | Tracker | conf | iou | Quan sát khi xem video | Đã thử nhưng loại |
|---|---|---|---|---|---|
| video_1 (quảng trường, tĩnh, ban ngày) | `botsort` | 0.3 | 0.7 | HOTA cao nhất trong 31 lượt chấm (30.00). Bà áo tím giữ ID 3 từ frame 1 tới 350, cô áo xanh nhạt giữ một ID từ frame 250 tới 450 ([hình](hinh/video_1_3_tracker.jpg)). Lỗi còn lại chủ yếu là **bỏ sót**: chỉ 22% hộp nhãn được phát hiện (CLR_Re 22.5), vì người ở xa quá nhỏ với ảnh 640 px. | `bytetrack` 0.3/0.5: HOTA 26.91, bỏ sót nhiều hơn (DetA 15.07). `strongsort` 0.15/0.5: IDF1 cao nhất (32.58) nhưng 110 lần đổi ID và 203 ID cho 62 người thật. `ocsort` / `deepocsort` 0.15: IDSW 168 / 157. |
| video_2 (phố đêm, tĩnh, rất đông) | `botsort` | 0.15 | 0.7 | Người trong đám đông tối được bắt thêm mà không thấy hộp nào nằm trên đèn, cọc giao thông hay xe đạp ([hình](hinh/video_2_conf.jpg)). Track dài và ổn: 63 ID, độ dài trung vị 168 frame, chỉ 5% track ngắn. Ông áo vest đi giữa phố giữ ID 64 suốt frame 500–620 ([hình](hinh/video_2_nop_bai.jpg)). | `bytetrack` 0.3: frame 500–540 người đi giữa phố rõ ràng nhưng **không có hộp** ([hình](hinh/video_2_5_tracker.jpg)); ít ID chỉ vì bỏ sót người. `botsort` 0.3/0.5: 67 ID, trung vị 102 frame, mỗi track mất rồi nối lại 2.55 lần. `ocsort` / `deepocsort`: 78 / 77 ID, ~4.3 lần đứt mỗi track. |
| video_3 (camera di động, ảnh nhỏ) | `ocsort` | 0.3 | 0.5 | Frame 510→520 camera quay ngang. OC-SORT vẫn giữ ông áo trắng là ID 128 và cô quàng khăn hồng là ID 130 từ frame 500 tới 530 ([hình](hinh/video_3_ocsort_vs_botsort.jpg)). | `botsort` 0.3 và 0.15: cùng hai người đó đổi ID ngay lúc camera quay (182→185, 167→193; 171→174, 155→182), 169 / 161 ID. `ocsort` 0.15: 217 ID, 48% track ngắn. `ocsort` 0.5: ít ID hơn (114) nhưng mất 14% hộp. |
| video_4 (trong nhà, camera di chuyển) | `strongsort` | 0.3 | 0.4 | Frame ~321 một người đi sát camera che kín ông áo sơ mi trắng. StrongSORT nhận lại ông là **ID 6** và giữ tới frame 690; ông áo đen hoa văn giữ ID 51 (frame 273–743), ông áo đỏ giữ ID 2 suốt video ([hình bản nộp](hinh/video_4_nop_bai.jpg), [so sánh 4 tracker](hinh/video_4_che_khuat.jpg)). Trong các frame đã xem, không thấy hộp nào trên bóng phản chiếu ở sàn hay kính. | `bytetrack` và `botsort` (cả 0.3 và 0.15): ông áo trắng mất ID ở frame 321 và nhận ID mới sau khi bị che. `strongsort` 0.15: 161 ID, 59% track ngắn (mỗi hộp yếu mở một track). `strongsort` 0.5: bỏ sót người (6.2 hộp/frame so với 6.9). |
| video_5 (trên xe bus, giao lộ đông) | `botsort` | 0.15 | 0.5 | Rung lắc làm track hay đứt; BoT-SORT 0.15 ít đứt nhất: 0.53 lần mất rồi nối lại mỗi track, so với 1.74 ở 0.3. Nhóm 4 người ở góc giao lộ giữ nguyên ID (cùng màu) từ frame 400 tới 420 ([hình bản nộp](hinh/video_5_nop_bai.jpg), [so sánh 5 tracker](hinh/video_5_5_tracker.jpg)). Đám người rất nhỏ ở cuối giao lộ thì **mọi** cấu hình đều bỏ sót ([hình](hinh/video_5_conf.jpg)). | `bytetrack` 0.3: chỉ 2.7 hộp/frame, bỏ gần nửa số người. `strongsort` / `ocsort` 0.3: 105 / 98 ID, nhiều track ngắn (43–45%). `botsort` 0.5: 2.4 hộp/frame. |

Cách chọn với video không có nhãn: xem ảnh có vẽ ID to ([`scripts/compare_frames.py`](../scripts/compare_frames.py)) ở những đoạn có che khuất hoặc camera quay, rồi đối chiếu số đại diện của [`scripts/track_stats.py`](../scripts/track_stats.py). Các số đó **không phải điểm chất lượng**; chúng chỉ giúp tìm chỗ cần xem kỹ. Bảng đầy đủ ở Phụ lục B.

## 2. Số liệu video_1

Output của `scripts/evaluate_practice.py` cho `runs/nop_bai/video_1.txt` (botsort, conf 0.3, iou 0.7). Toàn văn ở [`results/eval_video_1_nop_bai.txt`](../results/eval_video_1_nop_bai.txt).

```
HOTA: nhom_viet_linh_video1-pedestrianHOTA      DetA      AssA      DetRe     DetPr     AssRe     AssPr     LocA      OWTA      HOTA(0)   LocA(0)   HOTALocA(0)
video_1                            30.001    18.423    49.119    19.15     75.053    52.441    80.973    83.068    30.623    37.161    76.942    28.593
COMBINED                           30.001    18.423    49.119    19.15     75.053    52.441    80.973    83.068    30.623    37.161    76.942    28.593

CLEAR: nhom_viet_linh_video1-pedestrianMOTA      MOTP      MODA      CLR_Re    CLR_Pr    MTR       PTR       MLR       sMOTA     CLR_TP    CLR_FN    CLR_FP    IDSW      MT        PT        ML        Frag
video_1                            19.278    80.815    19.455    22.485    88.125    14.516    17.742    67.742    14.964    4178      14403     563       33        9         11        42        105
COMBINED                           19.278    80.815    19.455    22.485    88.125    14.516    17.742    67.742    14.964    4178      14403     563       33        9         11        42        105

Identity: nhom_viet_linh_video1-pedestrianIDF1      IDR       IDP       IDTP      IDFN      IDFP
video_1                            29.749    18.67     73.17     3469      15112     1272
COMBINED                           29.749    18.67     73.17     3469      15112     1272

Count: nhom_viet_linh_video1-pedestrianDets      GT_Dets   IDs       GT_IDs
video_1                            4741      18581     54        62
COMBINED                           4741      18581     54        62
```

Tóm tắt: **HOTA 30.00 · MOTA 19.28 · IDF1 29.75 · IDSW 33**. Precision cao (88%) nhưng recall thấp (22%): 14 403 hộp nhãn bị bỏ sót, so với chỉ 563 hộp giả và 33 lần đổi ID. Điểm của video này bị giới hạn bởi detector nano ở 640 px, không phải bởi tracker.

`video_2` đến `video_5` không có nhãn trong gói lab. Không điền số cho các video đó.

## 3. Phân tích

**video_1 — vì sao BoT-SORT, và vì sao hạ conf không giúp mọi tracker như nhau.** Trên 31 lượt chấm, BoT-SORT chiếm 7 vị trí đầu theo HOTA ([biểu đồ](hinh/video_1_sweep.png)). Camera tĩnh, người đi chậm và hay đi thành nhóm, nên ghép theo chuyển động đã khá tốt; Re-ID của BoT-SORT giúp nối lại người sau khi bị che, nâng AssA lên 49 so với 42 của OC-SORT. Hạ `conf` xuống 0.15 tăng DetA với mọi tracker, nhưng hậu quả khác hẳn nhau. OC-SORT, DeepOCSORT và StrongSORT mở track ngay từ hộp đầu tiên (`min_hits` / `n_init` = 1), nên mỗi hộp yếu nhấp nháy thành một ID mới: IDSW tăng từ 46 lên 168 với OC-SORT. BoT-SORT cần điểm ≥ 0.21 mới mở track mới (`new_track_thresh`) nhưng dùng hộp ≥ 0.1 để nối track cũ, nên hộp yếu chỉ kéo dài track mà không đẻ ID. ByteTrack gần như không đổi theo `conf` vì chính nó bỏ mọi hộp dưới 0.5 khỏi bước mở track (`track_thresh: 0.5`).

**video_3 (chỉ xem bằng mắt) — vì sao OC-SORT thắng tracker có Re-ID.** Đây là cảnh camera cầm tay đi trên phố, ảnh 640×480 và ít frame mỗi giây, nên giữa hai frame người dịch chuyển rất xa. Khi camera quay (frame 510→520), BoT-SORT đổi ID hai người đang đi phía trước, còn OC-SORT giữ nguyên cả hai. OC-SORT sửa vận tốc Kalman dựa trên lần quan sát thật gần nhất thay vì tin vào dự đoán, nên nối lại được dù chuyển động không tuyến tính. Ngược lại, đặc trưng Re-ID cắt từ ảnh nhỏ và mờ không đủ phân biệt người để bù lại. Kết luận nhóm rút ra: Re-ID không tự động tốt hơn; nó cần ảnh người đủ lớn và đủ nét.

**video_4 (chỉ xem bằng mắt) — vì sao StrongSORT.** Camera tiến về phía trước sau lưng người đi bộ, nên cùng một người ở trong khung hình rất lâu và thường bị người khác đi sát camera che kín. Nhìn số đại diện thì BoT-SORT 0.15 có vẻ hơn (ít ID và ít track ngắn hơn), nhưng xem video thì thấy nó mất ông áo trắng ở frame 321. StrongSORT nhận lại ông là ID 6 sau khi bị che và giữ tới frame 680. Track dài nhất của StrongSORT là 874 frame, so với 709 của BoT-SORT. StrongSORT kết hợp khoảng cách ngoại hình (trung bình EMA của đặc trưng Re-ID) với bù chuyển động camera ECC, hợp với cảnh người lớn, rõ và camera trôi đều. Cái giá là nhiều mảnh track ngắn hơn (33%), chủ yếu ở người đi ngang mép khung.

**video_2 (chỉ xem bằng mắt) — đêm, rất đông, camera tĩnh.** Vấn đề lớn nhất là bỏ sót người trong vùng tối và đông, không phải đổi ID. ByteTrack trông ổn nhất về số ID (47) chỉ vì nó không vẽ hộp cho nhiều người. Hạ `conf` xuống 0.15 với BoT-SORT bắt thêm người thật trong đám đông, và track dài ra (trung vị 102 → 168 frame) vì người không còn bị mất hộp giữa chừng. `iou` 0.7 giữ lại hộp của hai người đứng chồng lên nhau mà NMS ở 0.4–0.5 sẽ xóa, hợp với cảnh đông.

**video_5 (chỉ xem bằng mắt) — rung lắc trên xe bus.** Xe rung làm hộp nhảy giữa hai frame. BoT-SORT có bù chuyển động camera bằng optical flow thưa (`cmc_method: sparseOptFlow`), nên ít đứt track nhất (0.53 lần mỗi track ở conf 0.15). Phần người đứng xa ở giao lộ thì mọi cấu hình đều bỏ sót, nên không tracker nào có thể nối được.

## 4. Nếu có thêm thời gian

Thử detector lớn hơn hoặc ảnh 1280 px như một phần mở rộng ngoài bài nộp chính, vì recall 22% của video_1 cho thấy detector mới là nút thắt. Với tracker, thử nâng `new_track_thresh` / `min_hits` của OC-SORT và StrongSORT để giữ lợi ích của `conf` thấp mà không nổ số ID. Với video_3 và video_4, thử OC-SORT có thêm Re-ID (DeepOCSORT tắt bù chuyển động camera) để xem phần nào của cách ghép thực sự giữ được ID.

---

## Phụ lục A — Quá trình làm (CP1, CP2)

**CP1 — giả thuyết trước khi chạy và kết quả đối chiếu.**

| Giả thuyết trước khi chạy | Kết quả |
|---|---|
| video_2 rất đông: tracker chỉ theo chuyển động sẽ gán nhầm khi người cắt nhau; tracker có Re-ID sẽ hơn. | Đúng một phần. BoT-SORT (Re-ID) hơn, nhưng lỗi lớn nhất của cảnh là bỏ sót người trong vùng tối, nên `conf` 0.15 quan trọng hơn lựa chọn tracker. |
| video_3 / video_5 camera chuyển động: Re-ID sẽ cứu được khi chuyển động khó đoán. | Sai với video_3. Ảnh nhỏ, mờ làm Re-ID yếu; OC-SORT giữ ID tốt hơn. Đúng với video_5, nhưng phần giúp là bù chuyển động camera của BoT-SORT. |
| video_1 cảnh vừa phải: ByteTrack đủ dùng. | Sai. ByteTrack có ít đổi ID nhất (12) nhưng bỏ sót nhiều nhất, nên HOTA thấp hơn BoT-SORT 2.5–3 điểm. |

Notebook [`on_tap_metrics.ipynb`](../on_tap_metrics.ipynb) đã chạy trên kernel `cv_robotics_lab21`: ba câu True/False là `True / False / True`, đúng cả ba. YOLO trên frame 1 của video_1 ra 6 hộp ở conf 0.3, 14 hộp ở 0.15 và 5 hộp ở 0.5, chưa có ID.

**CP2 — baseline ByteTrack, 150 frame** (`runs/thu_nhanh/`, 16.9 FPS trên GPU). Bà áo tím giữ ID 3 và cô áo đỏ giữ ID 2 suốt 150 frame. Người bị che sau lưng bà áo tím chỉ có hộp từ khoảng frame 100, với ID mới ([hình](hinh/cp2_baseline_video1.jpg)).

**Thứ tự thử nghiệm.** (A) Cả 5 tracker ở conf 0.3 / iou 0.5 cho cả 5 video, đủ frame. (B) Với tracker có vẻ hơn, mỗi lượt đổi **một** tham số: conf 0.15 / 0.5, rồi iou 0.4 / 0.7. Ở video_1 nhóm làm bước B cho cả 5 tracker. (C) Phần mở rộng: quét conf mịn 0.15–0.4 cho BoT-SORT ở video_1, và vòng iou thứ hai ở conf 0.15 cho video_2. Tổng cộng 31 lượt chấm số trên video_1 và 46 lượt đánh giá bằng mắt cùng số đại diện trên video_2–5. Toàn bộ lượt thử đều chạy đủ frame.

**Hai người làm song song, rồi đối chiếu.** Linh chạy độc lập trên CPU và nộp một phương án lên `main` (commit `a00bbd6`, vẫn còn trong lịch sử repo). Hai bên trùng ở video_3 (`ocsort` 0.3/0.5) và khác ở bốn video còn lại. Nhóm giữ cấu hình có bằng chứng mạnh hơn:

| Video | Phương án của Linh | Bản nộp cuối | Vì sao đổi |
|---|---|---|---|
| video_1 | `bytetrack` 0.3/0.5 | `botsort` 0.3/0.7 | Có số đo: HOTA 26.91 → 30.00, IDF1 25.71 → 29.75. ByteTrack đổi ID ít nhất (12) nhưng bỏ sót nhiều nhất (CLR_Re 17.9%). |
| video_2 | `bytetrack` 0.25/0.5 | `botsort` 0.15/0.7 | ByteTrack không mở track cho hộp dưới 0.5 (`track_thresh`), nên hạ `conf` xuống 0.25 gần như không đổi gì. Ở frame 500–540 nó không vẽ hộp cho người đi giữa phố ([hình](hinh/video_2_5_tracker.jpg)). |
| video_3 | `ocsort` 0.3/0.5 | `ocsort` 0.3/0.5 | Trùng. Hai người tự đi đến cùng kết luận: OC-SORT giữ ID khi camera quay. |
| video_4 | `botsort` 0.3/0.5 | `strongsort` 0.3/0.4 | BoT-SORT mất ông áo trắng ở frame 321 sau khi bị che; StrongSORT nhận lại ông là ID 6 tới frame 690 ([hình](hinh/video_4_che_khuat.jpg)). |
| video_5 | `ocsort` 0.3/0.5 | `botsort` 0.15/0.5 | File của Linh (OC-SORT): 99 ID, 45% track ngắn, mỗi track đứt 2.07 lần. BoT-SORT 0.15: 79 ID, 23% track ngắn, 0.53 lần. |

File kết quả của Linh và của Việt ở cùng cấu hình có số dòng chênh nhau 0–2 và gần như cùng số đại diện; chỉ khác vài chữ số thập phân do một bên chạy CPU, một bên chạy GPU.

## Phụ lục B — Bảng đầy đủ

### video_1 — 31 lượt, xếp theo HOTA

Nguồn: [`results/stageA_video_1.csv`](../results/stageA_video_1.csv), [`stageB_video_1.csv`](../results/stageB_video_1.csv), [`stageC_video_1.csv`](../results/stageC_video_1.csv). Cột "Số ID" đếm trực tiếp từ file nộp, trước khi TrackEval lọc vùng không chấm.

| Hạng | Tracker | conf | iou | HOTA | DetA | AssA | MOTA | IDF1 | IDSW | Số ID |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | botsort | 0.3 | 0.7 | 30.00 | 18.42 | 49.12 | 19.28 | 29.75 | 33 | 61 |
| 2 | botsort | 0.15 | 0.7 | 29.67 | 19.49 | 45.52 | 20.45 | 30.04 | 41 | 62 |
| 3 | botsort | 0.25 | 0.7 | 29.53 | 18.77 | 46.76 | 19.61 | 28.97 | 33 | 64 |
| 4 | botsort | 0.3 | 0.5 | 29.46 | 18.09 | 48.24 | 19.79 | 29.34 | 25 | 59 |
| 5 | botsort | 0.2 | 0.7 | 29.45 | 19.13 | 45.67 | 19.92 | 29.14 | 35 | 62 |
| 6 | botsort | 0.15 | 0.5 | 29.34 | 19.29 | 45.00 | 20.83 | 29.72 | 29 | 59 |
| 7 | botsort | 0.3 | 0.4 | 29.32 | 17.36 | 49.65 | 19.45 | 29.81 | 19 | 57 |
| 8 | strongsort | 0.15 | 0.5 | 29.19 | 21.61 | 40.06 | 19.92 | 32.58 | 110 | 203 |
| 9 | botsort | 0.4 | 0.7 | 29.18 | 17.07 | 50.14 | 17.24 | 27.23 | 32 | 52 |
| 10 | botsort | 0.35 | 0.7 | 28.76 | 17.83 | 46.62 | 18.49 | 27.91 | 31 | 54 |
| 11 | strongsort | 0.2 | 0.5 | 28.74 | 20.31 | 41.10 | 20.86 | 31.80 | 82 | 150 |
| 12 | strongsort | 0.3 | 0.5 | 28.66 | 17.71 | 46.61 | 19.72 | 29.87 | 40 | 85 |
| 13 | strongsort | 0.3 | 0.4 | 28.66 | 17.70 | 46.63 | 19.78 | 29.91 | 36 | 81 |
| 14 | ocsort | 0.3 | 0.4 | 28.62 | 17.86 | 46.03 | 19.81 | 29.85 | 39 | 70 |
| 15 | strongsort | 0.3 | 0.7 | 28.20 | 17.77 | 44.98 | 19.55 | 29.52 | 58 | 97 |
| 16 | deepocsort | 0.3 | 0.4 | 27.49 | 17.83 | 42.57 | 19.80 | 27.96 | 45 | 72 |
| 17 | ocsort | 0.3 | 0.5 | 27.44 | 17.88 | 42.30 | 19.76 | 28.67 | 46 | 73 |
| 18 | deepocsort | 0.3 | 0.5 | 27.38 | 17.85 | 42.20 | 19.75 | 27.79 | 51 | 77 |
| 19 | bytetrack | 0.15 | 0.5 | 27.32 | 15.86 | 47.15 | 18.31 | 26.99 | 13 | 37 |
| 20 | botsort | 0.5 | 0.5 | 27.17 | 14.30 | 51.66 | 15.25 | 24.55 | 10 | 37 |
| 21 | deepocsort | 0.5 | 0.5 | 27.04 | 14.21 | 51.49 | 16.00 | 24.81 | 16 | 38 |
| 22 | bytetrack | 0.3 | 0.4 | 26.92 | 15.07 | 48.16 | 17.29 | 25.71 | 12 | 36 |
| 23 | bytetrack | 0.3 | 0.5 | 26.91 | 15.07 | 48.14 | 17.29 | 25.71 | 12 | 36 |
| 24 | ocsort | 0.5 | 0.5 | 26.89 | 14.20 | 50.94 | 15.98 | 24.83 | 20 | 38 |
| 25 | bytetrack | 0.3 | 0.7 | 26.02 | 15.05 | 45.02 | 17.22 | 24.85 | 13 | 37 |
| 26 | ocsort | 0.3 | 0.7 | 25.83 | 17.91 | 37.46 | 19.40 | 26.57 | 92 | 89 |
| 27 | deepocsort | 0.15 | 0.5 | 25.27 | 21.47 | 30.29 | 19.50 | 28.09 | 157 | 159 |
| 28 | bytetrack | 0.5 | 0.5 | 25.26 | 13.94 | 45.80 | 15.86 | 23.43 | 14 | 37 |
| 29 | ocsort | 0.15 | 0.5 | 25.24 | 21.57 | 30.08 | 19.50 | 28.44 | 168 | 161 |
| 30 | strongsort | 0.5 | 0.5 | 25.09 | 14.16 | 44.51 | 15.97 | 22.61 | 19 | 43 |
| 31 | deepocsort | 0.3 | 0.7 | 24.27 | 17.78 | 33.38 | 19.47 | 25.15 | 84 | 92 |

Khoảng cách giữa các cấu hình BoT-SORT đứng đầu chỉ khoảng 0.5–0.7 HOTA, trên một video 600 frame. Nhóm coi chúng gần như ngang nhau và chọn theo HOTA như hướng dẫn. Nếu ưu tiên ít đổi ID thì `botsort` 0.3/0.4 (IDSW 19) là lựa chọn kế tiếp.

### video_2–5 — số đại diện (không phải điểm chất lượng)

Nguồn: `results/stageA_video_N.csv`, `results/stageB_video_N.csv`. "Lần mất rồi nối lại" đếm số lần một ID biến mất rồi xuất hiện lại.

Ảnh đã dùng để quyết định:
- 5 tracker cùng thời điểm (conf 0.3 / iou 0.5): [video_2](hinh/video_2_5_tracker.jpg) · [video_3](hinh/video_3_5_tracker.jpg) · [video_4](hinh/video_4_5_tracker.jpg) · [video_5](hinh/video_5_5_tracker.jpg)
- BoT-SORT conf 0.3 so với 0.15: [video_2](hinh/video_2_conf.jpg) · [video_4](hinh/video_4_conf.jpg) · [video_5](hinh/video_5_conf.jpg)

**video_2**

| Tracker | conf | iou | Số ID | Hộp/frame | Độ dài track trung vị | Track ngắn (<10 f) | Lần mất rồi nối lại / track |
|---|---|---|---|---|---|---|---|
| bytetrack | 0.3 | 0.5 | 47 | 9.40 | 177 | 13% | 0.60 |
| ocsort | 0.3 | 0.5 | 78 | 11.92 | 64 | 22% | 4.31 |
| botsort | 0.3 | 0.5 | 67 | 11.73 | 102 | 18% | 2.55 |
| strongsort | 0.3 | 0.5 | 79 | 11.87 | 62 | 24% | 4.00 |
| deepocsort | 0.3 | 0.5 | 77 | 11.92 | 65 | 18% | 4.39 |
| botsort | 0.15 | 0.5 | 62 | 13.16 | 170 | 6% | 0.77 |
| botsort | 0.5 | 0.5 | 44 | 8.06 | 151.5 | 23% | 6.57 |
| botsort | 0.3 | 0.4 | 66 | 11.62 | 103.5 | 18% | 2.62 |
| botsort | 0.3 | 0.7 | 72 | 12.03 | 99.5 | 17% | 2.40 |
| botsort | 0.15 | 0.4 | 61 | 13.15 | 172 | 5% | 0.84 |
| **botsort** | **0.15** | **0.7** | **63** | **13.70** | **168** | **5%** | **0.79** |

**video_3**

| Tracker | conf | iou | Số ID | Hộp/frame | Độ dài track trung vị | Track ngắn (<10 f) | Lần mất rồi nối lại / track |
|---|---|---|---|---|---|---|---|
| bytetrack | 0.3 | 0.5 | 127 | 5.11 | 16 | 32% | 0.60 |
| **ocsort** | **0.3** | **0.5** | **137** | **5.80** | **15** | **34%** | **1.69** |
| botsort | 0.3 | 0.5 | 169 | 5.68 | 12 | 41% | 0.60 |
| strongsort | 0.3 | 0.5 | 160 | 5.71 | 11 | 46% | 0.95 |
| deepocsort | 0.3 | 0.5 | 169 | 5.76 | 13 | 40% | 1.12 |
| botsort | 0.15 | 0.5 | 161 | 6.03 | 15 | 33% | 0.48 |
| botsort | 0.5 | 0.5 | 146 | 5.11 | 12 | 41% | 0.66 |
| botsort | 0.3 | 0.4 | 167 | 5.67 | 13 | 41% | 0.62 |
| botsort | 0.3 | 0.7 | 172 | 6.62 | 14 | 39% | 0.65 |
| ocsort | 0.15 | 0.5 | 217 | 6.81 | 11 | 48% | 1.71 |
| ocsort | 0.5 | 0.5 | 114 | 4.98 | 15.5 | 31% | 1.46 |
| ocsort | 0.3 | 0.4 | 142 | 5.77 | 15 | 36% | 1.57 |
| ocsort | 0.3 | 0.7 | 154 | 5.93 | 14 | 40% | 2.14 |

ByteTrack có ít ID nhất nhưng cũng ít hộp nhất (5.11/frame). Lựa chọn OC-SORT dựa trên việc xem lại đoạn camera quay (frame 500–530), không dựa riêng vào bảng này.

**video_4**

| Tracker | conf | iou | Số ID | Hộp/frame | Độ dài track trung vị | Track ngắn (<10 f) | Lần mất rồi nối lại / track |
|---|---|---|---|---|---|---|---|
| bytetrack | 0.3 | 0.5 | 61 | 6.40 | 79 | 15% | 0.31 |
| ocsort | 0.3 | 0.5 | 79 | 7.00 | 30 | 33% | 1.54 |
| botsort | 0.3 | 0.5 | 73 | 6.91 | 45 | 27% | 0.89 |
| strongsort | 0.3 | 0.5 | 77 | 6.94 | 30 | 34% | 1.22 |
| deepocsort | 0.3 | 0.5 | 82 | 7.00 | 30 | 34% | 1.32 |
| botsort | 0.15 | 0.5 | 70 | 7.36 | 60.5 | 16% | 0.43 |
| botsort | 0.5 | 0.5 | 60 | 6.51 | 87.5 | 13% | 1.18 |
| botsort | 0.3 | 0.4 | 74 | 7.10 | 45 | 27% | 0.89 |
| botsort | 0.3 | 0.7 | 79 | 7.57 | 50 | 27% | 0.86 |
| strongsort | 0.15 | 0.5 | 161 | 7.80 | 6 | 59% | 0.86 |
| strongsort | 0.5 | 0.5 | 57 | 6.21 | 72 | 19% | 1.28 |
| **strongsort** | **0.3** | **0.4** | **76** | **6.93** | **30.5** | **33%** | **1.24** |
| strongsort | 0.3 | 0.7 | 91 | 6.98 | 18 | 42% | 1.18 |

Đây là video mà bảng số và mắt nhìn **không đồng ý**. BoT-SORT 0.15 thắng trên mọi cột, nhưng ở đoạn che khuất frame ~321 nó đổi ID người đi phía trước, còn StrongSORT thì không. Ba track dài nhất của StrongSORT là 874 / 668 / 469 frame, so với 709 / 469 / 354 của BoT-SORT 0.15. Nhóm chọn theo điều nhìn thấy, vì IDF1 phạt chính kiểu lỗi đó.

**video_5**

| Tracker | conf | iou | Số ID | Hộp/frame | Độ dài track trung vị | Track ngắn (<10 f) | Lần mất rồi nối lại / track |
|---|---|---|---|---|---|---|---|
| bytetrack | 0.3 | 0.5 | 62 | 2.70 | 23 | 37% | 0.16 |
| ocsort | 0.3 | 0.5 | 98 | 4.27 | 14.5 | 45% | 2.10 |
| botsort | 0.3 | 0.5 | 77 | 4.06 | 28 | 29% | 1.74 |
| strongsort | 0.3 | 0.5 | 105 | 4.21 | 16 | 43% | 1.60 |
| deepocsort | 0.3 | 0.5 | 93 | 4.36 | 20 | 35% | 2.47 |
| **botsort** | **0.15** | **0.5** | **79** | **4.43** | **31** | **23%** | **0.53** |
| botsort | 0.5 | 0.5 | 53 | 2.38 | 25 | 34% | 3.06 |
| botsort | 0.3 | 0.4 | 77 | 4.06 | 28 | 29% | 1.74 |
| botsort | 0.3 | 0.7 | 82 | 4.28 | 28 | 29% | 1.72 |

## Phụ lục C — Môi trường và hai chỗ phải sửa để chạy được

- Máy: Windows 11, RTX 4060 Laptop 8 GB. Không có conda, nên nhóm dùng một venv Python 3.11 (tạo bằng `uv`) với torch 2.7.1+cu126, ultralytics 8.4.174 và boxmot 10.0.42. boxmot 10.0.42 khai báo `numpy==1.23.1`, mâu thuẫn với `opencv-python` ≥ 4.8 (cần numpy ≥ 1.23.5). Nhóm cài boxmot với `--no-deps` trên numpy 1.26.4; mọi tracker chạy bình thường. Mỗi lượt đủ frame mất 15–90 giây, chạy hai lượt song song (ba lượt trở lên thì hết RAM / VRAM).
- **Gói `lab_data` thiếu `video_1/eval_config.json`**, file mà `evaluate_practice.py` cần để biết tên benchmark. Nhóm tạo file này **trong thư mục dữ liệu ở máy, không commit**, với một tên benchmark trung tính. Trong `mot_challenge_2d_box.py`, TrackEval chỉ đổi cách chấm với hai tên benchmark đặc biệt có sẵn trong code; mọi tên khác cho cùng cách chấm, với tiền xử lý bật (`DO_PREPROC: True`).
- **`evaluate_practice.py` vá `np.float` / `np.int` trong tiến trình cha, nhưng TrackEval chạy ở tiến trình con**, nên bản vá không có tác dụng (`AttributeError: module 'numpy' has no attribute 'float'`). TrackEval còn dùng `np.bool`. Nhóm sửa script để vá ngay trong tiến trình con (`TRACKEVAL_SHIM`); cách chấm không đổi.

## Phụ lục D — Công cụ thêm vào repo

| File | Việc |
|---|---|
| [`scripts/sweep.py`](../scripts/sweep.py) | Chạy nhiều cấu hình `tracker:conf:iou`, mỗi cấu hình một thư mục riêng; chấm video_1 bằng `evaluate_practice.py`; ghi CSV. |
| [`scripts/track_stats.py`](../scripts/track_stats.py) | Số đại diện cho video không nhãn: số ID, hộp/frame, độ dài track, tỉ lệ track ngắn, số lần mất rồi nối lại. |
| [`scripts/compare_frames.py`](../scripts/compare_frames.py) | Vẽ lại ID cỡ chữ lớn từ file kết quả, ghép thành lưới tracker × frame để so sánh bằng mắt. |
| [`scripts/plot_sweep.py`](../scripts/plot_sweep.py) | Biểu đồ HOTA / IDF1 / MOTA của video_1 theo tracker và tham số. |
| `tests/test_track_stats.py`, `tests/test_sweep.py`, `tests/test_compare_frames.py` | Test cho các hàm thuần (20 test, `pytest tests` đều qua; không cần GPU, ảnh lab hay mạng). |

Chạy lại toàn bộ (venv đã kích hoạt, `LAB_DATA` đã đặt):

```bash
python scripts/run_tracking.py --source "$LAB_DATA/video_1/img1" --seq-name video_1 --tracker botsort    --conf 0.3  --iou 0.7 --out runs/nop_bai --save-video --device cuda:0
python scripts/run_tracking.py --source "$LAB_DATA/video_2/img1" --seq-name video_2 --tracker botsort    --conf 0.15 --iou 0.7 --out runs/nop_bai --save-video --device cuda:0
python scripts/run_tracking.py --source "$LAB_DATA/video_3/img1" --seq-name video_3 --tracker ocsort     --conf 0.3  --iou 0.5 --out runs/nop_bai --save-video --device cuda:0
python scripts/run_tracking.py --source "$LAB_DATA/video_4/img1" --seq-name video_4 --tracker strongsort --conf 0.3  --iou 0.4 --out runs/nop_bai --save-video --device cuda:0
python scripts/run_tracking.py --source "$LAB_DATA/video_5/img1" --seq-name video_5 --tracker botsort    --conf 0.15 --iou 0.5 --out runs/nop_bai --save-video --device cuda:0
python scripts/evaluate_practice.py --trackeval-root TrackEval --lab-data-root "$LAB_DATA" --submission runs/nop_bai/video_1.txt --run-name nhom_viet_linh_video1
```

## Phụ lục E — Phần mở rộng của Linh

- **Tái lập kết quả trên CPU:** Đã chạy lại 5 cấu hình của bài nộp chính trên CPU (`runs/tai_lap_cpu`), chi tiết bảng so sánh HOTA/MOTA/IDF1 và số đại diện xem tại [`results/tai_lap_cpu.md`](../results/tai_lap_cpu.md).

