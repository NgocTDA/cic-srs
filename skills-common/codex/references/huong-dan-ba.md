# Hướng dẫn dùng skill `srs-help`

Dành cho BA. Đọc một lần, sau đó chỉ cần tra phần 2 và phần 5.

---

## 0. Cách làm việc — đọc kỹ phần này trước

Skill dùng được ở hai nơi, và **cách làm khác nhau hẳn**.

### Trên Claude Code (máy của bạn)

Có repo thật. Tạo thư mục một lần rồi dùng mãi:

```
du-an/
├── srs-config.json          ← chép từ assets/config.example.json trong skill
├── manifest.md              ← danh mục chức năng: cấp mã FUNC- ở đây trước
├── registries/              ← 8 sổ CSV, dùng chung cả dự án
├── project-rules/
│   └── srs-help.md          ← luật riêng dự án (nếu có). Skill đọc SAU skill lõi
│
├── sources/legacy/          ← BẤT BIẾN — không bao giờ sửa
│   ├── docx/qlnsd/
│   └── confluence/«SPACE»/roots/«page-id»/
│       ├── latest.json
│       └── snapshots/«run-id»/{pages,attachments,manifest.json}
│
├── staging/                 ← TÁI TẠO ĐƯỢC — bản bóc thô, xoá cũng không sao
│   ├── qlnsd/
│   └── qlsp/
│
├── migration/               ← kiểm kê và bảng ánh xạ
│   ├── qlnsd/
│   └── qlsp/
│
├── exports/                 ← .docx và .pdf xuất ra. Rác, sinh lại được
│
└── functions/               ← NGUỒN CHÍNH THỨC
    ├── qlnsd/               ← một thư mục mỗi phân hệ, tên VIẾT THƯỜNG
    │   ├── FUNC-QLNSD-001.md
    │   ├── FUNC-QLNSD-002.md
    │   ├── assets/          ← ảnh mockup của PHÂN HỆ NÀY
    │   │   ├── FEAT-QLNSD-001-01_danh-sach.png
    │   │   └── FEAT-QLNSD-002-01_phan-quyen.png
    │   └── diagrams/
    │       └── FUNC-QLNSD-001_seq-01.puml
    └── qlsp/
```

**Tên thư mục phân hệ viết thường, mã vẫn viết HOA.** `functions/qlnsd/` chứa
`FUNC-QLNSD-001.md`. Một phân hệ chỉ có đúng một cách viết trong cả dự án:
Windows không phân biệt hoa thường nên dùng lẫn `qlnsd` và `QLNSD` sẽ chạy
ngon trên máy bạn rồi tách thành hai thư mục ở nơi khác.

**Sổ đăng ký chỉ có một tên: `registries/`.** Đặt tên khác thì `project_check`
báo lỗi — và nếu dự án dùng BA Toolkit, lệnh `init` sẽ tự tạo `registries/`
rỗng bên cạnh, rồi mọi phép kiểm mã sau đó chạy trên sổ rỗng đó.

**Ba tầng, ba luật khác nhau:**

| Thư mục | Luật |
|---|---|
| `sources/legacy/` | **Bất biến.** Giữ nguyên trạng để còn đối chiếu. Mất bản gốc là mất luôn khả năng kiểm khi nghi tài liệu bị sửa tay |
| `staging/` | **Tái tạo được.** Bản `--raw` KHÔNG hợp lệ theo chuẩn — để riêng ra để không ai sửa dần nó thành bản chuẩn |
| `functions/` | **Nguồn chính thức.** Chỉ ở đây mới là SRS thật |

Hình dạng dưới `sources/legacy/confluence/` ở trên là thứ lệnh `pull` của BA
Toolkit sinh ra — mỗi lần kéo là một `run-id` riêng, có `manifest.json` ghi
hash từng tệp. Nếu bạn bóc tay, không dùng toolkit, thì xếp kiểu gì cũng được;
chỉ cần **không sửa gì trong đó**.

`project_check.py` **chỉ chấm tài liệu trong `functions/`**. Bản nháp ở
`staging/`, bản sao ở `sources/` và `migration/` bị bỏ qua có thông báo — vì
bản nháp chưa ai bảo là đúng, còn bản sao thì bạn không được phép sửa.

**`assets/` và `diagrams/` phải nằm ngay cạnh file `.md`** — đây là luật hay
bị vấp nhất. Khi render, đường dẫn `assets/abc.png` trong file `.md` được hiểu
là *cùng thư mục với file `.md` đó*, không phải gốc dự án. Để ở gốc thì bản
Word ra toàn khung `⟨ THIẾU HÌNH ⟩`, mà `validate.py` vẫn báo `0 lỗi` — vì
thiếu hình chỉ là cảnh báo. Chỉ `project_check.py` bắt được, và nó nói rõ tệp
đang ở đâu, cần ở đâu.

Đổi lại: mỗi thư mục phân hệ là một gói **tự đủ**. Nén `functions/qlnsd/` gửi
cho ai đó là họ có đủ mọi thứ để render.

`registries/` thì ngược lại — để ở gốc, dùng chung, vì mã vai trò, thông báo,
trạng thái và use case dùng chung toàn dự án. Truyền qua `--registry-dir` nên
nằm đâu cũng được.

Quy ước đặt tên trong `assets/` và `diagrams/` ở **mục 10**. Điểm cần nhớ
trước: tên ảnh lúc kiểm kê **khác** tên ảnh khi đã vào `functions/`, và việc
đổi tên là một bước có thật trong quy trình.

Claude đọc ghi trực tiếp. Không phải tải gì lên.

### Trên claude.ai (trình duyệt / app)

**Không có thư mục dự án nào.** Máy ảo xoá sạch giữa các phiên — nói *"tôi có
thư mục assets"* thì Claude không thấy gì.

Mỗi phiên làm ba việc:

**Đầu phiên — tải lên.** Nén cả thư mục dự án thành một file `.zip` rồi tải lên
chat. Claude giải nén và kiểm xem đủ chưa:

> Đây là gói dự án của tôi. Kiểm giúp xem đủ chưa.

Claude chạy `project_check.py` và nói rõ thiếu gì — thiếu ảnh nào, thiếu `.puml`
nào, sổ nào chưa có.

**Giữa phiên — làm việc.** Viết, sửa, soát, xuất Word và PDF như thường.

**Cuối phiên — tải về.** Claude trả lại file. **Bạn phải lưu về máy**, gồm:

- File `.md` đã sửa
- Thư mục `assets/` nếu có thêm ảnh mới
- File `.docx` và `.pdf`

Không lưu `assets/` về là lần sau render mất hết ảnh. Claude *nhìn* được ảnh bạn
dán nhưng **không tạo lại được nó**.

Cách gọn nhất: yêu cầu Claude nén lại thành một `.zip` ở cuối phiên, tải về, giải
nén ghi đè lên thư mục dự án trên máy.

### Không có gói dự án thì sao

Vẫn làm được, chỉ mất phần kiểm mã: tải riêng file `.md` cần sửa, dán ảnh vào
chat khi cần. Nhưng không có sổ đăng ký thì `ERR_999` bịa vẫn lọt, nên với việc
thật thì nên tải cả gói.

---

## 1. Nguyên tắc phải nhớ

**File `.md` là bản gốc.** `.docx` và `.pdf` là bản sinh ra. Sửa nội dung trong
Word sẽ mất khi render lần sau.

**Không xoá mục nào.** Mục không dùng thì ghi `Không áp dụng`.

**Không gõ tay số** — số mục, số hình, số bảng, **và cột `STT` trong bảng**
đều do máy sinh. Chèn dòng vào giữa bảng không phải đánh số lại: render tự
tính. Dòng nhãn kiểu *"Các button"* không bị đánh số.

**Nhấn mạnh trong câu** dùng `**chữ đậm**`, sẽ thành chữ đậm thật trong Word.
Không dùng in nghiêng hay gạch ngang — không đổ được sang style.

**Claude không được bịa.** Thiếu thông tin thì nó hỏi bạn. Chỗ nào nó suy luận
mà bạn chưa xác nhận sẽ có dấu `⟨?⟩` và một dòng ở mục *Vấn đề còn mở*. Còn dấu
đó thì chỉ ra được bản nháp.

---

## 2. Viết tài liệu mới

**Bước 1 — Bảo Claude tạo khung**

> Viết đặc tả chức năng `FUNC-QLNSD-001` Quản lý người dùng, loại UI, 2 tính năng.

Claude chạy `scaffold.py`, ra file `FUNC-QLNSD-001.md` có sẵn toàn bộ mục.

**Bước 2 — Đưa nguyên liệu**

Dán vào chat: trích BRD, biên bản họp, danh sách màn hình, quy tắc nghiệp vụ.
Càng cụ thể càng ít bị hỏi lại.

**Bước 3 — Gửi ảnh mockup**

Dán ảnh vào chat, nói rõ thuộc tính năng nào. Claude lưu vào `assets/` và chèn
tham chiếu.

> Ảnh này là màn hình danh sách của `FEAT-QLNSD-001-01`.

**Bước 4 — Trả lời câu hỏi của Claude**

Nó sẽ hỏi những chỗ thiếu. Trả lời hoặc bảo nó ghi vào *Vấn đề còn mở* để chốt
sau.

**Bước 5 — Kiểm và xuất**

> Kiểm tra chuẩn rồi xuất Word và PDF.

Kết quả:

| Báo | Nghĩa |
|---|---|
| `0 lỗi · 0 vướng cổng chặn` | Xuất được bản phát hành |
| `0 lỗi · n vướng cổng chặn` | Chỉ ra bản nháp có đóng dấu — còn `⟨?⟩` hoặc thiếu hình |
| `n lỗi` | Không xuất được, phải sửa |

**Bước 6 — Lưu về repo**

Lưu cả `.md`, thư mục `assets/` và `diagrams/`. Thiếu `assets/` thì lần render
sau mất hết ảnh.

---

## 2b. Xuất ra Word và PDF

Bảo Claude là xong:

> Kiểm tra chuẩn rồi xuất Word và PDF.

Nhưng có ba thứ bạn sẽ gặp ngay lần xuất đầu tiên, biết trước thì đỡ tưởng
hỏng.

### Mặc định là FILE CON, không có bìa

Bản `.docx` mặc định là **mảnh ghép** vào tài liệu tổng: bắt đầu từ
`Heading 3`, **không bìa, không logo, không số trang, header trống**. Mở ra
thấy trống trơn phần đầu là **đúng** — tài liệu tổng lo phần đó.

Cần một file đứng riêng để gửi ra ngoài thì nói rõ:

> Xuất bản độc lập có bìa.

Bản độc lập bắt đầu từ `Heading 1`, có bìa, logo, tên dự án, header và số
trang. Nó đọc `srs-config.json` ở gốc dự án — chưa điền `to_chuc` và `du_an`
thì bìa ra chỗ trống.

### Còn `⟨?⟩` thì tự động ra BẢN NHÁP

Không phải lỗi. Còn dấu `⟨?⟩` hoặc còn dòng `Đang chờ` ở *Vấn đề còn mở* thì
Claude tự đóng dấu **BẢN NHÁP** lên header và nói rõ vì sao:

```
CỔNG CHẶN: còn 3 dấu ⟨?⟩ · 2 vấn đề đang chờ
→ Xuất BẢN NHÁP. Sạch hết rồi render lại để có bản phát hành.
```

Muốn đóng dấu nháp lên một tài liệu vốn đã sạch — ví dụ gửi xin ý kiến trước
khi chốt — thì nói *"xuất bản nháp"*.

### Để file xuất ra ở `exports/`

`.docx` và `.pdf` là **sản phẩm phái sinh**, sinh lại được từ `.md` bất cứ lúc
nào. Để lẫn trong `functions/` thì nhìn vào không biết tệp nào là nguồn.

| Báo | Nghĩa |
|---|---|
| `0 lỗi · 0 vướng cổng chặn` | Xuất được bản phát hành |
| `0 lỗi · n vướng cổng chặn` | Chỉ ra bản nháp có đóng dấu |
| `n lỗi` | Không xuất được, phải sửa trước |

### Số Hình / Bảng trong PDF bị sai

Nếu thấy dòng *"trường SEQ/TOC KHÔNG được cập nhật"*, máy thiếu thư viện để
tính lại số hiệu. Cách chữa nhanh: mở `.docx` bằng Word, `Ctrl+A`, `F9`, rồi
lưu thành PDF từ Word. Hoặc báo Lead BA cài `python3-uno`.

### Định dạng Word lấy từ đâu

Toàn bộ font, cỡ chữ, màu, kiểu bảng nằm trong `assets/base.docx` của skill —
**bạn không chỉnh gì trong Word cả.** Sửa định dạng trong file `.docx` sẽ mất
khi render lần sau. Muốn đổi bộ nhận diện cho cả dự án thì báo Lead BA, xem
mục về `base.docx` trong `trien-khai.md`.

---

## 3. Sửa tài liệu đã có

> Sửa `FUNC-QLNSD-001`: bổ sung tính năng khoá tài khoản.

Claude sửa `.md`, đề xuất tăng phiên bản và nói rõ nó áp luật nào. Bạn duyệt
hoặc bác. Sau đó kiểm và xuất lại.

| Thay đổi | Tăng lên |
|---|---|
| Thêm/sửa/xoá tính năng, quy tắc, trường | `1.0` → `1.1` |
| Đổi phạm vi chức năng, hoặc sửa lớn sau khi đã duyệt | `1.1` → `2.0` |
| Sửa chính tả, câu chữ không đổi nghĩa | không tăng |

---

## 4. Soát tài liệu

Đính kèm file `.docx` hoặc `.md`:

> Soát tài liệu này theo chuẩn.

Với `.docx`, Claude nhập về `.md` trước rồi mới kiểm. Nó báo lỗi cấu trúc, mã
sai, mục trống, và đọc thêm những thứ máy không thấy được: tiêu chí chấp nhận
mơ hồ, quy tắc viết như ý định thay vì điều kiện kiểm được.

**Nếu ai đó lỡ sửa trong Word:**

> File `.docx` này bị sửa tay, so với bản `.md` giúp tôi.

Claude cho biết bên nào đã đổi và chỉ đúng chỗ khác biệt. Nó **không tự ghi
đè** — bạn quyết định giữ bên nào.

---

## 5. Quy tắc viết — áp dụng luôn cho mọi tài liệu

Đây là chuẩn văn phong. File mẫu `references/golden/FUNC-QLNSD-001.md` trong
skill là bản tham chiếu đầy đủ.

### 5.1. Điều kiện → kết quả

Mỗi câu quy tắc nêu rõ **khi nào** và **thì sao**.

| Không viết | Viết |
|---|---|
| Kiểm tra tên đăng nhập hợp lệ. | Khi tên đăng nhập đã tồn tại, hệ thống dừng việc ghi và hiển thị `ERR_101`. |
| Phân trang dữ liệu. | Kết quả hiển thị 20 dòng mỗi trang, sắp xếp mặc định theo ngày tạo giảm dần. |

### 5.2. Một ý một dòng — gạch đầu dòng tối đa 3 cấp

Thụt đầu dòng quyết định cấp: không thụt = cấp 1 (`T-Gach -`) · 2 dấu cách =
cấp 2 (`T-Gach +`) · 4 dấu cách = cấp 3 (`T-Gach *`). Sâu hơn thì nên tách mục
thay vì thụt tiếp.


Câu ghép nhiều điều kiện thì mỗi người tách một kiểu. Tách thành nhiều quy tắc,
mỗi quy tắc một mã.

### 5.3. Không dùng từ nước đôi

Bỏ hẳn: **thường · có thể · nên · tuỳ · linh hoạt · phù hợp · hợp lý · thân
thiện**.

| Không viết | Viết |
|---|---|
| Hệ thống nên cảnh báo người dùng. | Hệ thống hiển thị `CONF_001` trước khi đóng biểu mẫu. |
| Thời gian phản hồi hợp lý. | Thời gian phản hồi tối đa 3 giây với truy vấn dưới 10.000 bản ghi. |
| Giao diện thân thiện. | *(bỏ — không kiểm được)* |

Riêng mục *Vấn đề còn mở* được viết nước đôi, vì nó đang ghi điều chưa chốt.

### 5.4. Tham chiếu bằng mã, không chép lại

Quy tắc định nghĩa **một lần** ở *Quy tắc nghiệp vụ*. Nơi khác chỉ trỏ mã.

> Áp dụng `BR-QLNSD-001-001`. Vi phạm thì `ERR_101`.

Chép lại nghĩa là sau này sửa quy tắc phải nhớ sửa mấy chỗ — và sẽ quên.

### 5.5. Mỗi trường khai đúng một lần

Danh sách trường chỉ nằm ở *Mô tả các thành phần trên giao diện*. Mục *Luồng xử
lý* và *Xử lý sự kiện* nói về hành vi, không liệt kê lại trường.

### 5.6. Thông báo tách khỏi mô tả

Nội dung thông báo nằm ở bảng *Thông báo*. Nơi khác chỉ ghi mã.

Giọng: lịch sự, nói rõ phải làm gì, không đổ lỗi người dùng.

| Không viết | Viết |
|---|---|
| Bạn đã nhập sai! | Tên đăng nhập chỉ gồm chữ cái không dấu, chữ số và dấu chấm, dài 6–32 ký tự. |

**Thông báo dùng chung có tham số.** Nhiều câu chỉ khác nhau ở đối tượng — dùng
**một mã** với nguyên mẫu:

| Mã | Nội dung | Tham số |
|---|---|---|
| `ERR_042` | Không thể xóa {doi_tuong} ở trạng thái {trang_thai}. | `doi_tuong` = NGUOIDUNG · `trang_thai` = ST-NGUOIDUNG-01 |

Tham số viết `{khong_dau_khong_khoang_trang}`. Nguyên mẫu **không có** tham số
thì cột *Tham số* **để trống**, không ghi "Không áp dụng".

Mọi mã thông báo tham chiếu ở bất kỳ đâu trong file phải có dòng ở bảng *Thông
báo* của cùng file.

### 5.7. Tiêu chí chấp nhận phải kiểm được

3–6 câu mỗi tính năng, mỗi câu quan sát được đúng/sai.

| Không viết | Viết |
|---|---|
| Tìm kiếm hoạt động tốt. | Khi `ROLE-QTDV` tìm kiếm không nhập điều kiện, hệ thống chỉ trả về tài khoản thuộc đơn vị của người dùng đăng nhập. |

### 5.8. Phạm vi dữ liệu: nêu quy tắc, không liệt kê

> **Không:** Xem được đơn vị Hà Nội, Hải Phòng, Đà Nẵng.
> **Có:** Đơn vị của người dùng đăng nhập.

Danh sách đơn vị thay đổi theo thời gian, không thuộc đặc tả tĩnh.

### 5.9. Nói cả điều KHÔNG thuộc phạm vi

Bảng *Mô tả chung* có hai dòng riêng cho việc này — *Trong phạm vi* và *Ngoài
phạm vi*. Đừng nhét ranh giới vào *Mô tả chức năng*.

> **Trong phạm vi:** Tra cứu, tạo mới và gán vai trò đã tồn tại cho tài khoản.
> **Ngoài phạm vi:** Tạo/sửa vai trò thuộc `FUNC-QLNSD-002`; đổi mật khẩu thuộc
> `FUNC-QLNSD-003`; đồng bộ tài khoản từ AD không thuộc phiên bản này.

Bốn nguyên tắc: *Trong phạm vi* không lặp lại danh sách tính năng · *Ngoài
phạm vi* chỉ nêu phần dễ hiểu nhầm, không liệt kê mọi thứ không làm · chuyển
trách nhiệm sang nơi khác phải ghi mã `FUNC-`/`GRP-` · không ghi "Không áp
dụng" một cách máy móc, chỉ dùng khi thật sự không có ranh giới đáng nói.

### 5.10. Không đặc tả thuật toán

SRS khai quy tắc nào áp dụng ở đâu (mã `BR-`). Thuật toán nằm ở tài liệu đặc tả
thuật toán riêng. Viết logic khớp mờ hay chuẩn hoá tên vào SRS là tạo nguồn sự
thật thứ hai, và hai nguồn sẽ lệch.

---

## 6. Nhóm chức năng

Nhóm chức năng là **tầng cây menu** giữa Phân hệ và Chức năng. Nó khớp menu người
dùng nhìn thấy trong ứng dụng, **không phải cách gom tuỳ ý của BA**.

```
Phân hệ HTVH  (Hỗ trợ vận hành)
  └─ Nhóm GRP-HTVH-01  Người dùng & Phân quyền     ← menu người dùng thấy
       ├─ FUNC-HTVH-005  Quản lý người dùng
       ├─ FUNC-HTVH-010  Quản lý nhóm quyền
       └─ FUNC-HTVH-015  Phân quyền người dùng
```

**Nhóm không cần tài liệu mô tả.** Nó chỉ là một đề mục, rồi đi thẳng vào các
chức năng bên dưới:

> Viết nhóm chức năng `GRP-HTVH-01` "Người dùng & Phân quyền".

**Nhận được:** một đề mục `Heading 2` và chỗ để viết vài câu mô tả — hết. Không
mục con, không bảng, không biểu đồ.

Mô tả ngắn là **tuỳ chọn**. Chỉ viết khi ranh giới nhóm dễ gây nhầm, ví dụ để
nói rõ cái gì **không** thuộc nhóm này. Không có gì đáng nói thì xoá luôn dòng
đó.

Khi ghép vào tài liệu tổng: `Heading 2` tên nhóm → `Heading 3` tên chức năng.

| Lỗi | Xử lý |
|---|---|
| `mã 'GRP-QLSP-001' sai dạng GRP-«phân hệ»-«2 số»` | Nhóm dùng **2** chữ số: `01` |
| `mục "..." — nhóm chức năng chỉ gồm đề mục và vài câu mô tả` | Xoá mục con. Nội dung đó thuộc file Chức năng |
| `file nhóm không được có bảng` | Bảng thuộc file Chức năng |
| `mã nhóm ... không có trong groups.csv` | Nhóm phải khớp cây menu — thêm vào sổ trước |
| `còn dấu [[UCDIAGRAM: ...]] — biểu đồ Use Case cho nhóm đã bỏ` | Xoá dòng đó. File viết theo bản chuẩn cũ |

Tên file phải đúng quy ước, nếu không tài liệu tổng bỏ qua file của bạn:

```
groups/GRP-HTVH-01_Nguoi-dung-phan-quyen.docx
functions/htvh/FUNC-HTVH-005_Quan-ly-nguoi-dung.docx
```

Skill tự đặt đúng tên khi bạn không chỉ định. Đừng đổi tên tay.

---

## 7. Nâng tài liệu lên đề cương mới

Có **hai việc khác hẳn nhau**, đừng nhầm:

| Tình huống | Dấu hiệu | Việc phải làm |
|---|---|---|
| Tài liệu **đã theo chuẩn**, nhưng đề cương vừa lên phiên bản mới | Báo lỗi *"lệch phiên bản LỚN"* | Chạy `migrate_outline.py` — vài giây |
| Tài liệu viết **trước khi có khung này** | Báo *"FILE KHÔNG THEO ĐỀ CƯƠNG HIỆN HÀNH"* | Kiểm kê rồi chuyển tay theo mục 7.2 — một buổi |

### 7.1. Nâng phiên bản đề cương

Đề cương hiện hành là **v5.0**. Tài liệu khai `outline_version: "4.1"` sẽ bị
**chặn** (lỗi, không phải cảnh báo) vì bảng *Mô tả chung* nay có thêm hai dòng
bắt buộc *Trong phạm vi* và *Ngoài phạm vi*.

> Nâng `FUNC-QLNSD-001` lên đề cương mới giúp tôi.

Hoặc chạy thẳng:

```bash
python scripts/migrate_outline.py FUNC-QLNSD-001.md --nguoi "Tên bạn"
python scripts/migrate_outline.py functions/*.md --nguoi "Tên bạn"   # cả lô
python scripts/migrate_outline.py FUNC-QLNSD-001.md --thu            # xem trước
```

Lệnh này chèn hai dòng còn để `⟨?⟩`, mở hai dòng ở *Vấn đề còn mở*, tăng phiên
bản tài liệu và ghi changelog. **Nó không tự viết nội dung phạm vi** — đó là
việc của bạn, và cho tới khi điền xong thì tài liệu chỉ ra được bản nháp.

Chạy lại lần hai không hỏng gì: file đã ở v5.0 thì nó bỏ qua.

| Lỗi | Xử lý |
|---|---|
| `lệch phiên bản LỚN, cấu trúc đã khác nên không render được` | Chạy đúng lệnh trong thông báo, đừng sửa tay từng dòng |
| `không có đường nâng cấp v… → v…` | Tài liệu khai phiên bản đề cương không có thật. Kiểm lại `outline_version` ở front matter |
| Sau khi nâng vẫn `2 điểm vướng cổng chặn` | **Đúng như thiết kế.** Điền *Trong phạm vi* / *Ngoài phạm vi* rồi xoá dấu `⟨?⟩` và đóng hai dòng ở *Vấn đề còn mở* |

### 7.2. Chuyển tài liệu cũ sang mẫu mới

Tài liệu viết trước khi có khung này **không nhập tự động được**. Khung mới đòi
những mục tài liệu cũ không hề có — *Ma trận phân quyền*, *Phân loại dữ liệu*,
*Tiêu chí chấp nhận*, mã `BR-`/`MH-`. Không có nội dung nào để chuyển sang.

Đây cũng là chỗ dễ bịa nhất: khung có hàng chục mục trống, và những mục đó
*nghe có vẻ suy ra được* từ mô tả chức năng. Không suy ra.

**Cách làm — bốn bước:**

**Bước 1. Kiểm kê**

> Tài liệu cũ này tôi muốn chuyển sang loại UI, kiểm kê giúp tôi.

> Kiểm kê kèm lấy ảnh ra luôn.

Claude chạy `migrate_scan.py --lay-anh`, ra file kiểm kê gồm: bảng ánh xạ
trống, danh sách những gì tài liệu cũ có (tiêu đề, bảng và cột của nó, mã),
cảnh báo, và **bảng ảnh đã lấy ra**.

Ảnh được lưu vào `assets/`, **không phải copy/paste tay**. Tên dạng
`006_1.5.4_giao-dien-them-moi.png`: số thứ tự trong tài liệu · số mục cũ ·
chú thích. Nhờ vậy thư mục xếp đúng thứ tự từ đầu đến cuối tài liệu, và nhìn
tên là biết ảnh nằm ở mục nào của bản cũ.

Hai thứ **không** lấy tự động được, bản kiểm kê sẽ liệt kê riêng:

- **Ảnh vector** (`.emf`, `.wmf`) — mở Word, chuột phải → *Save as Picture*.
- **Đối tượng nhúng** (bản vẽ Visio, bảng tính, tệp đính kèm) — cái bạn thấy
  chỉ là ảnh xem trước, nội dung thật nằm trong tệp nhúng. Nháy đúp mở ra, lưu
  riêng, rồi dựng lại trong khung mới.

**Bước 2. Điền bảng ánh xạ**

Mỗi mục khung mới lấy nội dung từ mục nào của tài liệu cũ. Không có nguồn thì
ghi `KHÔNG CÓ`. Đây là bước **bạn phải làm**, không giao cho Claude.

Bảng ảnh có sẵn cột cuối để trống — điền mỗi ảnh thuộc tính năng nào của khung
mới. Đó là phần ánh xạ ảnh, làm cùng lượt với ánh xạ nội dung.

Điền xong cột đó thì **chép ảnh sang `functions/«phân hệ»/assets/` và đổi
tên** theo mã tính năng — xem mục 10.1. Đây là lúc duy nhất biết đủ thông tin
để đặt tên đúng, đừng để sang bước sau.

**Bước 3. Chuyển từng mục**

> Chuyển theo bảng ánh xạ này.

Claude dựng khung, chuyển nội dung theo đúng bảng, cấp mã mới, và mọi mục ghi
`KHÔNG CÓ` sẽ thành `⟨?⟩` + một dòng ở *Vấn đề còn mở*.

**Bước 4. Kiểm**

Danh sách *Vấn đề còn mở* sẽ dài. **Đó là kết quả đúng** — nó là backlog những
thứ tài liệu cũ thiếu, không phải lỗi của việc chuyển đổi.

Thực tế nên coi đây là **việc rà soát lại đặc tả**, không phải đổi định dạng.
Làm theo lô nhỏ, mỗi lô một loại chức năng, duyệt cách ánh xạ một lần rồi áp cho
cả lô.

---

## 8. Prompt mẫu

Mỗi tình huống: câu nói mẫu, kết quả nên nhận được, và lỗi hay gặp. Thông điệp
lỗi dưới đây là **nguyên văn** script trả về, tra được bằng cách tìm chuỗi.

---

### 8.1. Đầu phiên — kiểm gói dự án *(claude.ai)*

> Đây là gói dự án của tôi, giải nén và kiểm giúp xem đủ chưa.
> *(kèm file .zip)*

**Nhận được:** danh sách file đặc tả kèm loại và phiên bản · ảnh và `.puml` nào
thiếu · sổ đăng ký có mấy trong tám · kết luận *"Đủ để làm việc"* hoặc *"CÒN
THIẾU"*.

| Lỗi | Xử lý |
|---|---|
| `Ảnh mockup thiếu (2): FUNC-…: assets/…png` | Dán ảnh vào chat, hoặc tải kèm `assets/` |
| `File .puml thiếu` | Tải kèm `diagrams/` |
| `Không thấy sổ đăng ký. Sẽ BỎ QUA phép kiểm mã` | Tải kèm `registries/` — không có thì `ERR_999` bịa vẫn lọt |
| `objects.csv thiếu cột ten_hien_thi` | Việc của Lead BA, sửa sổ bên pipeline. Có dòng này thì kết luận sẽ luôn là *CÒN THIẾU*, không bao giờ ra *Đủ để làm việc* dù dòng khác đều ổn |

---

### 8.2. Viết chức năng mới

> Viết đặc tả chức năng `FUNC-QLSP-047` "Tạo lập sản phẩm", loại UI, 3 tính năng.
> Nguyên liệu tôi dán dưới đây: …

**Nhận được:** file `.md` đầy đủ mục theo loại · Claude hỏi lại chỗ thiếu · chỗ
nào nó suy luận mà bạn chưa xác nhận sẽ có `⟨?⟩` kèm một dòng ở *Vấn đề còn mở*.

Nguyên liệu càng cụ thể càng ít bị hỏi lại: trích BRD, danh sách màn hình, quy
tắc nghiệp vụ, danh sách vai trò.

| Lỗi | Xử lý |
|---|---|
| `LỖI: mã 'FUNC-QLSP-47' sai dạng FUNC-«phân hệ»-«3 số»` | Đủ 3 chữ số: `047` |
| `Loại 'GIAODIEN' không có trong đề cương` | Chỉ 6 giá trị: `UI` `TICHHOP` `JOB` `PHANTICH` `DANHMUC` `GROUP` |
| Claude hỏi quá nhiều | Bình thường ở lần đầu. Đó là chống bịa, không phải nó kém |

---

### 8.3. Viết nhóm chức năng

> Viết nhóm chức năng `GRP-QLSP-01` "Tạo lập sản phẩm".

**Nhận được:** một đề mục `Heading 2`, kèm chỗ viết vài câu mô tả tuỳ chọn. Hết
— nhóm là tầng cây menu, không phải tài liệu.

| Lỗi | Xử lý |
|---|---|
| `mã 'GRP-QLSP-001' sai dạng GRP-«phân hệ»-«2 số»` | Nhóm dùng **2** chữ số |
| Claude đề nghị thêm bảng danh sách chức năng | Từ chối. Danh sách đó do pipeline tự dựng từ manifest |

---

### 8.4. Thêm tính năng vào chức năng đã có

> Bổ sung tính năng "Sao chép sản phẩm" vào `FUNC-QLSP-047`.

**Nhận được:** khối tính năng mới với mã liên tiếp · Claude đề xuất tăng phiên
bản và **nói rõ nó áp luật nào** · dòng mới ở changelog · dòng mới ở *Ma trận
phân quyền*.

| Lỗi | Xử lý |
|---|---|
| `mã FEAT-QLSP-047-05 không liên tiếp — phải là FEAT-QLSP-047-04` | Đánh lại liên tiếp từ `01` |
| `tính năng FEAT-QLSP-047-04 chưa có dòng trong Ma trận phân quyền` | Mỗi tính năng phải có ít nhất một dòng |
| Claude tự tăng lên `2.0` | Bác được. Đổi phạm vi mới lên `X+1.0`, thêm tính năng chỉ `x.Y+1` |

---

### 8.5. Gửi ảnh mockup

> Ảnh này là màn hình danh sách của `FEAT-QLSP-047-01`, chú thích "Màn hình
> danh sách sản phẩm".
> *(dán ảnh)*

**Nhận được:** ảnh lưu vào `assets/` với tên suy từ mã tính năng · dòng
`![chú thích](assets/…png)` chèn vào mục *Thiết kế giao diện*.

Nói rõ **thuộc tính năng nào**. Không nói thì Claude phải hỏi lại.

| Lỗi | Xử lý |
|---|---|
| `ảnh rộng 800px, dưới ngưỡng 1200px — bản in sẽ mờ` | Xuất lại ảnh to hơn. Chỉ cảnh báo, vẫn render được |
| Ảnh mất ở phiên sau | **Chưa lưu `assets/` về máy.** Claude không tạo lại được ảnh |

---

### 8.6. Sơ đồ trình tự

> Viết sơ đồ trình tự cho `FEAT-KENH-005-01`, lưu vào `diagrams/`.

**Nhận được:** file `.puml` · dấu `[[DIAGRAM: …]]` trong `.md` · render tự sinh
ảnh kèm caption.

Bắt buộc với loại `TICHHOP` và `JOB`.

| Lỗi | Xử lý |
|---|---|
| `không tìm thấy diagrams/FUNC-…_seq-01.puml` | Tải kèm `diagrams/`, hoặc nhờ Claude viết |
| `CẢNH BÁO: không gọi được PlantUML server` | Bình thường trên claude.ai — nó tự lùi về jar. Chỉ đáng lo trên Claude Code |
| `KHÔNG TÌM THẤY JAVA` | Cài JRE 17+. PlantUML cần Java, không chỉ cần file jar |
| `KHÔNG TẢI ĐƯỢC plantuml.jar` | Mạng chặn github.com. Tải tay theo địa chỉ trong thông báo, đặt vào gốc dự án tên `plantuml.jar` |
| Tên participant sai | Phải là mã trong `participants.csv`. Mã có gạch ngang cần bí danh: `participant "HT-TCTD" as HT_TCTD` |

---

### 8.7. Kiểm và xuất

> Kiểm tra chuẩn rồi xuất Word và PDF.

**Nhận được:** báo cáo lỗi / cảnh báo / điểm vướng cổng chặn, rồi `.docx` +
`.pdf`.

| Kết quả | Nghĩa |
|---|---|
| `0 lỗi · 0 vướng cổng chặn` | Xuất được bản phát hành |
| `0 lỗi · n vướng cổng chặn` | Chỉ ra **bản nháp có đóng dấu** |
| `n lỗi` | Không xuất được |

| Lỗi | Xử lý |
|---|---|
| `mục "Sơ đồ trạng thái" để trống` | Điền, hoặc ghi `Không áp dụng` |
| `cột "«ROLE_1»" còn là placeholder` | Thay bằng mã vai trò thật. Số cột được phép khác 3 |
| `cột "..." không phải mã vai trò — phải dạng ROLE-«mã»` | Đổi tên cột thành mã thật trong `roles.csv`, không để tên thường |
| `mã ROLE-... không có trong roles.csv` | Mã bịa hoặc gõ sai. Dùng mã thật hoặc thêm vào sổ |
| `... trông giống mã UC/BR/... nhưng sai dạng chuẩn` | Sai số chữ số hay thừa/thiếu đoạn — sửa đúng khuôn ở mục 9 |
| `bảng ..., bảng ...: thiếu dòng "..."` / `dòng "..." không có trong đề cương` | Bảng *Mô tả chung* (hay bảng kv khác) thiếu, thừa hoặc sai thứ tự dòng — sửa lại đúng đề cương |
| `tính năng ... chưa có dòng trong Ma trận phân quyền — không thấy ở cột "Mã tính năng"` | Ghi đúng mã vào cột *Mã tính năng*, không phải cột tên thao tác |
| `tính năng ... không có ở cột "Tính năng đáp ứng"` | Ghi mã đúng cột đó, không phải cột *Ghi chú* |
| `bảng … dòng 4: 6 ô nhưng bảng có 7 cột — giá trị sẽ lệch cột` | Thiếu dấu `\|`. Đếm lại ô |
| `CỔNG CHẶN: còn 1 chỗ đánh dấu ⟨?⟩ chưa chốt` | Chốt nội dung rồi bỏ dấu và xoá dòng ở *Vấn đề còn mở* |
| `trường SEQ/TOC KHÔNG được cập nhật` | Máy thiếu `python3-uno`. Mở Word, `Ctrl+A`, `F9`, xuất lại |
| `version: 1.1 không khớp dòng changelog cuối (1.0)` | Sửa cho khớp |

---

### 8.8. Chốt các điểm treo

> Liệt kê các điểm `⟨?⟩` còn lại trong `FUNC-QLSP-047` để tôi chốt.

**Nhận được:** danh sách từng điểm kèm vị trí và đề xuất của Claude. Bạn trả lời
từng điểm, Claude bỏ dấu và cập nhật *Vấn đề còn mở*.

Đây là bước **bắt buộc** trước khi phát hành. Đừng dùng `--force-release` cho
xong việc — chỗ chưa chốt sẽ lọt xuống Dev.

---

### 8.9. Soát tài liệu người khác viết

> Soát tài liệu này theo chuẩn.
> *(kèm .docx hoặc .md)*

**Nhận được:** với `.docx` thì Claude nhập về `.md` trước · báo lỗi cấu trúc, mã
sai, mục trống · **và đọc thêm những thứ máy không thấy**: tiêu chí chấp nhận mơ
hồ, quy tắc viết như ý định thay vì điều kiện kiểm được, trường khai hai chỗ.

| Lỗi | Xử lý |
|---|---|
| `mã ERR_777 được tham chiếu nhưng không có dòng ở bảng Thông báo của file này` | Thêm dòng vào bảng *Thông báo* |
| `giá trị NGUOIDUNG có trong sổ nhưng chưa điền tên hiển thị` | Sổ thiếu `ten_hien_thi` — báo Lead BA |
| `tên hiển thị của ... — đối tượng nghiệp vụ viết thường` | Sổ viết sai kiểu. Đối tượng chữ thường, trạng thái hoa chữ đầu |
| `giá trị KHONGCO không có trong objects.csv / states.csv` | Mã bịa. Dùng mã thật hoặc thêm vào sổ |
| `changelog: dòng 1 thiếu ngay` | Bình thường khi nhập từ `.docx` — Word không mang ngày. Điền tay |

---

### 8.10. Ai đó sửa tay trong Word

> File `.docx` này bị sửa tay, so với bản `.md` của tôi giúp tôi.
> *(kèm cả hai)*

**Nhận được:** một trong bốn kết luận — *sạch* · *`.docx` bị sửa tay* · *`.md` đã
thay đổi* · *cả hai đổi* — kèm danh sách dòng khác biệt.

**Không bao giờ tự ghi đè.** Bạn quyết định giữ bên nào.

| Lỗi | Xử lý |
|---|---|
| `File .docx này KHÔNG do skill render` | File ngoài luồng. Nhập về rồi tự đối chiếu |
| `ĐÂY LÀ TÀI LIỆU TỔNG` | Skill làm việc trên từng file con. Tách bằng `split_master.py` của pipeline trước. Cổng này chặn tuyệt đối — không né được kể cả khi chỉ định `--profile` |
| `File render bằng bản skill cũ, chưa có dấu vết nội dung` | Không kết luận được. Render lại từ `.md` |

---

### 8.11. Chuyển tài liệu cũ

> Tài liệu cũ này tôi muốn chuyển sang loại UI, kiểm kê giúp tôi.

**Nhận được:** file kiểm kê gồm bảng ánh xạ trống, danh sách những gì tài liệu cũ
có, và cảnh báo ba mục hay bị bịa nhất.

Điền bảng ánh xạ là **việc của bạn**, không giao cho Claude. Xong rồi mới nói:

> Chuyển theo bảng ánh xạ này.

| Lỗi | Xử lý |
|---|---|
| `FILE KHÔNG THEO ĐỀ CƯƠNG HIỆN HÀNH` | Đúng như mong đợi. Dùng `migrate_scan`, không nhập trực tiếp |
| `n ô trong Word có nhiều dòng, đã gộp thành một dòng ngăn bằng ·` | Bình thường — bảng markdown không xuống dòng trong ô được. Mỗi `·` là một gạch đầu dòng cũ (`··` là cấp 2). Soát lại những ô nhiều `·` ở cột *Mô tả ràng buộc*: thường là nhiều quy tắc nên tách thành các mã `BR-` riêng |
| `` `ERR-001` sai dấu nối — sửa thành `ERR_001` `` | Tài liệu cũ hay dùng gạch ngang. Tìm-thay thế từng mã một, mã nào cũng có gợi ý sẵn |
| Danh sách *Vấn đề còn mở* rất dài | **Kết quả đúng.** Đó là backlog những gì tài liệu cũ thiếu |

---

### 8.12. Xuất tài liệu độc lập

> Xuất `FUNC-QLSP-047` thành tài liệu độc lập có bìa.

**Nhận được:** bìa có logo, tên tổ chức, tên dự án, bảng thông tin · header và số
trang · bắt đầu từ `Heading 1`.

Mặc định (không nói "độc lập") là **file con** để ghép vào tài liệu tổng: không
bìa, `Heading 3`.

| Lỗi | Xử lý |
|---|---|
| `không tìm thấy srs-config.json — sẽ không có bìa, logo` | Chép từ `assets/config.example.json`, điền tên tổ chức và dự án |
| `không tìm thấy logo assets/logo.png` | Đặt logo vào `assets/`, PNG nền trong suốt, rộng ≥ 600px |

---

### 8.13. Cuối phiên — lấy kết quả về *(claude.ai)*

> Nén toàn bộ kết quả thành một file zip để tôi tải về.

**Nhận được:** một `.zip` gồm `.md` đã sửa, `assets/`, `diagrams/`, `.docx`,
`.pdf`.

Giải nén ghi đè lên thư mục dự án trên máy. **Không làm bước này là mất hết công
của cả phiên** — máy ảo xoá sạch giữa các phiên.

---

### 8.14. Làm nhiều file một lượt

> Kiểm tra chuẩn cả 12 file trong thư mục `functions/`.

**Nhận được:** báo cáo từng file, kèm tổng số lỗi.

Xuất hàng loạt cũng được — khoảng 0,3 giây mỗi file. Nhưng **soát nội dung thì
nên làm từng file**: Claude đọc kỹ được một tài liệu, không đọc kỹ được mười hai
tài liệu trong một lượt.

---

## 9. Mã — hai loại, hai luật khác nhau

**Đừng gộp hai loại này làm một.** Nhầm ở đây làm skill lúc thì xin bạn cấp mã
nó tự cấp được, lúc thì tự chế mã đáng ra phải tra sổ.

| Loại | Gồm | Luật |
|---|---|---|
| **Dùng chung toàn hệ thống** | `UC-` · `ERR_`/`WAR_`/`INF_`/`SUC_`/`CONF_`/`MAIL_` · `ST-` · `ROLE-` · `GRP-` · tác nhân · component | **Phải có sẵn trong sổ.** Không tự đặt. Cần mã mới thì thêm vào sổ trong cùng lần nộp |
| **Nội bộ một file** | `FEAT-` · `BR-` · `MH-` | **Cấp ngay trong file**, đánh liên tiếp theo quy ước. Phải khai trước khi chỗ khác nhắc tới |
| **Cấp phát ở manifest** | `FUNC-` | **Đặt chỗ ở `manifest.md` trước, commit, rồi mới viết file** |

**Thêm một dòng vào sổ khác với việc nghĩ ra nội dung của dòng đó.** "Trong
cùng lần nộp" nghĩa là *dòng* đi kèm tài liệu để không có mã treo lơ lửng.
Nó không cho phép Claude tự viết nội dung: câu `noi_dung` của một thông báo là
câu người dùng sẽ đọc, `ten_uc` là cách nghiệp vụ gọi tên việc đó — cả hai là
nội dung nghiệp vụ, thuộc luật "không bịa". Đúng cách: giữ chỗ mã, để nội dung
`⟨?⟩`, mở một dòng *Vấn đề còn mở*, rồi hỏi bạn.

### `manifest.md` — danh mục chức năng của dự án

Đặt ở **gốc dự án**, cạnh `registries/`, đưa vào SVN/Git chung với sổ.

Đây là sổ **cấp phát**, không phải bản kiểm kê. Kiểm kê thì lúc nào cũng dựng
lại được từ đĩa. Cấp phát thì không: mã phải giữ chỗ **trước khi** file tồn
tại, nếu không hai BA cùng lấy `FUNC-QLSP-048` và không gì phát hiện ra.

| Mã | Tên chức năng | Loại | Phân hệ | Nhóm | Mã UC | Người phụ trách | Trạng thái | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| FUNC-QLNSD-001 | Quản lý người dùng | UI | QLNSD | GRP-QLNSD-01 | UC-0301 | Ngọc | Đã phát hành | |
| FUNC-QLSP-047 | Tạo lập sản phẩm | UI | QLSP | | | | Đang viết | |

Bốn trạng thái: `Đã cấp` (chưa viết) · `Đang viết` · `Đã phát hành` · `Bỏ`.
**Mã đã cấp không tái sử dụng**, kể cả khi bỏ chức năng — mã cũ còn nằm trong
tài liệu khác và trong lịch sử page.

`project_check.py` đối chiếu: file mang mã ngoài manifest là **lỗi**; mã ghi
`Đã phát hành` mà không thấy file là **cảnh báo**; mã trùng dòng là **lỗi**.
Không có manifest thì chỉ cảnh báo — làm một mình thì không cần cấp phát.

Mã `GRP-` **không** cấp ở đây, nó nằm ở `registries/groups.csv` vì phải khớp
cây menu ứng dụng. Cột *Nhóm* chỉ để tra cứu nhanh.

Mẫu: `assets/manifest.example.md` trong skill.



| Loại | Dạng | Ví dụ |
|---|---|---|
| Chức năng | `FUNC-«phân hệ»-«3 số»` | `FUNC-QLNSD-001` |
| Tính năng | `FEAT-«phân hệ»-«số CN»-«2 số»` | `FEAT-QLNSD-001-01` |
| Quy tắc | `BR-«phân hệ»-«số CN»-«3 số»` | `BR-QLNSD-001-001` |
| Màn hình | `MH-«phân hệ»-«số CN»-«3 số»` | `MH-QLNSD-001-001` |
| Thông báo | `«LOẠI»_«3 số»` | `ERR_014` |
| Vai trò | `ROLE-«mã»` | `ROLE-QTHT` |

Sai hình thức (đúng tiền tố, sai số chữ số hay thừa/thiếu đoạn — ví dụ `UC-301`
thay vì `UC-0301`, hay `ERR_QLNSD_002` thừa đoạn phân hệ) cũng bị bắt, không
chỉ mã hoàn toàn không đúng mẫu.

Loại thông báo: `ERR` lỗi · `WAR` cảnh báo · `INF` thông tin · `SUC` thành công
· `CONF` hỏi xác nhận · `MAIL` thư điện tử gửi ra ngoài.

Thư điện tử là **một loại thông báo**, không phải mục riêng. Tiêu đề và nội dung
đầy đủ nằm ở `messages.csv`; file chức năng chỉ khai mã, tham số và điều kiện
phát sinh.

Mã tính năng và mã quy tắc **phải thuộc chức năng chứa nó**. Chép khối tính năng
từ file khác mà quên đổi mã sẽ bị chặn.

**Mã nội bộ phải khai và phải được dùng.** Ba loại `FEAT-` `BR-` `MH-` chỉ tồn
tại trong chính file đó, nên skill kiểm cả hai chiều:

| Tình huống | Mức |
|---|---|
| Nhắc `MH-…-007` mà *Danh sách màn hình* không khai | **Lỗi** — đổi tên hoặc xoá rồi còn sót chỗ nhắc |
| Khai `BR-…-006` mà không nơi nào áp dụng | Cảnh báo — tàn dư sau khi bỏ nội dung liên quan |
| Nhắc `BR-QLSP-047-001` trong file `FUNC-QLNSD-001` | **Lỗi** — mã của chức năng khác |

**Hai bảng phải khớp nhau.** Cùng kiểu như trên, nhưng giữa các bảng:

| Tình huống | Mức |
|---|---|
| Tính năng không có dòng ở *Truy vết yêu cầu* — kiểm đúng cột *Tính năng đáp ứng*, mã nằm ở cột khác (vd. *Ghi chú*) không tính | **Lỗi** — yêu cầu không truy được về UC nào |
| Tính năng không có dòng ở *Ma trận phân quyền* — kiểm đúng cột *Mã tính năng* | **Lỗi** |
| Chỉ tiêu có công thức nhưng chưa khai ở *Danh mục chỉ tiêu*, hoặc ngược lại | **Lỗi** |
| Luồng thay thế quay về bước không có trong luồng chính | **Lỗi** |
| Vai trò nhắc trong nội dung nhưng không phải cột của *Ma trận phân quyền* | Cảnh báo |
| Cột vai trò không phải mã `ROLE-«…»` (vd. để tên thường "Quản trị viên") | **Lỗi** |
| Mã `ROLE-«…»` không có trong `roles.csv` | **Lỗi** |
| Bảng *Mô tả chung* (hoặc bảng kv khác) thiếu/thừa/sai thứ tự dòng so với đề cương | **Lỗi** |

Đây là chỗ sinh lỗi nhiều nhất khi **sửa tài liệu cũ**: bỏ một tính năng thì
thường quên xoá quy tắc và màn hình đi kèm, tài liệu vẫn đọc trôi chảy nên không
ai nhận ra.

Mã thông báo dùng chung **toàn hệ thống**. Tra `messages.csv` trước — cùng nội
dung thì dùng lại mã cũ, kể cả khi phân hệ khác đang dùng. Cần mã mới thì thêm
vào sổ trong cùng lần nộp.

---

## 10. Hình

**Mockup** — dán ảnh vào chat. PNG rộng ≥ 1200px, dưới ngưỡng sẽ bị cảnh báo mờ.

### 10.1. Tên ảnh có hai giai đoạn

Đừng ngạc nhiên khi `migrate_scan --lay-anh` đặt tên không giống quy ước —
**đó là chủ ý**. Lúc kiểm kê chưa ai biết ảnh thuộc tính năng nào.

| Giai đoạn | Tên | Vì sao |
|---|---|---|
| `staging/`, `migration/` | `001_1.5_giao-dien-them-moi.png` | Số thứ tự cho thư mục xếp đúng thứ tự tài liệu cũ; số mục cũ để đối chiếu |
| `functions/` | `FEAT-QLNSD-001-01_danh-sach.png` | Sau khi đã chốt ảnh thuộc tính năng nào |

**Đổi tên là một bước có thật trong quy trình**, làm đúng lúc bạn điền cột
"Gắn vào tính năng nào" ở bảng kiểm kê ảnh. Chép ảnh sang
`functions/«phân hệ»/assets/` rồi đổi tên, đồng thời sửa đường dẫn trong `.md`.

Vào `functions/` rồi thì tên giữ vĩnh viễn: `import_docx` đọc lại tên từ
alt-text nên nhập đi nhập lại không đổi tên.

**Không chép thẳng** tệp đính kèm Confluence hay ảnh nguồn vào
`functions/.../assets/`. Chỉ chép sau khi đã xác định được ảnh thuộc tài liệu
và tính năng nào — nếu không, thư mục `assets/` thành bãi chứa và không ai
biết ảnh nào còn dùng.

### 10.2. Tên sơ đồ theo **mã chức năng**, không phải mã tính năng

```
diagrams/
├── FUNC-QLNSD-001_seq-01.puml
├── FUNC-QLNSD-001_seq-02.puml     ← tính năng thứ hai của cùng chức năng
└── FUNC-QLNSD-002_seq-01.puml
```

Mã `FUNC-` là duy nhất trong phân hệ nên không xung đột dù một phân hệ có
nhiều tài liệu.

**Chỗ hay vấp:** chức năng có hai tính năng đều cần sơ đồ thì `scaffold` đặt
**cùng một marker `_seq-01`** cho cả hai. Bạn phải tự sửa cái thứ hai thành
`_seq-02` và đặt tên file `.puml` cho khớp. Số thứ tự đánh theo chức năng chứ
không theo tính năng, nên tên file không nói được nó thuộc tính năng nào —
việc đó do caption làm.

### 10.3. Sơ đồ trình tự

**Sơ đồ trình tự** — viết PlantUML, lưu ở `diagrams/«mã»_seq-01.puml`. Bắt buộc
với loại `TICHHOP` và `JOB`. Tên participant phải là mã trong `participants.csv`;
mã có dấu gạch ngang cần đặt trong ngoặc kép kèm bí danh:

```
participant "HT-TCTD" as HT_TCTD
```

**Thiếu hình** — bản Word sẽ có khung `⟨ THIẾU HÌNH ⟩` nhìn thấy được. Bạn được
phép chèn ảnh thẳng vào Word, **nhưng phải báo Claude nhập lại ngay sau đó**,
nếu không lần render sau sẽ mất ảnh.

---

## 11. Trước khi nộp

- [ ] Đủ mục, không xoá mục nào; mục không dùng ghi `Không áp dụng`
- [ ] *Trong phạm vi* / *Ngoài phạm vi* đã điền — không copy nguyên danh sách tính năng, không "Không áp dụng" một cách máy móc
- [ ] Mọi tính năng có dòng ở *Truy vết yêu cầu* (đúng cột *Tính năng đáp ứng*) và ở *Ma trận phân quyền* (đúng cột *Mã tính năng*)
- [ ] Cột vai trò dùng mã thật `ROLE-«…»`, không còn `«ROLE_1»`, và có trong `roles.csv`
- [ ] Mọi mã thông báo có trong `messages.csv` và có dòng ở bảng *Thông báo*
- [ ] Mỗi tính năng có 3–6 tiêu chí chấp nhận kiểm được
- [ ] `outline_version` khớp đề cương hiện hành (v6.1) — lệch thì chạy `migrate_outline.py`, đừng sửa tay
- [ ] `assets/` và `diagrams/` nằm **cạnh file `.md`**, không phải ở gốc dự án — chạy `project_check.py` để chắc
- [ ] Thư mục phân hệ viết thường (`functions/qlnsd/`), sổ đăng ký tên `registries/` — không phải tên khác
- [ ] Ảnh đã đổi tên theo mã tính năng, không còn tên tạm `001_1.5_…` của bước kiểm kê
- [ ] Không còn `⟨?⟩`, mục *Vấn đề còn mở* không còn dòng `Đang chờ`
- [ ] Kiểm chuẩn trả về `0 lỗi`
- [ ] Đã lưu `.md` + `assets/` + `diagrams/` vào repo

---

## 12. Gặp vấn đề

| Hiện tượng | Xử lý |
|---|---|
| "Mục ... để trống" | Điền, hoặc ghi `Không áp dụng` |
| "Cột «ROLE_1» còn là placeholder" | Thay bằng mã vai trò thật. Số cột được phép khác 3 |
| "Mã ... được tham chiếu nhưng không có dòng ở bảng Thông báo" | Thêm dòng vào bảng *Thông báo* của cùng file |
| "Mã tính năng không liên tiếp" | Đánh lại từ `01` |
| Khung `⟨ THIẾU HÌNH ⟩` trong Word | Gửi ảnh cho Claude, hoặc ghi `Không áp dụng` nếu mục đó không cần hình |
| Sơ đồ không hiện | Kiểm file `.puml` có đúng ở `diagrams/` và đúng tên không |
| `còn dấu [[UCDIAGRAM: ...]]` | Biểu đồ Use Case cho nhóm đã bỏ khỏi chuẩn. Xoá dòng đó |
| Bản Word không có bìa/logo | Chỉ tài liệu độc lập mới có. File con ghép vào tài liệu tổng thì tổng lo |
| `lệch phiên bản LỚN` | Chạy `migrate_outline.py` theo mục 7.1 |
| `… dính ngay sau bảng` / `… dính ngay trước bảng` | Thiếu dòng trắng giữa bảng và nội dung kế bên. Chạy `srs.py fix «file».md`. Skill vẫn đọc đúng, nhưng GitHub và trình xem markdown sẽ hút chữ vào ô cuối bảng |
| `cột “…”: n ô gộp nhiều ý` | Ô ở cột ràng buộc gộp nhiều quy tắc. Tách thành các mã `BR-` riêng — cột này cố ý render một dòng liền |
| `cột “…”: n ô có dấu · nhưng cột này không khai` | Gõ `·` vào cột không cho phép. Dấu sẽ hiện ra như ký tự thường trong Word. Xem bảng nhóm cột ở `md-syntax.md` |
| `file soạn theo đề cương v6.0, skill đang dùng v6.1` | Lệch **NHỎ** — không chặn, vẫn render được. Chạy `migrate_outline.py` khi rảnh để tắt cảnh báo |
| `n tệp ĐẶT SAI CHỖ` | `assets/` hoặc `diagrams/` để ở gốc dự án. Chuyển vào cạnh file `.md` — thông báo in rõ đang ở đâu, cần ở đâu |
| `Thấy so-dang-ky/ — tên sổ đăng ký duy nhất là registries/` | Đổi tên thư mục. Giữ tên cũ thì BA Toolkit tạo `registries/` rỗng bên cạnh, và mọi phép kiểm mã sau đó chạy trên sổ rỗng |
| `Bỏ qua n file .md ngoài functions/` | Không phải lỗi. Bản nháp ở `staging/` và bản sao ở `sources/` cố ý không bị chấm |
| `gạch đầu dòng n cấp — tối đa 3` | Thụt quá sâu trong một ô. Tách mục thay vì thụt tiếp |
| `objects.csv thiếu cột ...`, `mã trùng`, `roles.csv không có dòng nào` | Sổ đăng ký hỏng schema. Việc của Lead BA, sửa bên pipeline |
