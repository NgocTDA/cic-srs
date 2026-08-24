# Cờ dòng lệnh — tra cứu

**Bạn thường không cần dùng cờ.** Nói bằng tiếng Việt, Claude chọn cờ. Bảng này
để tra khi bạn tự chạy lệnh, hoặc khi muốn ép Claude làm đúng một kiểu.

---

## Nói thế nào thì Claude chạy cờ gì

| Bạn nói | Claude chạy |
|---|---|
| "Viết đặc tả `FUNC-QLNSD-001` Quản lý người dùng, loại UI, 2 tính năng" | `scaffold.py --profile UI --ma … --ten … --tinh-nang 2` |
| "Kiểm tra chuẩn" | `validate.py` |
| "Xuất Word và PDF" | `render.py` rồi `export_pdf.py` |
| "Xuất tài liệu độc lập có bìa" | `render.py --standalone` |
| "Soát file này" *(đính kèm .docx)* | `import_docx.py` rồi `validate.py` |
| "File Word này bị sửa tay, so với bản .md" | `import_docx.py --diff` |
| "Kiểm cả mã trong sổ đăng ký" | `validate.py --registry-dir …` |
| "Tài liệu cũ này chuyển sang mẫu mới được không" | `migrate_scan.py --profile …` |
| "Kiểm kê kèm lấy ảnh ra" | `migrate_scan.py --profile … --lay-anh` |
| "Nâng file này lên đề cương mới" | `migrate_outline.py --nguoi …` |
| "Kiểm gói dự án đủ chưa" | `project_check.py .` |

Từ bản này có thêm `srs.py` — một lệnh điều phối gói các script trên:
`srs.py new|check|render|pdf|review|migrate|export`. Riêng `export` chạy cả
chuỗi kiểm → render → PDF và dừng ngay khi có lỗi. Cờ của script gốc dùng
nguyên. `validate.py` (tức `srs.py check`) có thêm `--quiet` (chỉ in lỗi và
điểm vướng cổng chặn) và `--json`.

---

## Năm cờ đáng biết

### `--standalone` · `render.py`

Tài liệu **độc lập**: có bìa, logo, tên dự án, header, số trang. Bắt đầu từ
`Heading 1`.

Mặc định (không có cờ) là **file con** để ghép vào tài liệu tổng: bắt đầu từ
`Heading 3`, không bìa, không logo — vì tài liệu tổng đã có rồi. File con tự
thêm logo sẽ làm logo nằm giữa tài liệu sau khi ghép.

Cần `srs-config.json` ở gốc dự án. Không có thì vẫn chạy nhưng cảnh báo và ra
tài liệu trống bìa.

### `--draft` · `render.py`

Đóng dấu **BẢN NHÁP** lên header.

**Thường bạn không cần gõ.** `render.py` tự kiểm cổng chặn: còn `⟨?⟩` hoặc còn
dòng `Đang chờ` ở *Vấn đề còn mở* thì **tự động** ra bản nháp và nói rõ lý do:

```
CỔNG CHẶN: còn 1 chỗ đánh dấu ⟨?⟩ chưa chốt
CỔNG CHẶN: mục "Vấn đề còn mở" còn 1 dòng "Đang chờ"
→ Xuất BẢN NHÁP. Sạch hết rồi render lại để có bản phát hành.
```

Gõ `--draft` khi bạn muốn đóng dấu nháp lên một tài liệu vốn đã sạch — ví dụ gửi
đi lấy ý kiến trước khi ký duyệt.

### `--force-release` · `render.py`

Bỏ qua cổng chặn, xuất bản phát hành dù còn điểm treo.

Dùng khi thật sự gấp. Nó vẫn in ra đủ lý do bị chặn, nên bạn biết mình đang bỏ
qua cái gì. **Đừng dùng thành thói quen** — cổng chặn tồn tại để chỗ chưa chốt
không lọt xuống Dev.

### `--diff «file.md»` · `import_docx.py`

Chế độ **cứu hộ**. So file `.docx` với bản `.md`, cho biết bên nào đã đổi:

| Kết luận | Nghĩa |
|---|---|
| Sạch | `.docx` đúng bản render của `.md`, không ai sửa tay |
| `.docx` bị sửa tay | Có người sửa trong Word |
| `.md` đã thay đổi | `.docx` sạch, chỉ cần render lại |
| Cả hai đổi | Phải nhập thủ công từng điểm |

**Không ghi đè gì cả** — chỉ báo khác biệt, bạn tự quyết.

### `--registry-dir «thư mục»` · `validate.py`

Bật đối chiếu mã với các sổ `messages.csv`, `usecases.csv`, `states.csv`,
`objects.csv`…

Không có cờ này thì validator **bỏ qua** phép kiểm mã và cảnh báo. Nghĩa là mã
`ERR_999` không tồn tại vẫn lọt. Có sổ thì luôn nên dùng.

### `--profile «loại»` · `migrate_scan.py`

**Bắt buộc.** Kiểm kê một tài liệu cũ để lập bảng ánh xạ sang khung mới. Script
không đoán loại vì tài liệu cũ không có dấu hiệu nào để đoán — bạn phải nói rõ
định chuyển sang loại nào.

Kết quả là file `.md` gồm: bảng ánh xạ trống để BA điền, danh sách những gì tài
liệu cũ có (tiêu đề, bảng, ảnh, mã), và các bước tiếp theo.

**Không chuyển đổi tự động.** Xem lý do ở mục "Chuyển tài liệu cũ" trong hướng
dẫn.

### `--lay-anh` · `migrate_scan.py`

Lấy luôn mọi ảnh trong tài liệu cũ ra `assets/` (đổi chỗ bằng `--assets`), kèm
một bảng trong bản kiểm kê: số thứ tự · mục cũ · chú thích gốc · tên tệp · KB
· cột trống để bạn điền ảnh thuộc tính năng nào của khung mới.

Tên tệp dạng `006_1.5.4_giao-dien-them-moi.png` — thứ tự xuất hiện, số mục cũ,
rồi chú thích. Không ghi đè tệp nào; chạy lại trên cùng thư mục không sinh bản
sao.

Ảnh vector và **đối tượng nhúng** (Visio, bảng tính, tệp đính kèm) không lấy
được tự động — bản kiểm kê liệt kê riêng kèm cách xử lý tay.

### `--nguoi` · `--han` · `--thu` · `migrate_outline.py`

Nâng file **đã theo chuẩn** lên phiên bản đề cương hiện hành. Khác hẳn
`migrate_scan.py` ở trên: cái đó dành cho tài liệu chưa từng theo khung nào.

`--nguoi` ghi vào changelog và vào cột *Người quyết định* của các dòng mở ra ở
*Vấn đề còn mở* — bỏ trống thì thành `⟨?⟩`, và `⟨?⟩` chặn phát hành. `--han`
tương tự cho cột *Hạn chốt*. `--thu` chỉ in ra sẽ đổi gì, không ghi file.

Script **chỉ chèn dòng và đánh dấu**, không viết nội dung. Chỗ nào còn `⟨?⟩` là
chỗ chỉ BA trả lời được — đó là chủ ý, không phải script làm dở.

### Sơ đồ PlantUML — không có cờ, khai trong `srs-config.json`

Mặc định script **tải `plantuml.jar` về máy** (ghim phiên bản), cache lại, và chỉ
tải khi thật sự có `.puml` cần render. Không cần cấu hình gì.

Khai `plantuml_server` thì server được ưu tiên hơn jar — nhanh hơn, không cần
Java trên máy BA, nhưng **mất tính tái lập**: server nâng cấp là hình trong mọi
tài liệu đổi theo. Và server nội bộ chỉ gọi được từ Claude Code.

---

## Cờ ít dùng

| Cờ | Script | Khi nào cần |
|---|---|---|
| `-o «đường dẫn»` | tất cả | Đặt tên file ra khác mặc định |
| `--profile «loại»` | `import_docx` | Ép loại khi script đoán sai |
| `--config «file»` | `render` | Dùng cấu hình khác, không phải file tìm được |
| `--assets «thư mục»` | `import_docx` | Thư mục ảnh khác `assets/` |
| `--nguoi "Tên BA"` | `scaffold` | Điền sẵn người thực hiện vào changelog |
| `--outdir «thư mục»` | `export_pdf` | Xuất PDF sang chỗ khác |
| `--raw` | `import_docx` | Tài liệu **cũ không theo mẫu** — lấy phần thô ra để đọc đối chiếu. Kết quả **không hợp lệ**, không dùng để sửa dần thành bản chuẩn |

## Cờ gần như không bao giờ dùng

| Cờ | Vì sao có |
|---|---|
| `--outline «file»` | Thử nghiệm một bộ đề cương khác. Đề cương chuẩn đã đóng gói trong skill |
| `--base «file.docx»` | Thử một bộ style khác. Sai file này thì tài liệu vỡ định dạng |

---

## Ví dụ chuỗi lệnh đầy đủ

```bash
# Tạo mới
python scaffold.py --profile UI --ma FUNC-QLNSD-001 --ten "Quản lý người dùng" --tinh-nang 2 --nguoi "Ngọc TDA"

# ... điền nội dung vào FUNC-QLNSD-001.md ...

# Kiểm, có đối chiếu sổ
python validate.py FUNC-QLNSD-001.md --registry-dir ../registries

# Xuất file con để ghép vào tài liệu tổng
python render.py FUNC-QLNSD-001.md -o out/FUNC-QLNSD-001.docx
python export_pdf.py out/FUNC-QLNSD-001.docx

# Hoặc xuất tài liệu độc lập có bìa
python render.py FUNC-QLNSD-001.md --standalone -o out/FUNC-QLNSD-001.docx
```

```bash
# Soát một file Word bất kỳ
python import_docx.py ho-so.docx -o ho-so.md
python validate.py ho-so.md

# Nghi có người sửa tay
python import_docx.py ho-so.docx --diff FUNC-QLNSD-001.md
```
