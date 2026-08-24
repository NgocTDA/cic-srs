# Hướng dẫn sử dụng: Confluence Reader (Confluence to Markdown)

**`confluence_reader.py`** là công cụ độc lập, đọc trực tiếp nội dung một trang Confluence qua REST API và chuyển đổi sang Markdown chuẩn (dùng BeautifulSoup4 để xử lý triệt để bảng lồng nhau và các macro của Confluence). Tool hỗ trợ tải kèm ảnh đính kèm, và có chế độ riêng để gom nhiều trang con thành một file chức năng SRS duy nhất.

## 🚀 Các tính năng chính

1. **Chuyển đổi XHTML → Markdown đầy đủ:**
   - Xử lý heading, đoạn văn, danh sách (`ul`/`ol`), in đậm/in nghiêng, code inline và code block.
   - Xử lý bảng lồng nhau: gộp cả `tr` là con trực tiếp của `<table>` và `tr` nằm trong `<thead>`/`<tbody>`/`<tfoot>`, chuẩn hoá số cột.
   - Xử lý các macro Confluence phổ biến: `info`, `tip`, `note`, `warning`, `expand` (chuyển sang khối `> [!NOTE]`...), `code` (chuyển sang code block có ngôn ngữ), `status`, `children`.

2. **Xử lý ảnh và liên kết:**
   - Ảnh đính kèm (`ri:attachment`) và ảnh dán từ URL ngoài (`ac:image` + `ri:url`) đều được nhận diện.
   - Liên kết nội bộ Confluence (`ac:link` → `ri:page`) được giữ lại tên trang hiển thị thay vì bị mất trắng.
   - Khi lưu ra file, tool tự động tải các ảnh đính kèm về thư mục `assets/` cạnh file Markdown và thay thế placeholder bằng cú pháp `![]()` chuẩn.

3. **Hai chế độ output:** in ra Markdown (console hoặc file `.md`) hoặc xuất JSON đầy đủ metadata (`--json`).

4. **Chế độ gộp chức năng SRS (`--srs-func`):**
   - Tự động lấy toàn bộ trang con cấp 1 của trang đang đọc, gán mã `FEAT-xxx` tăng dần, và gộp chung vào **một file Markdown duy nhất**.
   - Khi một trang con lại có trang con của riêng nó (cấu trúc lồng nhiều cấp), tool áp dụng chiến lược xử lý theo `--subpage-strategy`: hỏi trực tiếp (`ask`), làm phẳng thành các FEAT ngang hàng tiếp theo (`flatten`), nhúng làm mục con của FEAT hiện tại (`embed`), hoặc dừng lại để sửa cây Confluence (`abort`).
   - Ảnh đính kèm trong chế độ này được đổi tên gắn theo mã FEAT tương ứng để tránh trùng và dễ tra ngược nguồn.

5. **Tự dò URL dự phòng:** nếu `CONFLUENCE_URL` (nội bộ) không truy cập được, tool tự thử `CONFLUENCE_FALLBACK_URL` khai báo trong `.env`.

---

## 💻 Hướng dẫn Chạy lệnh (Copy & Paste)

Mở Terminal / PowerShell / CMD tại thư mục gốc của dự án.

### 1. Đọc một trang và in ra console

```bash
python tools\confluence_reader.py 123456
```

*(Có thể thay `123456` bằng URL đầy đủ của trang, tool tự tách Page ID).*

### 2. Đọc một trang và lưu ra file `.md` chỉ định

```bash
python tools\confluence_reader.py 123456 -o output\Thanh_phan_dung_chung.md
```

### 3. Đọc một trang và tự lưu vào thư mục `confluence_pages/`

Không cần chỉ định tên file, tool tự đặt tên theo `<pageId>_<Title>.md`:

```bash
python tools\confluence_reader.py 123456 --save
```

### 4. Xuất dữ liệu dạng JSON (kèm metadata: version, tác giả, ngày, trang con...)

```bash
python tools\confluence_reader.py 123456 --json
```

### 5. Gộp trang con thành một file chức năng SRS

Dùng khi trang Confluence đang đọc là trang cha chứa các FEAT con, cần gộp thành file chức năng theo mã `FUNC-xxx`:

```bash
python tools\confluence_reader.py 123456 --srs-func FUNC-KKN-001 -o functions\KHAI-THAC-NHOM\FUNC-KKN-001.md
```

Nếu muốn chủ động chọn sẵn chiến lược xử lý trang con lồng nhau (không bị hỏi giữa chừng khi chạy hàng loạt), thêm `--subpage-strategy`:

```bash
python tools\confluence_reader.py 123456 --srs-func FUNC-KKN-001 --subpage-strategy flatten -o functions\KHAI-THAC-NHOM\FUNC-KKN-001.md
```

### 6. Bỏ kiểm chứng chứng chỉ TLS (server nội bộ dùng self-signed cert)

```bash
python tools\confluence_reader.py 123456 --save --insecure-tls
```

---

## ⚙️ Các Tham số hỗ trợ (Arguments)

| Tham số | Bắt buộc | Chức năng |
| :--- | :---: | :--- |
| `page` | **Có** | Page ID hoặc URL của trang Confluence cần đọc (vị trí đầu tiên, không cần cờ). |
| `-o`, `--output` | Không | Đường dẫn file `.md` đầu ra. Nếu bỏ trống và không có `--save`, tool in kết quả ra console. |
| `--save` | Không | Tự động lưu ra file `<pageId>_<Title>.md` tại thư mục `confluence_pages/`. |
| `--json` | Không | Xuất kết quả dạng JSON (đầy đủ metadata) thay vì Markdown. |
| `--token` | Không | Confluence Personal Access Token, ghi đè giá trị trong `.env`. |
| `--url` | Không | Confluence Base URL, ghi đè giá trị trong `.env`. |
| `--insecure-tls` | Không | Bỏ kiểm chứng chứng chỉ TLS (chỉ dùng khi server nội bộ dùng self-signed cert). |
| `--srs-func` | Không | Mã chức năng (VD: `FUNC-KKN-001`) để tự động pull các trang con, gán mã `FEAT-xxx` và gộp chung vào một file. |
| `--subpage-strategy` | Không | Chiến lược xử lý khi một trang FEAT lại có trang con: `ask` (hỏi, mặc định), `flatten`, `embed`, `abort`. |

---

## Biến môi trường (`.env`)

Copy `.env.example` ở gốc repo thành `.env` rồi điền. Bắt buộc: `CONFLUENCE_URL`
và (`CONFLUENCE_TOKEN` nếu `CONFLUENCE_AUTH_MODE=bearer`, mặc định) hoặc
(`CONFLUENCE_USERNAME` + `CONFLUENCE_PASSWORD` nếu `=basic`).

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `CONFLUENCE_AUTH_MODE` | `bearer` | `bearer` hoặc `basic` |
| `CONFLUENCE_TOKEN` | — | Personal Access Token, dùng khi `bearer` |
| `CONFLUENCE_USERNAME` / `CONFLUENCE_PASSWORD` | — | Dùng khi `basic` |
| `CONFLUENCE_URL` | — | Bắt buộc, không còn giá trị mặc định trong code |
| `CONFLUENCE_FALLBACK_URL` | — | Tuỳ chọn, thử tiếp nếu `CONFLUENCE_URL` lỗi |
| `CONFLUENCE_SPACE` | — | Tuỳ chọn |
| `CONFLUENCE_ALLOW_INSECURE_HTTP` | `false` | Phải `true` nếu `CONFLUENCE_URL` là `http://` (không phải `https://`), coi như xác nhận mạng nội bộ tin cậy |
| `CONFLUENCE_VERIFY_TLS` | `true` | Đặt `false` nếu server dùng self-signed cert (`https`) |
| `CONFLUENCE_CONNECT_TIMEOUT` / `CONFLUENCE_READ_TIMEOUT` | `5` / `30` | Giây |
| `CONFLUENCE_MAX_RETRIES` / `CONFLUENCE_BACKOFF_FACTOR` | `3` / `1` | Retry khi lỗi mạng hoặc HTTP 429/5xx, cách nhau `backoff_factor * 2^lần thử` |

**Yêu cầu hệ thống:** Cần cài `beautifulsoup4` (`pip install beautifulsoup4`).
