"""CHECK 2 — Dòng nhãn YOLO: sai định dạng, ID lớp lạ, box tràn ảnh, box rỗng, box lặp.   (Script 2 trong slide)   ★★

Test:  pytest tests/test_label_format.py -q

Mỗi dòng nhãn: `id cx cy w h` (5 số, toạ độ 0–1). Trả về list[Issue]; `Issue.line` = số dòng (đếm từ 1).

| code             | severity | khi nào                                                                  |
|------------------|----------|--------------------------------------------------------------------------|
| BAD_FORMAT       | ERROR    | không đúng 5 cột số (dùng `parse_yolo_line`, bắt `ValueError`)           |
| BAD_CLASS_ID     | ERROR    | id lớp ngoài 0..len(ds.classes)-1                                        |
| BOX_ZERO         | ERROR    | w <= 0 hoặc h <= 0                                                       |
| BOX_OUT_OF_IMAGE | ERROR    | mép box vượt [0,1] quá `cfg["label_format"]["overflow_tol"]`; extra={"overflow": mức tràn} |
| DUP_BOX          | ERROR    | cùng lớp với một dòng TRƯỚC ĐÓ và IoU > `dup_box_iou`; báo ở dòng SAU    |
| BOX_TINY         | WARN     | cạnh ngắn của box (px) < `min_box_px`  (cần `ds.image_size(stem)`)       |
| BOX_HUGE         | WARN     | w*h > `max_box_frac`                                                     |

Gợi ý
- Mép trái = x - w/2, mép phải = x + w/2 (xem câu hỏi "dòng YOLO nào lỗi?" trong slide).
- Một dòng hỏng (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO) thì `continue`, đừng kiểm tiếp hình học của dòng đó.
- Dòng thiếu cột làm script của slide dừng giữa chừng: đây là lý do phải `try/except`.
- `iou_xywh(a, b)` có sẵn trong common.py.
- Ngưỡng nằm trong `cfg["label_format"]` — đừng viết cứng số vào code.
"""
from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line  # noqa: F401


NAME = "label_format"


def _overflow(x, y, w, h):
    """Mức tràn lớn nhất của 4 mép box ra ngoài [0, 1] (0 nếu nằm trong ảnh)."""
    left, right = x - w / 2, x + w / 2
    top, bottom = y - h / 2, y + h / 2
    return max(0.0, -left, right - 1.0, -top, bottom - 1.0)


def run(ds, cfg):
    lf = cfg["label_format"]
    tol, min_px = lf["overflow_tol"], lf["min_box_px"]
    max_frac, dup_iou = lf["max_box_frac"], lf["dup_box_iou"]
    n_cls = len(ds.classes)
    issues = []

    def add(sev, code, stem, msg, line, **extra):
        issues.append(Issue(NAME, sev, code, stem, msg, line=line, extra=extra))

    for lab in ds.label_files():
        stem = lab.stem
        size = ds.image_size(stem) if ds.image_path(stem) else None   # nhãn mồ côi/ảnh hỏng: bỏ qua BOX_TINY
        kept = []                                                     # (line, box) các dòng hợp lệ trước đó, để so DUP_BOX
        for no, text in ds.read_label_lines(stem) or []:              # read_label_lines bỏ dòng trống, giữ số dòng gốc
            try:
                c, x, y, w, h = parse_yolo_line(text)
            except ValueError as e:
                add(ERROR, "BAD_FORMAT", stem, f"dòng không đúng 5 cột số: {e}", no, text=text.strip())
                continue
            if not 0 <= c < n_cls:
                add(ERROR, "BAD_CLASS_ID", stem, f"id lớp {c} ngoài 0..{n_cls - 1}", no, class_id=c)
                continue
            if w <= 0 or h <= 0:
                add(ERROR, "BOX_ZERO", stem, f"box rộng/cao <= 0 (w={w}, h={h})", no)
                continue

            over = _overflow(x, y, w, h)
            if over > tol:
                add(ERROR, "BOX_OUT_OF_IMAGE", stem, f"box tràn ra ngoài ảnh {over:.4f}", no, overflow=round(over, 6))

            box = (x, y, w, h)
            for prev_no, (pc, pbox) in kept:
                if pc == c and iou_xywh(pbox, box) > dup_iou:
                    add(ERROR, "DUP_BOX", stem, f"trùng box dòng {prev_no} (cùng lớp {ds.classes[c]})", no, dup_of=prev_no)
                    break
            kept.append((no, (c, box)))

            if size:
                short_px = min(w * size[0], h * size[1])
                if short_px < min_px:
                    add(WARN, "BOX_TINY", stem, f"cạnh ngắn {short_px:.1f}px < {min_px}px", no, short_px=round(short_px, 1))
            if w * h > max_frac:
                add(WARN, "BOX_HUGE", stem, f"box phủ {w * h:.0%} ảnh", no, area_frac=round(w * h, 4))
    return issues
