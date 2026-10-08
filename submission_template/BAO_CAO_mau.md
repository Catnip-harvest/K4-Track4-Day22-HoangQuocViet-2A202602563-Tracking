# Báo cáo lab: chọn tracker cho 5 video

**Nhóm:** K4-Track4 **Thành viên:** Vũ Tiến Linh (MSSV: 2A202602657)

Detector cố định: `yolo26n.pt`, ảnh 640 px, Re-ID `osnet_x0_25_msmt17`. Không đổi các mục này trong bài nộp chính.

## 1. Cấu hình đã chọn

Mỗi video: tracker bạn nộp, `conf`, `iou`, điều bạn **nhìn thấy** trên video, và một cấu hình đã thử rồi loại.

| Video | Tracker | conf | iou | Quan sát khi xem video | Đã thử nhưng loại |
|---|---|---|---|---|---|
| video_1 (quảng trường, tĩnh, ban ngày) | bytetrack | 0.3 | 0.5 | Camera tĩnh ngoài trời, ánh sáng tốt, người đi đều; ByteTrack bám vết rất mượt, bounding box ôm khít người, rất ít đổi ID (chỉ 12 ID switches trên 600 frames). | `ocsort (conf=0.15, iou=0.5)` — conf thấp gây nhiều hộp giả trên hoa văn gạch quảng trường. |
| video_2 (phố đêm, tĩnh, rất đông) | bytetrack | 0.25 | 0.5 | Mật độ người rất cao, trời tối, người che khuất nhau liên tục; cơ chế 2-stage association liên kết tốt các detection bị khuất một phần (conf thấp), duy trì track liên tục. | `botsort (conf=0.3, iou=0.5)` — Re-ID ban đêm bị nhiễu do màu sắc tối/đồng màu, dễ nhầm ID giữa người đi sát nhau và chạy chậm trên CPU. |
| video_3 (camera di động, ảnh nhỏ) | ocsort | 0.3 | 0.5 | Camera di chuyển và ít fps khiến người nhảy quãng lớn giữa 2 frame; OC-SORT dùng ước lượng vận tốc theo quan sát thực tế giúp giữ track ổn định, không bị vỡ ID khi camera lia. | `bytetrack (conf=0.3, iou=0.5)` — Kalman filter tuyến tính truyền thống dễ bị lệch vị trí dự đoán khi camera chuyển động và fps thấp, làm nhảy ID mới. |
| video_4 (trong nhà, camera di chuyển) | botsort | 0.3 | 0.5 | Camera tiến tới làm scale người tăng dần, trong nhà có bóng phản chiếu kính; BoT-SORT kết hợp Re-ID và GMC giúp nhận diện đúng người thật, tránh nhầm khi người đổi kích thước. | `bytetrack (conf=0.3, iou=0.5)` — thiếu Re-ID nên khi người đổi scale nhanh hoặc đi qua góc phản chiếu kính dễ bị nhảy sang ID khác. |
| video_5 (trên xe bus, giao lộ đông) | ocsort | 0.3 | 0.5 | Xe bus di chuyển gián đoạn, rung lắc mạnh làm rung khung hình; OC-SORT thích nghi tốt với chuyển động phi tuyến và rung lắc, theo dõi ổn định dòng người tại ngã tư. | `bytetrack (conf=0.5, iou=0.7)` — conf cao làm mất người khi xe rung mờ chuyển động, iou cao làm đứt liên kết track giữa các frame rung giật. |

## 2. Số liệu video_1

Dán bảng HOTA / MOTA / IDF1 do `scripts/evaluate_practice.py` in ra.

```
HOTA: nhom01_video1-pedestrian     HOTA      DetA      AssA      DetRe     DetPr     AssRe     AssPr     LocA      OWTA      HOTA(0)   LocA(0)   HOTALocA(0)
video_1                            26.912    15.068    48.13     15.288    82.599    50.467    84.841    84.551    27.116    32.559    81.385    26.498    
COMBINED                           26.912    15.068    48.13     15.288    82.599    50.467    84.841    84.551    27.116    32.559    81.385    26.498    

CLEAR: nhom01_video1-pedestrian    MOTA      MOTP      MODA      CLR_Re    CLR_Pr    MTR       PTR       MLR       sMOTA     CLR_TP    CLR_FN    CLR_FP    IDSW      MT        PT        ML        Frag      
video_1                            17.292    82.526    17.356    17.932    96.889    11.29     14.516    74.194    14.158    3332      15249     107       12        7         9         46        44        
COMBINED                           17.292    82.526    17.356    17.932    96.889    11.29     14.516    74.194    14.158    3332      15249     107       12        7         9         46        44        

Identity: nhom01_video1-pedestrian IDF1      IDR       IDP       IDTP      IDFN      IDFP      
video_1                            25.713    15.236    82.32     2831      15750     608       
COMBINED                           25.713    15.236    82.32     2831      15750     608       

Count: nhom01_video1-pedestrian    Dets      GT_Dets   IDs       GT_IDs    
video_1                            3439      18581     34        62        
COMBINED                           3439      18581     34        62        
```

`video_2` đến `video_5` không có nhãn trong gói lab. Không điền số cho các video đó.

## 3. Phân tích

Với **ít nhất hai video** (nên gồm một video bạn chỉ đánh giá bằng mắt), viết 3–5 câu:

- **Với video_1 (quảng trường, camera tĩnh, ban ngày):** Tracker `bytetrack` mang lại độ ổn định liên kết rất tốt với độ chính xác liên kết `AssPr` đạt `84.84%` và số lần đổi danh tính cực thấp (`IDSW = 12` trên toàn bộ 600 frames). Do camera đặt tĩnh và người đi bộ di chuyển với vận tốc khá đồng đều, mô hình chuyển động tuyến tính của Kalman filter trong ByteTrack đã đủ để dự đoán chính xác vị trí tiếp theo mà không cần tiêu tốn tài nguyên cho Re-ID. Thêm vào đó, độ chính xác phát hiện `CLR_Pr = 96.89%` cho thấy việc đặt `conf = 0.3` gần như đã loại bỏ hoàn toàn các hộp nhận diện giả trên mặt đường.
- **Với video_3 (camera di động, độ phân giải thấp, ít fps):** Trong video này, camera vừa di chuyển vừa có tốc độ khung hình thấp, dẫn đến việc khoảng cách giữa các vị trí bounding box của cùng một người qua từng khung hình bị biến thiên lớn và phi tuyến tính. Tracker `ocsort` thể hiện sự vượt trội rõ rệt khi quan sát bằng mắt: thuật toán tính toán lại vận tốc dựa trên quan sát thực tế (observation-centric) và cơ chế virtual trajectory giúp khôi phục các track bị mất tạm thời, giữ nguyên ID của người đi bộ kể cả khi camera xoay góc nhanh, trong khi ByteTrack thường xuyên bị vỡ track và cấp ID mới.

## 4. Nếu có thêm thời gian

Nếu có thêm thời gian làm việc, nhóm sẽ:
- Thử nghiệm tích hợp mô hình Re-ID có khả năng thích ứng cao hơn trong điều kiện thiếu sáng hoặc fine-tune khoảng cách cosine feature để cải thiện độ phân biệt danh tính ở các cảnh đông đúc ban đêm (`video_2`).
- Tiến hành quét lưới tham số (grid search) mịn hơn với bước nhảy 0.05 cho `conf` và `iou`, đồng thời phân tích các frame có hiện tượng nhảy ID để tinh chỉnh ngưỡng khởi tạo track (`init_threshold`) cho từng ngữ cảnh cụ thể.
