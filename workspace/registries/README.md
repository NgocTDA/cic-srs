# Sổ đăng ký dùng chung

`so-dang-ky.xlsx` là **nguồn thật**. Các file `*.csv` là **bản build**, sinh
lại bằng:

```bash
python xuat-csv.py so-dang-ky.xlsx .
```

## Quy tắc

- Sửa trong `so-dang-ky.xlsx`, không sửa tay CSV — script `validate_child.py`
  và `project_check.py` đọc CSV, nhưng CSV lệch xlsx sẽ không tự bị phát hiện.
- Sau khi sửa xlsx: chạy `xuat-csv.py` ngay, commit **cả xlsx lẫn mọi CSV thay
  đổi** trong cùng một lần push.
- xlsx là file binary — Git không merge được. Hai người sửa cùng lúc = một
  người mất phần sửa của mình. Báo trong kênh chung của nhóm trước khi mở
  sửa, sửa xong commit/push ngay, đừng giữ file mở lâu.
- Xoá dòng ví dụ mẫu trước khi dùng thật — `xuat-csv.py` sẽ cảnh báo (không
  chặn) nếu còn sót mã ví dụ.

Chi tiết quy trình đầy đủ: [`../project-rules/srs-help.md`](../project-rules/srs-help.md).
