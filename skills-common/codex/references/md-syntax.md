# Cú pháp Markdown — bản giao kèo

Trình đọc của skill chỉ chấp nhận các dạng dưới đây. Viết ra ngoài các dạng này
thì `validate.py` báo lỗi chứ không đoán.

Lý do phải chặt: mỗi mục được đổ vào Word bằng một style khác nhau. Nếu cú pháp
mở, hai người viết cùng một nội dung sẽ ra hai kiểu định dạng, và mục đích của
cả bộ chuẩn là để điều đó không xảy ra.

---

## 1. Front matter

Bắt buộc, nằm ngay đầu file, mở và đóng bằng `---`.

```yaml
---
ma: FUNC-QLNSD-001
ten: Quản lý người dùng
profile: UI
nhom: GRP-QLNSD-01
version: "1.0"
status: approved
outline_id: SRS-STANDARD-DEFAULT
outline_version: "6.1"
changelog:
  - {v: 0.1, ngay: 2026-07-20, nguoi: Ngọc TDA, mo_ta: Tạo mới tài liệu}
  - {v: "1.0", ngay: 2026-08-05, nguoi: Ngọc TDA, mo_ta: "Chốt sau họp 04/08"}
---
```

| Khoá | Bắt buộc | Ghi chú |
|---|---|---|
| `ma` | Có | `FUNC-«phân hệ»-«3 số»` |
| `ten` | Có | |
| `profile` | Có | `UI` / `TICHHOP` / `JOB` / `PHANTICH` / `DANHMUC` |
| `nhom` | Không | mã trong `groups.csv` |
| `version` | Có | phải khớp dòng `changelog` cuối |
| `status` | Có | `draft` / `review` / `approved` |
| `outline_id` | Không | lệch với đề cương của skill thì báo lỗi |
| `outline_version` | Không | lệch số nhỏ thì cảnh báo; lệch số LỚN là lỗi — chạy `migrate_outline.py` |
| `changelog` | Có | ít nhất một dòng, đủ `v` `ngay` `nguoi` `mo_ta` |

Ngày viết `YYYY-MM-DD`. Giá trị chứa dấu `:` hoặc `,` phải đặt trong ngoặc kép.

Đây là tập con của YAML, không phải YAML đầy đủ: chỉ có giá trị đơn và một danh
sách các bản ghi dạng `{k: v}`. Viết YAML phức tạp hơn sẽ báo lỗi cú pháp.

---

## 2. Tiêu đề

| Dạng | Nghĩa | Word |
|---|---|---|
| `# Chức năng [MÃ] Tên` | tên chức năng | Heading 3 *(hoặc 1 nếu `--standalone`)* |
| `## Tên mục` | mục cấp chức năng | Heading 4 |
| `## Tính năng [MÃ] Tên` | mở một khối tính năng | Heading 4 |
| `### Tên mục` | mục trong khối tính năng | Heading 5 |

Tiêu đề mục do `scaffold.py` sinh — **không gõ tay, không sửa chữ, không đổi thứ
tự, không xoá**. Mục không dùng thì ghi `Không áp dụng` ở phần thân.

Không gõ số thứ tự (`1.2`, `a)`) vào tiêu đề. Word tự sinh.

Dòng `## Tính năng [...]` phải đúng khuôn, mã liên tiếp từ `01`.

---

## 3. Thân mục

**Đoạn văn** — một dòng liền, không xuống dòng giữa chừng.

```markdown
Quản trị viên tìm tài khoản theo tên đăng nhập, họ tên và đơn vị.
```

**Gạch đầu dòng** — tối đa **3 cấp**, phân biệt bằng số dấu cách thụt đầu dòng:

| Thụt | Cấp | Style Word |
|---|---|---|
| không thụt | 1 | `T-Gach -` |
| 2 dấu cách | 2 | `T-Gach +` |
| 4 dấu cách | 3 | `T-Gach *` |

```markdown
- ST-NGUOIDUNG-01 — Đang hoạt động.
  - Chuyển sang ST-NGUOIDUNG-02 khi quản trị viên khoá tài khoản.
    - Chỉ ROLE-QTHT thực hiện được thao tác khoá.
```

Sâu hơn 3 cấp gần như luôn là dấu hiệu mục đó nên tách ra, nên cấp 4 trở đi bị
gộp về cấp 3.

Nếu mẫu Word chưa có style `T-Gach *`, cấp 3 tạm dùng cấp 2 và script cảnh báo —
tài liệu vẫn ra, không bị chặn.

**Nhấn mạnh trong câu** — `**chữ đậm**` thành chữ đậm thật trong Word. Dùng tiết
chế, chủ yếu để nhấn từ phủ định: *"Chức năng **không** xử lý đăng nhập"*.

Dấu nháy ngược `` `mã` `` được bỏ dấu, chỉ giữ chữ — giao kèo style không có
style chữ đơn cách. Không dùng `*in nghiêng*`, `~~gạch ngang~~`, hay liên kết
`[chữ](địa chỉ)`.

**Ghi chú hướng dẫn** — dòng bắt đầu bằng `>`. Đây là lời nhắc cho BA;
`render.py` **bỏ hẳn**, không đưa vào tài liệu. Giữ hay xoá đều được.

---

## 4. Bảng

Bảng pipe chuẩn. **Số cột và tiêu đề cột phải khớp đề cương** — đó là điều
`validate.py` kiểm.

```markdown
| Mã quy tắc | Nội dung quy tắc | Áp dụng cho | Mã thông báo khi vi phạm |
|---|---|---|---|
| BR-QLNSD-001-001 | Tên đăng nhập là duy nhất. | FEAT-QLNSD-001-02 | ERR_101 |
```

Mục có nhiều bảng (ví dụ *Luồng xử lý*) thì mỗi bảng có dòng nhãn in đậm ngay
trên, viết đúng nhãn trong đề cương:

```markdown
**Luồng chính**

| Bước | Tác nhân | Hành động | Phản hồi của hệ thống |
|---|---|---|---|
```

**Cột `«...»` là chỗ trống.** Trong *Ma trận phân quyền*, `«ROLE_1» «ROLE_2»
«ROLE_3»` thay bằng mã vai trò thật, và **số cột được phép khác 3** — chức năng
cần 2 hay 5 vai trò đều hợp lệ. Còn để nguyên `«ROLE_1»` thì báo lỗi.

**Bảng phải cách nội dung khác bằng một dòng trắng** — cả trên lẫn dưới.

```markdown
**Luồng thay thế**
                        ← dòng trắng, bắt buộc
| Mã luồng | Xử lý |
|---|---|
| ALT-01 | … |
                        ← dòng trắng, bắt buộc
### Thiết kế giao diện
```

Trình đọc của skill vẫn hiểu đúng khi thiếu dòng trắng, **nhưng mọi trình
markdown khác thì không**: nội dung dính ngay sau bảng bị hút vào ô cuối
(`### Thiết kế giao diện` thành một dòng mới, còn nguyên dấu `###`), còn nội
dung dính ngay trước bảng làm bảng không dựng được. File `.md` là bản gốc và
được soát trên GitHub hay trình xem của trình soạn thảo, nên `validate.py` báo
đây là **lỗi**. Sửa: `python scripts/srs.py fix «file».md`.

**Dòng nguồn của bảng luôn là một dòng** — markdown không cho một hàng trải
qua nhiều dòng. Nhưng *ô* thì mang được nhiều ý, bằng dấu `·`:

```markdown
| EXC-01 | Không có bản ghi | Hệ thống: ·· Giữ nguyên điều kiện ·· Hiển thị lưới rỗng · Ghi nhật ký | INF_001 |
```

Số dấu `·` là cấp: `·` cấp 1, `··` cấp 2, `···` cấp 3 — tối đa 3 cấp. Khi
render, các ý này thành **gạch đầu dòng thật** trong Word (`T-Gach -/+/*`).
Nhập ngược lại cho đúng chuỗi ban đầu, nên vòng khép kín không đổi.

**Chỉ một số cột được như vậy**, khai ở `multiline_columns` trong
`outline.json`:

| Nhóm cột | Nhiều ý | Vì sao |
|---|---|---|
| **Hệ thống xử lý** — *Xử lý của hệ thống*, *Xử lý*, *Phản hồi của hệ thống*, *Kết quả / Mã thông báo*, *Ghi nhận kết quả*, *Hành động khi sai*, *Xử lý giá trị thiếu* | **Được** | Các bước tuần tự — nhiều ý là bản chất |
| **Điều kiện** — *Điều kiện*, *Điều kiện rẽ nhánh*, *Điều kiện phát sinh*, *Điều kiện lọc*, *Điều kiện lấy dữ liệu* | **Được** | Một tình huống thường do nhiều mệnh đề hợp lại; tách thành dòng riêng sẽ nhân bản y hệt phần xử lý |
| **Công thức** — *Truy vấn / Công thức tính*, *Công thức nghiệp vụ* | **Được** | Vốn đã nhiều dòng ngoài đời |
| *Nội dung vấn đề* | **Được** | Một vấn đề còn mở thường gồm mấy nhánh chờ quyết |
| *Mô tả ràng buộc*, *Nội dung quy tắc*, *Nội dung kiểm tra*, *Tiêu chí chấp nhận* | Không — render một dòng liền, kèm cảnh báo | Chuẩn quy định mỗi ràng buộc một mã `BR-` riêng. Cho bullet vào đây sẽ làm một ô chật đọc dễ chịu, và mất luôn động cơ tách |
| **Thao tác của tác nhân** — *Hành động*, *Sự kiện / Thao tác*, *Thao tác thủ công*, *Endpoint / Thao tác* | Không | Bảng đã có cột *Bước* / *Mã tính năng* làm trục tuần tự — gộp vào một ô là né việc tách bước |
| **Mô tả** — *Mô tả*, *Mô tả / Ghi chú*, *Mô tả nghiệp vụ*, *Ý nghĩa*, *Ghi chú* | Không | Mô tả là văn xuôi |
| Còn lại | Không | Vốn ngắn — trung vị 8 ký tự. Cột *Nội dung* ở bảng thông báo cũng giữ nguyên: đó là chuỗi hiển thị thật cho người dùng |

Danh sách đầy đủ ở `multiline_columns.cho_phep` / `.canh_bao`; bảng trên chỉ
nhóm lại cho dễ nhớ. Gõ `·` vào cột không khai thì `validate.py` nhắc — dấu sẽ
hiện ra như ký tự thường chứ không thành gạch đầu dòng.

Vì dòng nguồn vẫn là một dòng, `git diff` vẫn gọn và `grep` một mã vẫn ra đúng
một dòng — hai ưu điểm của luật cũ được giữ nguyên.

Khi **nhập từ tài liệu cũ**, `import_docx.py` tự sinh các dấu `·` này từ gạch
đầu dòng trong Word. Dòng văn xuôi thiếu dấu câu cuối được thêm dấu chấm; ký
tự `|` trong nội dung được escape thành `\|`.

**Cột `STT` không phải gõ tay.** Nó là số thứ tự dòng, cùng loại với số mục,
số hình, số bảng — `render.py` **luôn tính lại** lúc xuất, nên số trong `.md`
sai hay trống đều không lọt vào tài liệu. Chèn một dòng vào giữa bảng thì
không phải đánh số lại gì cả.

Hai ngoại lệ được giữ nguyên: ô `STT` có **chữ** (không phải số) thì không bị
ghi đè, và **dòng nhãn** — dòng chỉ có chữ ở ô đầu, các ô còn lại trống, dùng
làm dải phân cách trong bảng như *"Các button"* — không được đánh số và không
tính vào số đếm.

---

## 5. Hình

**Ảnh** — cú pháp markdown thường, đường dẫn tương đối tới `assets/`:

```markdown
![Màn hình danh sách người dùng](assets/FEAT-QLNSD-001-01_danh-sach.png)
```

Chú thích trong ngoặc vuông trở thành caption `Hình n.` — không gõ tay số hình.
Đặt tên file theo mã tính năng để lần dán sau ghi đè đúng chỗ.

**Sơ đồ** — chỉ để dấu, không dán ảnh:

```markdown
[[DIAGRAM: FUNC-QLNSD-001_seq-01]]
```

File nguồn nằm ở `diagrams/FUNC-QLNSD-001_seq-01.puml`. `render.py` tự render
và chèn kèm caption.

Thiếu hình thì `render.py` chèn khung `⟨ THIẾU HÌNH ⟩` nhìn thấy được trong
`.docx`, kèm hướng dẫn bổ sung. Khung này tính vào cổng chặn.

---

## 6. Đánh dấu chỗ chưa chốt

Chỗ nào suy luận mà BA chưa xác nhận thì chèn `⟨?⟩` ngay tại đó:

```markdown
| 3 | Thư điện tử | Ô nhập văn bản | Có | tối đa 150 ký tự | Áp dụng BR-QLNSD-001-003 ⟨?⟩ |
```

Đồng thời thêm một dòng vào mục *Vấn đề còn mở*:

```markdown
| 1 | Chưa rõ thư điện tử có bắt buộc duy nhất theo đơn vị hay toàn hệ thống | Lead BA | 2026-08-15 | Đang chờ |
```

Còn `⟨?⟩` hoặc còn dòng `Đang chờ` thì chỉ render được bản nháp có đóng dấu.

Mục *Vấn đề còn mở* rỗng (chỉ có dòng tiêu đề bảng) là trạng thái **đúng** của
tài liệu đã chốt — không phải lỗi thiếu nội dung.

---

## 7. Những thứ không dùng

| Không dùng | Vì sao |
|---|---|
| `####` trở xuống | Sâu hơn 5 cấp là dấu hiệu chia mục sai |
| Gạch đầu dòng cấp 4 trở đi | Gộp về cấp 3. Sâu thế thì nên tách mục |
| Bảng lồng bảng, ô gộp | Trình đọc không hỗ trợ; đề cương đã khoá hình dạng mọi bảng |
| HTML thô | Không đổ được sang style Word |
| Khối mã ``` | Không có mục nào cần đến |
| Ngắt trang, ngắt phần | Bố cục do `base.docx` quyết định |
| Gõ tay `Hình 3`, `Bảng 5` | Số do trường SEQ sinh |
| `*in nghiêng*`, `~~gạch~~`, liên kết `[a](b)` | Không đổ được sang style Word; chỉ hỗ trợ `**đậm**` |
