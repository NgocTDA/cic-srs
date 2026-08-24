#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_check.py — Kiem mot thu muc du an co du thu de lam viec chua.

Chay dau phien tren claude.ai (sau khi BA tai goi du an len) hoac bat ky luc nao
tren Claude Code. Muc dich: noi ro CAI GI CON THIEU truoc khi bat tay, thay vi de
render xong moi phat hien mat anh.

    python project_check.py .
    python project_check.py /mnt/user-data/uploads
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import srslib as S

REG_FILES = ["messages.csv", "usecases.csv", "roles.csv", "states.csv",
             "participants.csv", "components.csv", "objects.csv", "groups.csv"]

# Only `functions/` holds documents of record. The rest of a project tree is
# working area or evidence, and both can contain a valid-looking `.md`:
# `staging/` is where a draft lands before anyone has decided it is right, and
# `sources/`, `migration/*/raw/` are frozen copies that must not be judged at
# all. Scoring them reports faults the analyst is not allowed to fix — the
# snapshot is hashed — and buries the real findings under drafts.
BO_QUA = {"staging", "migration", "sources", "reports", "exports",
          ".ba-toolkit", "references", "evals", "luu-tru", "__pycache__"}


def _find_upwards(start: Path, root: Path, rel: str) -> str | None:
    """Where a referenced file actually sits, if not beside the spec.

    Render resolves `assets/…` and `diagrams/…` against the folder holding
    the `.md`, never against the project root. A project laid out with one
    shared `assets/` at the top therefore renders every mockup as a missing
    box — while the files sit right there, one level up.
    """
    here = start.resolve()
    stop = root.resolve()
    for d in [here, *here.parents]:
        if (d / rel).exists():
            if d == here:
                return None
            try:
                return str((d / rel).relative_to(stop))
            except ValueError:
                return str(d / rel)
        if d == stop:
            break
    return None


def doc_manifest(path: Path) -> tuple[dict[str, str], list[str]]:
    """`{mã: trạng thái}` from the project manifest, plus duplicated codes.

    The manifest allocates `FUNC-` codes. Allocation cannot be derived from
    disk the way an inventory can: a code has to be reserved *before* the file
    exists, or two analysts working without a shared lock both take
    `FUNC-QLSP-048` and nothing notices until the documents meet.
    """
    rows: dict[str, str] = {}
    dup: list[str] = []
    pat = S.code_pattern("FUNC")
    trong_ghi_chu = False
    for line in path.read_text(encoding="utf-8").split("\n"):
        # A commented-out row is the natural way to leave an example in a file
        # meant to be filled in — counting it would report a code as allocated
        # that nobody allocated.
        if "<!--" in line:
            trong_ghi_chu = True
        if trong_ghi_chu:
            if "-->" in line:
                trong_ghi_chu = False
            continue
        if not line.lstrip().startswith("|"):
            continue
        cells = S._table_row(line)
        if not cells:
            continue
        m = pat.search(cells[0])
        if not m:
            continue
        ma = m.group(0)
        # Status is wherever the row put it; matching by value rather than
        # column index keeps this working if the project adds a column.
        tt = next((c.strip() for c in cells[1:]
                   if c.strip() in ("Đã cấp", "Đang viết", "Đã phát hành",
                                    "Bỏ")), "")
        if ma in rows:
            dup.append(ma)
        else:
            rows[ma] = tt
    return rows, sorted(set(dup))


def find(root: Path, name: str) -> Path | None:
    """Look in the root and one level down — an unzipped bundle usually lands
    inside a folder named after the archive."""
    if (root / name).exists():
        return root / name
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if (d / name).exists():
            return d / name
    return None


# Columns beyond the key that other scripts read by name. Missing one does not
# stop a run — it makes messages come out as bare codes, which reads like a
# rendering bug rather than an unfilled registry.
EXTRA_COLS = {
    "objects.csv": ["ten_hien_thi"],
    "states.csv": ["ten_hien_thi"],
    "messages.csv": ["thamso"],
}


def check_registries(regdir: Path, outline: dict, docs: list) -> bool:
    """Schema and content checks over every registry present.

    Reads `DictReader.fieldnames` rather than the first data row: a CSV holding
    only a header line has no rows at all, so a row-based check silently passes
    a file that is missing the very column it exists to provide.
    """
    bad = False
    specs = outline["registries"]

    for fname in REG_FILES:
        p = regdir / fname
        if not p.exists():
            continue
        key = specs.get(fname, {}).get("key")
        with p.open(encoding="utf-8-sig", newline="") as fh:
            rd = csv.DictReader(fh)
            cols = rd.fieldnames or []
            rows = list(rd)

        if not cols:
            print(f"    [LỖI ] {fname} rỗng — không có cả dòng tiêu đề.")
            bad = True
            continue

        # A stray BOM or trailing space fuses into the column name, so
        # `row["ma"]` misses and every code reads as absent.
        dirty = [c for c in cols if c != c.strip() or "﻿" in c]
        if dirty:
            print(f"    [LỖI ] {fname}: tiêu đề cột có ký tự lạ hoặc khoảng "
                  f"trắng thừa: {', '.join(repr(c) for c in dirty)}.")
            bad = True

        dup_cols = sorted({c for c in cols if cols.count(c) > 1})
        if dup_cols:
            print(f"    [LỖI ] {fname}: tiêu đề cột trùng nhau "
                  f"({', '.join(dup_cols)}) — csv chỉ giữ lại cột cuối.")
            bad = True

        clean = [c.strip().lstrip("﻿") for c in cols]
        if key and key not in clean:
            print(f"    [LỖI ] {fname} thiếu cột khoá `{key}` — không đối "
                  f"chiếu được mã nào với sổ này.")
            bad = True
        for col in EXTRA_COLS.get(fname, []):
            if col not in clean:
                print(f"    [LỖI ] {fname} thiếu cột `{col}` — thông báo có "
                      f"tham số sẽ ra mã trần.")
                bad = True

        if key and key in clean:
            vals = [(r.get(key) or "").strip() for r in rows]
            n_blank = sum(1 for v in vals if not v)
            if n_blank:
                print(f"    [LỖI ] {fname}: {n_blank} dòng bỏ trống `{key}` — "
                      f"dòng không có mã thì không ai tra tới được.")
                bad = True
            dup = sorted({v for v in vals if v and vals.count(v) > 1})
            if dup:
                print(f"    [LỖI ] {fname}: mã trùng ({', '.join(dup[:5])}"
                      f"{'…' if len(dup) > 5 else ''}) — hai dòng cùng mã thì "
                      f"tra ra dòng nào là tuỳ thứ tự đọc.")
                bad = True

    # A registry that exists but holds nothing is worse than an absent one: the
    # absent case prints a loud warning, this one silently passes every code.
    roles = regdir / "roles.csv"
    if roles.exists():
        with roles.open(encoding="utf-8-sig", newline="") as fh:
            n_roles = sum(1 for r in csv.DictReader(fh)
                          if (r.get("ma") or "").strip())
        if n_roles == 0:
            used = set()
            for _, d in docs:
                for sec in d.sections + [s for f in d.features
                                         for s in f.sections]:
                    used |= set(S.find_codes(sec.text_content(), "ROLE"))
                    for b in sec.blocks:
                        if b.kind == "table" and b.rows:
                            used |= {c.strip() for c in b.rows[0]
                                     if S.CODE_PATTERNS["ROLE"].match(c.strip())}
            if used:
                print(f"    [LỖI ] roles.csv không có dòng nào nhưng tài liệu "
                      f"đang dùng {len(used)} mã vai trò "
                      f"({', '.join(sorted(used)[:4])}"
                      f"{'…' if len(used) > 4 else ''}) — mọi mã sẽ bị báo "
                      f"không có trong sổ.")
                bad = True
    return bad


def main() -> int:
    S.utf8_stdio()
    ap = argparse.ArgumentParser(description="Kiểm thư mục dự án.")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--outline", default=None)
    a = ap.parse_args()

    root = Path(a.root).resolve()
    if not root.is_dir():
        print(f"LỖI: {root} không phải thư mục.", file=sys.stderr)
        return 1
    outline = S.load_outline(a.outline)

    tat_ca = sorted(root.rglob("*.md"))
    # Whitelist the folders that hold documents of record, rather than
    # blacklisting the rest. A project root also carries `manifest.md` and
    # `project-rules/srs-help.md`, and counting those as failed specs turns a
    # correctly built skeleton into an error report.
    #
    # `groups/` belongs here as much as `functions/`: a `GRP-` file is a real
    # document, merged into the master like any other. Leaving it out dropped
    # every group file **silently** — worse than an error, because the run
    # then said "Đủ để làm việc" about a project it had only half read.
    #
    # Ask whether the folder *is* a project, not whether it already has specs
    # — an empty `functions/` is exactly the state a fresh skeleton is in.
    NGUON = ("functions", "groups")
    la_du_an = (any((d / n).is_dir() for n in NGUON
                    for d in (root, *(p for p in root.iterdir() if p.is_dir())))
                or any(set(p.parts) & set(NGUON) for p in tat_ca))
    if la_du_an:
        specs = [p for p in tat_ca if set(p.parts) & set(NGUON)]
    else:
        # Pointed straight at a subsystem folder: neither name is in the path.
        specs = [p for p in tat_ca if not (set(p.parts) & BO_QUA)]
    bo_qua = [p for p in tat_ca if p not in specs]
    print(f"=== {root} ===\n")
    if bo_qua:
        # Say it out loud. A count of files the tool declined to judge is the
        # difference between "my drafts are fine" and "my drafts were never
        # looked at" — and the analyst can only tell those apart if we print it.
        n_stg = sum(1 for p in bo_qua if "staging" in p.parts)
        extra = f", trong đó {n_stg} bản nháp ở `staging/`" if n_stg else ""
        print(f"  [ ghi ] Bỏ qua {len(bo_qua)} file .md ngoài `functions/` và "
              f"`groups/`{extra}. Chỉ tài liệu chính thức mới được chấm.\n")

    # -- specs -------------------------------------------------------------
    docs = []
    for p in specs:
        try:
            d = S.read_markdown(p)
        except Exception as e:
            print(f"  [LỖI ] {p.name}: không đọc được front matter — {e}")
            continue
        if not d.ma or not S.known_kind(outline, d.profile):
            continue
        docs.append((p, d))

    # An empty project is not a broken one. Distinguishing the two matters
    # because running this on a fresh skeleton is the first thing anyone does,
    # and greeting them with [LỖI] teaches them the tool cries wolf. But a
    # folder that *has* `.md` files none of which parsed is a real fault —
    # usually a zip that lost its contents, or specs written outside the
    # standard.
    du_an_moi = not docs and not specs
    if du_an_moi:
        print("  [ ghi ] Chưa có tài liệu nào — dự án mới. Dựng file đầu tiên "
              "bằng `srs.py new`, sau khi đã cấp mã ở manifest.md.")
    elif not docs:
        print(f"  [LỖI ] Có {len(specs)} file .md dưới `functions/` nhưng "
              f"không file nào có front matter hợp lệ.")
        print("    Gói tải lên thiếu nội dung, hoặc tài liệu viết ngoài chuẩn.")
    else:
        print(f"  {len(docs)} file đặc tả:")
        for p, d in docs:
            n = f" · {len(d.features)} tính năng" if d.features else ""
            print(f"    {d.ma:<20} {d.profile:<9} v{d.meta.get('version','?')}"
                  f" · {d.meta.get('status','?')}{n}")

    missing_img, missing_puml = [], []
    misplaced: list[str] = []
    for p, d in docs:
        base = p.parent
        for sec in d.sections + [s for f in d.features for s in f.sections]:
            for b in sec.blocks:
                if b.kind == "image" and not (base / b.path).exists():
                    found = _find_upwards(base, root, b.path)
                    if found:
                        # Misplaced, not missing — do not also report it as
                        # absent, or the analyst is told two contradictory
                        # things about one file.
                        misplaced.append((b.path, found, base))
                    else:
                        missing_img.append(f"{d.ma}: {b.path}")
                if b.kind == "diagram":
                    rel = f"diagrams/{b.code}.puml"
                    if not (base / rel).exists():
                        found = _find_upwards(base, root, rel)
                        if found:
                            misplaced.append((rel, found, base))
                        else:
                            missing_puml.append(f"{d.ma}: {rel}")

    print()
    if misplaced:
        # The distinction that matters: the file exists, it is just in the
        # wrong folder. Both this skill's own deployment docs used to show a
        # single `assets/` at the project root with the specs one level down
        # in `functions/`, which renders every mockup as a ⟨THIẾU HÌNH⟩ box —
        # and `validate.py` still says "0 lỗi", because a missing optional
        # image is only a warning. Saying "thiếu ảnh" here would send the
        # analyst hunting for files they already have.
        print(f"  [LỖI ] {len(misplaced)} tệp ĐẶT SAI CHỖ — có trên đĩa, "
              f"nhưng không phải nơi skill tìm:")
        shown = set()
        for rel, found, base in misplaced:
            try:
                want = str((base / rel).resolve().relative_to(root.resolve()))
            except ValueError:
                want = str(base / rel)
            key = (found, want)
            if key in shown:
                continue
            shown.add(key)
            if len(shown) > 6:
                break
            print(f"    đang ở : {found}")
            print(f"    cần ở  : {want}")
        if len(misplaced) > len(shown):
            print(f"    … còn {len(misplaced) - len(shown)} tệp nữa")
        print("    → `assets/` và `diagrams/` phải nằm NGAY CẠNH file .md, "
              "không phải ở gốc dự án.")
        print("      Chia theo phân hệ thì mỗi phân hệ có bộ riêng:")
        print("      functions/qlnsd/{FUNC-QLNSD-001.md, assets/, diagrams/}")

    for label, items, hint in (
            ("Ảnh mockup thiếu", missing_img,
             "gửi ảnh cho Claude, hoặc tải kèm thư mục assets/"),
            ("File .puml thiếu", missing_puml,
             "tải kèm thư mục diagrams/")):
        if items:
            print(f"  [LỖI ] {label} ({len(items)}):")
            for x in items[:8]:
                print(f"    {x}")
            if len(items) > 8:
                print(f"    … còn {len(items) - 8}")
            print(f"    → {hint}")
        else:
            print(f"  [  ok ] {label.replace(' thiếu', '')}: đủ")

    # -- registries --------------------------------------------------------
    # One name only. A project that called the folder something else and then
    # gained a `registries/` alongside it — which is what BA Toolkit's `init`
    # creates, with eight empty CSVs — would pass every schema check against
    # the empty set while the real registry sat unread one folder away. Every
    # code check after that is theatre, and nothing says so.
    regdir = find(root, "registries")
    if regdir is not None and not regdir.is_dir():
        regdir = None
    if regdir is None and find(root, "messages.csv"):
        regdir = find(root, "messages.csv").parent

    print()
    # Kept apart from the column check below on purpose: that one reassigns the
    # flag, and folding the two together would let a clean column check erase a
    # naming error — the same silent-contradiction shape already fixed twice in
    # this file.
    reg_sai_ten = False
    lac_ten = find(root, "so-dang-ky")
    if lac_ten is not None and lac_ten.is_dir():
        print(f"  [LỖI ] Thấy `{lac_ten.name}/` — tên sổ đăng ký duy nhất được "
              f"chấp nhận là `registries/`. Đổi tên thư mục.")
        print("    Giữ tên cũ thì BA Toolkit sẽ tự tạo `registries/` rỗng bên "
              "cạnh, và mọi phép kiểm mã từ đó là giả.")
        reg_sai_ten = True
    reg_col_missing = False
    if regdir is None:
        print("  [CẢNH] Không thấy sổ đăng ký. Sẽ BỎ QUA phép kiểm mã — mã bịa "
              "như ERR_999 vẫn lọt.")
    else:
        have = [f for f in REG_FILES if (regdir / f).exists()]
        lack = [f for f in REG_FILES if f not in have]
        print(f"  [  ok ] Sổ đăng ký: {regdir.name}/ — có {len(have)}/8")
        if lack:
            print(f"    thiếu: {', '.join(lack)}")
        reg_col_missing = check_registries(regdir, outline, docs)

    # -- config ------------------------------------------------------------
    print()
    cfgp = find(root, "srs-config.json")
    if cfgp is None:
        print("  [CẢNH] Không thấy srs-config.json. Chỉ cần khi xuất tài liệu "
              "độc lập (bìa, logo, số trang).")
    else:
        try:
            cfg = json.loads(cfgp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [LỖI ] srs-config.json không đọc được: {e}")
            cfg = {}
        print(f"  [  ok ] Cấu hình: {cfgp.name}")
        for k in ("to_chuc", "du_an"):
            v = str(cfg.get(k, ""))
            if not v or v.startswith("«"):
                print(f"    [CẢNH] `{k}` chưa điền.")
        logo = cfg.get("logo")
        if logo and not (cfgp.parent / logo).exists():
            print(f"    [CẢNH] không thấy logo `{logo}`.")
        if cfg.get("plantuml_server"):
            print(f"    [TIN  ] dùng PlantUML server "
                  f"{cfg['plantuml_server']} — chỉ gọi được từ Claude Code, và "
                  f"mất tính tái lập so với jar ghim phiên bản.")

    # -- manifest ----------------------------------------------------------
    print()
    man_bad = False
    manp = find(root, "manifest.md")
    if manp is None:
        print("  [CẢNH] Không thấy manifest.md — không đối chiếu được mã "
              "`FUNC-` đã cấp. Một BA làm một mình thì bỏ qua được; nhiều "
              "người thì hai bên sẽ cùng lấy một số.")
        print("    Mẫu: assets/manifest.example.md trong skill.")
    else:
        cap, dup = doc_manifest(manp)
        print(f"  [  ok ] Danh mục chức năng: {manp.name} — {len(cap)} mã đã cấp")
        if dup:
            print(f"    [LỖI ] mã ghi hai lần: {', '.join(dup)} — không biết "
                  f"dòng nào là thật.")
            man_bad = True
        tren_dia = {d.ma for _, d in docs if d.ma.startswith("FUNC-")}
        chua_cap = sorted(tren_dia - set(cap))
        if chua_cap:
            print(f"    [LỖI ] có file nhưng chưa cấp trong manifest: "
                  f"{', '.join(chua_cap)}")
            print("      Cấp mã ở manifest.md trước rồi mới viết file — "
                  "ngược lại thì người khác có thể đã lấy số đó.")
            man_bad = True
        # Only "Đã phát hành" is worth a warning. "Đã cấp" and "Đang viết"
        # having no file yet is the normal state of a reservation.
        thieu = sorted(m for m, tt in cap.items()
                       if tt == "Đã phát hành" and m not in tren_dia)
        if thieu:
            print(f"    [CẢNH] manifest ghi “Đã phát hành” nhưng không thấy "
                  f"file: {', '.join(thieu)}")

    # -- project overlay ---------------------------------------------------
    # An overlay changes how the skill behaves, so its presence has to be
    # visible. Silence here means two analysts on the same project get
    # different output and neither has a reason to suspect why.
    rules = find(root, "project-rules")
    overlay = (rules / "srs-help.md") if rules and rules.is_dir() else None
    if overlay is not None and overlay.is_file():
        n = len(overlay.read_text(encoding="utf-8").split("\n"))
        print(f"  [  ok ] Luật riêng dự án: project-rules/srs-help.md "
              f"({n} dòng) — skill đọc file này SAU SKILL.md.")
    else:
        print("  [ ghi ] Không có project-rules/srs-help.md. Skill chạy thuần "
              "theo chuẩn, không có ngoại lệ riêng của dự án.")

    # -- verdict -----------------------------------------------------------
    print()
    # `misplaced` has to count too. Pulling those files out of `missing_img`
    # so they are not reported twice also pulled them out of the verdict, and
    # the run printed a [LỖI] block then concluded "Đủ để làm việc" — the same
    # contradiction the registry-column check had.
    blockers = bool(missing_img or missing_puml or (not docs and not du_an_moi)
                    or reg_col_missing or reg_sai_ten or misplaced or man_bad)
    if blockers:
        print("  → CÒN THIẾU. Bổ sung những mục [LỖI] ở trên rồi chạy lại.")
    elif du_an_moi:
        print("  → Khung dự án dựng đúng. Chưa có tài liệu nào.")
        print("     Bước tiếp: cấp mã ở manifest.md, rồi `srs.py new "
              "--profile UI --ma FUNC-«phân hệ»-001 --ten «tên»`")
    else:
        print("  → Đủ để làm việc.")
        cmd = f"--registry-dir {regdir.name}" if regdir else "(không có sổ)"
        print(f"     Bước tiếp: validate.py «file».md {cmd}")
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
