#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
srslib.py — Shared helpers for the srs-help skill.

Everything that touches the document model lives here so scaffold / validate /
render / import cannot drift apart. The outline is the single source of truth;
no script hardcodes a section name.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
OUTLINE_PATH = SKILL_DIR / "references" / "outline.json"
BASE_DOCX = SKILL_DIR / "assets" / "base.docx"


def utf8_stdio() -> None:
    """Make stdout/stderr UTF-8 with replacement, whatever the console is.

    Every script prints Vietnamese; on a default Windows PowerShell the
    console encoding is cp1252, which cannot encode "LỖI", so the very first
    finding crashes the run with UnicodeEncodeError. The eval suite masked
    this by exporting PYTHONUTF8=1 for its children — the direct CLI had no
    such cover. Call this first in every entry point's main().
    """
    import sys as _sys
    for stream in (_sys.stdout, _sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass  # non-reconfigurable stream (pytest capture, pipes on old versions)

DIAGRAM_RE = re.compile(r"\[\[DIAGRAM:\s*([^\]]+?)\s*\]\]")
UCDIAGRAM_RE = re.compile(r"\[\[UCDIAGRAM:\s*([^\]]+?)\s*\]\]")
IMAGE_RE = re.compile(r"!\[(?P<cap>[^\]]*)\]\((?P<path>[^)]+)\)")
FEATURE_H_RE = re.compile(r"^##\s+Tính năng\s*\[(?P<ma>[^\]]+)\]\s*(?P<ten>.*)$")


# ---------------------------------------------------------------------------
# Outline
# ---------------------------------------------------------------------------
def load_outline(path: str | Path | None = None) -> dict:
    return json.loads(Path(path or OUTLINE_PATH).read_text(encoding="utf-8"))


CONFIG_NAMES = ("srs-config.json", ".srs/config.json")


def find_config(start: Path, explicit: str | None = None) -> tuple[dict, Path | None]:
    """Locate the project config by walking up from the spec file.

    Deliberately NOT bundled in the skill: organisation name, project name and
    logo belong to a project, not to the standard. A skill shipping one
    company's logo would silently brand every other project's documents.
    """
    if explicit:
        p = Path(explicit)
        return json.loads(p.read_text(encoding="utf-8")), p
    here = Path(start).resolve()
    for d in [here if here.is_dir() else here.parent, *here.parents]:
        for name in CONFIG_NAMES:
            p = d / name
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8")), p
    return {}, None


GROUP = "GROUP"


def profile_of(outline: dict, name: str) -> dict:
    """Return a profile spec. The group document is normalised to the same
    shape so scaffold / validate / render / import need no special casing.

    A group has no feature tier and its section labels are bold body text
    rather than headings: the group title sits at Heading 2 and Heading 3 is
    already taken by the function titles nested under it, so headings would
    collide.
    """
    if name == GROUP:
        return {
            "ten": "Nhóm chức năng",
            "has_features": False,
            "require_diagram": False,
            "is_group": True,
            "function_sections": [],
            "feature_sections": [],
        }
    p = outline["profiles"].get(name)
    if p is None:
        raise KeyError(
            f"Loại '{name}' không có trong đề cương. "
            f"Hợp lệ: {', '.join(outline['profile_order'])}, {GROUP}")
    return dict(p, is_group=False)


def section_index(profile: dict) -> dict[str, dict]:
    """name -> section spec, across both levels."""
    out = {}
    for s in profile["function_sections"] + profile["feature_sections"]:
        out[s["name"]] = s
    return out


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def strip_accents(s: str) -> str:
    s = s.replace("Đ", "D").replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def slug(s: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", strip_accents(s).lower()).strip("-")
    return re.sub(r"-+", "-", s)[:maxlen]


def norm(s: str) -> str:
    """Normalise a heading for comparison: collapse whitespace, strip markers."""
    s = unicodedata.normalize("NFC", s or "")
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# Document model
# ---------------------------------------------------------------------------
@dataclass
class Block:
    """One piece of content inside a section."""
    kind: str                       # para | bullet | table | image | diagram | note
    text: str = ""
    level: int = 1                  # bullet depth
    rows: list[list[str]] = field(default_factory=list)   # table incl. header
    label: str = ""                 # table label / image caption
    path: str = ""                  # image path
    code: str = ""                  # diagram code


@dataclass
class Section:
    name: str
    blocks: list[Block] = field(default_factory=list)

    def text_content(self) -> str:
        parts = []
        for b in self.blocks:
            if b.kind in ("para", "bullet"):
                parts.append(b.text)
            elif b.kind == "table":
                # Columns the scaffold fills on its own do not count as
                # content: a key/value table arrives with its label column
                # already written, and an `STT` column now arrives numbered.
                # Counting either would make an untouched section look
                # complete and silence the "mục để trống" check.
                head = [c.strip() for c in b.rows[0]] if b.rows else []
                skip = 1 if head[:2] == ["Hạng mục", "Nội dung"] else 0
                if head[:1] == [STT_HEADER]:
                    skip = 1
                parts += [c for r in b.rows[1:] for c in r[skip:]]
        return " ".join(p for p in parts if p).strip()

    def is_empty(self) -> bool:
        return not self.text_content() and not any(
            b.kind in ("image", "diagram") for b in self.blocks)


@dataclass
class Feature:
    ma: str
    ten: str
    sections: list[Section] = field(default_factory=list)


@dataclass
class FunctionDoc:
    meta: dict = field(default_factory=dict)
    sections: list[Section] = field(default_factory=list)
    features: list[Feature] = field(default_factory=list)
    source: Path | None = None

    @property
    def profile(self) -> str:
        return self.meta.get("profile", "")

    @property
    def ma(self) -> str:
        return self.meta.get("ma", "")

    def section(self, name: str) -> Section | None:
        n = norm(name)
        return next((s for s in self.sections if norm(s.name) == n), None)


# ---------------------------------------------------------------------------
# Front matter
# ---------------------------------------------------------------------------
def _scalar(v: str):
    v = v.strip()
    if v.startswith(("'", '"')) and v.endswith(("'", '"')) and len(v) > 1:
        return v[1:-1]
    if v in ("true", "false"):
        return v == "true"
    return v


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Minimal YAML subset: scalars, and `changelog:` as a list of {k: v} maps.

    A full YAML parser is not assumed to be installed, and the front matter
    shape here is fixed by the template, so a strict small parser gives better
    error messages than a permissive general one.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("Front matter mở bằng --- nhưng không có --- đóng.")
    raw = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")

    meta: dict = {}
    cur_list: list | None = None
    for lineno, line in enumerate(raw.split("\n"), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if cur_list is None:
                raise ValueError(f"Dòng {lineno}: mục danh sách không có khoá cha.")
            item_raw = line[4:].strip()
            if item_raw.startswith("{") and item_raw.endswith("}"):
                item = {}
                for part in _split_top(item_raw[1:-1]):
                    if ":" not in part:
                        raise ValueError(f"Dòng {lineno}: thiếu ':' trong '{part}'.")
                    k, v = part.split(":", 1)
                    item[k.strip()] = _scalar(v)
                cur_list.append(item)
            else:
                cur_list.append(_scalar(item_raw))
            continue
        if line.startswith(" "):
            raise ValueError(f"Dòng {lineno}: thụt lề không hợp lệ ({line!r}).")
        if ":" not in line:
            raise ValueError(f"Dòng {lineno}: thiếu dấu ':' ({line!r}).")
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v == "":
            cur_list = []
            meta[k] = cur_list
        else:
            meta[k] = _scalar(v)
            cur_list = None
    return meta, body


def _split_top(s: str) -> list[str]:
    """Split on commas not inside quotes."""
    out, buf, q = [], "", ""
    for ch in s:
        if q:
            if ch == q:
                q = ""
            buf += ch
        elif ch in "'\"":
            q = ch
            buf += ch
        elif ch == ",":
            out.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        out.append(buf)
    return out


def dump_front_matter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                if isinstance(item, dict):
                    inner = ", ".join(f"{ik}: {_q(iv)}" for ik, iv in item.items())
                    lines.append(f"  - {{{inner}}}")
                else:
                    lines.append(f"  - {_q(item)}")
        else:
            lines.append(f"{k}: {_q(v)}")
    lines.append("---")
    return "\n".join(lines)


def _q(v) -> str:
    s = str(v)
    return f'"{s}"' if (":" in s or "," in s or s.strip() != s or s == "") else s


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------
def _table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _is_sep(line: str) -> bool:
    return bool(re.fullmatch(r"\|?[\s:|-]+\|?", line.strip())) and "-" in line


GROUP_DESC = "Mô tả nhóm"


def parse_markdown(text: str, source: Path | None = None) -> FunctionDoc:
    meta, body = parse_front_matter(text)
    doc = FunctionDoc(meta=meta, source=source)
    is_group = meta.get("profile") == GROUP

    cur_sec: Section | None = None
    cur_feat: Feature | None = None
    pending_label = ""
    lines = body.split("\n")
    i = 0

    def target() -> list[Section]:
        return cur_feat.sections if cur_feat is not None else doc.sections

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue

        if stripped.startswith("## "):
            m = FEATURE_H_RE.match(stripped)
            if m:
                cur_feat = Feature(ma=m.group("ma").strip(),
                                   ten=m.group("ten").strip())
                doc.features.append(cur_feat)
                cur_sec = None
            else:
                cur_feat = None
                cur_sec = Section(name=norm(stripped[3:]))
                doc.sections.append(cur_sec)
            pending_label = ""
            i += 1
            continue

        if stripped.startswith("### "):
            cur_sec = Section(name=norm(stripped[4:]))
            target().append(cur_sec)
            pending_label = ""
            i += 1
            continue

        if cur_sec is None:
            if is_group and stripped and not stripped.startswith(("#", ">")):
                # A group carries only a short description under its heading;
                # there are no subsections to attach it to.
                cur_sec = Section(name=GROUP_DESC)
                doc.sections.append(cur_sec)
            else:
                i += 1
                continue

        # guidance blockquote — instructions to the BA, never document content
        if stripped.startswith(">"):
            cur_sec.blocks.append(Block("note", text=stripped.lstrip("> ").strip()))
            i += 1
            continue

        if not stripped or stripped == "---":
            i += 1
            continue

        m = IMAGE_RE.fullmatch(stripped)
        if m:
            cur_sec.blocks.append(Block("image", label=m.group("cap"),
                                        path=m.group("path")))
            i += 1
            continue

        m = DIAGRAM_RE.fullmatch(stripped)
        if m:
            cur_sec.blocks.append(Block("diagram", code=m.group(1)))
            i += 1
            continue
        m = UCDIAGRAM_RE.fullmatch(stripped)
        if m:
            # Kept only to recognise legacy files. Use-case diagrams for groups
            # were dropped: a group is a menu tier, not a document. Silently
            # ignoring the marker would leave the BA wondering where the image
            # went, so it is tagged and reported.
            cur_sec.blocks.append(Block("obsolete", code=m.group(1),
                                        text="ucdiagram"))
            i += 1
            continue

        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not _is_sep(lines[i]):
                    rows.append(_table_row(lines[i]))
                i += 1
            if rows:
                cur_sec.blocks.append(Block("table", rows=rows, label=pending_label))
            pending_label = ""
            continue

        if stripped.startswith(("- ", "+ ", "* ")):
            # Depth by leading whitespace: 0 / 2 / 4 spaces (a tab counts as
            # one step). Deeper than three levels almost always means the
            # section itself should have been split.
            lead = len(line) - len(line.lstrip(" \t"))
            if line[:lead].count("\t"):
                depth = min(3, line[:lead].count("\t") + 1)
            else:
                depth = 3 if lead >= 4 else (2 if lead >= 2 else 1)
            cur_sec.blocks.append(Block("bullet", text=stripped[2:].strip(),
                                        level=depth))
            i += 1
            continue

        if stripped.startswith("**") and stripped.endswith("**"):
            pending_label = stripped.strip("*").strip()
            cur_sec.blocks.append(Block("tlabel", text=pending_label))
            i += 1
            continue

        cur_sec.blocks.append(Block("para", text=stripped))
        i += 1

    return doc


def read_markdown(path: str | Path) -> FunctionDoc:
    p = Path(path)
    return parse_markdown(p.read_text(encoding="utf-8"), source=p)


# ---------------------------------------------------------------------------
# Multi-line table cells
# ---------------------------------------------------------------------------
BULLET_MARK = "·"
_CELL_SPLIT = re.compile(r"\s*(·+)\s*")


def multiline_spec(outline: dict) -> dict:
    return outline.get("multiline_columns") or {}


def cell_segments(val: str) -> list[tuple[str, int]]:
    """`(text, level)` for a cell, where level 0 is ordinary prose.

    A markdown table row cannot span source lines, so the `·` marks carry the
    structure that Word will show as real bullets. One source line either way;
    only the rendered document changes.
    """
    toks = _CELL_SPLIT.split(val)
    out: list[tuple[str, int]] = []
    head = toks[0].strip()
    if head:
        out.append((head, 0))
    for i in range(1, len(toks) - 1, 2):
        text = toks[i + 1].strip()
        if text:
            out.append((text, len(toks[i])))
    return out


def cell_is_multiline(val: str) -> bool:
    return any(lv for _, lv in cell_segments(val))


# ---------------------------------------------------------------------------
# Table spacing
# ---------------------------------------------------------------------------
def table_spacing_faults(text: str) -> list[tuple[int, str]]:
    """Lines where a table touches other content with no blank line between.

    This parser tolerates the missing blank line, which is exactly why it has
    to be reported: every *other* markdown reader does not. In CommonMark a
    table ends at the first blank line, so content pressed against it is
    absorbed — `### Thiết kế giao diện` becomes a new row with the `###` shown
    literally in column one, and a paragraph before a table stops the table
    from rendering at all.

    The `.md` is the source of truth and gets reviewed on GitHub, in an editor
    preview, anywhere. A file that only renders correctly inside this skill is
    a trap, so the fault is reported even though nothing here breaks.
    """
    lines = text.split("\n")
    out: list[tuple[int, str]] = []

    def is_row(s: str) -> bool:
        return s.lstrip().startswith("|")

    for i in range(len(lines) - 1):
        cur, nxt = lines[i], lines[i + 1]
        if is_row(cur) and nxt.strip() and not is_row(nxt):
            out.append((i + 2, f"dòng {i + 2} `{nxt.strip()[:44]}` dính ngay "
                               f"sau bảng — trình markdown khác sẽ hút nó vào "
                               f"ô cuối bảng"))
        elif not is_row(cur) and cur.strip() and is_row(nxt):
            out.append((i + 1, f"dòng {i + 1} `{cur.strip()[:44]}` dính ngay "
                               f"trước bảng — trình markdown khác sẽ không "
                               f"dựng được bảng"))
    return out


def normalize_table_spacing(text: str) -> tuple[str, int]:
    """Insert the blank lines `table_spacing_faults` complains about."""
    lines = text.split("\n")
    out: list[str] = []
    fixed = 0

    def is_row(s: str) -> bool:
        return s.lstrip().startswith("|")

    for i, cur in enumerate(lines):
        prev = out[-1] if out else ""
        if is_row(cur) and prev.strip() and not is_row(prev):
            out.append("")
            fixed += 1
        elif (not is_row(cur) and cur.strip()
                and prev.strip() and is_row(prev)):
            out.append("")
            fixed += 1
        out.append(cur)
    return "\n".join(out), fixed


# ---------------------------------------------------------------------------
# Extracted images
# ---------------------------------------------------------------------------
# Word stores a picture's file type in the package part, not in the name it
# shows. Guessing from the alt-text produced extension-less files that landed
# in the output document as `media/image2.` — so map the content type instead.
IMAGE_EXT = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
    "image/bmp": ".bmp", "image/tiff": ".tif", "image/svg+xml": ".svg",
    "image/x-emf": ".emf", "image/x-wmf": ".wmf",
    "image/emf": ".emf", "image/wmf": ".wmf",
}
# Vector formats Word accepts but that cannot be re-embedded as a picture
# without conversion. Reported rather than dropped: a silent skip looks like
# the document simply had fewer images.
VECTOR_EXT = {".emf", ".wmf"}

_CAPTION_PREFIX = re.compile(r"^\s*(figure|hình|hinh|bảng|bang|table)"
                             r"\s*\d*\s*[.:–—-]*\s*", re.I)


def section_number(counters: list[int], base_level: int,
                   deepest: int) -> str:
    """`1.5.3` from the heading counters, trimmed to the levels in play.

    A child file starts at `Heading 3`, so counting from level 1 yields
    `0.0.1.5` — two leading zeros for headings the file does not contain.
    Trimming to the shallowest level actually present gives the number the
    analyst sees on screen.

    The result is relative to this file: once merged into the master document
    the same section sits somewhere else. It locates content for review; it is
    not the published section number.
    """
    if deepest < base_level:
        return ""
    return ".".join(str(counters[i]) for i in range(base_level - 1, deepest))


def image_name(seq: int, sec_num: str, caption: str, context: str,
               ext: str, maxlen: int = 46) -> str:
    """`006_1.5.4_giao-dien-them-moi.png`.

    Ordinal first so the folder sorts in document order; section number next
    so the analyst can find where it came from; then words.

    The words come from the caption when there is one, because the nearest
    heading is nearly useless here: in this outline every mockup sits under
    *Thiết kế giao diện*, so naming by heading gave fifteen files called
    `thiet-ke-giao-dien` distinguishable only by their number. The fallback is
    the enclosing feature or function title, which does distinguish them.
    """
    words = _CAPTION_PREFIX.sub("", caption or "").strip() or context or ""
    tail = slug(words, maxlen) if words else ""
    parts = [f"{seq:03d}"]
    if sec_num:
        parts.append(sec_num)
    if tail:
        parts.append(tail)
    return "_".join(parts) + ext


@dataclass
class ImageHit:
    """One picture in a .docx, with where it sat and what it is."""
    seq: int
    rel_id: str
    sec_num: str = ""
    heading: str = ""
    context: str = ""       # enclosing feature/function title
    caption: str = ""
    name: str = ""          # filename decided later
    ext: str = ""
    size: int = 0


def scan_images(doc, styles: dict) -> list[ImageHit]:
    """Every picture in document order, with its section context.

    Walks the body itself rather than `doc.paragraphs`, because pictures sit
    inside table cells too and those never appear in the paragraph list.

    Section numbers are computed from the heading sequence: this document's
    headings carry no number at all, in the text or on the paragraph — Word
    draws them from numbering attached to the *styles*. Same family as the
    `STT` column and the bullet marks: what Word renders is not what the file
    stores, so it has to be recomputed rather than read.
    """
    from docx.oxml.ns import qn as _qn
    from docx.text.paragraph import Paragraph

    counters = [0] * 10
    stack: dict[int, str] = {}
    base = None
    cap_style = styles.get("caption", "Caption")
    pending_caption = ""
    out: list[ImageHit] = []
    seq = 0

    def context_of() -> str:
        for lvl in sorted(stack, reverse=True):
            t = stack[lvl]
            if "Tính năng" in t or "Chức năng" in t:
                m = re.search(r"\]\s*(.+)", t)
                return (m.group(1) if m else t).strip()
        return stack[max(stack)].strip() if stack else ""

    def collect(el, caption=""):
        nonlocal seq
        for docPr in el.iter(_qn("wp:docPr")):
            blip = None
            holder = docPr.getparent().getparent()
            for b in holder.iter(_qn("a:blip")):
                blip = b.get(_qn("r:embed"))
                break
            if not blip:
                continue
            seq += 1
            out.append(ImageHit(
                seq=seq, rel_id=blip,
                sec_num=section_number(counters, base or 1,
                                       max(stack) if stack else 0),
                heading=stack[max(stack)] if stack else "",
                context=context_of(), caption=caption))

    for ch in doc.element.body.iterchildren():
        if ch.tag == _qn("w:p"):
            p = Paragraph(ch, doc)
            style = p.style.name or ""
            m = re.fullmatch(r"Heading (\d)", style)
            if m and p.text.strip():
                lvl = int(m.group(1))
                base = lvl if base is None else min(base, lvl)
                counters[lvl - 1] += 1
                for k in range(lvl, 10):
                    counters[k] = 0
                stack[lvl] = p.text.strip()
                for k in [x for x in stack if x > lvl]:
                    del stack[k]
            if style == cap_style and p.text.strip():
                pending_caption = p.text.strip()
                continue
            collect(ch, pending_caption)
            if list(ch.iter(_qn("wp:docPr"))):
                pending_caption = ""
        elif ch.tag == _qn("w:tbl"):
            collect(ch)
    return out


def unique_path(folder, name: str, blob: bytes | None = None):
    """`name`, or `name-2`, `name-3`… if taken. Never overwrites.

    Overwriting is how nineteen extracted images became two files on disk
    while the run still reported nineteen: Word's default alt-text is
    `Picture 1` for almost every image, and each write clobbered the last.

    Identical content is the exception: re-importing a document back into the
    project it was rendered from must land on the same filenames, or the `.md`
    starts pointing at `…-2.png` and the round trip stops being a round trip.
    """
    p = folder / name
    if not p.exists():
        return p
    if blob is not None and p.read_bytes() == blob:
        return p
    stem, ext = name.rsplit(".", 1) if "." in name else (name, "")
    dot = "." + ext if ext else ""
    n = 2
    while (folder / f"{stem}-{n}{dot}").exists():
        n += 1
    return folder / f"{stem}-{n}{dot}"


def embedded_objects(src) -> list[dict]:
    """OLE objects embedded in a .docx — a Visio drawing, a spreadsheet, an
    attached file.

    They are not pictures and `scan_images` does not see them: what sits in the
    document is a `w:object` whose visible part is an EMF *preview*, with the
    real payload in `word/embeddings/`. Reporting them matters because the
    analyst sees a diagram on screen and expects it to come across; saying
    nothing makes the new document look like it simply lost content.
    """
    import re as _re
    import zipfile
    out = []
    try:
        with zipfile.ZipFile(src) as z:
            body = z.read("word/document.xml").decode("utf-8")
            rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    except Exception:
        return out
    rmap = dict(_re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
    for blk in _re.findall(r"<w:object.*?</w:object>", body, _re.S):
        img = _re.search(r'v:imagedata[^>]*r:id="([^"]+)"', blk)
        prog = _re.search(r'ProgID="([^"]*)"', blk)
        out.append({
            "preview": rmap.get(img.group(1), "") if img else "",
            "progid": prog.group(1) if prog else "",
        })
    return out


def save_images(doc, hits: list[ImageHit], folder) -> tuple[list, list]:
    """Write every hit to `folder`. Returns (saved, vector) — vector formats
    are listed, not written, because they cannot be re-embedded as pictures.
    """
    folder.mkdir(parents=True, exist_ok=True)
    saved, vector = [], []
    for h in hits:
        try:
            part = doc.part.related_parts[h.rel_id]
        except KeyError:
            continue
        ext = IMAGE_EXT.get(getattr(part, "content_type", ""), "")
        if not ext:
            ext = Path(str(getattr(part, "partname", ""))).suffix or ".bin"
        h.ext = ext
        h.size = len(part.blob)
        h.name = image_name(h.seq, h.sec_num, h.caption, h.context, ext)
        if ext in VECTOR_EXT:
            vector.append(h)
            continue
        dst = unique_path(folder, h.name, part.blob)
        dst.write_bytes(part.blob)
        h.name = dst.name
        saved.append(h)
    return saved, vector


# ---------------------------------------------------------------------------
# Derived table columns
# ---------------------------------------------------------------------------
STT_HEADER = "STT"


def _is_label_row(row: list[str]) -> bool:
    """A band across the table rather than a data row.

    In Word these are cells merged across every column ("Các trường thông
    tin", "Các button"). They are dividers: they carry no ordinal and must not
    consume one, or every number after them is off by one.

    Two shapes, because both exist in the wild. Files imported before merged
    spans were de-duplicated repeat the same text in every column. Files
    imported since carry the label in the first column with the rest blank —
    which a data row never looks like, since in an `STT` table the first
    column holds a number and the content sits to its right.
    """
    vals = [c.strip() for c in row]
    filled = [v for v in vals if v]
    if len(filled) > 1 and len(set(filled)) == 1:
        return True
    return len(filled) == 1 and bool(vals[0]) and not vals[0].isdigit()


def renumber_stt(rows: list[list[str]]) -> list[list[str]]:
    """Fill column 0 with 1..n when the table's first column is `STT`.

    STT is a derived value — the row's position, nothing more — and the
    standard already refuses hand-numbering for sections, figures and tables
    for the same reason. Leaving it to hand also broke import: a legacy spec
    numbered its rows with Word's own list numbering, which lives in
    `numbering.xml` and never appears in the cell text, so 260 visible numbers
    read back as empty strings and there was nothing to carry across.

    Rewrites a copy. Cells holding text that is not a number are left alone —
    an analyst who wrote something there meant it.
    """
    if not rows or not rows[0] or norm(rows[0][0]) != STT_HEADER:
        return rows
    out = [list(rows[0])]
    n = 0
    for row in rows[1:]:
        row = list(row)
        if not row:
            out.append(row)
            continue
        if _is_label_row(row) or not " ".join(row).strip():
            out.append(row)
            continue
        cur = row[0].strip()
        if cur == "" or cur.isdigit():
            n += 1
            row[0] = str(n)
        # else: real text in the STT cell — the BA put it there on purpose.
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# Codes
# ---------------------------------------------------------------------------
CODE_PATTERNS = {
    "FUNC": re.compile(r"^FUNC-[A-Z]{3,6}-\d{3}$"),
    "FEAT": re.compile(r"^FEAT-[A-Z]{3,6}-\d{3}-\d{2}$"),
    "BR": re.compile(r"^BR-[A-Z]{3,6}-\d{3}-\d{3}$"),
    "MH": re.compile(r"^MH-[A-Z]{3,6}-\d{3}-\d{3}$"),
    "GRP": re.compile(r"^GRP-[A-Z]{3,6}-\d{2}$"),
    "UC": re.compile(r"^UC-\d{4}$"),
    "MSG": re.compile(r"^(ERR|WAR|INF|SUC|CONF|MAIL)_\d{3}$"),
    "ST": re.compile(r"^ST-[A-Z0-9]+-\d{2}$"),
    "ROLE": re.compile(r"^ROLE-[A-Z0-9]+$"),
}

CODE_SHAPES = {
    "FUNC": "FUNC-«phân hệ 3–6 chữ hoa»-«3 số»",
    "FEAT": "FEAT-«phân hệ»-«số chức năng 3 số»-«2 số»",
    "BR": "BR-«phân hệ»-«số chức năng 3 số»-«3 số»",
    "MH": "MH-«phân hệ»-«số chức năng 3 số»-«3 số»",
    "GRP": "GRP-«phân hệ»-«2 số»",
    "UC": "UC-«4 số»",
    "MSG": "«LOẠI»_«3 số» (LOẠI: ERR/WAR/INF/SUC/CONF/MAIL, không có đoạn phân hệ ở giữa)",
    "ST": "ST-«đối tượng viết hoa»-«2 số»",
    "ROLE": "ROLE-«mã», khớp roles.csv",
}

# Loose companions to CODE_PATTERNS: right prefix, permissive body AND
# permissive separator. Used only to *notice* a token that is probably a code
# but shaped wrong — `find_codes` below extracts nothing for these, so without
# this every typo reads as if the reference simply did not exist.
#
# The separator has to be permissive, not just the body. An earlier version
# pinned `_` for MSG and `-` for the rest, which meant a document written with
# the other convention was invisible in bulk rather than one token at a time:
# a real 2 900-cell legacy spec carried 104 references in `ERR-001` form and
# the validator reported zero message codes in it — every registry check, every
# declared-vs-referenced check, silently inert on the one document that most
# needed them. `SEP` therefore covers hyphen, underscore, space and nothing.
#
# Two separators, not one, and the difference matters. The FIRST one may be a
# space (`ERR 001`) or absent (`ERR001`). Every LATER one must be a real
# hyphen or underscore. Allowing a space to continue a match let the pattern
# reach past the end of a perfectly valid code into whatever followed it:
# `BR-QLNSD-001-006 3` — where the `3` was the next table cell — matched whole
# and was then reported as malformed, in a file that was in fact clean.
_SEP_FIRST = r"(?:[-_]| (?=\d))?"
_SEP_CONT = r"[-_]"
_GRP = r"[A-Za-z0-9]+"


def _loose(prefix: str) -> re.Pattern:
    """Prefix, one loosely attached group, then strictly separated groups."""
    return re.compile(r"\b" + prefix + _SEP_FIRST + _GRP
                      + r"(?:" + _SEP_CONT + _GRP + r")*\b")


LOOSE_CODE_PATTERNS = {
    "FUNC": _loose("FUNC"),
    "FEAT": _loose("FEAT"),
    "BR": _loose("BR"),
    "MH": _loose("MH"),
    "GRP": _loose("GRP"),
    "UC": _loose("UC"),
    "MSG": _loose(r"(?:ERR|WAR|INF|SUC|CONF|MAIL)"),
    "ST": _loose("ST"),
    "ROLE": _loose("ROLE"),
}

# Words that begin with a code prefix but are ordinary text. Without this the
# loose MSG pattern flags every "INFORMATION" and the loose ST pattern every
# "STT" — noise that would train the BA to ignore the whole category.
_LOOSE_STOPWORDS = re.compile(
    r"^(?:STT|ST|STATUS|STRING|INFO|INFORMATION|BR|BRD|UC|GRP|MH|ERR|ERROR|"
    r"WAR|WARNING|SUC|CONF|CONFIG|CONFIRM|MAIL|FUNC|FUNCTION|FEAT|FEATURE|"
    r"ROLE)$", re.I)


def find_codes(text: str, kind: str) -> list[str]:
    pat = {
        "FUNC": r"FUNC-[A-Z]{3,6}-\d{3}",
        "FEAT": r"FEAT-[A-Z]{3,6}-\d{3}-\d{2}",
        "BR": r"BR-[A-Z]{3,6}-\d{3}-\d{3}",
        "MH": r"MH-[A-Z]{3,6}-\d{3}-\d{3}",
        "UC": r"UC-\d{4}",
        "MSG": r"(?:ERR|WAR|INF|SUC|CONF|MAIL)_\d{3}",
        "ST": r"ST-[A-Z0-9]+-\d{2}",
        "ROLE": r"ROLE-[A-Z0-9]+",
    }[kind]
    return re.findall(pat, text)


def find_malformed_codes(text: str, kind: str) -> list[str]:
    """Tokens matching the loose shape for `kind` but not the strict one —
    right prefix, wrong body or wrong separator. Order-preserving, deduped."""
    strict = CODE_PATTERNS[kind]
    loose = LOOSE_CODE_PATTERNS[kind]
    seen: list[str] = []
    for m in loose.finditer(text):
        tok = m.group(0)
        if strict.match(tok) or _LOOSE_STOPWORDS.match(tok) or tok in seen:
            continue
        # A token that is a well-formed code of *another* kind is that kind's
        # business, not a malformed one of this kind: `ST-NGUOIDUNG-01` must
        # not also be reported as a broken `ST` because the loose `MSG`
        # pattern happened to reach into it.
        if any(p.match(tok) for k, p in CODE_PATTERNS.items() if k != kind):
            continue
        seen.append(tok)
    return seen


def suggest_code_fix(token: str, kind: str) -> str | None:
    """Rewrite `token` into the strict shape when the only fault is the
    separator — the common case in specs written before the convention.

    Returning the corrected code, not just "wrong shape", is what makes a
    hundred occurrences fixable with one find-and-replace per code.
    """
    parts = [p for p in re.split(r"[-_ ]+", token) if p]
    if not parts:
        return None
    # `ERR001` — no separator at all. Split where letters meet digits so the
    # glued form is repairable too; it is the same authoring habit as the
    # wrong-separator form, just one step further.
    if len(parts) == 1:
        m = re.fullmatch(r"([A-Za-z]+)(\d+)", parts[0])
        if m:
            parts = [m.group(1), m.group(2)]
    joiner = "_" if kind == "MSG" else "-"
    cand = joiner.join(parts)
    if kind == "MSG" and len(parts) == 2 and parts[1].isdigit():
        cand = f"{parts[0].upper()}_{int(parts[1]):03d}"
    elif kind == "UC" and len(parts) == 2 and parts[1].isdigit():
        cand = f"UC-{int(parts[1]):04d}"
    return cand if CODE_PATTERNS[kind].match(cand) else None


def known_kind(outline: dict, name: str) -> bool:
    return name == GROUP or name in outline["profiles"]


def all_kinds(outline: dict) -> list[str]:
    return list(outline["profile_order"]) + [GROUP]


def code_pattern(kind: str) -> re.Pattern:
    return CODE_PATTERNS["GRP" if kind == GROUP else "FUNC"]


def code_shape(kind: str) -> str:
    return ("GRP-«phân hệ»-«2 số»" if kind == GROUP
            else "FUNC-«phân hệ»-«3 số»")


def feature_code(func_code: str, n: int) -> str:
    parts = func_code.split("-")
    return f"FEAT-{parts[1]}-{parts[2]}-{n:02d}"


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    level: str          # error | warn | info
    where: str
    message: str

    def __str__(self) -> str:
        tag = {"error": "LỖI ", "warn": "CẢNH", "info": "TIN "}[self.level]
        return f"[{tag}] {self.where}: {self.message}"


# ---------------------------------------------------------------------------
# Content hash
# ---------------------------------------------------------------------------
def content_sha(texts) -> str:
    """Hash over the document's visible text, in order.

    Hashing the .docx bytes would not work: the file is zipped with timestamps
    and Word rewrites internals on every save, so byte equality fails even when
    nothing was edited. Hashing the text catches exactly what we care about —
    somebody changing wording inside Word.
    """
    import hashlib
    h = hashlib.sha256()
    for t in texts:
        t = norm(t)
        if t:
            h.update(t.encode("utf-8"))
            h.update(b"\x1f")
    return h.hexdigest()[:16]
