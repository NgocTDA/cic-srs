# Migrating a legacy spec

Read this **only** when converting a document written before the outline
existed. Split out of `agent-notes.md` because it is 40% of that file and
never needed while drafting normally.

Migration is a reasoning task, the highest-risk one in this skill.

`import_docx.py` refuses documents whose headings don't match the outline —
their headings mean something else, and the content the outline demands does
not exist to be moved. Migration is a reasoning task, the highest-risk one in
this skill.

1. `migrate_scan.py cu.docx --profile UI -o kiem-ke.md` — inventory with an
   empty mapping column.
2. Fill the mapping **with the BA**. Sections with no source get `KHÔNG CÓ`.
3. `scaffold.py` a new file; move content one section at a time — copy
   meaning, don't paraphrase away detail, don't smooth over gaps.
4. Everything absent goes to `⟨?⟩` plus a row in *Vấn đề còn mở*. Never infer
   a permission matrix, an acceptance criterion, or a code.
5. Assign new `BR-`/`MH-`/`FEAT-` codes; keep a mapping so the BA can trace.
6. Validate. A long open-issues list is the correct output — it is the
   migration backlog.

`--raw` extracts old text without conforming — for side-by-side reading only.

### What happens to a multi-line Word cell

A markdown table row cannot span lines, so a cell holding several paragraphs
collapses into one. Boundaries are kept as marks rather than dropped: a bullet
becomes `·` (repeated for depth — `··` is level 2), a prose line without end
punctuation gets a full stop, and a literal `|` is escaped. Bullets are
recognised from the outline's own styles (`T-Gach -/+/*`) as well as Word
numbering — house-styled specs carry no `w:numPr` at all, so checking only
that missed every bullet in real documents.

`import_docx.py` reports how many cells were merged and which columns they sat
in. Treat a constraint cell with several `·` as a finding, not a formatting
detail: it is usually several business rules that each want their own `BR-`
row, and only the BA can decide.

### Images out of a legacy .docx

`migrate_scan.py --lay-anh` pulls every picture into `assets/` at inventory
time and adds an *Ảnh lấy ra* table to the report: ordinal, old section
number, original caption, filename, size, and an empty column for the BA to
record which new feature each image belongs to. That is the image half of the
mapping table — do it in the same pass as the content mapping.

Names read `006_1.5.4_giao-dien-them-moi.png`: ordinal first so the folder
sorts in document order, then the old section number so the analyst can find
where it came from, then words taken from the caption (falling back to the
enclosing feature title). The nearest heading is a poor source here — every
mockup in this outline sits under *Thiết kế giao diện*, so naming by heading
produced fifteen identical names.

Three things that used to go wrong silently, now guarded:

- **Names came from alt-text.** Word's default is `Picture 1` for nearly every
  image, so writes collided: a 26-image spec left two files on disk while
  still reporting nineteen extracted, and every figure in the delivered
  document pointed at the same picture. Names are now derived, never
  overwritten, and the count of body-referenced pictures is checked against
  what reached disk.
- **No file extension**, because it was taken from alt-text rather than the
  part's content type — the output document carried `media/image2.` with a
  trailing dot.
- **Section numbers do not exist in the file.** Headings here carry no number
  in the text or on the paragraph; Word draws them from numbering attached to
  the *styles*. They are recomputed from the heading sequence, and are
  relative to the child file — after merging into the master the same section
  sits elsewhere.

`w:object` embeddings (Visio drawings, spreadsheets, attached files) are not
pictures: what the document shows is an EMF *preview*, with the payload in
`word/embeddings/`. They are listed in their own table with instructions,
never silently dropped.

### Codes with the wrong separator

Legacy specs commonly write `ERR-001` where the standard says `ERR_001`. The
malformed-code check accepts hyphen, underscore, space or nothing as the first
separator, and names the corrected code in the message so one find-and-replace
fixes every occurrence. Later separators must be a real hyphen or underscore —
a space there would let a match run past a valid code into the next cell.

## Outline version migration (4.1 → 5.0 and onward)

A major-version mismatch means structure changed; `validate.py` refuses the
file and prints the fix. `migrate_outline.py` inserts exactly the added rows,
marks each `⟨?⟩`, opens matching rows in *Vấn đề còn mở*, bumps the changelog.
It fills nothing in — inventing scope is the same failure as inventing a table
name. Current: v6.1. The chain is 4.1 → 5.0 → 6.0 → 6.1 and `migrate_outline.py`
walks all of it in one run; `validate.py` names the number of hops in its
message. Only a major bump blocks — 6.0 → 6.1 warns and still renders.

