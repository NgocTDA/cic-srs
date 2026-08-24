# Văn phong và quy ước trình bày

Phần A là giọng văn — thứ script không kiểm được, phải tự giữ. Phần B là quy
ước hình thức, `validate.py` kiểm được phần lớn.

---

# A. Giọng văn

## A1. Điều kiện → kết quả

Mỗi câu quy tắc nêu rõ **khi nào** và **thì sao**. Câu thiếu một trong hai vế
là câu chưa đặc tả xong.

| Không viết | Viết |
|---|---|
| Kiểm tra tên đăng nhập hợp lệ. | Khi tên đăng nhập đã tồn tại, hệ thống dừng việc ghi và hiển thị `ERR_101`. |
| Hệ thống xử lý lỗi gửi thư. | Khi ghi thành công nhưng gửi thư thất bại, hệ thống giữ tài khoản đã tạo và hiển thị `WAR_001`. |
| Phân trang dữ liệu. | Kết quả hiển thị 20 dòng mỗi trang, sắp xếp mặc định theo ngày tạo giảm dần. |

## A2. Một ý một dòng

Câu ghép nhiều điều kiện làm người đọc phải tự tách ra, và mỗi người tách một
kiểu.

> **Không:** Tên đăng nhập phải duy nhất, dài 6–32 ký tự, chỉ gồm chữ và số, và
> không được trùng với tài khoản đã ngừng hiệu lực.

> **Có:** tách thành `BR-…-001` (duy nhất), `BR-…-002` (độ dài và ký tự), và
> nêu riêng phạm vi kiểm trùng có tính cả tài khoản đã ngừng hiệu lực hay không.

## A3. Không dùng từ nước đôi

Trong câu quy phạm, bỏ hẳn: **thường**, **có thể**, **nên**, **tuỳ**, **linh
hoạt**, **phù hợp**, **hợp lý**, **thân thiện**.

| Không viết | Viết |
|---|---|
| Hệ thống nên cảnh báo người dùng. | Hệ thống hiển thị `CONF_001` trước khi đóng biểu mẫu. |
| Thời gian phản hồi hợp lý. | Thời gian phản hồi tối đa 3 giây với truy vấn dưới 10.000 bản ghi. |
| Giao diện thân thiện. | *(bỏ — không kiểm được, không thuộc đặc tả)* |

Ngoại lệ: mục *Vấn đề còn mở* được phép viết nước đôi, vì nó đang ghi lại điều
chưa chốt.

## A4. Tham chiếu bằng mã, không chép lại

Quy tắc định nghĩa **một lần** ở *Quy tắc nghiệp vụ*. Mọi nơi khác trỏ bằng mã.

> **Không:** *(ở bảng thành phần)* Tên đăng nhập phải duy nhất, dài 6–32 ký tự…

> **Có:** Áp dụng `BR-QLNSD-001-001` và `BR-QLNSD-001-002`. Vi phạm thì
> `ERR_101` hoặc `ERR_102`.

Chép lại nghĩa là sau này sửa quy tắc thì phải nhớ sửa mấy chỗ — và sẽ quên.

## A5. Mỗi trường khai đúng một lần

Danh sách trường chỉ nằm ở *Mô tả các thành phần trên giao diện* (loại `UI`) hoặc
*Danh sách trường* (loại `DANHMUC`). Mục *Luồng xử lý* và *Xử lý sự kiện* nói về
hành vi, không liệt kê lại trường.

## A6. Thông báo tách khỏi mô tả

Nội dung thông báo nằm ở bảng *Thông báo*, không nằm trong ô mô tả trường. Chỗ
khác chỉ ghi mã.

Giọng thông báo: lịch sự, nói rõ phải làm gì, không đổ lỗi người dùng.

| Không viết | Viết |
|---|---|
| Bạn đã nhập sai! | Tên đăng nhập chỉ gồm chữ cái không dấu, chữ số và dấu chấm, dài 6–32 ký tự. |
| Lỗi hệ thống. | Hệ thống đang bận. Vui lòng thử lại sau. |

## A6b. Thông báo có tham số

Nhiều thông báo chỉ khác nhau ở đối tượng. Những câu đó dùng **một mã duy nhất**
với nguyên mẫu có tham số, không tách thành nhiều mã.

Trong `messages.csv`:

```
ERR_042 | Không thể xóa {doi_tuong} ở trạng thái {trang_thai}. | doi_tuong, trang_thai
```

Tại bảng *Thông báo* trong file chức năng, cột *Nội dung* giữ **nguyên mẫu**,
cột *Tham số* khai giá trị thay thế:

| Mã | Nội dung | Tham số | Điều kiện phát sinh |
|---|---|---|---|
| ERR_042 | Không thể xóa {doi_tuong} ở trạng thái {trang_thai}. | `doi_tuong` = NGUOIDUNG · `trang_thai` = ST-NGUOIDUNG-01 | Xoá tài khoản đang hoạt động |

Người dùng cuối sẽ thấy: *"Không thể xóa người dùng ở trạng thái Hoạt động"* —
chữ hiển thị lấy từ cột tên hiển thị trong `objects.csv` và `states.csv`, không
phải mã trần.

**Viết hoa tên hiển thị — cố ý bất đối xứng:**

| Loại | Cách viết | Ví dụ |
|---|---|---|
| Đối tượng nghiệp vụ | **chữ thường** | `người dùng`, `sản phẩm` |
| Trạng thái | **hoa chữ đầu** | `Chờ phê duyệt`, `Đang xử lý` |

Đối tượng là danh từ chung, trạng thái là tên riêng do hệ thống định nghĩa. Thế
cả hai vào cùng một câu chỉ đọc xuôi khi mỗi loại giữ đúng kiểu viết của nó:
*"Không thể xóa **người dùng** ở trạng thái **Chờ phê duyệt**"*.

**Bốn luật:**

- Tham số viết `{ten_khong_dau}` — không dấu, không khoảng trắng. `{đối tượng}`
  sẽ vỡ khi parse và khi đưa sang i18n.
- Nguyên mẫu **không có** tham số thì cột *Tham số* **để trống**, không ghi
  "Không áp dụng". Cột này suy ra được từ cột *Nội dung*, nên validator kiểm
  được cả hai chiều — không có chỗ mơ hồ giữa "không có tham số" và "quên điền".
- Chỉ gộp khi câu **giống hệt nhau trừ tham số**. Gần giống thì tách mã riêng.
  Bẻ câu cho vừa khuôn sẽ ra thông báo gượng gạo — đó là dấu hiệu nên tách.
- Cột tên hiển thị lưu **cụm danh từ hoàn chỉnh**; nguyên mẫu không tự thêm loại
  từ. Chỗ nào ngữ pháp không thế được thì tách mã, đừng ép.

**Mọi mã thông báo tham chiếu ở bất kỳ đâu trong file** — bảng quy tắc nghiệp
vụ, luồng ngoại lệ, xử lý sự kiện — **phải có dòng ở bảng *Thông báo* của cùng
file**. Không có thì dev đọc thấy mã mà không tra được nội dung.

## A7. Tiêu chí chấp nhận phải kiểm được

3–6 câu mỗi tính năng. Mỗi câu quan sát được đúng/sai. Đây không phải kịch bản
kiểm thử đầy đủ — kịch bản thuộc tài liệu kiểm thử.

| Không viết | Viết |
|---|---|
| Tìm kiếm hoạt động tốt. | Khi `ROLE-QTDV` tìm kiếm không nhập điều kiện, hệ thống chỉ trả về tài khoản thuộc đơn vị của người dùng đăng nhập. |
| Xử lý lỗi đúng. | Khi truy vấn không có kết quả, hệ thống giữ nguyên điều kiện đã nhập và hiển thị `INF_001`. |

## A8. Phạm vi dữ liệu: nêu quy tắc, không liệt kê

> **Không:** Xem được đơn vị Hà Nội, Hải Phòng, Đà Nẵng.

> **Có:** Đơn vị của người dùng đăng nhập.

Danh sách đơn vị là dữ liệu vận hành, thay đổi theo thời gian, không thuộc đặc
tả tĩnh.

## A9. Nói cả điều KHÔNG thuộc phạm vi

Dùng hai dòng *Trong phạm vi* / *Ngoài phạm vi* ở bảng *Mô tả chung* — không
nhét ranh giới vào *Mô tả chức năng*. Người đọc cần biết chỗ nào phải tìm sang
tài liệu khác, và tra được đồng nhất trên hàng trăm đặc tả vì luôn nằm đúng một
dòng.

> **Trong phạm vi:** Tra cứu, tạo mới và gán vai trò đã tồn tại cho tài khoản.
> **Ngoài phạm vi:** Tạo/sửa vai trò thuộc `FUNC-QLNSD-002`; đổi mật khẩu thuộc
> `FUNC-QLNSD-003`; đồng bộ tài khoản từ AD không thuộc phiên bản này.

Bốn nguyên tắc:

- *Trong phạm vi* không phải bản sao danh sách tính năng — nêu trách nhiệm và
  kết quả, không liệt kê lại từng `FEAT-`.
- *Ngoài phạm vi* chỉ nêu phần **dễ bị hiểu nhầm** là thuộc chức năng này, không
  liệt kê mọi thứ chức năng không làm.
- Chuyển trách nhiệm sang nơi khác thì phải ghi mã `FUNC-`/`GRP-` liên quan.
- Không viết "Không áp dụng" một cách máy móc — chỉ dùng khi thực sự không có
  ranh giới nào đáng nói. Nội dung chưa chốt vẫn đánh dấu `⟨?⟩` như mọi mục
  khác.

---

# B. Quy ước trình bày

## B1. Style — đúng 6 style, không hơn

| Dùng cho | Style |
|---|---|
| Tên chức năng | `Heading 3` |
| Mục cấp chức năng · tiêu đề khối Tính năng | `Heading 4` |
| Mục trong khối Tính năng | `Heading 5` |
| Đoạn văn | `T-NoiDung` |
| Gạch đầu dòng cấp 1 / 2 / 3 | `T-Gach -` / `T-Gach +` / `T-Gach *` |
| Ghi chú, và mô tả nhóm chức năng | `T-GhiChu` |
| Chú thích ảnh, sơ đồ, bảng | `Caption` |
| Bảng | `TableStyle3` |

Cỡ chữ do style quyết định: thân bài 13pt · bảng 12pt · caption 11pt. Times New
Roman toàn bộ, thân bài căn đều hai bên. **Cấm tạo style mới, cấm định dạng trực
tiếp.**

Lý do: khi ghép vào tài liệu tổng, style trùng tên nhưng khác định nghĩa sẽ bị
master ghi đè — file con nhìn đẹp lúc soạn, vào bản tổng thì biến dạng.

## B2. Đánh số — không gõ tay

Số mục, số hình, số bảng đều do Word sinh. Gõ tay sẽ sai ngay khi chèn thêm một
mục ở trên.

## B3. Mã tham chiếu

Mã tính năng và mã quy tắc **phải thuộc chức năng chứa nó**: `FUNC-QLSP-047`
chỉ chứa `FEAT-QLSP-047-nn` và `BR-QLSP-047-nnn`. Chép khối Tính năng từ file
khác mà quên đổi mã sẽ bị chặn.

Mã thông báo dùng chung toàn hệ thống, đánh số theo từng loại. Tra `messages.csv`
trước: cùng nội dung thì dùng lại mã cũ, kể cả khi phân hệ khác đang dùng.

**Mã thông báo KHÔNG mang mã phân hệ.** Dạng đúng là `ERR_014`, không phải
`ERR_QLSP_014`. Số chạy chung toàn hệ thống theo từng loại — không theo đối
tượng, không theo phân hệ. Đây là chỗ hay hiểu ngược, dẫn tới đẻ mã mới cho một
câu đã có sẵn.

Cần mã mới thì thêm vào sổ **trong cùng lần nộp**, không tự đặt trong file rồi
tính sau.

## B4. Tham chiếu chéo

| Loại | Cách làm |
|---|---|
| Trong cùng file | Cross-reference — được phép |
| Sang chức năng khác | Gõ theo mã: "xem `FUNC-QLSP-047`" |
| Sang phần chung | Gõ theo tên mục |

Không Cross-reference sang file khác — bookmark chỉ tồn tại trong file gốc, sau
khi ghép sẽ hiện `Error! Reference source not found`.

## B5. Bố cục

Không chèn ngắt trang, ngắt phần, text box. Không sửa header/footer, khổ giấy,
lề. Bố cục do `base.docx` quyết định.

---

# C. Checklist trước khi nộp

**Cấu trúc**
- [ ] Đủ mục theo loại, không thiếu không thừa, đúng thứ tự
- [ ] Mục không áp dụng đã ghi `Không áp dụng`, không xoá mục
- [ ] Mỗi tính năng đủ mục cấp tính năng *(trừ `PHANTICH` — không có tầng này)*
- [ ] Mã tính năng liên tiếp từ `01`, thuộc đúng chức năng

**Nội dung**
- [ ] Bảng *Mô tả chung* điền đủ, có nêu ranh giới phạm vi
- [ ] Mọi tính năng có ít nhất một dòng ở *Ma trận phân quyền*
- [ ] Cột vai trò dùng mã thật, không còn `«ROLE_n»`
- [ ] Phạm vi dữ liệu nêu quy tắc, không liệt kê tên đơn vị
- [ ] *(`UI`)* Màn hình có mã `MH-…`, được tham chiếu ở *Luồng màn hình* và
      *Thiết kế giao diện*
- [ ] Mọi mã thông báo có trong `messages.csv`
- [ ] *Phân loại dữ liệu* khai đủ mọi trường là dữ liệu cá nhân
- [ ] Mỗi tính năng có 3–6 tiêu chí chấp nhận kiểm được
- [ ] *(`PHANTICH`)* Mọi mã chỉ tiêu ở *Danh mục chỉ tiêu* có dòng ở
      *Công thức và truy vấn*

**Phát hành**
- [ ] Không còn `⟨?⟩` trong thân bài
- [ ] Mục *Vấn đề còn mở* không còn dòng `Đang chờ`
- [ ] Không còn khung `⟨ THIẾU HÌNH ⟩`
- [ ] `version` khớp dòng `changelog` cuối
- [ ] `validate.py` trả về `0`
