#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_skills.py — sinh bản phát của skill cho từng trợ lý AI từ MỘT nguồn duy nhất.

Nguồn thật là `.claude/skills/<tên>/`. Mọi bản khác (Codex, Antigravity, gói
`.skill` cho claude.ai) đều sinh ra từ đây, không bản nào được sửa tay.

Trước đây kho này giữ ba bản chép tay trong `skills-common/`. Chúng lệch nhau
thật — `validate.py` của một bản có phép kiểm mà hai bản kia thiếu, nên cùng
một tài liệu cho ba kết quả khác nhau. Script này tồn tại để chuyện đó không
lặp lại.

Chỉ dùng thư viện chuẩn: skill scripts cũng vậy, và máy của BA thường không có
pyyaml.

    python tools/build_skills.py                 # sinh toàn bộ vào dist/
    python tools/build_skills.py --check         # so dist với nguồn, không ghi
    python tools/build_skills.py --skill srs-help --target codex
    python tools/build_skills.py --list
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

# Console Windows mặc định cp1252, không in nổi tiếng Việt. Skill scripts xử lý
# bằng S.utf8_stdio(); ở đây làm cùng cách vì không import được srslib.
for _stream in (sys.stdout, sys.stderr):
    if _stream and _stream.encoding and _stream.encoding.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

# Ngày giờ cố định trong zip: cùng nội dung phải cho cùng byte, nếu không
# `--check` sẽ báo lệch chỉ vì build lại ở thời điểm khác.
ZIP_DATE = (2026, 1, 1, 0, 0, 0)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).resolve().parent / "skill-targets.json"


def fail(msg: str) -> None:
    print(f"[!] {msg}", file=sys.stderr)
    sys.exit(1)


def load_config() -> dict:
    if not CONFIG.exists():
        fail(f"Không thấy file định tuyến: {CONFIG}")
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"{CONFIG.name} sai cú pháp JSON: {e}")


def is_excluded(rel: Path, cfg: dict) -> bool:
    if any(part in cfg["exclude_dirs"] for part in rel.parts):
        return True
    return any(fnmatch.fnmatch(rel.name, pat) for pat in cfg["exclude_globs"])


def collect(src_dir: Path, cfg: dict) -> list[Path]:
    """Đường dẫn tương đối của mọi file được phát, sắp xếp để build tái lập được."""
    out = []
    for p in src_dir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(src_dir)
        if not is_excluded(rel, cfg):
            out.append(rel)
    return sorted(out, key=lambda r: r.as_posix())


def emitted_files(src_dir: Path, target: dict) -> dict[str, bytes]:
    """File riêng của từng đích (vd. agents/openai.yaml cho Codex).

    Adapter chép nguyên văn, không diễn giải — cái BA thấy trong
    `adapters/` đúng bằng cái nằm trong bản phát.
    """
    out = {}
    for src_rel, dst_rel in target.get("emit", {}).items():
        src = src_dir / src_rel
        if src.exists():
            out[dst_rel] = src.read_bytes()
    return out


def build_payload(src_dir: Path, cfg: dict, target: dict) -> dict[str, bytes]:
    payload = {rel.as_posix(): (src_dir / rel).read_bytes()
               for rel in collect(src_dir, cfg)}
    for dst, data in emitted_files(src_dir, target).items():
        if dst in payload:
            fail(f"Adapter ghi đè file có sẵn của skill: {dst}")
        payload[dst] = data
    return payload


def write_dir(dest: Path, payload: dict[str, bytes]) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    for rel, data in payload.items():
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)


def write_zip(dest: Path, payload: dict[str, bytes]) -> None:
    """Gói .skill: file nằm ở GỐC zip, không bọc thêm thư mục tên skill.

    Bản `.skill` phát hành trước đây có cấu trúc này; bọc thêm một tầng thì
    Claude không nhận ra skill lúc cài.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    dirs = sorted({parent for rel in payload
                   for parent in Path(rel).parents if parent.as_posix() != "."})
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for d in dirs:
            info = zipfile.ZipInfo(d.as_posix() + "/", date_time=ZIP_DATE)
            info.external_attr = (0o755 << 16) | 0x10
            z.writestr(info, b"")
        for rel in sorted(payload):
            info = zipfile.ZipInfo(rel, date_time=ZIP_DATE)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, payload[rel])


def read_dir(dest: Path) -> dict[str, bytes]:
    if not dest.is_dir():
        return {}
    return {p.relative_to(dest).as_posix(): p.read_bytes()
            for p in dest.rglob("*") if p.is_file()}


def read_zip(dest: Path) -> dict[str, bytes]:
    if not dest.is_file():
        return {}
    with zipfile.ZipFile(dest) as z:
        return {n: z.read(n) for n in z.namelist() if not n.endswith("/")}


def digest(payload: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    for rel in sorted(payload):
        h.update(rel.encode("utf-8"))
        h.update(hashlib.sha256(payload[rel]).digest())
    return h.hexdigest()[:12]


def dest_path(out_root: Path, tname: str, skill: str, target: dict) -> Path:
    if target.get("package") == "zip":
        return out_root / tname / f"{skill}{target.get('ext', '.zip')}"
    return out_root / tname / skill


def report_drift(current: dict[str, bytes], wanted: dict[str, bytes]) -> list[str]:
    problems = []
    for rel in sorted(set(wanted) - set(current)):
        problems.append(f"thiếu     {rel}")
    for rel in sorted(set(current) - set(wanted)):
        problems.append(f"thừa      {rel}")
    for rel in sorted(set(current) & set(wanted)):
        if current[rel] != wanted[rel]:
            problems.append(f"lệch nội dung {rel}")
    return problems


def guard_stray_copies(cfg: dict) -> None:
    """Bắt lại đúng cái lỗi script này sinh ra để chống: một bản skill chép tay."""
    src_root = (ROOT / cfg["source_dir"]).resolve()
    out_root = (ROOT / cfg["out_dir"]).resolve()
    for skill_md in ROOT.rglob("SKILL.md"):
        p = skill_md.resolve()
        if src_root in p.parents or out_root in p.parents:
            continue
        if ".git" in p.parts:
            continue
        rel = p.relative_to(ROOT).as_posix()
        print(f"[!] Có bản skill nằm ngoài nguồn: {rel}")
        print("    Nguồn thật chỉ ở .claude/skills/. Xoá bản này, hoặc thêm một")
        print("    đích trong tools/skill-targets.json nếu nó là bản phát.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Sinh bản phát của skill cho từng trợ lý AI từ một nguồn duy nhất.")
    ap.add_argument("--check", action="store_true",
                    help="So bản trong dist/ với nguồn; không ghi gì. Lệch thì thoát mã 1.")
    ap.add_argument("--skill", action="append",
                    help="Chỉ build skill này (lặp lại được). Mặc định: tất cả.")
    ap.add_argument("--target", action="append",
                    help="Chỉ build đích này (lặp lại được). Mặc định: tất cả.")
    ap.add_argument("--list", action="store_true", help="Liệt kê skill và đích rồi thoát.")
    args = ap.parse_args()

    cfg = load_config()
    out_root = ROOT / cfg["out_dir"]

    skills = args.skill or cfg["skills"]
    targets = args.target or list(cfg["targets"])

    for s in skills:
        if not (ROOT / cfg["source_dir"] / s).is_dir():
            fail(f"Không thấy skill nguồn: {cfg['source_dir']}/{s}")
    for t in targets:
        if t not in cfg["targets"]:
            fail(f"Đích không khai trong {CONFIG.name}: {t} "
                 f"(có: {', '.join(cfg['targets'])})")

    if args.list:
        print(f"Nguồn: {cfg['source_dir']}/   →   Đích: {cfg['out_dir']}/")
        for s in cfg["skills"]:
            n = len(collect(ROOT / cfg["source_dir"] / s, cfg))
            print(f"  skill  {s}  ({n} file)")
        for t, spec in cfg["targets"].items():
            print(f"  đích   {t}  ({spec.get('package', 'dir')})"
                  f"{'  +' + ', '.join(spec['emit'].values()) if spec.get('emit') else ''}")
        return 0

    guard_stray_copies(cfg)

    drift = 0
    for skill in skills:
        src_dir = ROOT / cfg["source_dir"] / skill
        for tname in targets:
            target = cfg["targets"][tname]
            payload = build_payload(src_dir, cfg, target)
            dest = dest_path(out_root, tname, skill, target)
            rel_dest = dest.relative_to(ROOT).as_posix()

            if args.check:
                current = (read_zip(dest) if target.get("package") == "zip"
                           else read_dir(dest))
                if not current:
                    print(f"[?] {rel_dest} — chưa build")
                    drift += 1
                    continue
                problems = report_drift(current, payload)
                if problems:
                    drift += 1
                    print(f"[!] {rel_dest} — lệch {len(problems)} điểm so với nguồn:")
                    for line in problems[:10]:
                        print(f"      {line}")
                    if len(problems) > 10:
                        print(f"      … và {len(problems) - 10} điểm nữa")
                else:
                    print(f"[✓] {rel_dest} — khớp nguồn")
                continue

            if target.get("package") == "zip":
                write_zip(dest, payload)
            else:
                write_dir(dest, payload)
            print(f"[✓] {rel_dest}  ({len(payload)} file · {digest(payload)})")

    if args.check:
        if drift:
            print(f"\n{drift} bản lệch nguồn. Chạy `python tools/build_skills.py` để sinh lại.")
            return 1
        print("\nMọi bản phát đều khớp nguồn.")
        return 0

    print(f"\nXong. Bản phát nằm ở {cfg['out_dir']}/ — không commit, không sửa tay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
