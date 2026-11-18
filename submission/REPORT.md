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
| `duplicates.phash_dist` | 2 | TODO(học viên) | | |
| `second_opinion.conf` | 0.25 | TODO(học viên) | | |

TODO(học viên): **một chỗ calibration có thể đánh lừa bạn**, kèm bằng chứng từ dữ liệu của bạn (vd. mở xem vài cặp ảnh bị cho là trùng; số ảnh bị loại ở bước 1 có hợp lý không?).

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
