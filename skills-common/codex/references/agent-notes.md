# Agent notes — operational detail

Moved out of SKILL.md so it loads only when the situation calls for it. Each
section is self-contained; read the one you need.

## Groups (GRP-)

`GRP-` sits between the subsystem and the functions and **mirrors the
application's menu tree** — it is not the analyst's own way of grouping things.

```
Phân hệ HTVH
  └─ GRP-HTVH-01  Người dùng & Phân quyền     ← what the user sees in the menu
       ├─ FUNC-HTVH-005  Quản lý người dùng
       └─ FUNC-HTVH-010  Quản lý nhóm quyền
```

A group file is **a Heading 2 and, if genuinely useful, two or three sentences
styled `T-GhiChu`**. No sections, no tables, no diagrams. In a group file
`T-GhiChu` is the content itself, not guidance to be dropped on import; in a
function file it is guidance and is dropped.

Do not offer to add a scope table, an actor list, or a use-case diagram to a
group — the detail lives one level down, and duplicating it creates a second
place to keep in sync. Use-case diagrams for groups were **removed** from the
standard; a file still carrying `[[UCDIAGRAM: …]]` is from the earlier version
and `validate.py` reports it as an error.

## PHANTICH specifics

`PHANTICH` is flat: one use case is one report is one form, so a repeating
feature block would almost always hold exactly one entry. Indicators are rows
in *Danh mục chỉ tiêu* instead. Its *Ma trận phân quyền* and *Truy vết yêu
cầu* tables therefore differ from the other profiles': no `Mã tính năng`, no
`Tính năng đáp ứng` — permissions are declared per operation (chạy / xem trước
/ kết xuất) and use cases point straight at the function. Check `has_features`
in the outline rather than assuming.

## Where assets and diagrams live

`assets/…` and `diagrams/…` resolve against **the folder holding the `.md`**,
not the project root (`root = src.parent` in `render.py`). So the layout is:

```
du-an/
├── registries/                 ← shared, passed via --registry-dir
├── srs-config.json             ← found by walking up
├── project-rules/srs-help.md   ← optional project overlay, read after SKILL.md
└── functions/qlnsd/            ← subsystem folder lowercase, codes stay upper
    ├── FUNC-QLNSD-001.md
    ├── assets/                 ← beside the .md, not at the root
    └── diagrams/
```

Three naming rules the project depends on, and the reason each exists:

- **Subsystem folder lowercase, code uppercase** (`functions/qlnsd/FUNC-QLNSD-001.md`).
  Windows is case-insensitive, so mixing `qlnsd` and `QLNSD` works on the
  analyst's machine and splits into two folders elsewhere.
- **The registry folder is `registries/`, no alternative name.** A project that
  used another name and later gained an empty `registries/` beside it — which
  is what BA Toolkit's `init` creates — would pass every schema check against
  the empty set. `project_check.py` treats another name as an error for that
  reason, not for tidiness.
- **`.docx`/`.pdf` go to `exports/`.** Derived output; leaving it in
  `functions/` hides which file is the source.

A project may also carry BA Toolkit folders (`.ba-toolkit/`, `sources/`,
`staging/`, `migration/`, `reports/`). They change nothing here:
`project_check.py` scores only `functions/` and reports how many files it
declined to judge.

Getting this wrong fails quietly: mockups render as ⟨ THIẾU HÌNH ⟩ boxes
while `validate.py` still reports `0 lỗi`, because a missing optional image
is only a warning. `project_check.py` is the only thing that catches it, and
it distinguishes *missing* from *misplaced* — if the file exists further up
the tree it says so and prints both paths.

Never "fix" this by rewriting image paths in the `.md` to climb out of the
folder (`../../assets/…`). Move the folder instead: a per-subsystem directory
is meant to be self-contained, so zipping one gives someone everything they
need to render it.

The `logo` key in `srs-config.json` resolves the same way, so it wants an
absolute path if the project has several subsystems and one shared logo.

## Pipeline naming

Child files are merged into a master document by the pipeline, and `merge.py`
finds them by globbing — naming and placement are load-bearing:

| | Folder | Filename |
|---|---|---|
| Function | `functions/«phân hệ»/` | `FUNC-XXX-001_Ten-co-gach.docx` |
| Group | `groups/` | `GRP-XXX-01_Ten-co-gach.docx` |

`render.py` defaults to this name; only override with `-o` when the output is
not going into the pipeline.

## Project configuration

Organisation name, project name, document code, confidentiality label and logo
live in `srs-config.json` at the project root (or `.srs/config.json`). Scripts
walk up from the spec file to find it; `--config` overrides.

**Deliberately not bundled in the skill** — a skill shipping one company's
logo would silently brand every other project's documents. Copy
`assets/config.example.json` into the project and edit.

It applies **only to `--standalone`**. In merge mode the child is a fragment
and the master document owns cover, logo and running header — which is why
`base.docx` has an empty header and footer.

Logo: PNG, transparent background, ≥600px wide, cropped tight, sRGB, under
1MB. Not SVG — python-docx cannot embed it. The script sets width only, so
aspect ratio is preserved.

## Versioning nuance

Sources, in order: `git log` → front matter → ask the BA. **Say which bump
rule you applied** so the BA can overrule you. You only know what you changed
in this session — never assert a history you didn't observe.

## Images

**Diagrams** — PlantUML source in `diagrams/«mã»_seq-01.puml`, referenced as
`[[DIAGRAM: …]]`. Rendering needs **Java on the machine**, not just the jar.
Jar lookup order: `plantuml_jar` in project config → `plantuml.jar` at project
root → cache → download from GitHub. Report which cause failed (missing Java,
blocked network, broken `.puml`) — they need different fixes. Kept as source
because an embedded picture can't be diffed. Participant names must be codes
from `participants.csv`; a code containing `-` needs quoting with an alias
(`participant "HT-TCTD" as HT_TCTD`).

**Mockups** — when the user pastes an image, ask which feature it belongs to
and the caption, then copy into `assets/` named after the feature code. Don't
keep the original filename: a re-paste should overwrite, not accumulate
`Screenshot (3).png`. Below 1200px wide prints blurry — warn, don't block.

On import, filenames are recovered from each picture's alt-text; a picture
without alt-text was pasted into Word by hand and gets a positional name plus
a warning. Where a required image is missing, `render.py` inserts a visible
box in the `.docx`; the user may paste directly into the `.docx` but must run
import immediately afterwards or the next render discards it.

## Rescue: hand-edited .docx

`render.py` stores two hashes in the document properties — one of the `.md`
source, one of the rendered text. `import_docx.py --diff FUNC-….md` compares
both and tells you whether the `.docx` drifted, the `.md` drifted, or both.
It never overwrites; the decision stays with the BA. Front matter is excluded
because a `.docx` doesn't carry enough to rebuild it.

## Registries

Eight CSVs hold the shared codes (`messages.csv`, `usecases.csv`, `roles.csv`,
`states.csv`, `participants.csv`, `components.csv`, `objects.csv`,
`groups.csv`). Pass `--registry-dir` when they exist; without them the
validator warns and skips code checks rather than blocking.
`references/golden/registries/` shows each file's expected columns.

**Putting a row in a registry is not the same as writing its content.** The
rule that a new code "goes into the registry in the same submission" exists so
nothing dangles — it does not license inventing what the row says. `noi_dung`
is the literal sentence a user reads; `ten_uc` is how the business names the
work. Both are business content and the no-invention rule governs them.
Reserve the code, leave the wording `⟨?⟩`, open an issue, ask. This was a real
forward-test failure (B4, 18/08): one run refused and asked for the wording,
another wrote four plausible Vietnamese sentences straight into `messages.csv`
and `usecases.csv`. The second is worse than a missing row because it looks
finished.

Outbound email is a message type (`MAIL_001`), not a separate section: subject
and body live in `messages.csv`; the function file declares code, parameters
and trigger. Message codes are **system-wide**, numbered per type (`ERR_014`)
— look up `messages.csv` before creating one; the same text reuses the same
code even across subsystems. Indicator codes (`D101`) come from an outside
authority and have no registry — never invent one.

## Several points in one table cell

A markdown table row cannot span source lines, so the `·` marks carry what
Word will show as real bullets: `·` level 1, `··` level 2, `···` level 3.
Render expands them, import puts them back, and the round trip is unchanged —
the `.md` line stays one line, so diffs and `grep` behave exactly as before.

Which columns may do this is declared in `outline.json` under
`multiline_columns`, never hardcoded. Three families may: what the system does
(*Xử lý của hệ thống*, *Hành động khi sai*, *Ghi nhận kết quả*…), conditions
(*Điều kiện lọc*, *Điều kiện phát sinh*…), and formulas (*Công thức nghiệp
vụ*…). Several points is what a procedure, a compound condition and a query
each are.

The list is per *column*, and a column reaches whichever templates happen to
use its table — so the declaration can look complete while one template gets
almost nothing. v6.0 shipped that way: `UI` had five allowed columns and
`TICHHOP`, `PHANTICH`, `DANHMUC` had one apiece. If you add a column, check
coverage per profile; the eval group *Ô nhiều dòng × loại* does this and fails
when a template has nothing beyond the shared open-issues table.

Constraint columns (*Mô tả ràng buộc*, *Nội dung quy tắc*, *Nội dung kiểm
tra*, *Tiêu chí chấp nhận*) may not, and this is the deliberate part. The standard already says
each rule takes its own `BR-` code. A crowded cell there is a finding, and
rendering it as a tidy bullet list would make the anti-pattern comfortable —
nobody would split it afterwards. Those cells render as one line and
`validate.py` reports a per-column count so the analyst can work through them.

Do not "improve" a constraint cell by adding `·`. Split it into `BR-` rows.

## The STT column is derived

`render.py` recomputes it on every render, so the ordinal that reaches the
document is always the row's real position. Import and scaffold seed it too,
purely so the `.md` reads sensibly — since render overrides, a stale number in
the source can never ship, which is what makes seeding safe rather than a
second source of truth. Inserting a row upstream needs no renumbering pass.

Two exceptions: a cell holding text that is not a number is left alone, and a
**label row** — text in the first column, the rest blank, used as a divider
band like *"Các button"* — is neither numbered nor counted.

Why it is computed at all: legacy specs numbered these rows with Word's own
list numbering, which lives in `numbering.xml` and never appears in the cell
text. A real document showed 260 numbers on screen and returned 260 empty
strings to the importer. There was nothing to carry across.

## Migrating a legacy spec

A separate job with its own reference: **`references/migration-legacy.md`**.
Read it only when converting a pre-outline document — it is the largest note
here and irrelevant to normal drafting.

## Full file map

| Path | What |
|---|---|
| `references/outline.json` | The outline — scripts read it; you don't need to |
| `assets/base.docx` | Styles, A4 geometry. Header/footer intentionally empty |
| `assets/config.example.json` | Template for the project's `srs-config.json` |
| `scripts/srs.py` | Dispatcher: `new` `check` `review` `render` `pdf` `migrate` `export` |
| `scripts/srslib.py` | Shared document model |
| `scripts/scaffold.py` · `validate.py` · `render.py` · `export_pdf.py` | The write path |
| `scripts/import_docx.py` | `.docx` → `.md`; rescue via `--diff` |
| `scripts/migrate_scan.py` | Legacy-spec inventory |
| `scripts/migrate_outline.py` | Outline version upgrade |
| `scripts/outline_check.py` · `project_check.py` | Outline / project folder checks |
| `references/migration-legacy.md` | Converting a pre-outline document — read only for that |
| `evals/run_evals.py` | Regression suite — for skill development |
| `evals/forward-tests.md` | Manual behaviour checks — for skill development |

To change the outline, edit `references/outline.json` and re-run every script;
they all derive from it.
