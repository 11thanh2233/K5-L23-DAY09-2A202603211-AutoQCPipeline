# Báo cáo Day 09 — VoDuyThanh, 2A202603211

> Xoá mọi `TODO(học viên)` và dòng gợi ý. Mỗi ý trả lời bằng **số lấy từ `submission/reports/`**, kèm mẫu số. Cả báo cáo ~1–2 trang.

## 1. Kết luận trước
TODO(học viên): pipeline kết luận **Release / Hold / Rework**? Bao nhiêu ảnh vào, bao nhiêu ảnh ra dataset? Lý do chính (1–3 câu).

## 2. Lỗi và phân việc
Lấy từ `02_error_list_v1` (gom theo mã lỗi). Cột "ai sửa": **máy** (autofix) hay **người** (hàng đợi); chỉ ghi những mã có mặt trong lô của bạn.

| Mã lỗi | Số ảnh/dòng | Ai sửa (máy/người) | Vì sao |
|---|---:|---|---|
| TODO(học viên) | | | |

TODO(học viên): vì sao `05_review_queue.csv` xếp ảnh đầu hàng như vậy? Với ngân sách 80 ảnh, người xem được bao nhiêu lỗi ngữ nghĩa?

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do (đánh đổi) |
|---|---|---|---|---|
| `duplicates.phash_dist` | 2 | **12** | NEAR: 1.00 / 0.50 → **1.00 / 0.67** (4/6); EXACT giữ 1.00 / 1.00 | Lỗi bắt buộc → **xoá ảnh**, nên ưu tiên precision. Trên calib 4–14 cho cùng kết quả; trên raw 10–14 cũng giống nhau (loại 17 ảnh trùng/rò rỉ). Chọn 12 ở **giữa** cặp trùng thật xa nhất đã mở xem (dist 10) và cặp sai đầu tiên (dist 16), chừa biên an toàn hai phía. |
| `second_opinion.conf` | 0.25 | **0.6** | WRONG_CLASS 0.56 / 0.83 → **0.62 / 0.83**; MISSING 0.50 / 1.00 → **0.57 / 1.00**; LOOSE_BOX 0.29 / 0.40 → 0.20 / 0.20; FALSE_POS không đổi 0.31 / 1.00 (dùng `fp_conf`) | Cảnh báo cho người nên ưu tiên **recall**. 0.6 là giá trị **cao nhất** mà MISSING vẫn giữ recall 1.00 (ở 0.7 tụt còn 0.88, ở 0.8 còn 0.75) và WRONG_CLASS giữ 0.83, trong khi bớt báo động giả: FP của MISSING 8 → 6, WRONG_CLASS 4 → 3; hàng đợi trên raw 143 → 125 ảnh. Đánh đổi: LOOSE_BOX mất 1/5 lỗi chèn (mẫu chỉ 5 nên mỗi lỗi = 20%). |

**Không chọn `conf` = 0.8 dù nó cho Release.** Tôi chạy thử pipeline trên raw với từng `conf` (`phash_dist` = 12): 0.25 → 0.7 đều **Hold** (28.7% → 14.4% ảnh còn cảnh báo), chỉ 0.8 cho **Release** (7.9%). Nhưng ở 0.8 checker bỏ sót 2/8 box bị xoá trên calib: hàng đợi nhỏ đi vì checker mù hơn, không phải vì dữ liệu sạch hơn, tức là Release giả. Tôi chọn theo sweep, chấp nhận Hold.

**Chỗ calibration đánh lừa: `phash_dist`.** Trên calib, sweep nói **16 là tốt nhất** (NEAR 1.00 / 0.83, F1 0.91, precision vẫn 1.00). Áp lên raw:

| `phash_dist` | 2–4 | 6–8 | 10–14 | 16 | 20 |
|---|---:|---:|---:|---:|---:|
| ảnh raw bị loại vì trùng/rò rỉ | 14 | 16 | 17 | **26** | **134 / 224** |

Mở xem các cặp bị cho là trùng (`work/dup_pairs.png`): img_0223–img_0077 (dist 6, đổi sáng) và img_0186–img_0061 (dist 10, cắt ảnh) là trùng thật; ở dist 16 img_0084–img_0074 trùng thật nhưng **img_0011 (tennis) – img_0008 (trượt tuyết)** và **img_0177 (lướt sóng) – img_0113 (người ngồi bàn)** là ảnh **hoàn toàn khác**, và số `LEAK_TEST` nhảy 5 → 11. Precision 1.00 trên calib là ảo: calib chỉ có 9 ảnh trùng và **không có ca LEAK_TEST**, nên báo rò rỉ sai không bị tính FP; ở dist 20 recall EXACT trên calib còn tụt (1.00 → 0.33) vì ảnh trùng byte bị gắn nhầm thành LEAK_TEST trước. Ngưỡng "tốt nhất trên calib" sẽ xoá nhầm ít nhất 2 ảnh tốt của raw. Cái giá: cặp img_0084–img_0074 (trùng thật, dist 16) lọt qua, đây là **điểm mù đã biết** (ảnh trùng biến đổi mạnh).

## 4. Cửa chặn và điều pipeline KHÔNG bắt được
**(a) Gate chặn đúng.** `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb` (không có người duyệt):
kết luận **REWORK — còn 6 lỗi bắt buộc (MISSING_LABEL_FILE) trên 6 ảnh** (img_0031, 0053, 0126, 0135, 0170, 0219), **mã thoát 20**,
log in "KHÔNG xuất: còn lỗi bắt buộc (Rework)" và thư mục `work/exp_nb` **không được tạo**. Autofix chỉ ghi `needs_label` cho 6 ảnh này,
không tạo file nhãn rỗng (rỗng = "ảnh nền", khác "chưa gán"), nên lỗi không thể bị "sửa giả" để lọt cổng.

**Lỗi tôi tự nhìn thấy khi mở `work/viz/` (10 ảnh) và đối chiếu với máy:**

| Ảnh | Mắt thấy | File nhãn / máy báo | Bài học |
|---|---|---|---|
| img_0001 | thiếu box người lính bên phải | dòng 1 và 3 gần như trùng hệt → `DUP_BOX` (dòng 3); model báo `POSSIBLE_MISSING` person conf 0.95 | box lặp **mắt không thấy** (2 khung chồng khít) nhưng máy bắt chắc chắn; box thiếu thì chỉ model nghi được |
| img_0004 | không có box nào; có tàu hỏa + 1 car | file nhãn **rỗng** → `EMPTY_LABEL`; model báo 2× `POSSIBLE_MISSING` car (conf 0.89, 0.79) | tàu hỏa ngoài 4 lớp nên không gán là đúng, nhưng car bị xoá: cần người phân biệt "ảnh nền" và "mất nhãn" |
| img_0030 | thiếu vài người, vài box lố biên | dòng 9 `x=-0.0038` → `BOX_OUT_OF_IMAGE` tràn 0.023 (máy cắt lại); model: 2× `POSSIBLE_MISSING`, 1× `POSSIBLE_LOOSE_BOX` (IoU 0.34), `POSSIBLE_FALSE_POS` dòng 9 | lỗi hình học máy tự sửa; người đứng nhỏ, chen nhau thì cần người xem |

**(b) Điểm mù có bằng chứng:**
1. **Vật nhỏ bị bỏ sót.** img_0007 thiếu vài box car (mắt thấy rõ) nhưng `second_opinion` **không cờ** gì: các xe ở xa có diện tích < `min_area_px` = 600 px², dự đoán bị lọc bỏ. Guideline "vật quá nhỏ không gán" khiến loại lỗi này lọt hoàn toàn.
2. **Đối tượng mơ hồ.** img_0002 (box 2) và img_0005 (box 5): tôi không chắc có phải người. Ở img_0005 model chỉ thấy thêm một person conf 0.30, sát ngưỡng `conf`; ngưỡng cao hơn là im lặng. Máy không phân xử được, chỉ người theo guideline mới quyết định.
3. **Lớp ngoài dự án.** Tàu hỏa (img_0004), máy bay (img_0007) không thuộc `car/person/truck/bus`. Model đã bị giới hạn 4 lớp nên không bao giờ báo; nếu người gán nhầm máy bay thành `bus`, máy chỉ bắt được khi IoU với một dự đoán khác lớp ≥ `iou_match`.
4. **Ảnh không có dự đoán trong cache** (img_0136): `second_opinion` gọi model thật, cần `ultralytics`. Ảnh này bị loại ở intake nên pipeline không gặp, nhưng nếu một ảnh mới lọt qua intake mà không có cache thì check sẽ dừng thay vì cảnh báo.

## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Chưa train: ghi "chưa chạy" và lý do, rồi bỏ qua phần còn lại của mục này. Nếu đã train: dán bảng từ `submission/results/comparison.md` (model, epoch, seed, số ảnh train mỗi biến thể).

TODO(học viên): chênh mAP50 (clean − raw) so với **độ lệch chuẩn giữa các seed**; kết luận **trung thực** (nằm trong nhiễu thì nói là chưa kết luận được); ≥ 2 giả thuyết giải thích (ảnh trùng/rò rỉ test trong `raw`, nhãn máy còn lại trong `clean`, test chỉ 100 ảnh…) và cách kiểm.

## 6. Quyết định và ghi chú AI
TODO(học viên): (a) quyết định cuối; nếu Hold/Rework cần làm gì để thành Release?

**(b) Ghi chú AI** (có dùng: Claude Code viết 4 module `label_format`, `gate`, `autofix`, `second_opinion`):
- **Prompt chính:** dán docstring của stub + file test tương ứng (`tests/test_<tên>.py`) + `pipeline/common.py`; yêu cầu: chỉ sửa đúng file stub, không viết cứng ngưỡng (đọc từ `cfg`), không sửa `data/raw` hay `tests/`, chạy `pytest tests/test_<tên>.py -q`.
- **Cách kiểm:** đọc từng hàm (autofix chỉ ghi vào `ds` = bản sao `work/run/ds`, không có `except: pass`); 79/79 test xanh; thử thêm ca ngoài test (một dòng dính 2 lỗi `93 1.2 ...` chỉ ra `BAD_CLASS_ID`, dòng trống giữa file giữ số dòng gốc, đuôi `.JPG`); chạy trên raw và đối chiếu với lỗi tự nhìn thấy (img_0001 dòng 3 `DUP_BOX`, img_0030 dòng 9 tràn 0.023, img_0004 `POSSIBLE_MISSING` car).
- **Một lần AI sai:** khi thử `second_opinion.run(ds, cfg)` trực tiếp trên `data/raw`, script chết với `RuntimeError: ... chưa cài ultralytics` vì img_0136 không có trong cache (ảnh bị loại ở intake nên pipeline thật không gặp). Sửa cách kiểm: truyền `preds=load_cache(...)`; ghi lại thành điểm mù 4 ở mục 4.

*(Thưởng +2, tùy chọn)* CVAT: lọc `width < 20`, ảnh/số box khớp, đối chiếu `BOX_TINY` (xem docs/CVAT_FILTER.md), 1 câu về `can_review`.
