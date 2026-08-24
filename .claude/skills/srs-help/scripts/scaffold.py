#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scaffold.py — Sinh file .md rong theo dung de cuong.

BA khong bao gio go tay tieu de muc: script do het tu outline.json. Nho vay
file moi luon dung cau truc, va validate.py chi con phai kiem noi dung.

    python scaffold.py --profile UI --ma FUNC-QLNSD-001 \
        --ten "Quản lý người dùng" --tinh-nang 3 -o FUNC-QLNSD-001.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import srslib as S


def md_table(spec: dict) -> list[str]:
    out = []
    if spec.get("label"):
        out.append(f"**{spec['label']}**")
        out.append("")
    heads = spec["headers"]
    out.append("| " + " | ".join(heads) + " |")
    out.append("|" + "|".join(["---"] * len(heads)) + "|")
    if spec["kind"] == "kv":
        for lab in spec["labels"]:
            out.append(f"| {lab} |  |")
    else:
        # Seed the ordinal so an empty scaffold already shows the row numbers
        # the BA will see in Word. Render recomputes them, so these can never
        # go stale in the document.
        stt = S.norm(heads[0]) == S.STT_HEADER
        for i in range(spec["rows"]):
            cells = [" "] * len(heads)
            if stt:
                cells[0] = f" {i + 1} "
            out.append("| " + " | ".join(cells) + " |")
    out.append("")
    return out


def render_section(sec: dict, outline: dict, level: int, ma: str) -> list[str]:
    out = [f"{'#' * level} {sec['name']}", ""]
    if sec.get("note"):
        out += [f"> {sec['note']}", ""]
    if sec.get("note_md"):
        out += [f"> {sec['note_md']}", ""]

    vis = sec.get("visual")
    if vis:
        req = "bắt buộc" if sec.get("visual_required") else "tuỳ chọn"
        if vis == "puml":
            out += [f"> Hình ({req}): viết PlantUML, lưu ở "
                    f"`diagrams/{ma}_seq-01.puml`.", ""]
            out += [outline["markers"]["diagram"].format(ma=ma), ""]
        elif vis == "image":
            out += [f"> Hình ({req}): gửi ảnh cho skill, hoặc đặt vào "
                    f"`assets/` rồi chèn `![chú thích](assets/tên-file.png)`.", ""]
        else:
            out += [f"> Hình ({req}): PlantUML ở `diagrams/`, hoặc ảnh trong "
                    f"`assets/`. Không có thì ghi "
                    f"“{outline['lexicon']['not_applicable']}”.", ""]

    if sec.get("auto"):
        out += [f"> Script tự đổ ({sec['auto']}) — không gõ tay phần này.", ""]

    for tid in sec.get("tables", []):
        out += md_table(outline["tables"][tid])
    if not sec.get("tables"):
        out += ["", ""]
    return out


def build(outline: dict, profile_name: str, ma: str, ten: str,
          n_feat: int, author: str) -> str:
    prof = S.profile_of(outline, profile_name)
    lex = outline["lexicon"]
    today = dt.date.today().isoformat()

    meta = {
        "ma": ma,
        "ten": ten,
        "profile": profile_name,
        "nhom": "",
        "version": "0.1",
        "status": "draft",
        "outline_id": outline["id"],
        "outline_version": outline["version"],
        "changelog": [
            {"v": "0.1", "ngay": today, "nguoi": author,
             "mo_ta": "Tạo mới tài liệu"},
        ],
    }

    L = [S.dump_front_matter(meta), ""]
    if prof.get("is_group"):
        L += [f"# Nhóm chức năng [{ma}] {ten}", ""]
        L += ["> Nhóm chức năng là tầng cây menu giữa Phân hệ và Chức năng — "
              "khớp menu người dùng thấy, không phải cách gom tuỳ ý.",
              "> Không cần tài liệu mô tả. Viết vài câu ngắn ở đây nếu thật sự "
              "cần, rồi thôi; chi tiết nằm ở từng file Chức năng.",
              "> Không có mục con, không bảng, không biểu đồ.", ""]
        L += ["«Vài câu mô tả ngắn, hoặc xoá dòng này nếu không cần.»", ""]
        return "\n".join(L).rstrip() + "\n"
    else:
        L += [f"# Chức năng [{ma}] {ten}", ""]
        L += [f"> Loại chức năng: `{profile_name}` — {prof['ten']}", ""]

    for g in outline["guidance"]:
        L.append(f"> - {g}")
    L.append("")

    for sec in prof["function_sections"]:
        L += render_section(sec, outline, 2, ma)

        # feature blocks sit between the shared head and tail sections
        if prof["has_features"] and sec["name"] == _last_head(prof):
            for n in range(1, n_feat + 1):
                fc = S.feature_code(ma, n)
                L += [f"## Tính năng [{fc}] «Tên tính năng»", ""]
                L += [f"> {lex['feature_note']}", ""]
                for fs in prof["feature_sections"]:
                    L += render_section(fs, outline, 3, ma)

    return "\n".join(L).rstrip() + "\n"


def _last_head(prof: dict) -> str:
    """Section after which the feature blocks are inserted.

    The tail sections are the shared closing ones; everything before them is
    the head. Anchoring on the tail rather than a hardcoded index keeps this
    correct when the outline gains or loses sections.
    """
    tail = {"Dữ liệu và tích hợp", "Phân loại dữ liệu",
            "Vấn đề còn mở", "Lịch sử thay đổi"}
    names = [s["name"] for s in prof["function_sections"]]
    for i in range(len(names) - 1, -1, -1):
        if names[i] not in tail:
            return names[i]
    return names[-1]


def main() -> int:
    S.utf8_stdio()
    ap = argparse.ArgumentParser(description="Sinh file đặc tả chức năng rỗng.")
    ap.add_argument("--profile", required=True,
                    help="UI / TICHHOP / JOB / PHANTICH / DANHMUC / GROUP")
    ap.add_argument("--ma", required=True, help="vd FUNC-QLNSD-001")
    ap.add_argument("--ten", required=True)
    ap.add_argument("--tinh-nang", type=int, default=1)
    ap.add_argument("--nguoi", default="«Tên BA»")
    ap.add_argument("--outline", default=None)
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()

    outline = S.load_outline(a.outline)

    if not S.code_pattern(a.profile).match(a.ma):
        print(f"LỖI: mã '{a.ma}' sai dạng {S.code_shape(a.profile)}.",
              file=sys.stderr)
        return 1

    prof = S.profile_of(outline, a.profile)
    n = a.tinh_nang if prof["has_features"] else 0
    if not prof["has_features"] and a.tinh_nang != 1:
        print(f"Ghi chú: loại {a.profile} không có tầng Tính năng — bỏ qua "
              f"--tinh-nang.", file=sys.stderr)

    text = build(outline, a.profile, a.ma, a.ten, n, a.nguoi)
    out = Path(a.out) if a.out else Path(f"{a.ma}.md")
    out.write_text(text, encoding="utf-8")

    print(f"OK -> {out}")
    if prof.get("is_group"):
        print(f"  tài liệu cấp nhóm · {len(prof['function_sections'])} mục")
    else:
        print(f"  loại {a.profile} · {len(prof['function_sections'])} mục chức "
              f"năng"
              + (f" · {n} khối tính năng" if prof["has_features"] else " · phẳng"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
