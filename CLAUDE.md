# Ngữ cảnh repo — đọc file này trước

**Đây là kho NGUỒN của bộ skill, không phải kho soạn SRS.** Sản phẩm đầu ra là
bộ skill phát cho BA dùng trên nhiều trợ lý AI khác nhau. Tài liệu SRS thật nằm
ở kho khác.

> Kho này **không có** `tools/outline.py`, `tools/phanhe.py`, `docs/SO-THEO-DOI.md`,
> `functions/`, `merge.py`. Nếu có CLAUDE.md nào ở thư mục cha nhắc tới chúng thì
> đó là ngữ cảnh của kho khác — bỏ qua.

## Ba phần

| Thư mục | Là gì | Sửa ở đâu |
|---|---|---|
| `.claude/skills/` | **Nguồn thật** của 2 skill: `srs-help`, `soat-nghiep-vu` | Sửa trực tiếp tại đây |
| `workspace/` | Bộ khởi tạo phát cho BA: `manifest.md`, `registries/*.csv`, `project-rules/`, `srs-config.json` | Sửa trực tiếp; là mẫu, không phải dữ liệu chạy |
| `tools/` | Công cụ Confluence (đọc/ghi) + `build_skills.py` | Sửa trực tiếp |

## Nguyên tắc lõi — một nguồn, nhiều đích

`.claude/skills/<tên>/` là **bản duy nhất được sửa tay**. Bản cho Codex,
Antigravity, và gói `.skill` cho claude.ai đều **sinh ra** bằng:

```bash
python tools/build_skills.py          # sinh toàn bộ vào dist/
python tools/build_skills.py --check  # so bản dist hiện có với nguồn, không ghi
```

Đã từng có `skills-common/` chứa 3 bản chép tay (~2,2 MB). Chúng lệch nhau thật:
`validate.py` của bản Antigravity có một phép kiểm mà hai bản kia thiếu → cùng
một tài liệu, ba agent cho ba kết quả. Đó là lý do thư mục đó bị xoá. **Đừng
dựng lại nó.**

Phần khác nhau giữa các đích chỉ là metadata, khai ở
`.claude/skills/<tên>/adapters/<đích>.yaml`. Không chép nội dung skill vào đó.

## Đừng làm

- **Đừng sửa file trong `dist/`** — bị ghi đè mỗi lần build, và không được commit.
- **Đừng chép skill sang thư mục thứ hai** để "cho agent khác dùng". Thêm đích thì
  thêm một adapter, không thêm một bản sao.
- **Đừng commit `__pycache__/`, `*.pyc`, `dist/`** — đã chặn bằng `.gitignore`.
- **Đừng sửa `references/outline.json` bằng tay** — sửa xong phải chạy
  `scripts/outline_check.py` và `evals/run_evals.py`, xem `references/trien-khai.md` mục 6.

## Kiểm chứng sau khi sửa skill

```bash
cd .claude/skills/srs-help
python scripts/outline_check.py
python evals/run_evals.py            # phải 327/327 (321/321 nếu thiếu LibreOffice)
cd ../../.. && python tools/build_skills.py
```

Sửa `assets/base.docx` hoặc `references/outline.json` thì bước `run_evals.py`
**không bỏ được** — nó bắt lệch style và lệch độ rộng cột, thứ mà mắt không thấy
và chỉ lộ ra khi Word báo "file hỏng" trên máy BA.

## Công cụ Confluence

`tools/confluence_reader.py` (Confluence → Markdown) và
`tools/confluence_writer.py` (Markdown → Confluence). Mỗi cái có README riêng
cạnh nó. Cần `.env` khai `CONFLUENCE_TOKEN`, `CONFLUENCE_URL`.
