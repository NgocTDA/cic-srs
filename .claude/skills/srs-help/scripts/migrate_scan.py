#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_scan.py — Kiem ke mot tai lieu cu de lap bang anh xa sang khung moi.

KHONG chuyen doi tu dong. Chuyen doi la viec suy luan, va chuyen doi tu dong se
lap day nhung muc ma tai lieu cu khong he co — dung dieu skill nay sinh ra de
chan.

Cong cu nay chi lam mot viec: liet ke tai lieu cu co GI, va khung moi doi GI,
de BA va Claude lap bang anh xa tuong minh truoc khi viet mot chu nao.

    python migrate_scan.py cu.docx --profile UI -o kiem-ke.md
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

import srslib as S

CODE_HINT = re.compile(
    r"\b(UC-?\d+|MSG\d+|BR-?\d+|[A-Z]{2,}[-_]\d{2,}|ERR_\d+|WAR_\d+)\b")


def iter_body(doc):
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    for ch in doc.element.body.iterchildren():
        if ch.tag == qn("w:p"):
            yield Paragraph(ch, doc)
        elif ch.tag == qn("w:tbl"):
            yield Table(ch, doc)


def scan(src: Path) -> dict:
    doc = Document(str(src))
    out = {"headings": [], "tables": [], "images": 0, "codes": Counter(),
           "words": 0, "paras": 0}
    cur = "(đầu tài liệu)"

    for item in iter_body(doc):
        if hasattr(item, "rows"):
            rows = [[c.text.strip() for c in r.cells] for r in item.rows]
            out["tables"].append({
                "under": cur,
                "headers": rows[0] if rows else [],
                "n_rows": max(0, len(rows) - 1),
                "n_cols": len(rows[0]) if rows else 0,
            })
            for r in rows:
                for c in r:
                    out["codes"].update(CODE_HINT.findall(c))
            continue

        m = re.fullmatch(r"Heading (\d)", item.style.name or "")
        txt = item.text.strip()
        if m and txt:
            cur = txt
            out["headings"].append((int(m.group(1)), txt))
            continue
        if txt:
            out["paras"] += 1
            out["words"] += len(txt.split())
            out["codes"].update(CODE_HINT.findall(txt))
        out["images"] += len(list(item._p.iter(qn("wp:docPr"))))
    return out


def report(src: Path, info: dict, outline: dict, profile: str) -> str:
    prof = S.profile_of(outline, profile)
    L = []
    w = L.append

    w(f"# Kiểm kê để chuyển đổi — `{src.name}`\n")
    w(f"Khung đích: loại **{profile}** — {prof['ten']}\n")
    w(f"- {len(info['headings'])} tiêu đề · {len(info['tables'])} bảng · "
      f"{info['images']} ảnh · {info['paras']} đoạn · ~{info['words']} từ\n")

    w("\n---\n\n## 1. Bảng ánh xạ — BA điền trước khi viết\n")
    w("Mỗi mục của khung mới lấy nội dung từ đâu. Không có nguồn thì ghi "
      "`KHÔNG CÓ` — mục đó sẽ thành một dòng ở *Vấn đề còn mở*, **không được "
      "suy ra**.\n")

    def block(title, secs):
        w(f"\n**{title}**\n")
        w("| Mục khung mới | Lấy từ mục nào của tài liệu cũ | Ghi chú |")
        w("|---|---|---|")
        for s in secs:
            tag = ""
            if s.get("auto"):
                tag = "*script tự đổ*"
            elif s.get("visual_required"):
                tag = "*cần hình*"
            w(f"| {s['name']} |  | {tag} |")

    block("Cấp chức năng", prof["function_sections"])
    if prof["has_features"]:
        block("Cấp tính năng — lặp cho mỗi tính năng",
              prof["feature_sections"])

    w("\n---\n\n## 2. Tài liệu cũ có gì\n")
    w("### Cấu trúc tiêu đề\n")
    for lvl, t in info["headings"]:
        w(f"{'  ' * (lvl - 1)}- `H{lvl}` {t}")

    w("\n### Bảng\n")
    if not info["tables"]:
        w("*Không có bảng nào.*")
    else:
        w("| Nằm dưới mục | Cột | Số dòng |")
        w("|---|---|---|")
        for t in info["tables"]:
            heads = " · ".join(t["headers"][:6]) or "*(không có tiêu đề)*"
            w(f"| {t['under']} | {heads} | {t['n_rows']} |")

    w("\n### Mã bắt gặp trong nội dung\n")
    if not info["codes"]:
        w("*Không thấy mã nào theo khuôn quen thuộc.*")
    else:
        w("Các mã này **không tự động hợp lệ** ở khung mới — quy ước khác. "
          "Cần cấp mã mới và giữ bảng đối chiếu để truy ngược.\n")
        for c, n in info["codes"].most_common(30):
            w(f"- `{c}` × {n}")

    w("\n---\n\n## 3. Việc phải làm sau khi điền bảng ánh xạ\n")
    w("""1. `scaffold.py` dựng khung mới đúng loại và đúng số tính năng.
2. Chuyển nội dung theo bảng ánh xạ, **từng mục một**. Chép nghĩa, không diễn
   giải làm mất chi tiết.
3. Mục ghi `KHÔNG CÓ` → đánh `⟨?⟩` và thêm một dòng ở *Vấn đề còn mở*.
4. Cấp mã `FEAT-`, `BR-`, `MH-` mới. Giữ bảng đối chiếu mã cũ ↔ mã mới.
5. Ảnh trong tài liệu cũ: lấy ra bằng `import_docx.py --raw`, đặt lại tên theo
   mã tính năng, để vào `assets/`.
6. `validate.py`. Danh sách *Vấn đề còn mở* dài là **kết quả đúng** — đó là
   backlog những thứ tài liệu cũ thiếu, không phải lỗi của việc chuyển đổi.""")

    w("\n---\n\n## 4. Cảnh báo\n")
    n_fn = len(prof["function_sections"])
    n_ft = len(prof["feature_sections"])
    w(f"Khung mới có **{n_fn} mục cấp chức năng**"
      + (f" và **{n_ft} mục cho mỗi tính năng**" if prof["has_features"] else "")
      + f", trong khi tài liệu cũ có {len(info['headings'])} tiêu đề các cấp.\n")
    w("Chênh lệch này là **bình thường và phải giữ nguyên**. Cám dỗ lớn nhất "
      "khi chuyển đổi là lấp đầy mục trống bằng suy luận hợp lý — ma trận phân "
      "quyền, tiêu chí chấp nhận, phân loại dữ liệu là những chỗ hay bị bịa "
      "nhất, vì chúng *nghe có vẻ suy ra được* từ mô tả chức năng. Không suy "
      "ra. Hỏi BA, hoặc ghi vào *Vấn đề còn mở*.")
    return "\n".join(L)


def extract_images(src: Path, outline: dict, assets: Path) -> str:
    """Pull every picture into `assets/` and return an inventory table.

    Done here, at inventory time, because that is when the BA is deciding what
    maps where — having the images already on disk and named after the section
    they came from turns "find the screenshot for this feature" from a hunt
    through Word into reading a filename.
    """
    doc = Document(str(src))
    hits = S.scan_images(doc, outline["styles"])
    saved, vector = S.save_images(doc, hits, assets)

    out = ["\n## Ảnh lấy ra\n"]
    if not hits:
        out.append("*Tài liệu không có ảnh nào.*")
        return "\n".join(out)

    out.append(f"{len(saved)} ảnh đã lưu vào `{assets.name}/`. Cột cuối để "
               f"BẠN điền — mỗi ảnh thuộc tính năng nào của khung mới.\n")
    out.append("| # | Mục cũ | Chú thích gốc | Tệp | KB | Gắn vào tính năng nào |")
    out.append("|---|---|---|---|---|---|")
    for h in saved:
        cap = (h.caption or "").replace("|", "/")[:52]
        out.append(f"| {h.seq:03d} | {h.sec_num or '—'} | {cap or '—'} | "
                   f"`{h.name}` | {h.size // 1024} | |")

    if vector:
        out.append(f"\n**{len(vector)} ảnh định dạng vector chưa lấy được** "
                   f"({', '.join(sorted({v.ext for v in vector}))}) — mở Word, "
                   f"chuột phải từng ảnh → *Save as Picture*, đặt vào "
                   f"`{assets.name}/` theo cách đặt tên ở trên.\n")

    objs = S.embedded_objects(src)
    if objs:
        from collections import Counter
        kinds = Counter(o["progid"] or "(không rõ)" for o in objs)
        out.append(f"\n## Đối tượng nhúng — KHÔNG phải ảnh\n")
        out.append(f"Tài liệu có **{len(objs)} đối tượng nhúng** "
                   f"({', '.join(f'{k}×{n}' for k, n in kinds.most_common())}). "
                   f"Trong Word chúng hiện ra như một hình, nhưng thứ được lưu "
                   f"là **tệp đính kèm** — bản vẽ Visio, bảng tính, hoặc file "
                   f"nén — còn hình chỉ là ảnh xem trước.\n")
        out.append("Không lấy tự động được. Với mỗi cái, mở tài liệu cũ trong "
                   "Word rồi chọn một trong hai cách:\n")
        out.append("- Nháy đúp để mở đối tượng, lưu ra tệp riêng, rồi dựng lại "
                   "nội dung trong khung mới (nếu là bản vẽ, cân nhắc viết lại "
                   "bằng PlantUML để về sau diff được).")
        out.append("- Chuột phải → *Save as Picture* nếu chỉ cần giữ hình.\n")
        out.append("| # | Ảnh xem trước | Loại |")
        out.append("|---|---|---|")
        for i, o in enumerate(objs, 1):
            out.append(f"| {i} | `{o['preview'] or '—'}` | "
                       f"{o['progid'] or '(không rõ)'} |")
    return "\n".join(out)


def main() -> int:
    S.utf8_stdio()
    ap = argparse.ArgumentParser(
        description="Kiểm kê tài liệu cũ để lập bảng ánh xạ.")
    ap.add_argument("src")
    ap.add_argument("--profile", required=True,
                    help="loại chức năng của khung đích")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--lay-anh", dest="lay_anh", action="store_true",
                    help="lấy luôn ảnh ra thư mục assets/ kèm bảng kiểm kê ảnh")
    ap.add_argument("--assets", default="assets",
                    help="thư mục nhận ảnh khi dùng --lay-anh")
    ap.add_argument("--outline", default=None)
    a = ap.parse_args()

    outline = S.load_outline(a.outline)
    src = Path(a.src)
    info = scan(src)
    text = report(src, info, outline, a.profile)

    n_saved = 0
    if a.lay_anh:
        assets = Path(a.assets)
        if not assets.is_absolute():
            assets = (Path(a.out).parent if a.out else src.parent) / a.assets
        block = extract_images(src, outline, assets)
        text = text.rstrip() + "\n" + block + "\n"
        n_saved = len(list(assets.glob("*"))) if assets.exists() else 0

    out = Path(a.out) if a.out else src.with_name(f"kiem-ke-{src.stem}.md")
    out.write_text(text, encoding="utf-8")
    print(f"OK -> {out}")
    print(f"  {len(info['headings'])} tiêu đề · {len(info['tables'])} bảng · "
          f"{info['images']} ảnh · {len(info['codes'])} loại mã")
    if a.lay_anh:
        print(f"  Ảnh: {n_saved} tệp -> {a.assets}/ (xem bảng “Ảnh lấy ra”)")
    else:
        print("  Thêm --lay-anh để lấy ảnh ra kèm bảng kiểm kê ảnh.")
    print("  Điền bảng ánh xạ ở mục 1 trước khi bắt đầu viết.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
