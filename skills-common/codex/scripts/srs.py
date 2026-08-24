#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
srs.py — Mot lenh dieu phoi, thay cho viec nho tung script.

    srs.py new     …    → scaffold.py
    srs.py check   …    → validate.py
    srs.py render  …    → render.py
    srs.py pdf     …    → export_pdf.py
    srs.py review  X.docx|X.md    → import (ra file rieng) roi validate
    srs.py fix     X.md …    → sua dong trang quanh bang
    srs.py migrate …    → migrate_outline.py
    srs.py export  X.md …    → validate → render → pdf, dung ngay khi loi

Moi cờ cua script goc dung nguyen — srs.py chi chuyen tiep, khong dien giai.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import srslib as S  # noqa: E402

PY = sys.executable

FORWARD = {
    "new": "scaffold.py",
    "check": "validate.py",
    "render": "render.py",
    "pdf": "export_pdf.py",
    "migrate": "migrate_outline.py",
    "import": "import_docx.py",
    "scan": "migrate_scan.py",
    "project": "project_check.py",
}


def run(script: str, args: list[str], capture: bool = False):
    return subprocess.run([PY, str(HERE / script)] + args,
                          capture_output=capture, text=capture,
                          encoding="utf-8" if capture else None,
                          errors="replace" if capture else None)


def cmd_review(args: list[str]) -> int:
    """Import to a *separate* file, then validate that.

    Review must never touch the user's sources. Importing a `.docx` straight
    onto `<stem>.md` silently overwrote the canonical Markdown whenever one
    sat next to the `.docx` — the exact "review rewrote my document" failure
    the mode split exists to prevent. Only an explicit `srs.py import` writes
    to a name the user chose.
    """
    if not args:
        print("Cách dùng: srs.py review «file.docx|file.md» [cờ validate]")
        return 1
    src, rest = Path(args[0]), args[1:]
    if src.suffix.lower() == ".docx":
        md = src.with_suffix("")
        md = md.parent / (md.name + ".review-import.md")
        r = run("import_docx.py", [str(src), "-o", str(md)])
        if r.returncode != 0:
            return r.returncode
        print(f"(bản nhập để soát: {md.name} — file .md gốc không bị đụng tới)")
        src = md
    return run("validate.py", [str(src)] + rest).returncode


def cmd_fix(args: list[str]) -> int:
    """Repairs that are mechanical and have exactly one right answer.

    Only blank lines around tables for now. Deliberately separate from
    `check`: validation reports, it never edits — an agent that silently
    rewrites the analyst's file is the failure this skill exists to avoid.
    """
    if not args:
        print("Cách dùng: srs.py fix «file».md [«file2».md …]")
        return 1
    total = 0
    for f in args:
        p = Path(f)
        if not p.exists():
            print(f"  [LỖI ] không thấy {p}")
            return 1
        text = p.read_text(encoding="utf-8")
        fixed, n = S.normalize_table_spacing(text)
        if n:
            p.write_text(fixed, encoding="utf-8")
            print(f"  [  ok ] {p.name}: chèn {n} dòng trắng quanh bảng.")
        else:
            print(f"  [ bỏ ] {p.name}: không có gì phải sửa.")
        total += n
    if total:
        print("\n  Bảng markdown phải cách nội dung khác bằng một dòng trắng; "
              "thiếu thì trình\n  đọc khác sẽ hút nội dung vào ô cuối bảng, "
              "dù skill vẫn đọc đúng.")
    return 0


def cmd_export(argv: list[str]) -> int:
    """validate → render → pdf. Chained here rather than folded into
    render.py: validate's 0/1/2 and render's own gate logic each mean
    something on their own, and merging them would blur both."""
    ap = argparse.ArgumentParser(prog="srs.py export",
                                 description="validate → render → pdf")
    ap.add_argument("src")
    ap.add_argument("--registry-dir", default=None)   # validate only
    ap.add_argument("--outline", default=None)        # validate AND render
    ap.add_argument("-o", "--out", default=None)      # render only
    ap.add_argument("--standalone", action="store_true")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--force-release", action="store_true")
    ap.add_argument("--config", default=None)
    a = ap.parse_args(argv)

    vargs = [a.src, "--json"]
    if a.registry_dir:
        vargs += ["--registry-dir", a.registry_dir]
    if a.outline:
        vargs += ["--outline", a.outline]

    # --json, parsed, not the raw exit code: argparse also exits 2 on a bad
    # command line, and treating that as "gate only, proceed to render" once
    # let a typo ship a .docx that was never validated. No parseable JSON
    # confirming gate-only means stop, whatever the number says.
    r = run("validate.py", vargs, capture=True)
    verdict = None
    try:
        verdict = json.loads(r.stdout)
    except (json.JSONDecodeError, TypeError):
        pass
    if verdict is None or "exit" not in verdict:
        sys.stdout.write(r.stdout or "")
        sys.stderr.write(r.stderr or "")
        print("→ export dừng: validate không trả kết quả đọc được "
              "(sai cú pháp lệnh?).")
        return r.returncode or 1

    for f in verdict.get("files", []):
        for e in f.get("errors", []):
            print(f"  [LỖI ] {e['where']}: {e['message']}")
        for gt in f.get("gate", []):
            print(f"  [TIN ] {gt['where']}: {gt['message']}")
    if verdict["exit"] == 1:
        print("→ export dừng: còn lỗi. Sửa rồi chạy lại.")
        return 1
    if verdict["exit"] == 2:
        print("→ còn vướng cổng chặn: render sẽ ra BẢN NHÁP.")

    rargs = [a.src]
    if a.out:
        rargs += ["-o", a.out]
    if a.outline:
        rargs += ["--outline", a.outline]
    if a.standalone:
        rargs.append("--standalone")
    if a.draft:
        rargs.append("--draft")
    if a.force_release:
        rargs.append("--force-release")
    if a.config:
        rargs += ["--config", a.config]
    r = run("render.py", rargs)
    if r.returncode != 0:
        return r.returncode

    md = Path(a.src)
    if a.out:
        docx = Path(a.out)
    else:
        cands = sorted(md.parent.glob(md.stem.split("_")[0] + "*.docx"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        docx = cands[0] if cands else None
    if docx is None or not docx.exists():
        print("→ không tìm thấy .docx vừa render để xuất PDF.")
        return 1
    return run("export_pdf.py", [str(docx)]).returncode


def main() -> int:
    S.utf8_stdio()
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "review":
        return cmd_review(args)
    if cmd == "fix":
        return cmd_fix(args)
    if cmd == "export":
        return cmd_export(args)
    if cmd in FORWARD:
        return run(FORWARD[cmd], args).returncode
    print(f"Không có lệnh `{cmd}`. Các lệnh: "
          f"{', '.join(list(FORWARD) + ['review', 'export'])}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
