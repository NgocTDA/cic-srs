#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_outline.py — Nang mot file .md tu de cuong cu len de cuong hien hanh.

Chi lam phan CO CHE: chen dung dong con thieu, dat dau ⟨?⟩, mo mot dong o muc
"Van de con mo", cap nhat outline_version va changelog.

KHONG dien noi dung. Doan ho pham vi cua mot chuc nang la dung loai loi ma ca
bo kiem nay sinh ra de chan — file doc troi chay, khong ai soat lai, va sai
lech chi lo ra khi Dev lam den.

    python migrate_outline.py FUNC-QLNSD-001.md
    python migrate_outline.py functions/*.md --nguoi "Ngoc TDA"
    python migrate_outline.py FUNC-QLNSD-001.md --thu          # xem truoc
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import srslib as S


def _table_bounds(lines: list[str], start: int) -> tuple[int, int]:
    """Index of the first and last line of the markdown table at/after `start`."""
    i = start
    while i < len(lines) and not lines[i].lstrip().startswith("|"):
        i += 1
    if i >= len(lines):
        return -1, -1
    j = i
    while j < len(lines) and lines[j].lstrip().startswith("|"):
        j += 1
    return i, j - 1


def _section_range(lines: list[str], name: str) -> tuple[int, int]:
    """Line range of a `## name` section, end-exclusive."""
    want = S.norm(name)
    start = -1
    for i, ln in enumerate(lines):
        if ln.startswith("## ") and S.norm(ln[3:]) == want:
            start = i
            break
    if start < 0:
        return -1, -1
    j = start + 1
    while j < len(lines) and not lines[j].startswith("## "):
        j += 1
    return start, j


def add_kv_rows(lines: list[str], sec_name: str, table_labels: list[str],
                marker: str) -> tuple[list[str], list[str]]:
    """Insert every missing kv row, each in its outline position.

    Position matters as much as presence: `validate.py` checks order too, so
    appending at the bottom would trade one error for another.
    """
    s, e = _section_range(lines, sec_name)
    if s < 0:
        return lines, []
    t0, t1 = _table_bounds(lines[:e], s)
    if t0 < 0:
        return lines, []

    body = lines[t0:t1 + 1]
    # Header + separator, then one line per label.
    head = body[:2]
    rows = body[2:]
    have = [r.split("|")[1].strip() if r.count("|") >= 2 else "" for r in rows]

    added: list[str] = []
    out_rows: list[str] = []
    ri = 0
    for lab in table_labels:
        if lab in have:
            # Keep every existing row byte-for-byte; only ordering of *new*
            # rows is ours to decide.
            while ri < len(rows) and (rows[ri].split("|")[1].strip()
                                      if rows[ri].count("|") >= 2 else "") != lab:
                out_rows.append(rows[ri])
                ri += 1
            if ri < len(rows):
                out_rows.append(rows[ri])
                ri += 1
        else:
            out_rows.append(f"| {lab} | {marker} |")
            added.append(lab)
    out_rows += rows[ri:]

    return lines[:t0] + head + out_rows + lines[t1 + 1:], added


def add_open_issues(lines: list[str], sec_name: str, items: list[str],
                    pending: str, nguoi: str, han: str) -> list[str]:
    """Append one row per unresolved item to the open-issues table."""
    if not items:
        return lines
    s, e = _section_range(lines, sec_name)
    if s < 0:
        return lines
    t0, t1 = _table_bounds(lines[:e], s)
    if t0 < 0:
        return lines
    existing = [r for r in lines[t0 + 2:t1 + 1] if r.strip().strip("|").strip()]
    n = len(existing)
    new = []
    for k, it in enumerate(items, 1):
        new.append(f"| {n + k} | {it} | {nguoi} | {han} | {pending} |")
    return lines[:t1 + 1] + new + lines[t1 + 1:]


def bump_front_matter(text: str, outline: dict, nguoi: str,
                      note: str) -> tuple[str, str | None]:
    """Set outline_version and add a changelog line. Returns (text, old_ver)."""
    meta, body = S.parse_front_matter(text)
    old = str(meta.get("outline_version") or "")
    meta["outline_version"] = outline["version"]

    ver = str(meta.get("version") or "0.1")
    # A migration changes structure, not scope: x.Y+1 per the outline's own
    # bump rules. Saying which rule applies is required of the skill, so the
    # script that does it automatically says it too.
    try:
        maj, minor = ver.split(".")[:2]
        newver = f"{int(maj)}.{int(minor) + 1}"
    except Exception:
        newver = ver
    meta["version"] = newver

    cl = meta.get("changelog") or []
    cl.append({"v": newver, "ngay": dt.date.today().isoformat(),
               "nguoi": nguoi, "mo_ta": note})
    meta["changelog"] = cl
    return S.dump_front_matter(meta) + "\n\n" + body, old


def migrate_file(path: Path, outline: dict, nguoi: str, han: str,
                 dry: bool) -> int:
    text = path.read_text(encoding="utf-8")
    try:
        doc = S.parse_markdown(text, source=path)
    except ValueError as e:
        print(f"  [LỖI ] {path.name}: không đọc được — {e}")
        return 1

    have_ver = str(doc.meta.get("outline_version") or "")
    want = outline["version"]
    if have_ver == want:
        print(f"  [ bỏ ] {path.name}: đã ở v{want}.")
        return 0

    # Follow the chain rather than looking for one direct hop: upgrades
    # accumulate (4.1 → 5.0 → 6.0), and a document left on the oldest version
    # must still be able to reach the head in one run.
    steps = {str(m["tu"]): m for m in outline.get("migrations", [])
             if m.get("tu") and m.get("den")}
    path_hops, cur, seen = [], have_ver, set()
    while cur in steps and cur not in seen:
        seen.add(cur)
        path_hops.append(steps[cur])
        cur = str(steps[cur]["den"])
    if not path_hops or cur != want:
        print(f"  [LỖI ] {path.name}: không có đường nâng cấp "
              f"v{have_ver or '?'} → v{want} trong outline.json.")
        return 1
    mig = path_hops[-1]
    if len(path_hops) > 1:
        chain = " → ".join([f"v{have_ver}"]
                           + [f"v{h['den']}" for h in path_hops])
        print(f"  [TIN  ] {path.name}: đi qua {len(path_hops)} chặng — {chain}")

    if doc.profile == S.GROUP:
        # A group is a heading plus a description; the scope rows live in the
        # function-level table it does not have.
        new_text, _ = bump_front_matter(text, outline, nguoi,
                                        f"Nâng đề cương v{have_ver} → v{want}")
        if dry:
            print(f"  [ xem ] {path.name}: chỉ cập nhật outline_version.")
            return 0
        path.write_text(new_text, encoding="utf-8")
        print(f"  [  ok ] {path.name}: cập nhật outline_version (nhóm chức "
              f"năng, không có bảng Mô tả chung).")
        return 0

    marker = outline["lexicon"]["open_marker"]
    pending = outline["lexicon"]["status_pending"]
    gate_sec = outline["gate"]["section"]
    labels = outline["tables"]["TBL_KV_LOAI_CHUC_NANG"]["labels"]

    lines = text.split("\n")
    lines, added = add_kv_rows(lines, "Mô tả chung", labels, marker)
    if added:
        lines = add_open_issues(
            lines, gate_sec,
            [f"Điền “{lab}” ở mục Mô tả chung — nâng đề cương v{have_ver} → "
             f"v{want} chèn dòng này, nội dung chưa có." for lab in added],
            pending, nguoi, han)

    new_text, _ = bump_front_matter(
        "\n".join(lines), outline, nguoi,
        f"Nâng đề cương v{have_ver} → v{want}"
        + (f"; chèn {', '.join(added)} còn để {marker}" if added else ""))

    if dry:
        print(f"  [ xem ] {path.name}: sẽ chèn {len(added)} dòng "
              f"({', '.join(added) or 'không có'}) và mở {len(added)} vấn đề.")
        return 0

    path.write_text(new_text, encoding="utf-8")
    print(f"  [  ok ] {path.name}: chèn {len(added)} dòng "
          f"({', '.join(added) or 'không có'}), mở {len(added)} dòng ở "
          f"“{gate_sec}”.")
    return 0


def main() -> int:
    S.utf8_stdio()
    ap = argparse.ArgumentParser(
        description="Nâng file .md lên đề cương hiện hành.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--nguoi", default="⟨?⟩",
                    help="người thực hiện, ghi vào changelog")
    ap.add_argument("--han", default="⟨?⟩",
                    help="hạn chốt cho các dòng mở ra ở Vấn đề còn mở")
    ap.add_argument("--thu", action="store_true",
                    help="chỉ xem trước, không ghi file")
    ap.add_argument("--outline", default=None)
    a = ap.parse_args()

    outline = S.load_outline(a.outline)
    print(f"=== nâng lên đề cương v{outline['version']} ===")
    rc = 0
    for f in a.files:
        p = Path(f)
        if not p.exists():
            print(f"  [LỖI ] không thấy {p}")
            rc = 1
            continue
        rc = max(rc, migrate_file(p, outline, a.nguoi, a.han, a.thu))

    if not a.thu:
        print("\nBước tiếp: điền nội dung ở những chỗ còn "
              f"{outline['lexicon']['open_marker']}, rồi chạy validate.py. "
              f"Còn dấu đó thì chỉ ra được bản nháp — đó là chủ ý.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
