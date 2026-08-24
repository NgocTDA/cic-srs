#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
outline_check.py — Kiem chinh file outline.json.

Chay sau khi sua outline.json bang tay. De cuong hong thi moi thu phia sau hong
theo, va loi se hien ra o cho khac — vi du bang lech cot o mot profile khong lien
quan — nen bat ngay tai day re hon nhieu.

    python outline_check.py
    python outline_check.py --outline /duong/dan/outline.json --base base.docx
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import srslib as S

REQUIRED_TOP = ["schema", "id", "version", "lexicon", "layout", "styles",
                "heading_base", "markers", "msg_types", "code_rules",
                "registries", "tables", "profile_order", "profiles", "group",
                "gate", "versioning"]

REQUIRED_LEXICON = ["figure", "table", "not_applicable", "open_marker",
                    "status_pending", "missing_image"]


def check(outline: dict, base: Path | None) -> list[S.Finding]:
    out: list[S.Finding] = []

    def err(w, m):
        out.append(S.Finding("error", w, m))

    def warn(w, m):
        out.append(S.Finding("warn", w, m))

    for k in REQUIRED_TOP:
        if k not in outline:
            err("gốc", f"thiếu khoá `{k}`.")
    if out:
        return out

    for k in REQUIRED_LEXICON:
        if not outline["lexicon"].get(k):
            err("lexicon", f"thiếu `{k}` — chuỗi này xuất hiện trong tài liệu.")

    usable = outline["layout"].get("usable_twips")
    if not usable:
        err("layout", "thiếu `usable_twips`.")

    # -- tables ------------------------------------------------------------
    used: set[str] = set()
    for tid, t in outline["tables"].items():
        w = f"bảng `{tid}`"
        if t.get("kind") not in ("grid", "kv"):
            err(w, f"`kind` phải là grid hoặc kv, đang là {t.get('kind')!r}.")
            continue
        heads, widths = t.get("headers"), t.get("widths")
        if not heads or not widths:
            err(w, "thiếu `headers` hoặc `widths`.")
            continue
        if len(heads) != len(widths):
            err(w, f"{len(heads)} cột nhưng {len(widths)} độ rộng.")
        if usable and sum(widths) != usable:
            err(w, f"tổng độ rộng {sum(widths)} ≠ {usable}. Lệch "
                   f"{sum(widths) - usable} twips — bảng sẽ tràn hoặc hụt lề.")
        if any(x <= 0 for x in widths):
            err(w, "có cột độ rộng ≤ 0.")
        if t["kind"] == "kv":
            if not t.get("labels"):
                err(w, "bảng kv thiếu `labels`.")
            elif t.get("rows") is not None and t["rows"] != len(t["labels"]):
                err(w, f"`rows` ghi {t['rows']} nhưng có "
                       f"{len(t['labels'])} `labels` — hai số phải khớp.")
        if len(set(heads)) != len(heads):
            warn(w, "có tiêu đề cột trùng nhau.")

    # -- profiles ----------------------------------------------------------
    kinds = list(outline["profile_order"])
    for k in kinds:
        if k not in outline["profiles"]:
            err("profile_order", f"`{k}` không có trong `profiles`.")
    for k in outline["profiles"]:
        if k not in kinds:
            err("profiles", f"`{k}` không có trong `profile_order`.")

    def scan_sections(secs, where):
        names = []
        for s in secs:
            if not s.get("name"):
                err(where, "có mục thiếu `name`.")
                continue
            names.append(s["name"])
            for tid in s.get("tables", []):
                used.add(tid)
                if tid not in outline["tables"]:
                    err(where, f"mục “{s['name']}” trỏ bảng `{tid}` không tồn "
                               f"tại.")
            if s.get("visual") and s["visual"] not in ("puml", "image",
                                                       "puml|image"):
                err(where, f"mục “{s['name']}”: `visual` không hợp lệ "
                           f"({s['visual']!r}).")
            if s.get("visual_required") and not s.get("visual"):
                err(where, f"mục “{s['name']}”: có `visual_required` nhưng "
                           f"không có `visual`.")
            if s.get("auto") and not re.match(
                    r"^(changelog|column:.+|registry:.+)$", str(s["auto"])):
                err(where, f"mục “{s['name']}”: `auto` không hợp lệ "
                           f"({s['auto']!r}).")
        if len(set(names)) != len(names):
            dup = {n for n in names if names.count(n) > 1}
            err(where, f"tên mục trùng nhau: {', '.join(sorted(dup))}.")
        return names

    for k, prof in outline["profiles"].items():
        fn = scan_sections(prof.get("function_sections", []), f"profile {k}")
        ft = scan_sections(prof.get("feature_sections", []),
                           f"profile {k} (tính năng)")
        if not fn:
            err(f"profile {k}", "không có mục cấp chức năng nào.")
        if prof.get("has_features") and not ft:
            err(f"profile {k}", "`has_features` là true nhưng "
                                "`feature_sections` rỗng.")
        if not prof.get("has_features") and ft:
            err(f"profile {k}", "`has_features` là false nhưng vẫn có "
                                "`feature_sections`.")
        if outline["gate"]["section"] not in fn:
            warn(f"profile {k}", f"không có mục “{outline['gate']['section']}” "
                                 f"— cổng chặn sẽ không áp dụng được.")

    scan_sections(outline["group"].get("sections", []), "nhóm chức năng")

    orphan = set(outline["tables"]) - used
    for tid in sorted(orphan):
        warn("bảng", f"`{tid}` không mục nào dùng tới.")

    # -- styles ------------------------------------------------------------
    if base and base.exists():
        # `w:styleId` is an identifier, and Word only ever generates
        # alphanumerics for it. One shipped as `T-Gach*`, and every document
        # rendered from the template opened with "Errors were detected in this
        # file… Styles 1" — a repair prompt on a file that was otherwise fine.
        # The display name may hold anything; the id may not.
        try:
            import zipfile as _zip
            import re as _re
            with _zip.ZipFile(str(base)) as z:
                sx = z.read("word/styles.xml").decode("utf-8")
            for sid in set(_re.findall(r'w:styleId="([^"]+)"', sx)):
                odd = [c for c in sid if not (c.isalnum() or c == "-")]
                if odd:
                    err("style", f"`styleId` “{sid}” chứa ký tự {odd} — Word sẽ "
                                 f"báo hỏng file và tự sửa. Đổi id, giữ nguyên "
                                 f"`w:name` để đề cương không phải sửa theo.")
        except Exception as e:
            warn("style", f"không đọc được styles.xml trong {base.name}: {e}")

        try:
            from docx import Document
            have = {s.name for s in Document(str(base)).styles if s.name}
            for key, name in outline["styles"].items():
                if name not in have:
                    lvl = "warn" if key.startswith("bullet_3") else "error"
                    (warn if lvl == "warn" else err)(
                        "style", f"`{key}` trỏ style “{name}” không có trong "
                                 f"{base.name}.")
        except Exception as e:
            warn("style", f"không đọc được {base}: {e}")
    else:
        warn("style", "không kiểm được style vì không thấy base.docx.")

    # -- misc --------------------------------------------------------------
    if "{ma}" not in outline["markers"].get("diagram", ""):
        err("markers", "`diagram` phải chứa `{ma}`.")
    if "uc_diagram" in outline["markers"]:
        err("markers", "`uc_diagram` đã bỏ — nhóm chức năng không có biểu đồ "
                       "Use Case.")
    for t in outline["msg_types"]:
        if not re.fullmatch(r"[A-Z]{3,4}", t):
            err("msg_types", f"loại `{t}` phải là 3–4 chữ hoa.")

    # -- migrations --------------------------------------------------------
    # A breaking change with no migration entry leaves every existing document
    # failing with no way forward but hand-editing, which is exactly what the
    # migration script exists to prevent.
    migs = outline.get("migrations", [])
    ver = outline.get("version", "")
    # Upgrades chain: 4.1 → 5.0 → 6.0. Only the last hop has to land on the
    # current version; the earlier ones are steps on the way, and demanding
    # that each reach the head would make every bump noisy.
    steps = {}
    for i, mg in enumerate(migs, 1):
        w = f"migration {i}"
        for k in ("tu", "den", "ly_do", "lenh"):
            if not mg.get(k):
                err(w, f"thiếu khoá `{k}`.")
        if mg.get("tu") and mg.get("den"):
            if str(mg["tu"]) in steps:
                err(w, f"có hai đường nâng cấp cùng xuất phát từ "
                       f"v{mg['tu']} — không biết chọn đường nào.")
            steps[str(mg["tu"])] = str(mg["den"])
    if migs:
        if ver not in steps.values():
            warn("migrations", f"không có đường nâng cấp nào dẫn tới v{ver}.")
        # Every hop must eventually reach the head, or a document sitting on
        # an old version has nowhere to go.
        for start in list(steps):
            seen, cur = set(), start
            while cur in steps and cur not in seen:
                seen.add(cur)
                cur = steps[cur]
            if cur != ver:
                warn("migrations", f"từ v{start} đi theo chuỗi nâng cấp dừng "
                                   f"ở v{cur}, không tới được v{ver}.")
    for hb in ("merge", "standalone"):
        v = outline["heading_base"].get(hb)
        if not isinstance(v, int) or not 1 <= v <= 7:
            err("heading_base", f"`{hb}` phải là số 1–7, đang là {v!r}.")
    return out


def main() -> int:
    S.utf8_stdio()
    ap = argparse.ArgumentParser(description="Kiểm file outline.json.")
    ap.add_argument("--outline", default=None)
    ap.add_argument("--base", default=None)
    a = ap.parse_args()

    path = Path(a.outline or S.OUTLINE_PATH)
    try:
        outline = S.load_outline(path)
    except Exception as e:
        print(f"LỖI: không đọc được {path}: {e}", file=sys.stderr)
        return 1

    base = Path(a.base or S.BASE_DOCX)
    items = check(outline, base)
    n_err = sum(1 for i in items if i.level == "error")

    print(f"=== {path} ===")
    print(f"  {outline.get('id')} v{outline.get('version')} · "
          f"{len(outline.get('profiles', {}))} profile · "
          f"{len(outline.get('tables', {}))} bảng")
    for i in items:
        print("  " + str(i))
    if not items:
        print("  Sạch.")
    print(f"  → {n_err} lỗi · {len(items) - n_err} cảnh báo")
    return 1 if n_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
