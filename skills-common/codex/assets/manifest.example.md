# Manifest — danh mục chức năng của dự án

Chép file này ra gốc dự án, đặt tên `manifest.md`, rồi đưa vào SVN/Git cùng
với `registries/`.

Đây là **sổ cấp phát mã `FUNC-`**, không phải bản kiểm kê. Kiểm kê thì dẫn
xuất được từ đĩa bất cứ lúc nào (`project_check.py` liệt kê mọi file đặc tả).
Cấp phát thì không: mã phải giữ chỗ **trước khi** file tồn tại, nếu không hai
BA cùng lấy `FUNC-QLSP-048` và không gì phát hiện ra.

Vì vậy quy trình là: **cấp mã ở đây trước, commit, rồi mới viết file.**

## Quy tắc

- Một dòng một mã. Mã đã cấp thì **không tái sử dụng**, kể cả khi bỏ chức năng
  — mã cũ còn nằm trong tài liệu khác và trong lịch sử page Confluence.
- Số đánh liên tiếp trong từng phân hệ, bắt đầu từ `001`.
- Cột *Trạng thái*: `Đã cấp` (chưa viết) · `Đang viết` · `Đã phát hành` ·
  `Bỏ` (không dùng nữa, mã vẫn giữ chỗ).
- Bỏ trống cột *Mã UC* nếu chức năng chưa gắn use case nào trong BRD.

`project_check.py` đối chiếu file trên đĩa với bảng này: file mang mã không có
trong manifest là **lỗi**; mã ghi `Đã phát hành` mà không thấy file là **cảnh
báo**; mã trùng dòng là **lỗi**.

Không có `manifest.md` thì skill vẫn chạy, chỉ cảnh báo — một BA làm một mình
không cần cấp phát.

## Danh mục

| Mã | Tên chức năng | Loại | Phân hệ | Nhóm | Mã UC | Người phụ trách | Trạng thái | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| FUNC-QLNSD-001 | Quản lý người dùng | UI | QLNSD | GRP-QLNSD-01 | UC-0301, UC-0302 | Ngọc | Đã phát hành | |
| FUNC-QLNSD-002 | Quản lý vai trò | UI | QLNSD | GRP-QLNSD-01 | | Ngọc | Đã cấp | Tiền đề của FUNC-QLNSD-001 |
| FUNC-QLSP-047 | Tạo lập sản phẩm | UI | QLSP | | | | Đang viết | |
| FUNC-KTOAN-012 | Đối soát giao dịch | JOB | KTOAN | | | | Đã cấp | Chờ BRD |

## Nhóm chức năng

Mã `GRP-` **không** cấp ở đây — nó nằm trong `registries/groups.csv`, vì nhóm
là mã dùng chung phải khớp cây menu ứng dụng. Cột *Nhóm* ở trên chỉ để tra
cứu nhanh.
