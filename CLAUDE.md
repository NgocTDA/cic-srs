# Ngữ cảnh repo — đọc file này trước

**Đây là kho SỐNG cho dự án CIC_CORE** — 15 BA cùng viết SRS thật ở
`workspace/`, không phải mẫu. Bộ skill (`srs-help`, `soat-nghiep-vu`) thì
**phát triển ở kho khác** (`workspace/srs-help/` — kho dev riêng, có
`SYNC.md`, `adapters/`, eval) và được **đồng bộ vào đây** khi có bản duyệt
mới, không sửa tay tại chỗ.

> Kho này **không có** `tools/outline.py`, `tools/phanhe.py`, `docs/SO-THEO-DOI.md`,
> `merge.py`. Nếu có CLAUDE.md nào ở thư mục cha nhắc tới chúng thì đó là ngữ
> cảnh của kho khác (một thế hệ công cụ cũ hơn) — bỏ qua.

## Ba phần

| Thư mục | Là gì | Sửa ở đâu |
|---|---|---|
| `.claude/skills/` | Bản cài của 2 skill: `srs-help`, `soat-nghiep-vu` | **Không sửa tay ở đây.** Sửa ở kho dev skill riêng, xong đồng bộ lại (xem dưới) |
| `workspace/` | Dữ liệu SRS thật: `manifest.md`, `registries/`, `functions/<phân hệ>/`, `project-rules/`, `srs-config.json` | Sửa trực tiếp — đây là nơi 15 BA làm việc hàng ngày |
| `tools/` | Công cụ Confluence (đọc/ghi) + `build_skills.py` (tái xuất skill cho Codex/Antigravity nếu dự án cần) | Sửa trực tiếp |

## Đồng bộ skill từ kho dev

Kho dev skill (`workspace/srs-help/` cạnh kho này) coi `claude/srs-help.skill`
là upstream duy nhất, sinh Codex/Antigravity từ đó qua
`tools/sync_from_claude.py` (xem `SYNC.md` ở kho đó). Khi có bản `.skill` mới
đã duyệt, đồng bộ vào kho này bằng cách giải nén đè lên `.claude/skills/<tên>/`
rồi chạy lại bộ kiểm chứng bên dưới.

Đã từng có `skills-common/` chứa 3 bản chép tay (~2,2 MB) lệch nhau thật —
`validate.py` của bản Antigravity có một phép kiểm mà hai bản kia thiếu, cùng
một tài liệu ba agent ra ba kết quả. Đó là lý do một nguồn duy nhất
(`claude/srs-help.skill` ở kho dev) là bắt buộc, không phải tuỳ chọn. **Đừng
tạo thêm bản chép tay thứ hai ở đâu đó.**

## Đừng làm

- **Đừng sửa trực tiếp file trong `.claude/skills/`** — sẽ mất khi đồng bộ đè
  bản mới lên. Sửa nội dung skill ở kho dev.
- **Đừng sửa file trong `dist/`** — bị ghi đè mỗi lần build, và không được commit.
- **Đừng commit `__pycache__/`, `*.pyc`, `dist/`** — đã chặn bằng `.gitignore`.
- **Đừng sửa `workspace/` coi như mẫu rồi xoá đi làm lại** — đây là dữ liệu
  thật, có lịch sử commit của 15 người.

## Kiểm chứng sau khi đồng bộ skill mới

```bash
cd .claude/skills/srs-help
python scripts/outline_check.py
python evals/run_evals.py            # phải 327/327 (321/321 nếu thiếu LibreOffice)
```

Bản `.skill` đồng bộ vào coi như đã qua kiểm ở kho dev, nhưng chạy lại ở đây
một lần để chắc quá trình giải nén/đè file không làm hỏng gì — Word báo "file
hỏng" là lỗi tệ nhất vì chỉ lộ ra khi BA mở file.

## Công cụ Confluence

`tools/confluence_reader.py` (Confluence → Markdown) và
`tools/confluence_writer.py` (Markdown → Confluence). Mỗi cái có README riêng
cạnh nó. Cần `.env` khai `CONFLUENCE_TOKEN`, `CONFLUENCE_URL`.
