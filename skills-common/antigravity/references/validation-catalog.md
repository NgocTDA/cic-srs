# Từ điển ràng buộc — cách diễn đạt chuẩn

Dùng khi viết cột *Mô tả ràng buộc* trong bảng thành phần giao diện, và cột
*Nội dung quy tắc* trong bảng quy tắc nghiệp vụ.

**Vì sao cần từ điển:** cùng một ràng buộc, mười BA viết mười kiểu. Dev đọc
mười kiểu thì kiểm mười kiểu, và bộ test case không tái sử dụng được. Câu chữ
thống nhất quan trọng hơn câu chữ hay.

**Luật chung:** nêu ràng buộc, rồi trỏ mã thông báo bằng `→`. Không viết nội
dung thông báo tại chỗ.

---

## Độ dài và kích thước

| Ràng buộc | Viết |
|---|---|
| Độ dài tối đa | `Tối đa 255 ký tự.` |
| Độ dài tối thiểu | `Tối thiểu 6 ký tự → ERR_012.` |
| Khoảng độ dài | `Từ 6 đến 32 ký tự → ERR_012.` |
| Kích thước tệp | `Tối đa 10 MB mỗi tệp → ERR_030.` |
| Số lượng tối đa | `Chọn tối đa 5 vai trò → ERR_104.` |

## Bắt buộc và mặc định

| Ràng buộc | Viết |
|---|---|
| Bắt buộc | `Bắt buộc — chặn lưu nếu trống → ERR_001.` |
| Bắt buộc có điều kiện | `Bắt buộc khi «điều kiện» → ERR_001.` |
| Giá trị mặc định | `Mặc định «giá trị».` |
| Chỉ đọc | `Chỉ đọc. Giá trị lấy từ «nguồn».` |
| Chỉ đọc có điều kiện | `Chỉ đọc khi bản ghi ở trạng thái ST-«…»-«nn».` |

## Định dạng

| Ràng buộc | Viết |
|---|---|
| Thư điện tử | `Phải đúng định dạng thư điện tử → ERR_020.` |
| Số điện thoại | `Chỉ chữ số, 10 ký tự → ERR_021.` |
| Mật khẩu | `Tối thiểu 8 ký tự, gồm chữ hoa, chữ thường và chữ số → ERR_022.` |
| Ký tự cho phép | `Chỉ chữ cái không dấu, chữ số và dấu chấm → ERR_102.` |
| Mã theo khuôn | `Theo dạng «khuôn». Sai dạng → ERR_023.` |

## Số

| Ràng buộc | Viết |
|---|---|
| Chỉ số dương | `Chỉ nhập số dương. Ký tự không hợp lệ bị chặn khi gõ.` |
| Khoảng giá trị | `Giá trị từ 0 đến 100 → ERR_015.` |
| Số chữ số thập phân | `Tối đa 2 chữ số thập phân, làm tròn xuống.` |
| Tiền tệ | `Đơn vị đồng. Hiển thị phân cách hàng nghìn, nhập không cần phân cách.` |

## Ngày tháng

| Ràng buộc | Viết |
|---|---|
| Không cho quá khứ | `Chỉ chọn từ hôm nay trở đi. Ngày quá khứ bị vô hiệu.` |
| Không cho tương lai | `Chỉ chọn đến hôm nay. Ngày tương lai bị vô hiệu.` |
| Khoảng ngày | `"Đến ngày" phải lớn hơn hoặc bằng "Từ ngày" → ERR_010.` |
| Độ dài khoảng | `Khoảng tra cứu tối đa 12 tháng → ERR_011.` |
| Định dạng hiển thị | `Hiển thị dd/MM/yyyy. Lưu theo múi giờ hệ thống.` |

## Trùng lặp và tham chiếu

| Ràng buộc | Viết |
|---|---|
| Duy nhất toàn hệ thống | `Duy nhất trên toàn hệ thống → ERR_008.` |
| Duy nhất theo phạm vi | `Duy nhất trong phạm vi «đơn vị / kỳ / nhóm» → ERR_008.` |
| Không phân biệt hoa thường | `Duy nhất, không phân biệt chữ hoa chữ thường → ERR_008.` |
| Nguồn dữ liệu | `Nguồn: «tên danh mục / tên sổ».` |
| Phụ thuộc trường khác | `Danh sách lọc theo giá trị của «trường».` |
| Không xoá khi đang dùng | `Không xoá được khi còn bản ghi tham chiếu → ERR_040.` |

## Trạng thái và quyền

| Ràng buộc | Viết |
|---|---|
| Theo trạng thái | `Chỉ sửa được khi bản ghi ở trạng thái ST-«…»-«nn» → ERR_050.` |
| Theo vai trò | `Chỉ vai trò ROLE-«…» thực hiện được → ERR_105.` |
| Theo phạm vi dữ liệu | `Chỉ thao tác trên bản ghi thuộc đơn vị của người dùng đăng nhập → ERR_105.` |

## Tệp đính kèm

| Ràng buộc | Viết |
|---|---|
| Định dạng cho phép | `Chỉ nhận .pdf, .xlsx, .docx → ERR_031.` |
| Số lượng | `Tối đa 5 tệp mỗi bản ghi → ERR_032.` |
| Quét mã độc | `Tệp bị từ chối nếu không qua kiểm tra mã độc → ERR_033.` |

---

## Ba lỗi diễn đạt hay gặp

**Viết nội dung thông báo tại chỗ**

> Sai: `Bắt buộc. Nếu trống hiện "Vui lòng nhập tên đăng nhập".`
> Đúng: `Bắt buộc — chặn lưu nếu trống → ERR_001.`

Nội dung thông báo nằm ở bảng *Thông báo* và ở `messages.csv`. Viết tại chỗ là
tạo bản sao, và bản sao sẽ lệch.

**Gộp nhiều ràng buộc vào một câu**

> Sai: `Bắt buộc, tối đa 32 ký tự, duy nhất, chỉ chữ và số.`
> Đúng: tách thành các mã `BR-` riêng, ô mô tả chỉ trỏ mã.

Dùng gạch đầu dòng `·` cũng **không** làm nó đúng lên:

> Vẫn sai: `· Bắt buộc · Tối đa 32 ký tự · Duy nhất · Chỉ chữ và số`

Cột *Mô tả ràng buộc*, *Nội dung quy tắc*, *Nội dung kiểm tra* và *Tiêu chí
chấp nhận* cố ý nằm ở `multiline_columns.canh_bao` — chúng render một dòng liền
và `validate.py` đếm số ô như vậy để nhắc. Trình bày đẹp hơn ở đây chỉ che đi
việc phải tách.

*Nội dung kiểm tra* (bảng *Tầng kiểm tra*, loại `JOB`) nằm cùng nhóm vì dòng đã
mang sẵn một *Mã quy tắc*: hai phép kiểm trong một ô nghĩa là thiếu một dòng,
không phải thiếu gạch đầu dòng.

Các cột **bước xử lý** thì ngược lại — nhiều ý là bản chất, và ở đó `·` thành
gạch đầu dòng thật:

> Đúng: `Hệ thống: ·· Kiểm tra BR-QLSP-047-001 ·· Ghi bản ghi · Gửi MAIL_001`

**Mô tả cách làm thay vì ràng buộc**

> Sai: `Hệ thống gọi API kiểm tra trùng rồi hiện lỗi.`
> Đúng: `Duy nhất trên toàn hệ thống → ERR_008.`

Cách hiện thực thuộc về Dev. Đặc tả nêu điều kiện và kết quả.
