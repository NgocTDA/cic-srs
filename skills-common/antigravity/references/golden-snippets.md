# Mẫu tốt — trích từ file golden

Bản rút của `golden/FUNC-QLNSD-001.md`, đủ để viết đúng các cấu trúc hay dùng.
Chỉ mở file golden đầy đủ khi cần đối chiếu độ sâu nội dung của cả một mục,
hoặc khi soát văn phong.

## 1. Hai dòng phạm vi trong Mô tả chung

```markdown
| Mô tả chức năng | Quản trị viên tra cứu, tạo mới và ngừng hiệu lực tài khoản người dùng nội bộ. |
| Trong phạm vi | Tra cứu, tạo mới và ngừng hiệu lực tài khoản; gán vai trò đã tồn tại cho tài khoản. |
| Ngoài phạm vi | Tạo/sửa vai trò thuộc FUNC-QLNSD-002. Xác thực đăng nhập và đổi mật khẩu thuộc FUNC-QLNSD-003. Đồng bộ tài khoản từ AD không thuộc phiên bản này. |
```

*Trong phạm vi* nêu trách nhiệm, không lặp danh sách tính năng. *Ngoài phạm
vi* chỉ nêu điểm dễ hiểu nhầm, kèm mã `FUNC-` nhận trách nhiệm thay.

## 2. Quy tắc nghiệp vụ — điều kiện, kết quả, mã thông báo

```markdown
| BR-QLNSD-001-001 | Tên đăng nhập là duy nhất trên toàn hệ thống, không phân biệt chữ hoa chữ thường. | FEAT-QLNSD-001-02 | ERR_101 |
| BR-QLNSD-001-006 | Tài khoản ở trạng thái ST-NGUOIDUNG-03 không hiển thị trong kết quả tra cứu mặc định. | FEAT-QLNSD-001-01 | Không áp dụng |
```

Một quy tắc một mã, đánh liên tiếp. Không vi phạm được thì cột thông báo ghi
`Không áp dụng`.

## 3. Luồng chính — tác nhân và phản hồi tách bạch

```markdown
| Bước | Tác nhân | Hành động | Phản hồi của hệ thống |
|---|---|---|---|
| 1 | Quản trị viên | Mở MH-QLNSD-001-002 | Hiển thị biểu mẫu rỗng, danh sách đơn vị lọc theo phạm vi của vai trò. |
| 2 | Quản trị viên | Nhập thông tin và chọn “Lưu” | Kiểm tra BR-QLNSD-001-001 đến BR-QLNSD-001-005. |
| 3 | Hệ thống | — | Ghi tài khoản ở trạng thái ST-NGUOIDUNG-01, sinh mật khẩu tạm, gửi MAIL_001. |
```

Bước hệ thống tự làm: cột Tác nhân là `Hệ thống`, cột Hành động là `—`.
Tham chiếu quy tắc bằng mã `BR-`, không chép lại nội dung.

## 4. Luồng thay thế và ngoại lệ

```markdown
| ALT-01 | Quản trị viên chọn “Huỷ” | Đóng biểu mẫu, không ghi dữ liệu. Có thay đổi chưa lưu thì hỏi xác nhận bằng CONF_001. | — |

| EXC-01 | Tên đăng nhập đã tồn tại | Giữ nguyên dữ liệu đã nhập, đánh dấu trường vi phạm. | ERR_101 |
```

Cột "Quay về bước" phải trỏ số bước có thật trong luồng chính, hoặc `—`.

## 5. Thành phần giao diện — ràng buộc theo từ điển

```markdown
| 1 | Tên đăng nhập | Ô nhập văn bản | Có | 6–32 ký tự | Áp dụng BR-QLNSD-001-001 và BR-QLNSD-001-002. Vi phạm thì ERR_101 hoặc ERR_102. |
| 4 | Vai trò | Danh sách chọn nhiều | Có | tối đa 5 vai trò | Nguồn: roles.csv. Áp dụng BR-QLNSD-001-004. Vi phạm thì ERR_104. |
```

Cách diễn đạt cột cuối lấy từ `validation-catalog.md` — không tự chế câu.

## 6. Thông báo có tham số

```markdown
| 1 | SUC_001 | Toast | Tạo {doi_tuong} thành công. | doi_tuong = NGUOIDUNG | Ghi dữ liệu thành công. |
| 9 | MAIL_001 | Email | Thư cấp tài khoản — gửi tên đăng nhập và mật khẩu tạm cho {ten_nguoi_nhan}. | ten_nguoi_nhan = NGUOIDUNG | Ghi tài khoản thành công. Tiêu đề và nội dung đầy đủ ở messages.csv. |
```

Mọi `{tham_so}` trong Nội dung phải khai ở cột Tham số; nguyên mẫu không có
tham số thì cột đó **để trống**. Giá trị tham số là mã trong
`objects.csv`/`states.csv`.

## 7. Tiêu chí chấp nhận — quan sát được đúng/sai

```markdown
| 1 | Khi tên đăng nhập trùng tài khoản đã có, hệ thống dừng việc ghi và hiển thị ERR_101. | BR-QLNSD-001-001 |
| 5 | Khi chuyển trang, hệ thống giữ nguyên điều kiện tìm kiếm và thứ tự sắp xếp. | Không áp dụng |
```

Khuôn «Khi … thì hệ thống phải …». 3–6 câu mỗi tính năng.

## 8. Ma trận phân quyền — mã ở đúng cột

```markdown
| STT | Mã tính năng | Tính năng / Thao tác | ROLE-QTHT | ROLE-QTDV | ROLE-NVNV | Phạm vi dữ liệu |
|---|---|---|---|---|---|---|
| 1 | FEAT-QLNSD-001-01 | Tra cứu danh sách người dùng | X | X | X | ROLE-QTHT: toàn hệ thống. ROLE-QTDV và ROLE-NVNV: đơn vị của người dùng đăng nhập. |
```

Tiêu đề cột vai trò là mã thật trong `roles.csv`, số cột tuỳ chức năng. Mã
tính năng nằm ở cột "Mã tính năng" — để ở cột khác là lỗi.

## 9. Phạm vi dữ liệu — quy tắc, không liệt kê

Đúng: `Đơn vị của người dùng đăng nhập.` · Sai: `Hà Nội, Hải Phòng, Đà Nẵng.`

## 10. Điểm treo

```markdown
Thời gian giữ tệp kết quả: 30 ngày ⟨?⟩

| 1 | Chốt thời gian giữ tệp kết quả — BRD ghi 7 ngày, họp 04/08 ghi 30 ngày. | Ngọc TDA | 2026-09-01 | Đang chờ |
```

Mỗi dấu `⟨?⟩` có một dòng tương ứng ở *Vấn đề còn mở*. Hai nguồn mâu thuẫn thì
ghi cả hai, không tự chọn.
