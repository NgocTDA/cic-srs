# Thư mục này là mẫu tham khảo — đừng sửa, đừng cấp mã thật vào đây

**Không phải dữ liệu CIC_CORE.** `FUNC-QLNSD-001` / `GRP-QLNSD-01` là ví dụ
của bộ skill, giữ nguyên byte với bản trong
`.claude/skills/srs-help/references/golden/`. Phân hệ thật của dự án nằm ở
cột *Phân hệ* trong `../manifest.md` (không phải `qlnsd`).

`project_check.py` chỉ quét `functions/` và `groups/` ở cấp `workspace/` —
`vi-du/` nằm ngoài phạm vi đó, không bị tính vào kiểm kê hay cổng chặn phát
hành của dự án thật.

---

## Thử ngay — hai câu

Mở AI đã cài skill tại gốc `workspace/`, gõ:

> Kiểm chuẩn `vi-du/functions/qlnsd/FUNC-QLNSD-001.md` rồi xuất Word và PDF.

Phải ra `0 lỗi · 0 điểm vướng cổng chặn` và sinh file `.docx`/`.pdf` cạnh file
`.md` (đúng hành vi mặc định của `render.py` — xem `../../CLAUDE.md` phần
"sản phẩm render"). File xuất ra chỉ để xem, đừng commit.

Chạy được nghĩa là máy bạn đã sẵn sàng: skill cài đúng, ảnh mockup tìm thấy,
Word xuất được.

`FUNC-QLNSD-001.md` là **bản tham chiếu văn phong** của cả bộ chuẩn. Đọc nó
trước khi viết file đầu tiên của bạn sẽ tiết kiệm vài vòng sửa.

---

## Học bằng cách phá nó

Cách nhanh nhất để hiểu bộ kiểm là làm nó báo lỗi. Sửa **một bản chép** (đừng
sửa trực tiếp file này), rồi chạy lại `check` sau mỗi lần:

| Sửa gì | Sẽ báo |
|---|---|
| Đổi một mã thông báo thành `ERR_999` | `ERR_999` không có trong `messages.csv` |
| Xoá nội dung một mục bất kỳ | mục để trống |
| Thêm `⟨?⟩` vào một ô | vướng cổng chặn → chỉ ra được bản nháp |
| Đổi `ROLE-QTHT` thành `Quản trị viên` | tiêu đề vai trò phải là mã |
| Chuyển `assets/` ra khỏi `functions/qlnsd/` | `project_check` báo **ĐẶT SAI CHỖ**, kèm đường dẫn đang ở đâu / cần ở đâu |
| Thêm chức năng mới mà quên ghi vào `manifest.md` | có file nhưng chưa cấp mã |

Sửa hỏng bao nhiêu cũng được — cần bản sạch lại thì lấy từ
`.claude/skills/srs-help/references/golden/`.

---

## Hai cảnh báo bạn sẽ thấy, và chúng đúng

`check` trên `FUNC-QLNSD-001` ra **2 cảnh báo**: mục *Luồng màn hình* và *Sơ đồ
trạng thái* chưa có hình. Hình là **tuỳ chọn**, nên đây là cảnh báo chứ không
phải lỗi, và tài liệu vẫn ra bản phát hành.

Nếu xuất theo mặc định (không `--standalone`), bản `.docx` **không có bìa** —
đó là chế độ file con, mảnh ghép vào tài liệu tổng. Muốn bản đứng riêng có bìa
thì thêm cờ đó khi export.
