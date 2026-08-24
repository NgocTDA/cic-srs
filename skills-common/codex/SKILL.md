---
name: srs-help
description: "Write, review, validate, migrate, and render Vietnamese SRS specs (viết / soát / kiểm tra chuẩn đặc tả chức năng, nhóm chức năng) against the project's fixed outline — .md source, .docx/.pdf output. Use for requirements work: BRD or meeting notes into a spec, FUNC-/FEAT-/BR-/MH-/GRP- codes in an SRS context, .md/.docx specs checked against the standard. Codes alone are not a trigger; not for programming errors, test cases or test scripts, database design, or user manuals."
---

# SRS help

Produce and check function specifications that follow a fixed outline, so
hundreds of specs by different analysts stay queryable as one corpus.

**All document output is Vietnamese.** These instructions are English; every
string that lands in the document comes from `references/outline.json` via the
scripts, never from your own translation.

## The one rule that matters most

**Never invent business content.** A spec that reads fluently but contains a
fabricated table name, endpoint, business rule, or code is worse than an
obviously incomplete one, because nobody catches it until development.

| Situation | What to do |
|---|---|
| Information missing | **Ask the BA.** Do not fill it in. |
| Two sources disagree | Present both, name each source. Do not pick. |
| You can reasonably infer it | Propose it — but **mark it**, never state it as settled. |

To mark: put `⟨?⟩` at the spot **and** add a row to *Vấn đề còn mở* (nội dung
· người quyết định · hạn chốt · `Đang chờ`). `validate.py` counts these and
blocks release until they are settled — do not work around it.

## Two kinds of code — do not conflate them

| Kind | Codes | Rule |
|---|---|---|
| Shared system-wide | `UC-`, `MSG` (`ERR_`/`WAR_`/`INF_`/`SUC_`/`CONF_`/`MAIL_`), `ST-`, `ROLE-`, `GRP-`, participants, components | **Must already exist in a registry.** Never mint one. Need a new one? It goes into the registry in the same submission — but see below. |
| Internal to one file | `FEAT-`, `BR-`, `MH-` | **Minted here**, numbered consecutively. Must be declared in the file before anything references them. No registry covers these. |

**Adding a row to a registry is not the same as writing what goes in it.**
"In the same submission" means the *row* travels with the document so nothing
dangles. It does not license you to invent the row's content. A message's
`noi_dung` is the literal sentence a user will read, a use case's `ten_uc` is
how the business names the thing — both are business content, and the first
rule applies. Reserve the number, leave the wording `⟨?⟩`, open an issue, ask.
Silently supplying a plausible Vietnamese sentence is the failure this rule
exists to prevent, and it is harder to catch than a missing row because it
looks finished.

`FUNC-` sits between: the code is **allocated in `manifest.md` at the project
root** — reserve it there, commit, then write the file — while the file
carrying it is the one being written. A code has to exist before its file, or
two analysts take the same number and nothing notices. `validate.py` checks
both directions (reference without declaration = error; declaration nobody
uses = warning) and cross-table agreement — trust it over re-deriving the
rules yourself.

## Two modes

- **Write** — "viết SRS", "đặc tả chức năng", "soạn tài liệu yêu cầu", or the
  user hands over raw material (BRD extract, meeting notes, screen list).
- **Review** — "soát", "review tài liệu", "kiểm tra chuẩn", or they attach an
  existing spec. A review must never silently rewrite content.

**Ambiguous means ask first — before doing either, not after.** Requests like
*"tài liệu này cần chuẩn hơn"*, *"xem lại giúp tôi"*, *"hoàn thiện file này"*
name no mode. Picking one and delivering it, then asking at the end, is not
asking: by then the work is done and the user is reacting to it rather than
choosing. One short question costs a turn; guessing "review" wastes the
user's time and guessing "write" edits a document they never asked you to
touch.

## Document model

```
Chức năng [FUNC-«phân hệ»-«3 số»]        ← one file, one function
├── function-level sections (fixed per profile)
│     incl. Use Case ↔ Tính năng traceability TABLE
└── Tính năng [FEAT-…-«2 số»]            ← repeating block
      └── feature-level sections (vary by profile)
```

| Profile | For |
|---|---|
| `UI` | Anything with a screen |
| `TICHHOP` | System integration / APIs |
| `JOB` | Batch or scheduled processing |
| `PHANTICH` | Reports and indicators — **flat, no Tính năng tier** |
| `DANHMUC` | Reference data (trimmed `UI`) |

A group (`GRP-`) is a **menu tier, not a document**: one Heading 2 plus at
most a few sentences. No sections, no tables. Details in
`references/agent-notes.md` §Groups.

## Markdown is the source of truth

The `.md` file is the document; `.docx`/`.pdf` are generated and never edited
for content. Never hand-write section headings (`scaffold.py` emits them from
the outline), never delete a section (write `Không áp dụng`), never
hand-number anything. `references/md-syntax.md` defines the exact syntax the
parser accepts — read it before your first write in a session.

## Workflow

One dispatcher wraps the scripts — prefer it over remembering flags:

```bash
python scripts/srs.py new --profile UI --ma FUNC-QLNSD-001 --ten "Quản lý người dùng" --tinh-nang 2
python scripts/srs.py check FUNC-QLNSD-001.md            # validate (--registry-dir when present)
python scripts/srs.py export FUNC-QLNSD-001.md           # validate → render → pdf, stops on error
python scripts/srs.py review ho-so.docx                  # import → validate
python scripts/srs.py migrate FUNC-QLNSD-001.md          # outline version upgrade
python scripts/srs.py fix FUNC-QLNSD-001.md              # blank lines around tables
```

**When you write or edit a `.md` by hand**, a table must be separated from
whatever surrounds it by a blank line. This parser tolerates a missing one;
GitHub and every editor preview do not — they pull the next line into the last
cell. `check` reports it as an error and `fix` repairs it.

Individual scripts (`scaffold.py`, `validate.py`, `render.py`,
`export_pdf.py`, `import_docx.py`) take the same arguments if you need them
directly.

**Exit codes of `check`:** `0` clean · `1` errors, do not render · `2` release
gate only — draft render allowed. In a multi-file run, any error wins over
gate-only.

**Release gate:** files carrying `⟨?⟩` or pending rows in *Vấn đề còn mở*
render as a stamped draft. `--force-release` overrides — offer it only when
the BA asks, and restate what is being skipped.

**Editing an existing spec:** edit the `.md`, bump the version per the rules
below, add a changelog row, re-validate, re-render.

**Review flow:** run `check` first, then read the content yourself for what a
script cannot see — vague acceptance criteria, rules stated as intentions,
fields declared twice. A hand-edited `.docx` is a rescue job:
`import_docx.py --diff` (agent-notes §Rescue).

## Versioning

| Change | Bump |
|---|---|
| New file | `0.1` |
| First approval | `1.0` |
| Add/change/remove a feature, BR, field, rule | `x.Y+1` |
| Scope change, or large change after approval | `X+1.0` |
| Typo / wording, meaning unchanged | none |

Say which rule you applied so the BA can overrule you.

A front-matter `outline_version` behind the skill's **major** version is
refused by `validate.py`; run `srs.py migrate` — never hand-edit the missing
rows (agent-notes §Outline version migration).

## Two environments

On Claude Code the project is a real folder. On claude.ai the filesystem
resets between sessions: the user uploads a zip, you unpack, work, and hand
everything back — run `project_check.py` first to catch missing mockups,
`.puml` files, and registry columns. **Always return `assets/` with the
deliverable**: you can see a pasted image but cannot recreate it.

## What to read, when

| Situation | Read |
|---|---|
| First `.md` write of the session | `references/md-syntax.md` |
| Drafting a spec | `references/golden-snippets.md` — worked patterns for the common structures |
| Phrasing a field constraint | `references/validation-catalog.md` |
| Prose voice questions, pre-submission check | `references/style-guide.md` |
| Deep comparison of section depth, or reviewing voice | `references/golden/FUNC-QLNSD-001.md` (full worked example) |
| Groups, PHANTICH, config/logo, images, PlantUML, rescue, registries detail, `·` cells, STT | `references/agent-notes.md` — the section you need |
| **Converting a pre-outline document** | `references/migration-legacy.md` — that job only |
| BA asks how to use the skill | point them to `references/huong-dan-ba.md` |
| BA asks what a command-line flag does | point them to `references/co-dong-lenh.md` |
| Install / deployment questions | `references/trien-khai.md` |
| **Start of work in any project folder** | `project-rules/srs-help.md` **if the file exists** — read it after this file |

**Project overlay.** A project may keep its own rules in
`project-rules/srs-help.md` at the project root. Read it once at the start,
after this file, and say you have. It only *adds* to the defaults: it can name
folder conventions, tooling commands, or where shared codes come from. It can
never weaken the ban on inventing content, the validation rules, or the
release gate — a line that tries to is a mistake in that file, and the answer
is to say so, not to obey it. No such file means no exceptions; do not go
looking for one anywhere else.

**Do not read unless the situation demands it:** `scripts/` source (only when
a script errors or you are changing the skill) · `references/outline.json`
(scripts read it for you) · `evals/` (skill development only) ·
`huong-dan-ba.md` / `trien-khai.md` while drafting · the full golden file when
`golden-snippets.md` already answers the question. Structure review needs no
reading at all — run `check` and work from its findings.

## Writing style

One idea per line. Conditions as `khi … thì hệ thống phải …`. No hedging
words (`thường`, `có thể`, `nên`) in normative statements. Reference rules by
`BR-` code instead of restating them. Declare each field exactly once, in the
components table. Bullets at most three levels (0/2/4 spaces).

## Scope boundary

Do not specify algorithms. The SRS declares which rule applies where (by
`BR-` code); the algorithm belongs in the organization's separate algorithm
spec. Writing matching or normalization logic here creates a second source of
truth, and two sources drift.
