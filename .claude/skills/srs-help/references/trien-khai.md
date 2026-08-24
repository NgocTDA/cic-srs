# Triển khai skill `srs-help`

Dành cho người cài đặt (Lead BA). BA thường chỉ cần `references/huong-dan-ba.md`.

---

## 1. Cài skill

Cài `srs-help.skill` vào Claude.

**Gỡ hai bản cũ nếu còn:** `srs-writer` và `ntda-srs-helper`. Ba skill cùng mô
tả sẽ tranh nhau kích hoạt, và bản cũ có đề cương lỗi thời.

Kiểm nhanh: hỏi Claude *"skill nào đang xử lý đặc tả chức năng?"* — chỉ được ra
đúng một tên.

---

## 2. Dựng thư mục dự án

**Hai môi trường, hai cách dùng.** Trên **Claude Code** thư mục là thật, BA tạo
một lần rồi dùng mãi. Trên **claude.ai không có thư mục dự án** — máy ảo xoá sạch
giữa các phiên, BA phải **nén thư mục thành .zip và tải lên mỗi phiên**, rồi lưu
kết quả về máy. Đây là chỗ hay bị hiểu sai nhất khi tập huấn.

Đầu mỗi phiên trên claude.ai, chạy `scripts/project_check.py` để biết gói tải lên
thiếu gì — thiếu ảnh nào, thiếu `.puml` nào, sổ nào chưa có, cột `ten_hien_thi`
đã điền chưa.


```
du-an/
├── srs-config.json          ← chép từ assets/config.example.json rồi sửa
├── manifest.md              ← danh mục chức năng: cấp mã FUNC- ở đây trước khi viết file
├── registries/              ← 8 sổ CSV, hoặc trỏ sang repo pipeline
├── project-rules/
│   └── srs-help.md          ← luật riêng dự án, tuỳ chọn. Skill đọc SAU SKILL.md
└── functions/
    ├── qlnsd/               ← một thư mục mỗi phân hệ, tên VIẾT THƯỜNG
    │   ├── FUNC-QLNSD-001.md
    │   ├── assets/          ← ảnh mockup + logo.png nếu xuất độc lập
    │   └── diagrams/        ← file .puml
    └── qlsp/
        ├── FUNC-QLSP-047.md
        ├── assets/
        └── diagrams/
```

**Ba quy ước tên không được phá:**

| Quy ước | Vì sao |
|---|---|
| Thư mục phân hệ **viết thường**, mã vẫn **HOA** — `functions/qlnsd/FUNC-QLNSD-001.md` | Windows không phân biệt hoa thường, nên dùng lẫn hai cách viết chạy ngon trên máy BA rồi tách thành hai thư mục ở nơi khác |
| Sổ đăng ký chỉ có tên `registries/` | Đặt tên khác thì `project_check` báo lỗi. Nếu dự án dùng BA Toolkit, `init` sẽ tạo thêm `registries/` **rỗng** bên cạnh, và mọi phép kiểm mã sau đó chạy trên sổ rỗng |
| `.docx`/`.pdf` xuất ra `exports/` | Sản phẩm phái sinh, sinh lại được. Để lẫn trong `functions/` thì không ai biết tệp nào là nguồn |

Thư mục do BA Toolkit thêm vào (`.ba-toolkit/`, `sources/`, `staging/`,
`migration/`, `reports/`) **không ảnh hưởng skill** — `project_check` chỉ chấm
tài liệu trong `functions/` và bỏ qua phần còn lại có thông báo. Ngược lại,
`ba_toolkit init` an toàn trên thư mục dựng tay: mọi `mkdir` đều `exist_ok`,
mọi tệp chỉ ghi khi chưa tồn tại. Nên đường "soạn tài liệu trước, lắp toolkit
sau" chạy được.

**Luật quan trọng nhất của cấu trúc này: `assets/` và `diagrams/` nằm ngay
cạnh file `.md`, không phải ở gốc dự án.** Đường dẫn `assets/abc.png` viết
trong `.md` được giải theo thư mục chứa chính file đó (`root = src.parent`
trong `render.py`).

Xếp sai thì hỏng âm thầm: bản Word ra khung `⟨ THIẾU HÌNH ⟩` nhưng
`validate.py` **vẫn báo `0 lỗi`**, vì thiếu hình chỉ là cảnh báo.
`project_check.py` là chỗ duy nhất bắt được — nó phân biệt *thiếu tệp* với
*đặt sai chỗ*, và in ra tệp đang ở đâu, cần ở đâu.

Hai hệ quả đáng lưu ý:

- Khoá `logo` trong `srs-config.json` cũng giải theo thư mục `.md`, nên logo
  phải nằm ở `functions/«phân hệ»/assets/logo.png`. Không muốn nhân bản logo
  cho từng phân hệ thì khai đường dẫn tuyệt đối.
- Bù lại, mỗi thư mục phân hệ **tự đủ**: nén một thư mục gửi đi là người nhận
  render được ngay. Rất hợp với cách làm trên claude.ai, nơi BA tải lên và tải
  về theo thư mục.

`registries/` để ở gốc dùng chung — nó truyền qua `--registry-dir` nên đường
dẫn nào cũng chạy.

`srs-config.json` chỉ dùng khi xuất **tài liệu độc lập**. File con ghép vào tài
liệu tổng thì bìa và logo do tài liệu tổng lo — bỏ trống cũng được.

**`plantuml_server`: nên để trống.** Mặc định script tải `plantuml.jar` về
`~/.cache/srs-help/`, ghim phiên bản, dùng lại các lần sau. Khai server thì
nhanh hơn nhưng mất tính tái lập — server nâng cấp là hình trong mọi tài liệu
đổi theo. Server nội bộ cũng chỉ gọi được từ Claude Code.

---

## 3. Sổ đăng ký

Tám sổ: `messages.csv` · `usecases.csv` · `roles.csv` · `states.csv` ·
`participants.csv` · `components.csv` · `objects.csv` · `groups.csv`.

Không có sổ thì skill vẫn chạy, nhưng **bỏ qua phép kiểm mã** — nghĩa là
`ERR_999` bịa vẫn lọt. Luôn truyền `--registry-dir` khi có sổ.

Ba cột dễ bị bỏ sót, thiếu là thông báo có tham số sẽ ra mã trần thay vì chữ
tiếng Việt:

| Sổ | Cột | Ví dụ |
|---|---|---|
| `messages.csv` | `thamso` | `doi_tuong,trang_thai` |
| `messages.csv` | `chu_de` | chỉ với loại `MAIL` |
| `objects.csv` · `states.csv` | `ten_hien_thi` | `NGUOIDUNG` → `người dùng` |

Validator phân biệt hai lỗi khác nhau: mã **không có trong sổ**, và mã **có
trong sổ nhưng chưa điền tên hiển thị**. Hai lỗi này cần hai cách sửa khác nhau.

`project_check.py` kiểm schema cả tám sổ, đọc **dòng tiêu đề** chứ không đợi có
dữ liệu — sổ mới lập chỉ có header mà thiếu cột vẫn bị bắt. Những gì nó chặn:

| Lỗi | Vì sao chặn |
|---|---|
| Thiếu cột khoá (`ma`, `ma_uc`) | Không đối chiếu được mã nào với sổ đó |
| Thiếu `ten_hien_thi` / `thamso` | Thông báo có tham số ra mã trần |
| Mã bỏ trống | Dòng không có mã thì không ai tra tới |
| Mã trùng | Tra ra dòng nào là tuỳ thứ tự đọc file |
| Tiêu đề cột trùng, hoặc dính BOM/khoảng trắng | `csv` chỉ giữ cột cuối, hoặc tên cột không khớp nên mọi mã đọc thành rỗng |
| `roles.csv` có file nhưng không dòng nào, trong khi tài liệu dùng `ROLE-` | Nguy hơn không có sổ: không có thì cảnh báo to, rỗng thì lặng lẽ báo mọi mã là sai |

---

## 4. Kiểm sau khi cài — 5 bước

Chạy trong thư mục skill.

**Bước 1 — đề cương còn nguyên**

```bash
python scripts/outline_check.py
```

Phải ra `Sạch. → 0 lỗi · 0 cảnh báo`.

**Bước 2 — toàn bộ hồi quy**

```bash
python evals/run_evals.py --pipeline /đường/dẫn/srs-pipeline
```

Không có `--pipeline`, phải ra **`327 phép kiểm · 327 đạt · 0 hỏng`** khi máy
có LibreOffice, hoặc **`321 · 321 · 0`** khi không có — nhóm `Xuất PDF` (6
phép) tự rút còn 1 dòng "bỏ qua" nếu thiếu `soffice` trong `PATH`, để bộ kiểm
vẫn dùng được trên máy không cài. Có `--pipeline` thì cộng thêm phép đối chiếu
đề cương với `outline.py` bên pipeline — số tổng phụ thuộc phiên bản
`outline.py` phía đó, tự chạy lại để lấy số hiện hành.

Ngoài bộ này còn `evals/forward-tests.md` — **kiểm hành vi, chạy tay**. Nó kiểm
những thứ script không kiểm được: agent có bịa nội dung khi thiếu dữ liệu
không, có nhầm chế độ soát với chế độ viết không, có kích hoạt nhầm khi người
dùng chỉ nhắc `ERR_` trong ngữ cảnh lập trình không. Khoảng 45 phút, chạy
trước mỗi lần phát bản mới.

**Chạy lại lệnh này mỗi lần sửa `outline.py`, sửa script, hay thay
`base.docx`.** Đó là bộ bắt lệch giữa skill và pipeline.

**Bước 3 — file mẫu sạch với sổ thật**

```bash
cd references/golden
python ../../scripts/validate.py FUNC-QLNSD-001.md --registry-dir registries
python ../../scripts/validate.py GRP-QLNSD-01.md   --registry-dir registries
```

Cả hai phải ra `0 lỗi`.

**Bước 4 — xuất được Word và PDF**

```bash
python ../../scripts/render.py FUNC-QLNSD-001.md -o out/thu.docx
python ../../scripts/export_pdf.py out/thu.docx
```

Mở PDF, kiểm ba thứ: ảnh mockup **không bị méo**, caption đánh số `Hình 1`
`Hình 2` chứ không lặp lại `Hình 1`, và bảng không tràn lề.

Nếu thấy dòng *"trường SEQ/TOC KHÔNG được cập nhật"* thì máy thiếu
`python3-uno` — số hiệu Hình/Bảng trong PDF có thể sai. Cài `python3-uno`, hoặc
mở bằng Word, `Ctrl+A`, `F9` rồi xuất lại.

**Bước 5 — sơ đồ PlantUML**

Cần **Java** trên máy, không chỉ cần file jar. Kiểm trước:

```bash
java -version
```

Không có thì cài JRE 17+ (`winget install Microsoft.OpenJDK.17` trên Windows).
Không cài được Java thì dùng `plantuml_server` — đó là đường duy nhất không cần
Java.

Mạng chặn `github.com`: tải tay `plantuml-1.2026.0.jar` từ trang release của
PlantUML, đặt vào gốc dự án tên `plantuml.jar`, hoặc khai `plantuml_jar` trong
`srs-config.json`. Skill ưu tiên file này trước khi nghĩ đến tải.


Chỉ cần nếu dự án dùng loại `TICHHOP` hoặc `JOB`.

```bash
python scripts/render.py «file có [[DIAGRAM:...]]».md -o out/sd.docx
```

Không có dòng `CẢNH BÁO: không gọi được PlantUML server` tức là đường sơ đồ
chạy đúng. Lần đầu sẽ mất ~15 giây tải jar 26 MB từ GitHub.

---

## 4b. `base.docx` — template Word của toàn bộ tài liệu

Mọi font, cỡ chữ, màu, kiểu bảng và bố cục trang của bản `.docx` nằm trong
**một file duy nhất**: `assets/base.docx` trong skill. Không có định dạng nào
ghi cứng trong code — `render.py` mở `base.docx`, **xoá sạch phần thân**, rồi
đổ nội dung vào bằng các style có sẵn trong đó.

Nghĩa là đổi bộ nhận diện cho cả dự án = sửa đúng một file, không đụng code.

### Mười một style đang được dùng

`outline.json` tra style **theo tên**. Tên phải khớp tuyệt đối:

| Khoá trong outline | Tên style trong Word | Dùng cho |
|---|---|---|
| `function` | `Heading 3` | Đề mục chức năng |
| `function_section` | `Heading 4` | Mục cấp chức năng |
| `feature` | `Heading 4` | Đề mục tính năng |
| `feature_section` | `Heading 5` | Mục trong tính năng |
| `body` | `T-NoiDung` | Văn xuôi |
| `bullet_1` · `bullet_2` · `bullet_3` | `T-Gach -` · `T-Gach +` · `T-Gach *` | Gạch đầu dòng ba cấp |
| `caption` | `Caption` | Chú thích Hình / Bảng |
| `note` | `T-GhiChu` | Ghi chú, và là nội dung chính của file nhóm |
| `table` | `TableStyle3` | Mọi bảng |

### Sửa được gì, sửa gì thì hỏng

| Việc | Kết quả |
|---|---|
| Đổi **định nghĩa** style — font, cỡ, màu, giãn dòng, thụt lề | An toàn. Đây là cách đúng để áp bộ nhận diện công ty |
| Đổi **lề trang**, khổ giấy, hướng giấy | An toàn |
| Thêm style mới không dùng tới | Vô hại |
| **Đổi TÊN style** | **Hỏng.** Outline tra theo tên; đổi `T-NoiDung` thành `Body Text` là mọi đoạn văn mất style |
| Xoá một trong 11 style trên | **Hỏng** — render lùi về style mặc định, không báo gì |
| Đặt `styleId` có ký tự lạ (`*`, khoảng trắng) | **Hỏng.** Word báo *"Show Repairs"* khi mở. Đã từng xảy ra với `T-Gach *` — `w:name` giữ dấu `*` được, `w:styleId` thì không |

Header và footer của `base.docx` **cố ý để trống**: bản mặc định là file con
ghép vào tài liệu tổng, và tổng lo phần đó. Bìa, logo, số trang chỉ xuất hiện
với `--standalone`, và lấy dữ liệu từ `srs-config.json` của dự án.

### Quy trình thay `base.docx`

```bash
# 1. Sửa file bằng Word: đổi định nghĩa style, KHÔNG đổi tên
# 2. Chép đè vào assets/base.docx trong skill
# 3. Bắt buộc — chạy lại toàn bộ hồi quy
python evals/run_evals.py
# 4. Render file mẫu rồi mở bằng Word xem có bị báo "Show Repairs" không
cd references/golden && python ../../scripts/render.py FUNC-QLNSD-001.md -o out/thu.docx
```

Bước 3 không bỏ được: bộ eval có phép kiểm đối chiếu **từng style outline khai
với style thật có trong file**, và đó là thứ bắt được lỗi đổi tên trước khi nó
đến tay BA.

Đóng gói lại sau khi đổi: ở kho nguồn chạy `python tools/build_skills.py` —
một lệnh sinh lại cả gói `.skill` lẫn bản Codex/Antigravity trong `dist/`.
Không chép tay sang bản nào.

---

## 5. Tập huấn BA

Ba tài liệu, đọc theo thứ tự:

| Tài liệu | Ai đọc | Nội dung |
|---|---|---|
| `references/huong-dan-ba.md` | mọi BA | 12 mục: cài đặt, viết mới, sửa, soát, quy tắc viết, mã, hình, checklist, tra lỗi |
| `references/golden/FUNC-QLNSD-001.md` | mọi BA | Chuẩn văn phong. Đọc trước khi viết file đầu tiên |
| `references/validation-catalog.md` | mọi BA | 35 dòng ràng buộc → cách diễn đạt chuẩn |

Hai tài liệu tra cứu khi cần: `references/md-syntax.md` (cú pháp) và
`references/co-dong-lenh.md` (cờ dòng lệnh).

**Năm luật nhấn mạnh khi tập huấn** — đây là chỗ hay sai nhất:

1. **File `.md` là bản gốc.** Sửa nội dung trong Word sẽ mất khi render lần sau.
2. **Không xoá mục.** Không dùng thì ghi `Không áp dụng`.
3. **Không gõ tay số** mục, số hình, số bảng, **và cột `STT`** — render tự
   tính lại mỗi lần xuất, nên chèn dòng giữa bảng không phải đánh số lại.
4. **Claude không được bịa.** Chỗ nào chưa chốt sẽ có `⟨?⟩` và một dòng ở *Vấn
   đề còn mở*. Còn dấu đó thì chỉ ra được bản nháp — đó là tính năng, không phải
   lỗi.
5. **Lệch phiên bản đề cương thì chạy `migrate_outline.py`**, không sửa tay
   từng dòng. Sửa tay thì mỗi người chèn một kiểu, và những dòng chèn thêm sẽ
   không có ai theo dõi để điền nội dung.

---

## 6. Khi sửa chuẩn

Đề cương đóng gói **trong** skill, cập nhật thủ công:

```
1. Sửa tools/outline.py bên pipeline
2. Chạy lại make_child_template.py và make_child_template_md.py
3. Sinh lại references/outline.json trong skill cho khớp
4. python scripts/outline_check.py
5. python evals/run_evals.py --pipeline …     ← không --pipeline phải 327/327 (321/321 nếu thiếu LibreOffice)
6. python tools/build_skills.py   ← sinh lại mọi bản phát, rồi phát cho team
```

Bước 5 là bước không được bỏ. Nó bắt được đúng loại lỗi mà mắt không thấy: lệch
độ rộng cột, mục thêm/bớt, `has_features` sai, style tham chiếu không tồn tại.

**Nếu sửa chuẩn làm hỏng tài liệu cũ** — thêm/bớt mục, thêm dòng bắt buộc vào
bảng `kv`, đổi tên mục — thì đó là **thay đổi phá vỡ tương thích**, phải làm
thêm ba việc:

```
a. Tăng số MAJOR của `version` trong outline.json (vd. 4.1 → 5.0)
b. Thêm một mục vào mảng `migrations`: tu, den, ly_do, lenh
c. Sửa migrate_outline.py nếu kiểu thay đổi mới chưa được xử lý
```

`validate.py` **chặn** (lỗi, không phải cảnh báo) mọi file khai phiên bản major
cũ, và thông báo lỗi in thẳng lệnh migration lấy từ `migrations`. Không có mục
`migrations` thì BA nhận một đống lỗi "thiếu mục" không đầu không cuối và sẽ
sửa tay từng file — đúng thứ cần tránh.

Đề cương hiện hành: **v6.1**. Chuỗi nâng cấp có sẵn — `migrate_outline.py` tự
đi hết chuỗi trong một lượt:

| Chặng | Đổi gì |
|---|---|
| `4.1 → 5.0` | Thêm hai dòng *Trong phạm vi* / *Ngoài phạm vi* vào *Mô tả chung* |
| `5.0 → 6.0` | Ô ở các cột khai `multiline_columns.cho_phep` render thành gạch đầu dòng. **Nội dung `.md` không đổi** — chỉ cách trình bày đổi |
| `6.0 → 6.1` | `cho_phep` mở từ 5 lên 15 cột, `canh_bao` từ 3 lên 4, phủ đủ cả năm loại thay vì gần như chỉ `UI`. Lệch **NHỎ**: không chặn, chỉ cảnh báo cho tới khi chạy migration |

**Chặng 5.0 → 6.0 đòi render lại toàn bộ tài liệu đã phát hành.** `.docx` sinh
ra khác đi, nên `doc_sha` nhúng trong đó lệch với bản `.md`, và
`import_docx --diff` sẽ báo "bị sửa tay" hàng loạt nếu bỏ qua bước này.

```bash
python scripts/migrate_outline.py functions/*.md --nguoi "Lead BA"
```

---

## 7. Chưa kiểm chứng ở điều kiện thật

Nói trước để biết chỗ mà nhìn khi có vấn đề:

| Chỗ | Vì sao |
|---|---|
| **Ảnh mockup thật** | Chỉ thử với ảnh tự sinh. Ảnh Figma có thể rất lớn, tỉ lệ lạ, định dạng khác PNG |
| **PlantUML server** | Đường HTTP chưa gọi được server thật lần nào. Bộ mã hoá đã kiểm 3/3 ca |
| **Tài liệu SRS cũ thật** | `migrate_scan.py` chỉ thử trên file tự dựng |
| **Sửa tay .docx nhiều vòng** | Chỉ thử một vòng. Có comment hay track changes thì chưa biết |
| **Xuống dòng trong ô bảng** | Cú pháp md cấm. BA quen Word sẽ vấp chỗ này |

Hiệu năng đã đo: 25 tính năng render 1,6s · 40 file 13,1s · ước tính 661 chức
năng khoảng 4 phút.
