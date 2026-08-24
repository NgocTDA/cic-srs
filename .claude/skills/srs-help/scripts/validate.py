#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate.py — Kiem tra file .md truoc khi render.

Chia lam ba nhom:
  LOI     — sai chuan, phai sua
  CANH    — dang ngo, van render duoc
  CONG    — dieu kien phat hanh (⟨?⟩, van de con mo, thieu hinh)

Ma thoat: 0 sach · 1 co loi · 2 chi vuong cong chan (van render ban nhap duoc).

    python validate.py FUNC-QLNSD-001.md
    python validate.py FUNC-QLNSD-001.md --registry-dir ../registries
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import srslib as S


class Report:
    def __init__(self) -> None:
        self.items: list[S.Finding] = []

    def err(self, where, msg):
        self.items.append(S.Finding("error", where, msg))

    def warn(self, where, msg):
        self.items.append(S.Finding("warn", where, msg))

    def gate(self, where, msg):
        self.items.append(S.Finding("info", where, msg))

    @property
    def n_err(self):
        return sum(1 for i in self.items if i.level == "error")

    @property
    def n_gate(self):
        return sum(1 for i in self.items if i.level == "info")


# ---------------------------------------------------------------------------
def check_front_matter(doc: S.FunctionDoc, outline: dict, r: Report) -> None:
    m = doc.meta
    for k in ("ma", "ten", "profile", "version", "status"):
        if not m.get(k):
            r.err("front matter", f"thiếu khoá bắt buộc `{k}`.")

    ma = m.get("ma", "")
    kind = m.get("profile", "")
    if ma and kind and S.known_kind(outline, kind):
        if not S.code_pattern(kind).match(ma):
            r.err("front matter",
                  f"mã `{ma}` sai dạng {S.code_shape(kind)}.")

    if m.get("profile") and not S.known_kind(outline, m["profile"]):
        r.err("front matter",
              f"loại `{m['profile']}` không có trong đề cương. Hợp lệ: "
              f"{', '.join(S.all_kinds(outline))}.")

    if m.get("outline_id") and m["outline_id"] != outline["id"]:
        r.err("front matter",
              f"đề cương lệch: file khai `{m['outline_id']}`, "
              f"skill đang dùng `{outline['id']}`.")
    if m.get("outline_version") and str(m["outline_version"]) != outline["version"]:
        have, want = str(m["outline_version"]), outline["version"]
        # A major bump means sections or required rows changed, so the file is
        # structurally wrong until migrated — and it will *also* trip a pile of
        # confusing "thiếu dòng"/"thiếu mục" errors that read as if the BA had
        # deleted things. Say the real cause once, up front, with the command.
        if have.split(".")[0] != want.split(".")[0]:
            # Follow the chain, don't look for one direct hop. Upgrades
            # accumulate (4.1 → 5.0 → 6.0 → 6.1) and there is deliberately no
            # 4.1 → head entry, so a direct lookup silently degrades to "go
            # read outline.json" for exactly the documents furthest behind —
            # the ones whose author most needs the command spelled out.
            steps = {str(x["tu"]): x for x in outline.get("migrations", [])
                     if x.get("tu") and x.get("den")}
            hops, cur, seen = [], have, set()
            while cur in steps and cur not in seen:
                seen.add(cur)
                hops.append(steps[cur])
                cur = str(steps[cur]["den"])
            msg = (f"file soạn theo đề cương v{have}, skill đang dùng v{want} — "
                   f"lệch phiên bản LỚN, cấu trúc đã khác nên không render được.")
            if hops and cur == want:
                if len(hops) > 1:
                    chain = " → ".join([f"v{have}"]
                                       + [f"v{h['den']}" for h in hops])
                    msg += f" Đi qua {len(hops)} chặng: {chain}."
                msg += f" {hops[0]['ly_do']}"
                msg += (f" Chạy: `{hops[0]['lenh']}` rồi điền nội dung còn "
                        f"để ⟨?⟩.")
            else:
                msg += " Xem mục “migrations” trong outline.json."
            r.err("front matter", msg)
        else:
            r.warn("front matter",
                   f"file soạn theo đề cương v{have}, "
                   f"skill đang dùng v{want}.")

    cl = m.get("changelog") or []
    if not cl:
        r.err("front matter", "thiếu `changelog` — ít nhất một dòng.")
    else:
        if not isinstance(cl[-1], dict):
            r.err("front matter", "dòng changelog cuối sai định dạng.")
        else:
            last = cl[-1]
            if str(last.get("v")) != str(m.get("version")):
                r.err("front matter",
                      f"`version: {m.get('version')}` không khớp dòng changelog "
                      f"cuối (`{last.get('v')}`).")
            for i, row in enumerate(cl, 1):
                if not isinstance(row, dict):
                    continue
                for k in ("v", "ngay", "nguoi", "mo_ta"):
                    if not row.get(k):
                        r.err("changelog", f"dòng {i} thiếu `{k}`.")
                d = str(row.get("ngay", ""))
                if d and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
                    r.err("changelog", f"dòng {i}: ngày `{d}` phải dạng YYYY-MM-DD.")

    if m.get("status") == "approved":
        pass  # gate checks below decide


def check_structure(doc: S.FunctionDoc, prof: dict, r: Report) -> None:
    if prof.get("is_group"):
        # A group is a menu tier, not a document: a heading plus an optional
        # short description. There is no section list to conform to.
        if doc.features:
            r.err("cấu trúc", "nhóm chức năng không có tầng Tính năng.")
        extra = [s.name for s in doc.sections if s.name != S.GROUP_DESC]
        for n in extra:
            r.err("cấu trúc", f"mục “{n}” — nhóm chức năng chỉ gồm đề mục và "
                              f"vài câu mô tả, không có mục con.")
        # Mirrors tools/validate_group.py so a file cannot pass one side and
        # fail the other.
        for sec in doc.sections:
            for b in sec.blocks:
                if b.kind == "table":
                    r.err("cấu trúc", "file nhóm không được có bảng.")
                    break
        if "«" in _full_text(doc):
            r.warn("cấu trúc", "còn placeholder «…» chưa điền.")
        return

    want = [s["name"] for s in prof["function_sections"]]
    got = [s.name for s in doc.sections]

    missing = [n for n in want if n not in got]
    extra = [n for n in got if n not in want]
    for n in missing:
        r.err("cấu trúc", f"thiếu mục cấp chức năng “{n}”.")
    for n in extra:
        r.err("cấu trúc", f"mục “{n}” không có trong đề cương loại "
                          f"{doc.profile}.")

    common = [n for n in got if n in want]
    if common != [n for n in want if n in got]:
        r.err("cấu trúc", "thứ tự mục cấp chức năng không đúng đề cương.")

    if not prof["has_features"]:
        if doc.features:
            r.err("cấu trúc",
                  f"loại {doc.profile} không có tầng Tính năng, nhưng file có "
                  f"{len(doc.features)} khối.")
        return

    if not doc.features:
        r.err("cấu trúc", "chưa có khối Tính năng nào. Chức năng chỉ có một "
                          "tính năng vẫn phải giữ tầng này.")

    fwant = [s["name"] for s in prof["feature_sections"]]
    for i, f in enumerate(doc.features, 1):
        exp = S.feature_code(doc.ma, i) if doc.ma else None
        if not S.CODE_PATTERNS["FEAT"].match(f.ma):
            r.err(f"tính năng {i}", f"mã `{f.ma}` sai dạng.")
        elif exp and f.ma != exp:
            r.err(f"tính năng {i}",
                  f"mã `{f.ma}` không liên tiếp — phải là `{exp}`.")
        if not f.ten or "«" in f.ten:
            r.warn(f"tính năng {f.ma}", "tên còn là placeholder.")

        fgot = [s.name for s in f.sections]
        for n in fwant:
            if n not in fgot:
                r.err(f"tính năng {f.ma}", f"thiếu mục “{n}”.")
        for n in fgot:
            if n not in fwant:
                r.err(f"tính năng {f.ma}", f"mục “{n}” không có trong đề cương.")
        if [n for n in fgot if n in fwant] != [n for n in fwant if n in fgot]:
            r.err(f"tính năng {f.ma}", "thứ tự mục không đúng đề cương.")


def check_tables(sec: S.Section, spec: dict, outline: dict, where: str,
                 r: Report) -> None:
    want_ids = spec.get("tables", [])
    if not want_ids:
        return
    got = [b for b in sec.blocks if b.kind == "table"]
    if len(got) < len(want_ids):
        r.err(where, f"mục “{sec.name}” thiếu bảng "
                     f"({len(got)}/{len(want_ids)}).")
        return
    for tid, blk in zip(want_ids, got):
        t = outline["tables"][tid]
        if not blk.rows:
            continue
        head = [S.norm(c) for c in blk.rows[0]]

        # A data row with fewer cells than the header means every value after
        # the gap sits in the wrong column. Nothing downstream notices, so the
        # spec reads as if those values were deliberate.
        for n, row in enumerate(blk.rows[1:], 1):
            if len(row) != len(head) and " ".join(row).strip():
                r.err(where, f"mục “{sec.name}”, bảng `{tid}` dòng {n}: "
                             f"{len(row)} ô nhưng bảng có {len(head)} cột — "
                             f"giá trị sẽ lệch cột.")

        want = [S.norm(c) for c in t["headers"]]

        # Columns written as «...» are placeholders the BA replaces with real
        # codes, and their number varies per function — the permission matrix
        # ships with three role columns but a function may need two or five.
        # Match the fixed columns around them and let the middle float.
        wild = [i for i, c in enumerate(want) if c.startswith("«")]
        if wild:
            pre, post = want[:wild[0]], want[wild[-1] + 1:]
            n_var = len(head) - len(pre) - len(post)
            if n_var < 1:
                r.err(where, f"mục “{sec.name}”, bảng `{tid}`: cần ít nhất một "
                             f"cột thay cho {want[wild[0]]}.")
            elif head[:len(pre)] != pre or (post and head[-len(post):] != post):
                r.err(where, f"mục “{sec.name}”, bảng `{tid}`: sai tiêu đề cột "
                             f"cố định.")
            else:
                for c in head[len(pre):len(pre) + n_var]:
                    if c.startswith("«"):
                        r.err(where, f"mục “{sec.name}”, bảng `{tid}`: cột "
                                     f"“{c}” còn là placeholder.")
                    elif not S.CODE_PATTERNS["ROLE"].match(c):
                        # The wildcards in this outline are role columns
                        # only (`«ROLE_1»`…), so any resolved value here is
                        # supposed to be a real ROLE- code (style-guide.md
                        # A9 / roles.csv), not a free-text label like
                        # "Quản trị viên".
                        r.err(where, f"mục “{sec.name}”, bảng `{tid}`: cột "
                                     f"“{c}” không phải mã vai trò — phải "
                                     f"dạng `ROLE-«mã»` (vd. `ROLE-QTHT`), "
                                     f"khớp `roles.csv`.")
            continue

        if len(head) != len(want):
            r.err(where, f"mục “{sec.name}”, bảng `{tid}`: {len(head)} cột, "
                         f"đề cương yêu cầu {len(want)}.")
        elif head != want:
            diff = [f"“{a}” ≠ “{b}”" for a, b in zip(head, want) if a != b]
            r.err(where, f"mục “{sec.name}”, bảng `{tid}`: sai tiêu đề cột — "
                         + "; ".join(diff))

        if t.get("kind") == "kv":
            # Headers only say the table is a "Hạng mục | Nội dung" table;
            # nothing above checks that the actual rows are the ones the
            # outline requires. A row silently dropped, renamed, or
            # reordered read as a complete document and nothing noticed.
            want_labels = t.get("labels", [])
            got_labels = [row[0].strip() for row in blk.rows[1:] if row]
            missing = [l for l in want_labels if l not in got_labels]
            extra = [l for l in got_labels if l not in want_labels]
            dup = sorted({l for l in got_labels
                         if l and got_labels.count(l) > 1})
            for l in missing:
                r.err(where, f"mục “{sec.name}”, bảng `{tid}`: thiếu dòng "
                             f"“{l}”.")
            for l in extra:
                r.err(where, f"mục “{sec.name}”, bảng `{tid}`: dòng “{l}” "
                             f"không có trong đề cương.")
            for l in dup:
                r.err(where, f"mục “{sec.name}”, bảng `{tid}`: dòng “{l}” "
                             f"lặp lại.")
            if (not missing and not extra and not dup
                    and got_labels != want_labels):
                r.err(where, f"mục “{sec.name}”, bảng `{tid}`: thứ tự dòng "
                             f"sai — phải đúng thứ tự trong đề cương.")


def check_multiline_cells(doc: S.FunctionDoc, outline: dict, r: Report) -> None:
    """Where a cell packs several points, and whether that is allowed there.

    Sequential columns (Xử lý, Phản hồi của hệ thống…) may hold several
    points — that is the nature of a procedure, and render turns the `·`
    marks into real bullets.

    Constraint columns may not. The standard already says each rule gets its
    own `BR-` code, so a crowded cell there is a finding, not a formatting
    choice — and rendering it prettily would remove the reason to split it.
    Reported as a warning, not an error: a converted legacy spec would
    otherwise be unusable until every such cell had been rewritten, and that
    rewrite is analyst work, not a blocker.
    """
    spec = S.multiline_spec(outline)
    allow = set(spec.get("cho_phep", []))
    warn_cols = set(spec.get("canh_bao", []))
    max_lv = int(spec.get("max_cap", 3))
    if not allow and not warn_cols:
        return

    # Aggregated on purpose. A converted legacy spec has dozens of these, and
    # one warning per cell buries every other finding — the analyst needs to
    # know which columns are crowded and how badly, not to scroll past 55
    # near-identical lines.
    crowded: dict[str, list[int]] = {}
    stray: dict[str, int] = {}

    def scan(sections, where):
        for sec in sections:
            for b in sec.blocks:
                if b.kind != "table" or not b.rows:
                    continue
                head = [S.norm(c) for c in b.rows[0]]
                for n, row in enumerate(b.rows[1:], 1):
                    for j, val in enumerate(row):
                        if j >= len(head) or not S.cell_is_multiline(val):
                            continue
                        col = head[j]
                        segs = S.cell_segments(val)
                        deep = max(lv for _, lv in segs)
                        if deep > max_lv:
                            r.err(where, f"mục “{sec.name}” dòng {n}, cột "
                                         f"“{col}”: gạch đầu dòng {deep} cấp — "
                                         f"tối đa {max_lv}. Sâu hơn thì nên "
                                         f"tách mục, không thụt tiếp.")
                        n_pts = sum(1 for _, lv in segs if lv)
                        # One point is a sentence with a dash, not a packed
                        # cell; flagging it would be noise.
                        if col in warn_cols and n_pts >= 2:
                            crowded.setdefault(col, []).append(n_pts)
                        elif col not in warn_cols and col not in allow:
                            stray[col] = stray.get(col, 0) + 1

    scan(doc.sections, "chức năng")
    for f in doc.features:
        scan(f.sections, f"tính năng {f.ma}")

    for col, counts in sorted(crowded.items()):
        r.warn("gộp ý trong ô",
               f"cột “{col}”: {len(counts)} ô gộp nhiều ý (nhiều nhất "
               f"{max(counts)} ý). Cột này render một dòng liền — theo chuẩn, "
               f"mỗi ràng buộc nên tách thành một mã BR- riêng.")
    for col, n in sorted(stray.items()):
        r.warn("gộp ý trong ô",
               f"cột “{col}”: {n} ô có dấu `·` nhưng cột này không khai trong "
               f"`multiline_columns` — dấu sẽ hiện ra như ký tự thường.")


def check_obsolete(doc: S.FunctionDoc, r: Report) -> None:
    """Markers from an earlier version of the standard."""
    def scan(sections, where):
        for sec in sections:
            for b in sec.blocks:
                if b.kind == "obsolete" and b.text == "ucdiagram":
                    r.err(where, f"còn dấu `[[UCDIAGRAM: {b.code}]]` — biểu đồ "
                                 f"Use Case cho nhóm đã bỏ. Xoá dòng này; nhóm "
                                 f"chỉ gồm đề mục và vài câu mô tả.")
    scan(doc.sections, "chức năng")
    for f in doc.features:
        scan(f.sections, f"tính năng {f.ma}")


def check_content(doc: S.FunctionDoc, prof: dict, outline: dict,
                  r: Report) -> None:
    na = outline["lexicon"]["not_applicable"]
    idx = S.section_index(prof)

    def one(sec: S.Section, where: str) -> None:
        spec = idx.get(sec.name)
        if spec is None:
            return
        body = sec.text_content()
        is_na = S.norm(body).lower().startswith(na.lower())

        if spec.get("auto"):
            return
        if sec.is_empty():
            # An empty open-issues table is the *desired* end state, not an
            # omission: it means nothing is left for the BA to settle.
            if sec.name == outline["gate"]["section"] and any(
                    b.kind == "table" for b in sec.blocks):
                return
            r.err(where, f"mục “{sec.name}” để trống. Không áp dụng thì ghi "
                         f"“{na}”.")
            return

        check_tables(sec, spec, outline, where, r)

        vis = spec.get("visual")
        if vis and not is_na:
            has_img = any(b.kind == "image" for b in sec.blocks)
            has_dia = any(b.kind == "diagram" for b in sec.blocks)
            if not (has_img or has_dia):
                lvl = r.gate if spec.get("visual_required") else r.warn
                lvl(where, f"mục “{sec.name}” chưa có hình "
                           f"({'bắt buộc' if spec.get('visual_required') else 'tuỳ chọn'}). "
                           f"Gửi ảnh cho skill, hoặc chèn trực tiếp vào .docx rồi "
                           f"chạy import.")

    for sec in doc.sections:
        one(sec, "chức năng")
    for f in doc.features:
        for sec in f.sections:
            one(sec, f"tính năng {f.ma}")


def check_cross(doc: S.FunctionDoc, prof: dict, outline: dict,
                r: Report) -> None:
    for c in outline["cross_checks"]:
        if doc.profile not in c["ap_dung"]:
            continue

        if c["ten"] == "Tính năng có dòng phân quyền":
            pq = doc.section("Ma trận phân quyền")
            if pq is None:
                continue
            # Column-scoped on purpose: searching the whole row lets a code
            # sitting in "Tính năng / Thao tác" (or anywhere else) count as a
            # match even when "Mã tính năng" itself is blank.
            col = _table_col(outline, prof, "Ma trận phân quyền", "Mã tính năng")
            cells = _column_cells(pq, col)
            for f in doc.features:
                if not any(f.ma in cell for cell in cells):
                    r.err("kiểm tra chéo",
                          f"tính năng `{f.ma}` chưa có dòng trong Ma trận "
                          f"phân quyền — không thấy ở cột “Mã tính năng” "
                          f"(mã nằm ở cột khác không tính).")

        if c["ten"] == "Chỉ tiêu có công thức":
            dm = doc.section("Danh mục chỉ tiêu")
            ct = doc.section("Công thức và truy vấn")
            if dm is None or ct is None:
                continue
            codes = {row[0].strip() for b in dm.blocks if b.kind == "table"
                     for row in b.rows[1:] if row and row[0].strip()}
            body = " ".join(" ".join(row) for b in ct.blocks
                            if b.kind == "table" for row in b.rows)
            for code in sorted(codes):
                if code not in body:
                    r.err("kiểm tra chéo",
                          f"mã chỉ tiêu `{code}` có ở Danh mục chỉ tiêu nhưng "
                          f"không có dòng ở Công thức và truy vấn.")


PARAM_RE = re.compile(r"\{([^{}]*)\}")
ASSIGN_RE = re.compile(r"([A-Za-z0-9_]+)\s*=\s*([^\s·,;]+)")


def _msg_tables(doc: S.FunctionDoc, outline: dict):
    """Yield (where, table block) for every Thông báo / Mã lỗi table."""
    want = {S.norm(t["headers"][0]) + "|" + S.norm(t["headers"][3])
            for t in outline["tables"].values()
            if t["kind"] == "grid" and "Tham số" in t["headers"]}

    def scan(sections, where):
        for sec in sections:
            for b in sec.blocks:
                if b.kind != "table" or not b.rows:
                    continue
                sig = S.norm(b.rows[0][0]) + "|" + (
                    S.norm(b.rows[0][3]) if len(b.rows[0]) > 3 else "")
                if sig in want:
                    yield where, sec, b

    yield from scan(doc.sections, "chức năng")
    for f in doc.features:
        yield from scan(f.sections, f"tính năng {f.ma}")


def check_messages(doc: S.FunctionDoc, outline: dict, regdir, r: Report) -> None:
    cfg = outline["message_params"]
    name_ok = re.compile(cfg["name_pattern"])
    declared: dict[str, set] = {}
    seen_rows: set = set()

    display: dict[str, str] | None = None
    # Deliberately asymmetric: a business object is a common noun, a state is a
    # name the system defines. Substituting them into one template sentence
    # only reads right if each keeps its own capitalisation.
    case_of: dict[str, str] = {}
    if regdir:
        display = {}
        for fname, col in cfg["resolved_from"].items():
            p = regdir / fname
            if not p.exists():
                continue
            key = outline["registries"][fname]["key"]
            with p.open(encoding="utf-8-sig", newline="") as fh:
                for row in csv.DictReader(fh):
                    if row.get(key):
                        # Keep codes whose display name is blank: that is a
                        # different problem from a code that does not exist,
                        # and the two need different fixes.
                        display[row[key].strip()] = (row.get(col) or "").strip()
                        case_of[row[key].strip()] = (
                            "lower" if fname == "objects.csv" else "upper")

    for where, sec, b in _msg_tables(doc, outline):
        head = [S.norm(c) for c in b.rows[0]]
        try:
            i_ma, i_nd, i_ts = head.index(head[1]), head.index("Nội dung"), \
                head.index("Tham số")
        except ValueError:
            r.err(where, f"bảng “{sec.name}” thiếu cột «Nội dung» hoặc «Tham số».")
            continue
        i_ma = 1

        for n, row in enumerate(b.rows[1:], 1):
            if len(row) <= i_ts or not " ".join(row).strip():
                continue
            code = row[i_ma].strip()
            body = row[i_nd].strip()
            params = row[i_ts].strip()
            at = f"{where} / {sec.name} dòng {n}"

            if not code:
                continue
            if not S.CODE_PATTERNS["MSG"].match(code):
                r.err(at, f"mã `{code}` sai dạng «LOẠI»_«3 số».")

            # 5 — unbalanced braces
            if body.count("{") != body.count("}"):
                r.err(at, f"mã `{code}`: ngoặc `{{` `}}` không cân trong nội dung.")

            found = [m.strip() for m in PARAM_RE.findall(body)]

            # 4 — parameter name syntax
            for p_ in found:
                if not name_ok.match(p_):
                    r.err(at, f"mã `{code}`: tham số `{{{p_}}}` sai cú pháp — "
                              f"phải là {cfg['syntax']} (không dấu, không "
                              f"khoảng trắng).")

            given = dict(ASSIGN_RE.findall(params))

            # 3 — no params in template
            if not found:
                if params:
                    r.err(at, f"mã `{code}`: nội dung không có tham số nhưng "
                              f"cột «Tham số» lại ghi “{params}”. Để trống.")
            else:
                if not params:
                    r.err(at, f"mã `{code}`: nội dung có "
                              f"{', '.join('{'+p_+'}' for p_ in found)} nhưng "
                              f"cột «Tham số» để trống.")
                # 1 — every placeholder declared
                for p_ in found:
                    if name_ok.match(p_) and p_ not in given:
                        r.err(at, f"mã `{code}`: chưa khai giá trị cho "
                                  f"`{{{p_}}}`.")
                # 2 — nothing extra declared
                for p_ in given:
                    if p_ not in found:
                        r.err(at, f"mã `{code}`: khai thừa tham số `{p_}` — "
                                  f"nguyên mẫu không có.")
                # 6 — values must resolve
                if display is not None:
                    for v in given.values():
                        want = case_of.get(v)
                        got = display.get(v, "")
                        if want and got:
                            first = got.lstrip()[:1]
                            if want == "lower" and first.isupper():
                                r.warn(at, f"tên hiển thị của `{v}` là "
                                           f"“{got}” — đối tượng nghiệp vụ "
                                           f"viết thường (“người dùng”), "
                                           f"không hoa chữ đầu.")
                            elif want == "upper" and first.islower():
                                r.warn(at, f"tên hiển thị của `{v}` là "
                                           f"“{got}” — trạng thái viết hoa "
                                           f"chữ đầu (“Chờ phê duyệt”).")
                    for p_, v in given.items():
                        if v in display and not display[v]:
                            r.err(at, f"mã `{code}`: giá trị `{v}` có trong sổ "
                                      f"nhưng chưa điền tên hiển thị — thế vào "
                                      f"câu sẽ ra mã trần.")
                        elif v not in display:
                            r.err(at, f"mã `{code}`: giá trị `{v}` của "
                                      f"`{{{p_}}}` không có trong "
                                      f"objects.csv / states.csv.")

            # 10 — duplicate row
            sig = (code, tuple(sorted(given.items())))
            if sig in seen_rows:
                r.warn(at, f"mã `{code}` đã khai một dòng y hệt ở trên.")
            seen_rows.add(sig)
            declared.setdefault(code, set()).add(tuple(sorted(given.items())))

    _check_msg_refs(doc, declared, r)


def _check_msg_refs(doc: S.FunctionDoc, declared: dict, r: Report) -> None:
    """8 and 9 — referenced-but-undeclared, and declared-but-unused."""
    referenced: set = set()

    def scan(sections, where):
        for sec in sections:
            if "thông báo" in sec.name.lower() or "mã lỗi" in sec.name.lower():
                continue
            for code in S.find_codes(sec.text_content(), "MSG"):
                referenced.add((code, where))

    scan(doc.sections, "chức năng")
    for f in doc.features:
        scan(f.sections, f"tính năng {f.ma}")

    for code, where in sorted(referenced):
        if code not in declared:
            r.err(where, f"mã `{code}` được tham chiếu nhưng không có dòng ở "
                         f"bảng Thông báo của file này.")

    used = {c for c, _ in referenced}
    for code in sorted(declared):
        if code not in used:
            r.warn("thông báo", f"mã `{code}` khai ở bảng Thông báo nhưng không "
                                f"nơi nào trong file tham chiếu tới.")


def _declared_codes(doc: S.FunctionDoc, sec_name: str, col: int) -> set[str]:
    sec = doc.section(sec_name)
    if sec is None:
        return set()
    out = set()
    for b in sec.blocks:
        if b.kind != "table":
            continue
        for row in b.rows[1:]:
            if len(row) > col and row[col].strip():
                out.add(row[col].strip())
    return out


def check_internal_refs(doc: S.FunctionDoc, prof: dict, outline: dict,
                        r: Report) -> None:
    """Codes minted inside this file must be declared here and used here.

    A reference to `MH-…-004` that no screen list declares means the screen was
    renamed or dropped and the mention was left behind; a screen declared but
    never referenced means the opposite. Both read as complete documents, and
    neither is caught by any other check — the registries only cover codes that
    are shared system-wide.
    """
    KIND = {
        "FEAT": ("tính năng", None, None),
        "BR": ("quy tắc nghiệp vụ", "Quy tắc nghiệp vụ", 0),
        "MH": ("màn hình", "Danh sách màn hình", 1),
    }

    declared = {
        "FEAT": {f.ma for f in doc.features},
        "BR": _declared_codes(doc, "Quy tắc nghiệp vụ", 0),
        "MH": _declared_codes(doc, "Danh sách màn hình", 1),
    }

    # Where each code is referenced, excluding the section that declares it.
    used: dict[str, set[str]] = {k: set() for k in KIND}
    for kind, (_, decl_sec, _) in KIND.items():
        for sec in doc.sections:
            if decl_sec and S.norm(sec.name) == S.norm(decl_sec):
                continue
            for c in S.find_codes(sec.text_content(), kind):
                used[kind].add(c)
        for f in doc.features:
            used[kind].update(S.find_codes(f.ma, kind))
            for sec in f.sections:
                for c in S.find_codes(sec.text_content(), kind):
                    used[kind].add(c)

    ma = doc.ma
    prefix = "-".join(ma.split("-")[1:]) if ma else ""

    for kind, (label, decl_sec, _) in KIND.items():
        for code in sorted(used[kind] - declared[kind]):
            # A code carrying another function's number is a different fault:
            # copied from elsewhere rather than left dangling.
            if prefix and prefix not in code:
                r.err("truy vết nội bộ",
                      f"mã {label} `{code}` thuộc chức năng khác. Mã {kind}- "
                      f"phải mang số của chính chức năng này (`{ma}`).")
            else:
                if kind == "FEAT" and not prof["has_features"]:
                    r.err("truy vết nội bộ",
                          f"mã tính năng `{code}` xuất hiện nhưng loại "
                          f"{doc.profile} là cấu trúc PHẲNG — không có tầng "
                          f"Tính năng. Tàn dư từ bản chuẩn cũ; xoá đi.")
                    continue
                where = f"“{decl_sec}”" if decl_sec else "khối Tính năng"
                r.err("truy vết nội bộ",
                      f"mã {label} `{code}` được nhắc tới nhưng không khai ở "
                      f"{where}. Hoặc đã bị xoá mà còn sót chỗ nhắc, hoặc gõ "
                      f"sai số.")

        for code in sorted(declared[kind] - used[kind]):
            r.warn("truy vết nội bộ",
                   f"mã {label} `{code}` khai rồi nhưng không nơi nào trong "
                   f"file nhắc tới — kiểm xem có phải tàn dư sau khi bỏ nội "
                   f"dung liên quan không.")

    # Screens only exist where the outline gives a screen list.
    if not doc.section("Danh sách màn hình") and used["MH"]:
        r.err("truy vết nội bộ",
              f"loại {doc.profile} không có mục “Danh sách màn hình” nhưng file "
              f"vẫn nhắc mã màn hình: {', '.join(sorted(used['MH'])[:3])}.")


def check_diagram_files(doc: S.FunctionDoc, root: Path, r: Report) -> None:
    """A diagram marker pointing at a file that is not there."""
    def scan(sections, where):
        for sec in sections:
            for b in sec.blocks:
                if b.kind != "diagram":
                    continue
                if not (root / "diagrams" / f"{b.code}.puml").exists():
                    r.warn(where, f"dấu `[[DIAGRAM: {b.code}]]` trỏ tới "
                                  f"`diagrams/{b.code}.puml` không có. Sơ đồ sẽ "
                                  f"thành khung trống trong bản Word.")
    scan(doc.sections, "chức năng")
    for f in doc.features:
        scan(f.sections, f"tính năng {f.ma}")


def check_cross_tables(doc: S.FunctionDoc, prof: dict, outline: dict,
                       r: Report) -> None:
    """Pairs of tables that must agree with each other.

    Same failure shape as the internal-code checks: each table is correct on
    its own, the document reads fine, and nothing notices that the two no
    longer describe the same thing.
    """
    # -- 1. every feature must be traced to a use case ----------------------
    if prof["has_features"] and doc.features:
        tv = doc.section("Truy vết yêu cầu")
        if tv is not None:
            # Column-scoped: a code parked in "Ghi chú" instead of "Tính
            # năng đáp ứng" used to count as traced. It should not.
            col = _table_col(outline, prof, "Truy vết yêu cầu",
                             "Tính năng đáp ứng")
            cells = _column_cells(tv, col)
            for f in doc.features:
                if not any(f.ma in cell for cell in cells):
                    r.err("truy vết chéo",
                          f"tính năng `{f.ma}` không có ở cột “Tính năng đáp "
                          f"ứng” của bảng “Truy vết yêu cầu” — mã ở cột khác "
                          f"(vd. “Ghi chú”) không tính là truy vết được.")

    # -- 2. an indicator formula with no catalogue entry --------------------
    dm, ct = doc.section("Danh mục chỉ tiêu"), doc.section("Công thức và truy vấn")
    if dm is not None and ct is not None:
        cat = {row[0].strip() for b in dm.blocks if b.kind == "table"
               for row in b.rows[1:] if row and row[0].strip()}
        for b in ct.blocks:
            if b.kind != "table":
                continue
            for row in b.rows[1:]:
                code = row[0].strip() if row else ""
                if code and code not in cat:
                    r.err("truy vết chéo",
                          f"mã chỉ tiêu `{code}` có công thức nhưng không khai "
                          f"ở “Danh mục chỉ tiêu”.")

    # -- 3. roles used in prose but not columns of the permission matrix ----
    pq = doc.section("Ma trận phân quyền")
    if pq is not None:
        cols = set()
        for b in pq.blocks:
            if b.kind == "table" and b.rows:
                cols |= {c.strip() for c in b.rows[0] if c.strip().startswith("ROLE-")}
        if cols:
            elsewhere: set[str] = set()
            for sec in doc.sections:
                if S.norm(sec.name) == S.norm("Ma trận phân quyền"):
                    continue
                elsewhere |= set(re.findall(r"ROLE-[A-Z0-9]+", sec.text_content()))
            for f in doc.features:
                for sec in f.sections:
                    elsewhere |= set(re.findall(r"ROLE-[A-Z0-9]+",
                                                sec.text_content()))
            for role in sorted(elsewhere - cols):
                r.warn("truy vết chéo",
                       f"vai trò `{role}` được nhắc trong nội dung nhưng không "
                       f"phải một cột của “Ma trận phân quyền” — kiểm xem có "
                       f"thiếu cột không.")

    # -- 4. a flow branching back to a step that does not exist -------------
    def check_steps(sections, where):
        for sec in sections:
            tables = [b for b in sec.blocks if b.kind == "table" and b.rows]
            steps: set[str] = set()
            for b in tables:
                if S.norm(b.rows[0][0]) == "Bước":
                    steps |= {row[0].strip() for row in b.rows[1:]
                              if row and row[0].strip()}
            if not steps:
                continue
            for b in tables:
                head = [S.norm(c) for c in b.rows[0]]
                if "Quay về bước" not in head:
                    continue
                i = head.index("Quay về bước")
                for row in b.rows[1:]:
                    v = row[i].strip() if len(row) > i else ""
                    if v and v not in steps and v not in ("—", "-"):
                        r.err(where, f"mục “{sec.name}”: luồng thay thế quay về "
                                     f"bước `{v}` không có trong luồng chính "
                                     f"(có {', '.join(sorted(steps))}).")

    check_steps(doc.sections, "chức năng")
    for f in doc.features:
        check_steps(f.sections, f"tính năng {f.ma}")


MALFORMED_KINDS = ["FUNC", "FEAT", "BR", "MH", "GRP", "UC", "MSG", "ST", "ROLE"]


def check_malformed_codes(doc: S.FunctionDoc, r: Report) -> None:
    """A token with the right prefix but the wrong shape — `UC-301` (needs 4
    digits), `BR-QLNSD-001-06` (needs 3 digits in the last group), `ERR_QLNSD_002`
    (message codes carry no subsystem segment) — never reaches any other check,
    because every one of them extracts references through `find_codes`, which
    only recognises well-formed codes. A typo like this reads as if the
    reference were simply absent instead of tripping an error.
    """
    text = _full_text(doc)
    for kind in MALFORMED_KINDS:
        for tok in S.find_malformed_codes(text, kind):
            fix = S.suggest_code_fix(tok, kind)
            if fix:
                # Naming the corrected code turns a hundred occurrences into
                # one find-and-replace per code. Legacy specs are written with
                # a single wrong separator throughout, not one typo at a time.
                r.err("mã sai dạng",
                      f"`{tok}` sai dấu nối — sửa thành `{fix}`.")
            else:
                r.err("mã sai dạng",
                      f"`{tok}` trông giống mã {kind} nhưng sai dạng chuẩn — "
                      f"đúng phải là {S.CODE_SHAPES[kind]}.")


def check_registries(doc: S.FunctionDoc, outline: dict, regdir: Path | None,
                     r: Report) -> None:
    if regdir is None:
        r.warn("sổ đăng ký",
               "không chỉ định --registry-dir; bỏ qua phép đối chiếu mã.")
        return
    text = _full_text(doc)
    if doc.profile == S.GROUP:
        p = regdir / "groups.csv"
        if p.exists():
            key = outline["registries"]["groups.csv"]["key"]
            with p.open(encoding="utf-8-sig", newline="") as fh:
                known = {row[key].strip() for row in csv.DictReader(fh)
                         if row.get(key)}
            if doc.ma and doc.ma not in known:
                r.err("sổ đăng ký",
                      f"mã nhóm `{doc.ma}` không có trong `groups.csv`. Nhóm "
                      f"phải khớp cây menu — thêm vào sổ trước.")
        else:
            r.warn("sổ đăng ký", "không có `groups.csv` — bỏ qua kiểm mã nhóm.")
        return

    kinds = {"messages.csv": "MSG", "usecases.csv": "UC", "states.csv": "ST",
             "roles.csv": "ROLE"}
    for fname, kind in kinds.items():
        p = regdir / fname
        if not p.exists():
            r.warn("sổ đăng ký", f"không có `{fname}` — bỏ qua kiểm mã {kind}.")
            continue
        key = outline["registries"][fname]["key"]
        with p.open(encoding="utf-8-sig", newline="") as fh:
            known = {row[key].strip() for row in csv.DictReader(fh)
                     if row.get(key)}
        codes = set(S.find_codes(text, kind))
        if kind == "ROLE":
            # ROLE- codes mostly live as column *headers* in "Ma trận phân
            # quyền" (or its variants), and headers are excluded from
            # text_content() on purpose — otherwise an untouched kv table
            # would look "filled in". Pull them back in here explicitly.
            for sec in doc.sections:
                for b in sec.blocks:
                    if b.kind == "table" and b.rows:
                        codes |= {c.strip() for c in b.rows[0]
                                 if S.CODE_PATTERNS["ROLE"].match(c.strip())}
        for code in sorted(codes):
            if code not in known:
                r.err("sổ đăng ký",
                      f"mã `{code}` không có trong `{fname}`. Thêm vào sổ trong "
                      f"cùng lần nộp, không tự đặt trong file chức năng.")


def check_gate(doc: S.FunctionDoc, outline: dict, r: Report) -> None:
    lex = outline["lexicon"]
    text = _full_text(doc)

    n = text.count(lex["open_marker"])
    if n:
        r.gate("cổng chặn",
               f"còn {n} chỗ đánh dấu {lex['open_marker']} chưa được BA chốt.")

    vd = doc.section("Vấn đề còn mở")
    if vd:
        pend = 0
        for b in vd.blocks:
            if b.kind != "table":
                continue
            for row in b.rows[1:]:
                joined = " ".join(row).strip()
                if joined and lex["status_pending"].lower() in joined.lower():
                    pend += 1
        if pend:
            r.gate("cổng chặn",
                   f"mục “Vấn đề còn mở” còn {pend} dòng trạng thái "
                   f"“{lex['status_pending']}”.")


def _table_col(outline: dict, prof: dict, sec_name: str,
              header: str) -> int | None:
    """Index of `header` in the outline's spec for `sec_name`'s first table,
    or None if that table has no such column (e.g. PHANTICH's flat tables).
    """
    spec = S.section_index(prof).get(sec_name)
    tids = spec.get("tables") if spec else None
    if not tids:
        return None
    headers = outline["tables"][tids[0]]["headers"]
    return headers.index(header) if header in headers else None


def _column_cells(sec: S.Section, col: int | None) -> list[str]:
    """Cell values from one column across every table in `sec`, header row
    excluded. Falls back to every cell of every row when `col` is None (no
    such column in the outline) so callers degrade instead of crashing."""
    out: list[str] = []
    for b in sec.blocks:
        if b.kind != "table" or not b.rows:
            continue
        if col is None:
            out += [c for row in b.rows[1:] for c in row]
        else:
            out += [row[col] for row in b.rows[1:] if len(row) > col]
    return out


def _full_text(doc: S.FunctionDoc) -> str:
    parts = []
    for sec in doc.sections:
        parts.append(sec.text_content())
    for f in doc.features:
        parts.append(f.ma)
        for sec in f.sections:
            parts.append(sec.text_content())
    return "\n".join(parts)


# ---------------------------------------------------------------------------
def validate(path: Path, outline: dict, regdir: Path | None) -> Report:
    r = Report()
    try:
        doc = S.read_markdown(path)
    except ValueError as e:
        r.err("cú pháp", str(e))
        return r

    # Portability of the .md itself, checked before anything about content.
    # This parser is lenient about blank lines around tables; every other
    # markdown reader is not, and the .md is what gets reviewed.
    for _, msg in S.table_spacing_faults(path.read_text(encoding="utf-8")):
        r.err("khoảng cách bảng",
              msg + ". Chèn một dòng trắng, hoặc chạy `srs.py fix «file».md`.")

    check_front_matter(doc, outline, r)
    pname = doc.profile
    if not S.known_kind(outline, pname):
        return r

    if doc.source and pname == S.GROUP:
        lines = doc.source.read_text(encoding="utf-8").split("\n")
        h1_count = sum(1 for line in lines if line.strip().startswith("# "))
        if h1_count != 1:
            r.err("cấu trúc", f"Tài liệu nhóm phải có đúng 1 Heading 1 (tên nhóm), hiện có {h1_count}.")

    prof = S.profile_of(outline, pname)
    check_structure(doc, prof, r)
    check_content(doc, prof, outline, r)
    check_cross(doc, prof, outline, r)
    check_messages(doc, outline, regdir, r)
    if not prof.get("is_group"):
        check_internal_refs(doc, prof, outline, r)
        check_cross_tables(doc, prof, outline, r)
    check_diagram_files(doc, path.parent, r)
    check_multiline_cells(doc, outline, r)
    check_obsolete(doc, r)
    check_malformed_codes(doc, r)
    check_registries(doc, outline, regdir, r)
    check_gate(doc, outline, r)
    return r


def main() -> int:
    S.utf8_stdio()
    ap = argparse.ArgumentParser(description="Kiểm tra file đặc tả chức năng.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--registry-dir", default=None)
    ap.add_argument("--outline", default=None)
    ap.add_argument("--quiet", action="store_true",
                    help="chỉ in lỗi và điểm vướng cổng chặn, bỏ cảnh báo — "
                         "cho agent hoặc CI, ít token hơn")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="in kết quả dạng JSON, máy đọc được")
    a = ap.parse_args()

    outline = S.load_outline(a.outline)
    regdir = Path(a.registry_dir) if a.registry_dir else None
    # Priority, not magnitude: a real error in any file must dominate the
    # batch result even if another file only trips the gate. `max()` on the
    # raw exit codes got this backwards — 2 (gate-only, draft still renders)
    # outranked 1 (error, nothing renders) purely because 2 > 1 numerically.
    any_err = False
    any_gate = False
    out_json = []

    for f in a.files:
        p = Path(f)
        r = validate(p, outline, regdir)
        n_w = len(r.items) - r.n_err - r.n_gate

        if a.as_json:
            out_json.append({
                "file": p.name,
                "errors": [{"where": i.where, "message": i.message}
                           for i in r.items if i.level == "error"],
                "warnings": [{"where": i.where, "message": i.message}
                             for i in r.items if i.level == "warn"],
                "gate": [{"where": i.where, "message": i.message}
                         for i in r.items if i.level == "info"],
            })
        elif a.quiet:
            shown = [i for i in r.items if i.level in ("error", "info")]
            if shown:
                print(f"=== {p.name} ===")
                for it in shown:
                    print("  " + str(it))
            print(f"{p.name}: {r.n_err} lỗi · {n_w} cảnh báo (ẩn) · "
                  f"{r.n_gate} vướng cổng chặn")
        else:
            print(f"\n=== {p.name} ===")
            if not r.items:
                print("  Sạch — không có lỗi, không vướng cổng chặn.")
            for it in r.items:
                print("  " + str(it))
            print(f"  → {r.n_err} lỗi · {n_w} cảnh báo · {r.n_gate} điểm "
                  f"vướng cổng chặn")
            if r.n_err:
                print("  → KHÔNG render được. Sửa lỗi trước.")
            elif r.n_gate:
                print("  → Chỉ render được BẢN NHÁP (có watermark).")
            else:
                print("  → Render được bản phát hành.")

        if r.n_err:
            any_err = True
        elif r.n_gate:
            any_gate = True

    if a.as_json:
        import json as _json
        rc = 1 if any_err else (2 if any_gate else 0)
        print(_json.dumps({"exit": rc, "files": out_json},
                          ensure_ascii=False, indent=1))

    if any_err:
        return 1
    if any_gate:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
