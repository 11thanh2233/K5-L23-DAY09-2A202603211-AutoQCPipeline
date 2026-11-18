# Báo cáo Day 09 — VoDuyThanh, 2A202603211

## 1. Kết luận trước
**HOLD** (mã thoát 10). Vào **224 ảnh**, intake loại **22** (8 trùng byte, 4 gần trùng, 5 rò rỉ test, 3 quá nhỏ, 2 hỏng), xuất **202 ảnh** ra `submission/export/clean_v1/` dưới dạng **bản nháp** (`manifest.json`: `decision: Hold`, chưa phát hành).
Sau người duyệt **không còn lỗi bắt buộc** (0 ERROR trong `07_error_list_v3`), nhưng **38/202 ảnh (18.8%)** vẫn còn cảnh báo chưa duyệt, vượt ngưỡng 10%: hàng đợi có 125 ảnh mà ngân sách duyệt chỉ có 80.

## 2. Lỗi và phân việc
Số liệu từ `02_error_list_v1` (gom theo mã lỗi; mẫu số: 224 ảnh vào intake, 202 ảnh được nhận).

| Mã lỗi | Số ảnh/dòng | Ai sửa (máy/người) | Vì sao |
|---|---:|---|---|
| `DUP_IMAGE_EXACT` | 8 ảnh / 224 | máy (loại ảnh) | md5 trùng: chắc chắn, giữ ảnh đầu tiên |
| `LEAK_TEST` | 5 ảnh / 224 | máy (loại ảnh) | trùng ảnh test/val, để lại sẽ làm metric đẹp giả |
| `DUP_IMAGE_NEAR` | 4 ảnh / 224 | máy (loại ảnh) | phash ≤ 12 (đã mở xem, đúng là ảnh trùng) |
| `BAD_SIZE` / `CORRUPT_IMAGE` | 3 / 2 ảnh | máy (loại ảnh) | dưới 250 px / không mở được: không dùng để train được |
| `BAD_FORMAT` | 3 dòng / 3 ảnh | máy (xoá dòng) | thiếu cột / `nan`: không đoán được giá trị đúng |
| `BAD_CLASS_ID` | 6 dòng / 6 ảnh (id −1, 4, 7, 93) | máy (xoá dòng) | id ngoài 0..3: không biết lớp thật; box bị mất sẽ hiện lại thành `POSSIBLE_MISSING` cho người |
| `BOX_ZERO` | 4 dòng / 4 ảnh | máy (xoá dòng) | box không có diện tích |
| `DUP_BOX` | 7 dòng / 7 ảnh | máy (xoá dòng sau) | 2 box cùng lớp IoU > 0.9 (vd. img_0001 dòng 3) |
| `BOX_OUT_OF_IMAGE` | 8 dòng / 8 ảnh | máy (cắt box) | cắt về [0,1], giữ lớp (vd. img_0030 dòng 9) |
| `BAD_CLASS_NAME` | 2 tên (`Person`, `Bus`) / data.yaml | máy (ghi lại `names`) | tên lớp đã cố định trong config |
| `MISSING_LABEL_FILE` | 6 ảnh / 202 | **người** (gán nhãn) | máy không được bịa nhãn → `needs_label`, đưa lên đầu hàng đợi |
| `POSSIBLE_MISSING` | 53 / 52 ảnh | **người** | model thấy vật mà nhãn không có box |
| `POSSIBLE_FALSE_POS` | 29 / 27 ảnh | **người** | box nhãn không khớp vật nào model thấy |
| `POSSIBLE_LOOSE_BOX` | 28 / 24 ảnh | **người** | đúng vật, IoU < 0.5 |
| `POSSIBLE_WRONG_CLASS` | 18 / 18 ảnh | **người** | cùng vị trí, model nói lớp khác (car/truck/bus) |
| `EMPTY_LABEL` | 12 ảnh (v2: 15) | **người** | ảnh nền hay mất nhãn? (img_0004 có car mà file rỗng). Tăng 12 → 15 vì autofix xoá hết dòng hỏng của 3 file |
| `BOX_TINY` / `BOX_HUGE` | 6 dòng / 4 ảnh · 3 / 3 ảnh | **người** | quy tắc guideline, không chắc là lỗi |
| `CLASS_RARE` | 4 (lớp −1, 4, 7, 93) / dataset | máy (gián tiếp) | biến mất sau khi xoá các dòng `BAD_CLASS_ID` |

Tổng `02_error_list_v1`: **36 lỗi bắt buộc + 153 cảnh báo** trên 202 ảnh được nhận. Autofix: **35 thay đổi** trong `03_fixes.csv` (20 `drop_line`, 8 `clip_box`, 6 `needs_label`, 1 `rename_classes`).

**Hàng đợi (`05_review_queue.csv`, 125 ảnh).** Điểm ưu tiên = Σ trọng số mã × (1 + conf của model) + điểm cho dòng máy đã sửa. Đầu hàng là img_0020 (11.5: `FIXED_DROP_LINE` + `POSSIBLE_MISSING` + `POSSIBLE_WRONG_CLASS`), tiếp theo là 6 ảnh `NEEDS_LABEL` (trọng số 10: không có người thì chắc chắn Rework). Sau đó đến các ảnh `WRONG_CLASS` (trọng số 3) và `MISSING` / `FALSE_POS` (2) có conf cao, vì gán nhầm lớp và thiếu vật làm hại model nhiều nhất. Ảnh thứ 80 (img_0012, một `POSSIBLE_MISSING`) có điểm 3.34.
**Với ngân sách 80 ảnh:** người duyệt **74 ảnh có cảnh báo ngữ nghĩa** trên tổng 103 ảnh có loại cảnh báo này trong hàng đợi (72%), gồm **18/18** ảnh `WRONG_CLASS`, **50/52** `MISSING`, 12/23 `FALSE_POS`, nhưng chỉ **8/24** `LOOSE_BOX`, vì trọng số thấp nhất (1.5) nên bị xếp cuối. Sau duyệt, `07_error_list_v3` còn 13 `MISSING`, 3 `WRONG_CLASS`, 21 `FALSE_POS`, 20 `LOOSE_BOX`.

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

Train trên Colab (T4) bằng `scripts/train_compare.py`: **yolo26n, 20 epoch, batch 16, imgsz 640, seed 0 và 1**, cùng val (`gold_val`, 40 ảnh) và test (100 ảnh) cho cả hai biến thể. `clean` = `export/clean_v1` (bản nháp Hold, `manifest_sha1` khớp), `raw` = toàn bộ lô gốc.

| biến thể | #ảnh train | số seed | map50 (TB ± độ lệch) | map50_95 (TB ± độ lệch) | precision (TB ± độ lệch) | recall (TB ± độ lệch) |
|---|---|---|---|---|---|---|
| raw | 224 | 2 | 0.726 ± 0.000 | 0.512 ± 0.004 | 0.764 ± 0.061 | 0.649 ± 0.028 |
| clean | 202 | 2 | 0.701 ± 0.025 | 0.487 ± 0.008 | 0.759 ± 0.003 | 0.625 ± 0.019 |

**Chênh mAP50 (clean − raw) = −0.025**, bằng **độ lệch chuẩn giữa seed của clean (0.025)**; hai seed của clean là 0.718 và 0.683, khoảng của nó chứa cả 0.726 của raw. Với 2 seed và 100 ảnh test, **chưa kết luận được** clean tốt hơn hay kém hơn raw: khác biệt nằm trong nhiễu. Tôi **không** nói "pipeline làm dữ liệu tốt hơn".

AP50 theo lớp (seed 0 / seed 1): car raw 0.75 / 0.72 vs clean 0.74 / 0.74; person 0.81 / 0.83 vs 0.82 / 0.83 (gần như bằng nhau); bus 0.68 / 0.71 vs 0.73 / 0.68; **truck 0.66 / 0.64 vs 0.59 / 0.49**. Gần như toàn bộ chênh lệch đến từ **truck**, lớp chỉ có 41 box trong clean (`class_stats.csv`), và chính lớp này dao động mạnh nhất giữa 2 seed của clean (0.59 → 0.49).

**Giả thuyết và cách kiểm:**
1. **Raw được lợi nhờ rò rỉ test.** Raw chứa 5 ảnh `LEAK_TEST` trùng ảnh test (và 12 ảnh trùng lặp), nên model raw đã "thấy" một phần tập test, làm metric đẹp giả. Cách kiểm: train thêm biến thể `raw` bỏ đúng 5 ảnh rò rỉ, hoặc đo mAP trên test sau khi bỏ 5 ảnh test bị trùng; nếu khoảng cách thu hẹp thì giả thuyết đúng.
2. **Clean mất box truck.** Autofix xoá 20 dòng hỏng (6 `BAD_CLASS_ID`, 7 `DUP_BOX`, 4 `BOX_ZERO`, 3 `BAD_FORMAT`). Box bị xoá vì id sai mà chưa được người gán lại sẽ thành "thiếu nhãn", và 38 ảnh còn cảnh báo chưa duyệt vẫn mang nhãn máy (nhầm car↔truck↔bus). Với lớp ít box như truck, vài box sai/mất đủ làm AP dao động. Cách kiểm: đếm box truck raw so với clean theo ảnh; chạy lại với ngân sách duyệt lớn hơn cho đủ 38 ảnh.
3. **Nhiễu thống kê.** 2 seed, 20 epoch, 100 ảnh test (truck chỉ chiếm một phần nhỏ). Cách kiểm: ≥ 3–5 seed và bootstrap trên tập test để có khoảng tin cậy trước khi kết luận.

**Việc tiếp theo:** chạy ý 1 (bỏ ảnh rò rỉ khỏi raw) trước, vì đó là so sánh công bằng nhất; sau đó tăng số seed.

## 6. Quyết định và ghi chú AI
**(a) Quyết định cuối: HOLD.** Dataset `clean_v1` chỉ là bản nháp để thử nghiệm, chưa phát hành. Điều kiện để thành **Release**: số ảnh còn cảnh báo phải < 10% × 202, tức **≤ 20 ảnh**, nghĩa là người cần duyệt thêm **≥ 18 / 38** ảnh còn lại (ngân sách ~98 thay vì 80, hoặc thêm một vòng duyệt), ưu tiên 20 ảnh `LOOSE_BOX` và 21 ảnh `FALSE_POS` đang tồn. **Không** làm bằng cách nâng `second_opinion.conf` lên 0.8: cách đó cũng cho Release (7.9%) nhưng là vì checker mù hơn (mất 25% recall `MISSING` trên calib), không phải vì dữ liệu sạch hơn (xem mục 3).

**(b) Ghi chú AI** (có dùng: Claude Code viết 4 module `label_format`, `gate`, `autofix`, `second_opinion`):
- **Prompt chính:** dán docstring của stub + file test tương ứng (`tests/test_<tên>.py`) + `pipeline/common.py`; yêu cầu: chỉ sửa đúng file stub, không viết cứng ngưỡng (đọc từ `cfg`), không sửa `data/raw` hay `tests/`, chạy `pytest tests/test_<tên>.py -q`.
- **Cách kiểm:** đọc từng hàm (autofix chỉ ghi vào `ds` = bản sao `work/run/ds`, không có `except: pass`); 79/79 test xanh; thử thêm ca ngoài test (một dòng dính 2 lỗi `93 1.2 ...` chỉ ra `BAD_CLASS_ID`, dòng trống giữa file giữ số dòng gốc, đuôi `.JPG`); chạy trên raw và đối chiếu với lỗi tự nhìn thấy (img_0001 dòng 3 `DUP_BOX`, img_0030 dòng 9 tràn 0.023, img_0004 `POSSIBLE_MISSING` car).
- **Một lần AI sai:** khi thử `second_opinion.run(ds, cfg)` trực tiếp trên `data/raw`, script chết với `RuntimeError: ... chưa cài ultralytics` vì img_0136 không có trong cache (ảnh bị loại ở intake nên pipeline thật không gặp). Sửa cách kiểm: truyền `preds=load_cache(...)`; ghi lại thành điểm mù 4 ở mục 4.

**(Thưởng) CVAT: lọc `width < 20`.** Tạo project từ `cvat/labels.json` (CVAT bản mới đòi `values` của checkbox không rỗng, nên tôi dán bản sửa `"values": ["false"]`, không sửa file đề), task gồm **20 ảnh đầu `05_review_queue.csv`** lấy từ `work/run/ds`, import nhãn YOLO 1.1. Ảnh chụp: bộ lọc `Width < 20` ở `cvat/cvat_filter_rule.PNG`, kết quả từng ảnh ở `cvat/cvat_filter_img_*.PNG` (16 ảnh).
- **Khớp bộ lọc: 9 box trên 4/20 ảnh**, đều là `person`: img_0020 (3), img_0030 (3), img_0053 (1), img_0135 (2); các ảnh còn lại `Items: 0` (vd. img_0031, img_0160). Số này **trùng khớp** với số tôi tính trước từ file nhãn (box rộng 15.0–19.3 px).
- **Đối chiếu `BOX_TINY`: 0/9 box** bị pipeline báo. Pipeline xét **cạnh ngắn < 12 px**, còn 9 box này hẹp nhưng cao 36–75 px (người đứng xa), nên cạnh ngắn vẫn ≥ 12. Ngược lại, 5 ảnh pipeline báo `BOX_TINY` (img_0026, 0051, 0069, 0161, 0183) không nằm trong top 20 vì trọng số `BOX_TINY` chỉ 0.3. Hai công cụ bắt **hai tập khác nhau**: ngưỡng 20 px theo chiều rộng của slide bắt người xa (thường là nhãn hợp lệ), ngưỡng 12 px cạnh ngắn của dự án chỉ bắt box thật sự vụn.
- **`can_review`:** người gán tick khi chính họ không chắc (vật bị che, quá nhỏ, mơ hồ như box 2 ở img_0002), để người duyệt xem lại. Trong pipeline, vai trò này do các **cảnh báo WARN** (`POSSIBLE_*`, `BOX_TINY`, `EMPTY_LABEL`) đảm nhận: chúng không sửa nhãn mà đẩy ảnh vào `05_review_queue.csv` theo trọng số ưu tiên.
