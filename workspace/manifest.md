# Manifest — danh mục chức năng của dự án CIC_CORE

Đây là **sổ cấp phát mã `FUNC-`**, không phải bản kiểm kê. Kiểm kê thì dựng lại
được từ đĩa bất cứ lúc nào. Cấp phát thì không: mã phải giữ chỗ **trước khi**
file tồn tại, nếu không hai BA cùng lấy `FUNC-QLSP-048` và không gì phát hiện.

**Quy trình: cấp mã ở đây trước → commit → rồi mới viết file.**

## Quy tắc

- Một dòng một mã. **Mã đã cấp không tái sử dụng**, kể cả khi bỏ chức năng —
  mã cũ còn nằm trong tài liệu khác và trong lịch sử page Confluence.
- Số đánh liên tiếp trong từng phân hệ, bắt đầu từ `001`.
- Trạng thái: `Đã cấp` (chưa viết) · `Đang viết` · `Đã phát hành` · `Bỏ`.
- Mã `GRP-` **không** cấp ở đây — nó ở `registries/groups.csv` vì phải khớp
  cây menu ứng dụng. Cột *Nhóm* dưới đây chỉ để tra cứu nhanh.

`project_check.py` đối chiếu file trên đĩa với bảng này: file mang mã không có
trong manifest là **lỗi**; mã ghi `Đã phát hành` mà không thấy file là **cảnh
báo**; mã trùng dòng là **lỗi**.

## Danh mục

| Mã | Tên chức năng | Loại | Phân hệ | Nhóm | Mã UC | Người phụ trách | Trạng thái | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

<!-- Xoá dòng trống ở trên khi thêm dòng thật.
     Ví dụ một dòng đã điền:
| FUNC-QLNSD-001 | Quản lý người dùng | UI | QLNSD | GRP-QLNSD-01 | UC-0301 | Ngọc | Đang viết | |
-->
