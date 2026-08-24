#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_pdf.py — .docx -> .pdf, CO cap nhat truong truoc khi xuat.

Vi sao khong dung thang `soffice --convert-to pdf`: caption dung truong SEQ, va
muc luc dung truong TOC. Chuyen doi thang se xuat ra so cu (thuong la "Hinh 1"
lap lai o moi anh). Phai mo tai lieu qua cau UNO, goi refresh, roi moi xuat.

    python export_pdf.py out/FUNC-QLNSD-001.docx
    python export_pdf.py out/*.docx -o pdf/
"""
from __future__ import annotations

import argparse
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path


def free_port() -> int:
    """Ask the OS for an unused port instead of hardcoding one.

    A fixed port meant two exports running at once fought over the same
    socket: the second process either failed to bind or, worse, attached to
    the first one's LibreOffice and exported through a soffice instance that
    was about to be terminated. Binding to port 0 lets the kernel pick, and
    the socket is closed immediately so soffice can take it — a race in
    theory, but a far smaller window than a constant everybody shares.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def soffice_bin() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def start_soffice(profile: Path, port: int):
    exe = soffice_bin()
    if not exe:
        return None
    cmd = [exe, "--headless", "--invisible", "--nologo", "--norestore",
           f"--accept=socket,host=127.0.0.1,port={port};urp;",
           f"-env:UserInstallation={profile.resolve().as_uri()}"]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def connect(port: int, timeout=90):
    import uno  # type: ignore
    ctx_local = uno.getComponentContext()
    resolver = ctx_local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", ctx_local)
    url = (f"uno:socket,host=127.0.0.1,port={port};urp;"
           f"StarOffice.ComponentContext")
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            return resolver.resolve(url)
        except Exception as e:  # bridge not up yet
            last = e
            time.sleep(1.5)
    raise RuntimeError(f"Không kết nối được LibreOffice: {last}")


def refresh_and_export(ctx, src: Path, dst: Path) -> None:
    import uno  # type: ignore
    from com.sun.star.beans import PropertyValue  # type: ignore

    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext(
        "com.sun.star.frame.Desktop", ctx)

    def pv(name, value):
        p = PropertyValue()
        p.Name, p.Value = name, value
        return p

    doc = desktop.loadComponentFromURL(
        uno.systemPathToFileUrl(str(src.resolve())), "_blank", 0,
        (pv("Hidden", True), pv("ReadOnly", False)))
    try:
        # Order matters: text fields first so SEQ counters settle, then the
        # indexes that quote them.
        try:
            doc.getTextFields().refresh()
        except Exception:
            pass
        try:
            idx = doc.getDocumentIndexes()
            for i in range(idx.getCount()):
                idx.getByIndex(i).update()
        except Exception:
            pass
        try:
            doc.refresh()
        except Exception:
            pass

        doc.storeToURL(uno.systemPathToFileUrl(str(dst.resolve())),
                       (pv("FilterName", "writer_pdf_Export"),))
    finally:
        try:
            doc.close(False)
        except Exception:
            pass


def fallback(src: Path, outdir: Path) -> bool:
    """Plain conversion — fields keep their stale values, so warn loudly."""
    exe = soffice_bin()
    if not exe:
        return False
    try:
        subprocess.run([exe, "--headless", "--convert-to", "pdf",
                        "--outdir", str(outdir), str(src)],
                       check=True, capture_output=True, timeout=300)
        return True
    except Exception:
        return False


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import srslib as S
    S.utf8_stdio()
    ap = argparse.ArgumentParser(description="Xuất PDF có cập nhật trường.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--outdir", default=None)
    a = ap.parse_args()

    files = [Path(f) for f in a.files]
    outdir = Path(a.outdir) if a.outdir else files[0].parent
    outdir.mkdir(parents=True, exist_ok=True)

    # `/tmp` does not exist on Windows; gettempdir() resolves to whatever the
    # platform actually uses (%TEMP%, $TMPDIR, /tmp).
    profile = Path(tempfile.gettempdir()) / f"lo-{uuid.uuid4().hex[:8]}"
    port = free_port()
    proc = start_soffice(profile, port)
    if proc is None:
        print("LỖI: không tìm thấy LibreOffice.", file=sys.stderr)
        return 1

    rc = 0
    try:
        ctx = connect(port)
        for f in files:
            dst = outdir / (f.stem + ".pdf")
            refresh_and_export(ctx, f, dst)
            print(f"OK -> {dst}")
    except Exception as e:
        print(f"Cầu UNO không dùng được ({e}); chuyển sang cách thường.",
              file=sys.stderr)
        for f in files:
            if fallback(f, outdir):
                print(f"OK -> {outdir / (f.stem + '.pdf')}")
                print("  CẢNH BÁO: trường SEQ/TOC KHÔNG được cập nhật. Số hiệu "
                      "Hình/Bảng trong PDF có thể sai — mở bằng Word, Ctrl+A, "
                      "F9 rồi xuất lại nếu cần bản chính thức.")
            else:
                print(f"LỖI: không xuất được {f}", file=sys.stderr)
                rc = 1
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=20)
        except Exception:
            proc.kill()
        shutil.rmtree(profile, ignore_errors=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
