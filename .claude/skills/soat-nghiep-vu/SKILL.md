---
name: soat-nghiep-vu
description: Dùng khi cần SOÁT NỘI DUNG NGHIỆP VỤ của một tài liệu SRS đã viết — tìm điểm mờ nghiệp vụ, thiếu logic giao diện, thiếu logic chức năng — rồi ra một báo cáo .md xếp theo BLOCKING/WARNING/SUGGESTION. Hợp với tài liệu theo chuẩn srs-help (mã FUNC-/FEAT-/BR-/MH-), và với .docx/.pdf hoặc trang Confluence do BA gửi. Chỉ báo cáo, KHÔNG sửa tài liệu gốc. Dùng khi người dùng nói "soát nghiệp vụ", "review tài liệu này giúp tôi", "tài liệu còn mờ chỗ nào", "thiếu logic gì". Khác srs-help (viết đặc tả và kiểm chuẩn hình thức).
---

# Soát nghiệp vụ một tài liệu SRS

## Goal

Trả lời đúng ba câu hỏi của Lead BA khi cầm một bản SRS người khác viết:

1. **Chỗ nào nghiệp vụ còn mờ?** — câu chữ trôi chảy nhưng đọc xong vẫn không biết phải
   làm gì: *"theo quy định hiện hành"*, *"hệ thống tự động xử lý"*, *"dữ liệu hợp lệ"*.
2. **Thiết kế giao diện thiếu logic gì?** — thao tác không có nhánh lỗi, danh sách không
   có trạng thái rỗng, phần tử trên ảnh không có dòng mô tả, thông báo mồ côi.
3. **Chức năng thiếu logic gì?** — vào được trạng thái mà không ra được, có "khoá" mà
   không có "mở khoá", quyền cấp trong ma trận phân quyền mà không luồng nào dùng tới.

## Ranh giới — cái gì script làm, cái gì skill này làm

Đây là **ranh giới quan trọng nhất**. Vi phạm nó thì báo cáo đầy nhiễu và BA học cách
phớt lờ.

| Việc | Ai làm |
|---|---|
| Thiếu mục, sai thứ tự mục, bảng sai cột, bảng thiếu dòng trống | `srs.py check` (skill `srs-help`) |
| Mã tham chiếu mà không khai báo · khai mà không ai dùng | `srs.py check` |
| Mã dùng chung (`UC-`, `MSG`, `ST-`, `ROLE-`, `GRP-`) không có trong sổ | `srs.py check` |
| File mang mã không có trong `manifest.md` | `project_check.py` |
| **Nội dung nghiệp vụ mờ, thiếu logic, mâu thuẫn giữa các mục** | **skill này** |

**Luôn chạy `check` trước** (nếu môi trường cho phép). Tài liệu còn lỗi hình thức thì soi
nội dung là phí công — báo người dùng sửa hình thức rồi quay lại.

## Constraints

### Hard rules — không được vi phạm

- **Chỉ đọc, không sửa.** **KHÔNG** được sửa tài liệu SRS gốc, dù một dấu phẩy. Chỉ ghi
  đúng một file báo cáo. Muốn sửa → người dùng tự sửa, hoặc mở phiên `srs-help`.
- **Chống bịa — mọi finding phải có trích dẫn `file.md:dòng`.** Không trích được thì
  không in. Đây là chỗ dễ hỏng nhất: một finding bịa = BA đi sửa cái không hỏng.
- **Chứng minh cả hai vế khi báo "thiếu".** Trích được *"có khoá tài khoản"* chưa đủ để
  kết luận *"thiếu mở khoá"* — phải nêu **đã grep từ nào, trên file nào**, và tập file đó
  đã đóng chưa. Chưa đủ → hạ xuống *"cần kiểm thêm"*, không được viết "thiếu".
- **Ngôn ngữ nghi vấn, không phán xét.** Viết *"Có {A} (dòng 83), grep {từ} trên {N} file
  không thấy {B} — có chủ đích bỏ qua hay cần bổ sung?"*. **Không** viết *"THIẾU luồng X"*.
  Lead BA là người chốt, không phải skill.
- **Không phát hiện thì nói thẳng "không phát hiện".** Không bịa cho đủ số.
- **Hỏi người dùng duyệt trước khi ghi** báo cáo (xem Bước 6).
- **Ngôn ngữ báo cáo: tiếng Việt.**

### Pitfalls — dễ sai

- **Đừng lặp lại `check`.** Nếu định in "mục X thiếu" hay "mã Y không có trong sổ" — dừng
  lại, đó là việc của script.
- **`⟨?⟩` không phải lỗi.** Người viết đánh dấu điểm chưa chốt là **đúng quy trình**. Lỗi
  là `⟨?⟩` **không có** dòng tương ứng ở *Vấn đề còn mở*. Ngược lại, điểm mờ mà **không**
  đánh dấu `⟨?⟩` mới là thứ cần bắt.
- **Chưa tới bước ≠ thiếu.** Tài liệu `status: draft` chưa có *Tiêu chí chấp nhận* đầy đủ
  là bình thường — im lặng. Đã phát hành mà thiếu → BLOCKING. Đọc `status` trong front
  matter trước khi gắn mức.
- **Profile quyết định mục nào có mặt.** `PHANTICH` **không có** tầng *Tính năng* — đừng
  báo thiếu *Thiết kế giao diện* ở một tài liệu báo cáo thống kê. `TICHHOP` không có màn
  hình. Đọc `profile` trong front matter trước.
- **Nhóm chức năng (`GRP-`) là một tầng menu, không phải tài liệu.** Một Heading 2 và vài
  câu là đủ. Đừng soi nó như soi `FUNC-`.
- **Không tự đề xuất quyết định kỹ thuật** (tên bảng, endpoint, framework). Ở mức nghiệp vụ.

## Bước 0 — Xác định đang chạy ở môi trường nào

Skill này chạy được ở hai nơi, cách chạm file khác nhau. **Xác định trước, đừng đoán.**

| Môi trường | Dấu hiệu | Cách chạm file |
|---|---|---|
| **Claude Code (Terminal)** | Có tool `Read`/`Bash` thao tác thẳng thư mục dự án | Đường dẫn tương đối từ gốc dự án: `cic/functions/…`. Chạy `python .agents/skills/srs-help/scripts/srs.py …` |
| **Ứng dụng Claude trên máy (Cowork)** | Chỉ chạm được máy người dùng qua các tool `mcp__remote-devices__device_*` | Thư mục đã kết nối nằm ở `$HOME/mnt/<tên-thư-mục>/`. Dùng `device_bash` để `cat`/`grep`/chạy `python3`; dùng `device_list_dir` để liệt kê |

Ở Cowork: `device_bash` **không xoá được file** và **không có mạng**. Ghi báo cáo bằng
`device_bash` (heredoc) thẳng vào thư mục đã kết nối là cách gọn nhất.

Chưa có thư mục nào kết nối → báo người dùng bấm **"Add folder"** trong ứng dụng, đừng
loay hoay thử tiếp.

## Bước 1 — Đưa nguồn về một file .md đọc được

| Nguồn | Làm gì |
|---|---|
| `.md` chuẩn srs-help | Dùng luôn. |
| `.docx` | `python .agents/skills/srs-help/scripts/srs.py review <file.docx>` — import về `.md` rồi validate. Bản Word sửa tay là ca cứu hộ: thêm `--diff`. |
| `.pdf` | Không có importer. **Đọc thẳng**, soi nội dung, và **nói rõ trong báo cáo** rằng không đối chiếu được với outline chuẩn. |
| Confluence | `python tools/confluence_reader.py <pageId hoặc URL> --save` → file về `confluence_pages/`. Cần mạng — ở Cowork thì `device_bash` không có mạng, nhờ người dùng chạy hộ hoặc tải trang về trước. |

Nguồn không phải chuẩn srs-help → bỏ Bước 2, ghi rõ ở đầu báo cáo *"nguồn ngoài chuẩn,
chỉ soát nội dung"*.

## Bước 2 — Chạy kiểm hình thức trước

```bash
python .agents/skills/srs-help/scripts/srs.py check <file.md> --registry-dir cic/registries
```

- Exit `1` (có lỗi) → **dừng**. Báo người dùng: *"tài liệu còn N lỗi hình thức, sửa xong
  hẵng soát nội dung"* + dán output.
- Exit `0` hoặc `2` → đi tiếp. Giữ output để trích ở phần *Đã kiểm bằng script*.
- Không chạy được script (thiếu Python, nguồn ngoài chuẩn) → ghi rõ *"chưa kiểm hình
  thức"* ở đầu báo cáo, đừng lặng lẽ bỏ qua.

## Bước 3 — Đọc, và đọc đủ

Đọc **toàn bộ** file (không sample). Ghi lại từ front matter: `ma`, `profile`, `version`,
`status`. Rồi liệt kê ra — sẽ in vào báo cáo — **đã đọc những file nào**:

- File đặc tả chính; các `FUNC-` liên quan cùng phân hệ (nếu có tham chiếu chéo)
- `cic/registries/*.csv` — để hiểu mã, **không** để kiểm mã
- Chuẩn dùng chung của dự án nếu có (`KIEM-HANH-VI.md`, `Quy_dinh_chung.md`,
  `Thanh_phan_dung_chung.md`)
- Ảnh trong `assets/`, sơ đồ nguồn trong `diagrams/*.puml` (đọc `.puml`, đừng đoán từ ảnh)

Độ phủ này phải hiện trong báo cáo. BA cần biết kết luận dựa trên bao nhiêu tài liệu.

## Bước 4 — Bốn góc soi, chạy song song

Bốn góc soi nằm ở `references/goc-soi-*.md`. **Đọc file góc soi trước khi spawn** — mỗi
file là một persona đầy đủ (cách soi, thang mức nặng, bản đồ mục cho tài liệu srs-help).

Spawn 4 subagent **trong một lượt** (song song, không tuần tự). Với mỗi góc soi:

- Có sẵn `subagent_type` trùng tên (`senior-ba`, `uxui-reviewer`, `flow-reviewer`,
  `qa-reviewer` — trường hợp Claude Code có `.claude/agents/`) → dùng luôn.
- **Không có** → dùng `general-purpose`, và **dán toàn bộ nội dung file góc soi vào đầu
  prompt** làm khung nhân vật.

Mỗi agent nhận cùng một khối context: đường dẫn file, `profile`, `status`, danh sách file
đã đọc ở Bước 3, và output `check` ở Bước 2 (để không lặp lại).

| Góc soi | Soi cái gì | Mục chính |
|---|---|---|
| `goc-soi-senior-ba` | **Điểm mờ nghiệp vụ**, edge case, mâu thuẫn | Mô tả chung · Luồng nghiệp vụ · Quy tắc nghiệp vụ · Mô tả yêu cầu · Vấn đề còn mở |
| `goc-soi-uxui-reviewer` | **Thiếu logic giao diện** — trạng thái rỗng/tải/lỗi/thành công, phần tử ↔ ảnh, sự kiện ↔ thông báo | Danh sách màn hình · Thiết kế giao diện · Mô tả các thành phần · Xử lý sự kiện · Thông báo |
| `goc-soi-flow-reviewer` | **Thiếu luồng** — ngõ cụt, không ai tới được, thiếu chiều ngược | Luồng nghiệp vụ · Sơ đồ trạng thái · Luồng màn hình · Luồng xử lý |
| `goc-soi-qa-reviewer` | **Tiêu chí chấp nhận không kiểm được**, `BR-` không ai kiểm | Tiêu chí chấp nhận · Quy tắc nghiệp vụ · Thông báo |

**Profile quyết định gọi ai:**

- `UI`, `DANHMUC` → cả 4.
- `TICHHOP`, `JOB` → bỏ góc giao diện (không có màn hình); giữ 3.
- `PHANTICH` → bỏ góc giao diện; góc QA soi thêm *Công thức và truy vấn* + *Đối chiếu và
  kiểm chứng*.
- `GRP-` → không spawn ai. Đọc tay, soi đúng một thứ: mô tả nhóm có nói được nhóm này gom
  chức năng gì và cho vai trò nào không.

**Ở Cowork:** subagent không chạm được máy người dùng. Vì vậy **đọc nội dung file ra
trước** (bằng `device_bash cat -n` để có số dòng) rồi **truyền nguyên văn kèm số dòng vào
prompt** của từng agent. Không làm vậy thì agent không có gì để trích dẫn.

## Bước 5 — Gộp findings

Theo `references/review-format.md`:

1. **Khử trùng** — cùng một vấn đề từ 2 góc tính một lần, giữ bản chi tiết hơn, ghi
   *"(2 góc soi cùng nêu)"*.
2. **Leo mức khi đồng thuận** — từ 2 góc trở lên cùng gắn WARNING cho một vấn đề → nâng
   BLOCKING.
3. **Mức cuối = mức cao nhất.** Verdict: có BLOCKING → `block`; chỉ WARNING → `revise`;
   sạch → `approve`.
4. **Mâu thuẫn giữa hai góc** → in ra thành mục riêng, **không tự xử**, để Lead BA quyết.
5. **Lọc lần cuối bằng tay** — bỏ mọi finding không có trích dẫn `file:dòng`, và mọi
   finding trùng với output `check`.

## Bước 6 — Xin duyệt rồi ghi

In trước cho người dùng duyệt, bằng lời nghiệp vụ, không bảng kiểu log dev:

> Em sẽ ghi `cic/staging/qlsp/FUNC-QLSP-040.soat-2026-08-21.md` — nằm ngay cạnh
> `FUNC-QLSP-040.md`:
>
> - {N} điểm chặn, {M} cảnh báo, {K} gợi ý — trên {số} mục của tài liệu
> - Nặng nhất: {một câu về finding nghiêm trọng nhất}
> - Đã đọc {số} file; {profile}, phiên bản {version}, trạng thái {status}
>
> Ghi chứ? (Y / sửa)

Rồi ghi. **Không đụng vào file SRS gốc.**

## Output

Báo cáo nằm **liền sát file nó soát, trong cùng thư mục**, đặt tên sao cho hai file
xếp cạnh nhau khi sắp theo tên:

```
cic/staging/qlsp/
├── FUNC-QLSP-040.md                      ← tài liệu
├── FUNC-QLSP-040.soat-2026-08-21.md      ← báo cáo, nằm ngay dưới
├── FUNC-QLSP-041.md
├── FUNC-QLSP-041.soat-2026-08-21.md
└── QLSP.soat-lien-tai-lieu-2026-08-21.md ← mâu thuẫn chéo, cấp phân hệ
```

Quy tắc đặt tên: **`«tên file gốc».soat-«yyyy-mm-dd».md`**. Soát nhiều vòng thì mỗi
vòng một file, tự xếp theo ngày. Soát nhiều tài liệu một lượt và tìm ra mâu thuẫn
giữa chúng → thêm một file cấp phân hệ `«PHÂN HỆ».soat-lien-tai-lieu-«yyyy-mm-dd».md`.

**Báo cáo đi theo phiên bản nó soát.** Soát bản nháp trong `staging/` thì báo cáo ở
`staging/`; khi tài liệu được nâng lên `functions/` thì soát lại, và báo cáo mới nằm ở
`functions/`. Không kéo báo cáo cũ sang — nó soát một bản khác.

**An toàn với script — đã kiểm bằng thực nghiệm:** `project_check.py` chỉ đếm file `.md`
có front matter hợp lệ (`ma` + `profile` thuộc bộ chuẩn). File `.soat-*.md` không có front
matter nên bị bỏ qua hoàn toàn, kể cả khi nằm trong `functions/`. Vì vậy **tuyệt đối không**
thêm front matter kiểu srs-help vào báo cáo — thêm vào là script tưởng đó là một tài liệu
đặc tả và báo lỗi thiếu mục.

Nguồn ngoài chuẩn (docx/pdf rời chưa nhập vào dự án, trang Confluence) chưa có chỗ trong
cây thư mục → hỏi người dùng muốn để báo cáo ở đâu, đừng tự đoán.

## References

- `references/review-format.md` — mức nặng, verdict, luật gộp findings
- `references/goc-soi-senior-ba.md` — điểm mờ nghiệp vụ, edge case
- `references/goc-soi-uxui-reviewer.md` — logic giao diện
- `references/goc-soi-flow-reviewer.md` — ngõ cụt, thiếu chiều ngược
- `references/goc-soi-qa-reviewer.md` — tiêu chí chấp nhận kiểm được

<!-- Bốn góc soi chưng cất từ AI4BA BA-Kit (agent của /gap, /srs), đã ánh xạ sang outline
     của skill srs-help. Bản gốc trong mỗi file giữ nguyên để còn so với kit mới. -->
