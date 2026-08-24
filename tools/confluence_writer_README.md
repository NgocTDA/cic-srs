# Hướng dẫn sử dụng: Confluence Writer (Markdown to Confluence)

**`confluence_writer.py`** là công cụ giúp bạn đẩy trực tiếp nội dung từ file Markdown lên hệ thống Confluence nội bộ. Tool hỗ trợ tự động xử lý và tải lên các ảnh đính kèm trong Markdown, đồng thời bảo toàn định dạng bảng biểu, hình ảnh chuẩn theo cấu trúc của Confluence.

## 🚀 Các tính năng chính

1. **Hỗ trợ 2 Chế độ:**
   - **Tạo trang mới:** Chỉ định thư mục cha (Parent ID), tool sẽ tạo một trang mới hoàn toàn.
   - **Cập nhật trang:** Chỉ định trang hiện tại (Page ID), tool sẽ ghi đè và tăng version lên.

2. **Xử lý Ảnh thông minh (Hash MD5):**
   - Tự động nhận diện ảnh cục bộ trong Markdown.
   - Kiểm tra mã Hash MD5 của ảnh giữa file ở máy tính và file trên Confluence. Nếu ảnh không bị thay đổi, tool sẽ tự động bỏ qua (Skip) bước tải lên để tiết kiệm thời gian.

3. **Bảo toàn XHTML:** 
   - Tự động convert Markdown sang HTML (hỗ trợ Table).
   - Tự động bọc ảnh bằng Macro `<ac:image>` chuẩn của Confluence.
   - Nếu trong Markdown đã có sẵn thẻ XML/XHTML, tool sẽ không làm hỏng cấu trúc đó.

---

## 💻 Hướng dẫn Chạy lệnh (Copy & Paste)

Mở Terminal / PowerShell / CMD tại thư mục gốc của dự án (`workspace\test`).

### 1. Tạo trang MỚI
Nếu bạn muốn tạo một trang mới nằm trong một trang cha (Parent Page), hãy sử dụng cờ `--parent-id`:

```bash
python tools\confluence_writer.py --file Thanh_phan_dung_chung.md --parent-id 123456
```
*(Thay `123456` bằng ID của trang cha thực tế).*

### 2. Cập nhật trang ĐÃ CÓ SẴN
Nếu bạn muốn ghi đè nội dung lên một trang đã có sẵn (Ví dụ trang có ID `1212451`), hãy sử dụng cờ `--page-id`:

```bash
python tools\confluence_writer.py --file Thanh_phan_dung_chung.md --page-id 1212451
```

### 3. Cập nhật trang và ÉP tải lại toàn bộ ảnh
Nếu bạn nhận thấy ảnh trên Confluence bị lỗi và muốn tool bắt buộc tải lên lại toàn bộ ảnh (không quan tâm mã Hash giống hay khác nhau), hãy thêm cờ `--force-update-images`:

```bash
python tools\confluence_writer.py --file Thanh_phan_dung_chung.md --page-id 1212451 --force-update-images
```

---

## ⚙️ Các Tham số hỗ trợ (Arguments)

| Tham số | Bắt buộc | Chức năng |
| :--- | :---: | :--- |
| `--file` | **Có** | Đường dẫn đến file Markdown cần đọc. |
| `--page-id` | Tùy chọn* | ID của trang Confluence cần cập nhật nội dung. |
| `--parent-id` | Tùy chọn* | ID của trang cha nếu muốn tạo trang mới. |
| `--title` | Không | Tiêu đề trang. Nếu bỏ trống: khi **tạo trang mới** tool lấy tên file Markdown; khi **cập nhật trang có sẵn** tool giữ nguyên tiêu đề hiện tại của trang trên Confluence. |
| `--space` | Không | Space Key của Confluence (nếu bỏ trống, tool sẽ lấy trong file `.env`). |
| `--force-update-images` | Không | Ép tải lại tất cả ảnh bất chấp kiểm tra mã Hash. |

*\*Lưu ý: Bắt buộc phải cung cấp một trong hai tham số `--page-id` hoặc `--parent-id`.*

---
**Yêu cầu hệ thống:** Đảm bảo file `.env` đã khai báo đúng `CONFLUENCE_TOKEN` và `CONFLUENCE_URL`. Cần cài các package `requests`, `markdown`, `beautifulsoup4` (`pip install requests markdown beautifulsoup4`).
