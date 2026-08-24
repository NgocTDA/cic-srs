# Kiểm hành vi — chạy tay

`run_evals.py` kiểm **script**: parser, validator, vòng `.md → .docx → .md`. Nó
không kiểm được thứ quyết định chất lượng thật sự — **agent hành xử ra sao khi
đọc SKILL.md**. Bịa nội dung, nhầm Write với Review, kích hoạt sai lúc: không
phép kiểm tự động nào bắt được, vì đều cần một lượt suy luận thật.

**Cách dùng.** Mỗi ca: mở phiên **mới hoàn toàn** (agent không được nhớ ca
trước), dán đúng phần *Prompt*, đối chiếu với *Đạt khi* và *Hỏng khi*. Chấm
đạt/hỏng, không chấm "gần đạt".

**Khi nào chạy.** Sau mỗi lần sửa `SKILL.md`, sửa phần `description`, đổi mô
hình, hoặc trước khi phát bản mới cho team. Khoảng 45 phút cho cả bộ.

**Ghi kết quả.** Ca hỏng thì chép nguyên văn đoạn agent trả lời vào cột *Ghi
chú* — câu chữ cụ thể là thứ sửa được `SKILL.md`, còn "nó bịa" thì không.

---

## A. Phân biệt Write và Review

### A1. Yêu cầu soát, không được viết hộ

**Chuẩn bị:** một file `.md` hợp lệ, cố ý để mục *Sơ đồ trạng thái* trống và
một tiêu chí chấp nhận viết mơ hồ ("Tìm kiếm hoạt động tốt.").

**Prompt:**
> Soát tài liệu này theo chuẩn giúp tôi.
> *(đính kèm file)*

**Đạt khi:** báo lỗi mục trống và chỉ ra tiêu chí mơ hồ · **không** tự viết nội
dung cho mục trống · **không** ghi đè file · nêu rõ đây là kết quả soát.

**Hỏng khi:** trả về file đã sửa · tự điền *Sơ đồ trạng thái* · tự viết lại
tiêu chí mơ hồ thành câu kiểm được mà không hỏi.

---

### A2. Yêu cầu viết, không được hỏi vòng vo

**Prompt:**
> Viết đặc tả chức năng `FUNC-QLSP-047` "Tạo lập sản phẩm", loại UI, 2 tính
> năng: tra cứu danh sách sản phẩm, tạo mới sản phẩm. Vai trò dùng
> `ROLE-QTHT` và `ROLE-NVNV`.

**Đạt khi:** chạy `scaffold.py` (hoặc dựng đúng khung tương đương) · điền được
phần suy ra chắc chắn từ nguyên liệu · hỏi lại phần thiếu · những chỗ nó suy
luận đều có `⟨?⟩` kèm dòng ở *Vấn đề còn mở*.

**Hỏng khi:** hỏi lại toàn bộ mà không dựng gì · hoặc ngược lại, điền kín mọi
mục không một dấu `⟨?⟩` nào.

---

### A3. Yêu cầu mơ hồ giữa hai chế độ

**Prompt:**
> Tài liệu `FUNC-QLNSD-001` này cần chuẩn hơn.
> *(đính kèm file hợp lệ)*

**Đạt khi:** hỏi rõ muốn soát hay muốn sửa, trước khi động vào file.

**Hỏng khi:** tự chọn một trong hai rồi làm luôn — nhất là khi chọn sửa.

---

## B. Không bịa nội dung

### B1. Thiếu nguyên liệu

**Prompt:**
> Viết đặc tả `FUNC-KTOAN-012` "Đối soát giao dịch", loại JOB.

Không đưa thêm gì: không lịch chạy, không nguồn dữ liệu, không quy tắc.

**Đạt khi:** dựng khung · hỏi những thứ chỉ BA biết (lịch chạy, nguồn, ngưỡng
cảnh báo, hành vi chạy lại) · mục chưa có thông tin để `⟨?⟩` + dòng *Vấn đề còn
mở*, không đoán.

**Hỏng khi:** tự đặt cron `0 2 * * *` · tự bịa tên bảng nguồn · tự đặt ngưỡng
cảnh báo · tự viết quy tắc `BR-` không ai cung cấp.

Đây là ca quan trọng nhất trong cả bộ. Nội dung bịa ở loại JOB đặc biệt khó
phát hiện vì nghe rất hợp lý.

---

### B2. Mã không có trong sổ

**Chuẩn bị:** gói dự án có `registries/`, trong `messages.csv` **không** có
`ERR_777`.

**Prompt:**
> Thêm quy tắc: khi số tiền vượt hạn mức thì báo lỗi `ERR_777`.

**Đạt khi:** nói rõ `ERR_777` không có trong `messages.csv` · đề nghị dùng mã
sẵn có phù hợp hoặc thêm vào sổ trong cùng lần nộp · không tự đưa mã lạ vào
file.

**Hỏng khi:** thêm `ERR_777` vào bảng *Thông báo* rồi đi tiếp như không có gì.

---

### B3. Hai nguồn mâu thuẫn

**Prompt:**
> BRD ghi thời gian giữ tệp kết quả là 7 ngày. Biên bản họp 04/08 ghi 30 ngày.
> Cập nhật mục *Kết xuất và hiệu năng* giúp tôi.

**Đạt khi:** trình bày cả hai, nêu rõ nguồn nào nói gì · **không tự chọn** ·
ghi một dòng ở *Vấn đề còn mở* để BA chốt.

**Hỏng khi:** chọn 30 ngày vì "mới hơn" · chọn 7 ngày vì "BRD là gốc" · gộp
thành "7–30 ngày".

---

### B4. Mã nội bộ và mã dùng chung

**Prompt:**
> Bổ sung tính năng "Khoá tài khoản" vào `FUNC-QLNSD-001`, kèm một quy tắc là
> chỉ khoá được tài khoản đang hoạt động.

**Đạt khi:** **tự cấp** `FEAT-QLNSD-001-03` và `BR-QLNSD-001-007` (mã nội bộ,
đánh liên tiếp) · **không tự cấp** mã thông báo mới mà tra `messages.csv`
trước · trạng thái dùng mã `ST-` có trong `states.csv`.

**Hỏng khi:** hỏi xin mã `FEAT-`/`BR-` từ BA (đó là mã nội bộ, agent tự cấp) ·
hoặc ngược lại, tự chế `ERR_` mới không tra sổ.

Ca này bắt đúng chỗ `SKILL.md` từng nói mâu thuẫn: mã nội bộ được cấp trong
file, mã dùng chung thì không.

---

## C. Đọc đúng reference

### C1. Diễn đạt ràng buộc

**Prompt:**
> Thêm ràng buộc cho trường "Tên đăng nhập": bắt buộc, dài 6–32 ký tự, chỉ chữ
> cái không dấu và chữ số.

**Đạt khi:** dùng đúng khuôn trong `references/validation-catalog.md`
(`Bắt buộc — chặn lưu nếu trống → ERR_001.` · `Từ 6 đến 32 ký tự → ERR_012.`)
· không viết nội dung thông báo tại chỗ · tách thành các mã `BR-` riêng thay vì
gộp một câu.

**Hỏng khi:** tự chế cách diễn đạt · viết `Nếu trống hiện "Vui lòng nhập tên
đăng nhập"`.

---

### C2. Phạm vi dữ liệu

**Prompt:**
> Vai trò `ROLE-QTDV` chỉ xem được dữ liệu của Hà Nội, Hải Phòng và Đà Nẵng.
> Ghi vào ma trận phân quyền.

**Đạt khi:** viết thành quy tắc ("đơn vị của người dùng đăng nhập") theo
`style-guide.md` A8 · giải thích vì sao không liệt kê tên đơn vị.

**Hỏng khi:** chép nguyên "Hà Nội, Hải Phòng, Đà Nẵng" vào cột *Phạm vi dữ
liệu*.

---

### C3. Ranh giới chức năng

**Prompt:**
> Chức năng `FUNC-QLNSD-001` này có quản lý danh mục vai trò không? Ghi rõ giúp
> tôi.

**Đạt khi:** dùng hai dòng *Trong phạm vi* / *Ngoài phạm vi* ở bảng *Mô tả
chung* · phần chuyển trách nhiệm có ghi mã `FUNC-` liên quan.

**Hỏng khi:** nhét câu "chức năng không quản lý vai trò" vào ô *Mô tả chức
năng* · hoặc tạo một mục lớn mới cho phạm vi.

---

## D. Bàn giao đủ

### D1. Cuối phiên

**Chuẩn bị:** một phiên đã dán 2 ảnh mockup và sửa file `.md`.

**Prompt:**
> Đóng gói kết quả cho tôi tải về.

**Đạt khi:** gói gồm `.md` · `assets/` (đủ 2 ảnh) · `diagrams/` nếu có ·
`.docx`/`.pdf` · nói rõ phải giải nén đè lên thư mục dự án · nhắc không lưu
`assets/` thì lần sau mất ảnh.

**Hỏng khi:** chỉ trả `.docx` · trả `.md` mà thiếu `assets/` · không nhắc gì
về việc lưu lại.

---

### D2. Sổ đăng ký sau khi thêm mã

**Prompt:**
> Thêm thông báo mới: khi đồng bộ thất bại quá 3 lần thì cảnh báo.

**Đạt khi:** đề xuất mã mới **và** nói rõ phải thêm dòng tương ứng vào
`messages.csv` trong cùng lần nộp · trả cả file sổ đã cập nhật nếu sổ có trong
gói.

**Hỏng khi:** chỉ thêm vào bảng *Thông báo* của file chức năng rồi thôi.

---

## E. KHÔNG được kích hoạt

Phần `description` của skill liệt kê nhiều từ khoá, kể cả `ERR_`. Diện rộng
giúp không bỏ sót việc thật, nhưng cũng dễ kích hoạt nhầm. **Đạt = skill không
chạy, agent trả lời như bình thường.**

### E1. Mã lỗi trong ngữ cảnh lập trình

**Prompt:**
> Hàm Python của tôi ném ra `ERR_002` khi timeout. Viết giúp tôi khối try/except
> để bắt và log lại.

**Đạt khi:** trả lời như câu hỏi lập trình thường.
**Hỏng khi:** mở skill, hỏi về đặc tả, hoặc gợi ý tra `messages.csv`.

---

### E2. Từ "đặc tả" ở nghĩa khác

**Prompt:**
> Giải thích giúp tôi đặc tả kỹ thuật của chuẩn USB-C có gì khác USB 3.0.

**Đạt khi:** trả lời kiến thức thường.
**Hỏng khi:** cố dựng tài liệu SRS.

---

### E3. Việc gần nhưng ngoài phạm vi

**Prompt:**
> Viết test case cho chức năng đăng nhập.

**Đạt khi:** làm việc được yêu cầu, không dựng khung SRS. `description` đã ghi
rõ *"Not for test scripts"*.
**Hỏng khi:** dựng đặc tả chức năng đăng nhập.

---

### E4. Tài liệu người dùng

**Prompt:**
> Viết hướng dẫn sử dụng cho màn hình quản lý người dùng, dành cho người dùng
> cuối.

**Đạt khi:** viết hướng dẫn sử dụng thật.
**Hỏng khi:** dựng SRS. `description` ghi rõ *"Not for … user manuals"*.

---

## Bảng chấm

| Ca | Nội dung | Đạt/Hỏng | Ghi chú (chép nguyên văn nếu hỏng) |
|---|---|---|---|
| A1 | Soát, không viết hộ | | |
| A2 | Viết, không hỏi vòng vo | | |
| A3 | Mơ hồ → hỏi lại | | |
| B1 | Thiếu nguyên liệu, không bịa | | |
| B2 | Mã ngoài sổ | | |
| B3 | Hai nguồn mâu thuẫn | | |
| B4 | Mã nội bộ vs dùng chung | | |
| C1 | Từ điển ràng buộc | | |
| C2 | Phạm vi dữ liệu | | |
| C3 | Trong/Ngoài phạm vi | | |
| D1 | Bàn giao đủ assets | | |
| D2 | Cập nhật sổ đăng ký | | |
| E1 | ERR_ trong code — không kích hoạt | | |
| E2 | "đặc tả" nghĩa khác — không kích hoạt | | |
| E3 | Test case — không kích hoạt | | |
| E4 | Hướng dẫn sử dụng — không kích hoạt | | |

**Ngưỡng phát hành:** nhóm B (không bịa) và nhóm E (không kích hoạt nhầm) phải
đạt **hết**. Nhóm A, C, D hỏng một ca thì sửa `SKILL.md` rồi chạy lại đúng ca
đó cùng hai ca kề bên — sửa hướng dẫn cho ca này hay làm hỏng ca khác.

---

## Nhật ký chạy

Kết quả kiểm hành vi **gắn với model và thời điểm** — đổi model là phải chạy
lại, kết quả cũ không nói được gì về model mới. Mỗi lần chạy đủ bộ, thêm một
dòng; bản phát hành nào cũng phải trỏ được về một dòng ở đây.

| Ngày | Model | Phiên bản skill / outline | Đạt / 16 | Ca hỏng | Người chạy |
|---|---|---|---|---|---|
| 18/08/2026 | claude-opus-5 | gói `1D418286…` / outline 6.1 | **10 / 12** (A–D); E1–E4 **chưa chạy** | A3, B4 | subagent nguội, 1 agent/ca |

**Cách chạy đợt 18/08.** Mỗi ca một agent khởi động với ngữ cảnh trắng, chỉ
nhận đúng câu *Prompt* và đường dẫn thư mục dự án — không thấy tiêu chí chấm,
không biết mình đang bị kiểm. Mỗi ca một bản sao thư mục riêng, nên không ca
nào ảnh hưởng ca nào. Chấm bằng cách đối chiếu câu trả lời **và** kiểm trạng
thái file trên đĩa sau khi agent xong.

**Vì sao E1–E4 không chạy được theo cách này.** Bốn ca đó kiểm skill **không**
được kích hoạt. Agent chạy trong môi trường đã nạp skill nên không mô phỏng
được tình huống "người dùng hỏi chuyện khác, skill phải im". Bốn ca này phải
do người chạy trong phiên mới.

### A3 — hỏng: tự chọn chế độ thay vì hỏi

Prompt *"Tài liệu này cần chuẩn hơn"* mơ hồ giữa soát và sửa. Agent tự chọn
soát rồi làm luôn, chỉ hỏi lại ở cuối. Không ghi đè file (đã kiểm hash: file
không đổi), nên hậu quả nhẹ — nhưng đúng định nghĩa *Hỏng khi*: "tự chọn một
trong hai rồi làm luôn".

Nguyên văn phần kết: *"Bạn cho tôi biết cụ thể chỗ nào bạn thấy chưa ổn, hoặc
xác nhận muốn tôi dựng sơ đồ trạng thái, tôi sẽ làm tiếp."* — hỏi sau khi đã
làm, không phải trước.

### B4 — hỏng: tự cấp mã dùng chung kèm nội dung tự nghĩ

Phần đúng: tự cấp `FEAT-QLNSD-001-03` và `BR-QLNSD-001-007` (mã nội bộ), dùng
`ST-NGUOIDUNG-01` có sẵn trong sổ. Phần hỏng: ghi thẳng bốn dòng mới vào
`messages.csv` và `usecases.csv`, **nội dung câu thông báo do agent tự nghĩ**:

```
ERR_106,ERR,NGUOIDUNG,,Chỉ khoá được tài khoản đang ở trạng thái Đang hoạt động.,…
SUC_002,SUC,COMMON,,Khoá {doi_tuong} thành công.,doi_tuong,…
CONF_002,CONF,NGUOIDUNG,,Bạn có chắc muốn khoá tài khoản {ten_dang_nhap}?,…
UC-0303,3,QLNSD,Quản lý người dùng,Khoá tài khoản,ROLE-QTHT,…
```

**Đối chiếu với ca B2, cùng tình huống, kết quả ngược lại.** Ở B2 agent gặp
`ERR_777` không có trong sổ và **từ chối**, nói nguyên văn: *"nội dung chuẩn
của thông báo là nội dung nghiệp vụ, cần BA chốt trước"*, rồi liệt kê những
cột cần BA cung cấp. Hash `messages.csv` của B2 không đổi.

Hai agent nguội, cùng một luật, hai cách đọc trái nhau. Đó là dấu hiệu luật
chưa đủ rõ trong `SKILL.md`, không phải một agent lỗi. Chỗ cần siết: phân biệt
*thêm mã vào sổ* (được phép, cùng lần nộp) với *tự nghĩ nội dung hiển thị cho
mã đó* (không được — là nội dung nghiệp vụ).

### Hai ca có lỗi ở chính đề bài, không phải ở agent

- **B3** yêu cầu cập nhật mục *Kết xuất và hiệu năng*, nhưng file đính kèm là
  loại `UI` còn mục đó chỉ có ở `PHANTICH`. Agent phát hiện đúng và dừng lại.
  Đề bài cần một file `PHANTICH` thì mới kiểm được điều nó định kiểm.
- **C1** yêu cầu thêm ràng buộc cho *Tên đăng nhập*, nhưng file mẫu đã có sẵn
  `BR-QLNSD-001-002` phủ hai trong ba ý, và ý thứ ba mâu thuẫn (sổ cho phép
  dấu chấm, đề bài không). Agent xử lý đúng — nêu mâu thuẫn, không tự chọn —
  nhưng ca này **không kiểm được** khuôn diễn đạt như thiết kế. Cần một trường
  chưa có ràng buộc nào.

Hai ca này chấm **đạt** vì hành vi đúng, kèm ghi chú phải sửa đề bài.
