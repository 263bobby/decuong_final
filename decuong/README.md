# Hệ thống Quản lý Phân quyền Đề cương
## Stack: Flask + Jinja2 + SQL Server (SSMS)

## Cấu trúc project (SẠCH - không còn file cũ)
```
decuong/
├── app.py
├── config.py               ← SỬA _SERVER Ở ĐÂY
├── extensions.py
├── requirements.txt
├── models/
│   └── __init__.py         ← DonVi, CanBo, HocPhan, CanBoHocPhan, DeCuong, LichSuHieuChinh
├── routes/
│   ├── auth.py             ← Đăng nhập/xuất
│   ├── admin.py            ← Super Admin
│   ├── donvi.py            ← Admin Đơn vị
│   └── giaovien.py         ← Cán bộ hiệu chỉnh
├── services/
│   └── external_api.py     ← Gọi API bên thứ 3
└── templates/
    ├── base.html
    ├── auth/login.html
    ├── admin/              ← dashboard, can_bo, don_vi, hoc_phan
    ├── donvi/              ← dashboard, chi_tiet_hoc_phan
    └── giaovien/           ← dashboard, de_cuong
```

## Các bước cài đặt

### Bước 1 — Tạo database trong SSMS
Chạy file `decuong_sqlserver.sql` trong SSMS (đã có sẵn từ lần trước)

### Bước 2 — Sửa config.py
Mở `config.py`, chỉ cần sửa dòng `_SERVER`:
```python
_SERVER = r'TEN_MAY\SQLEXPRESS'   # VD: ADMIN\SQLEXPRESS
```
Xem tên server trong SSMS ở góc trên trái cửa sổ kết nối.

### Bước 3 — Cài thư viện (Terminal của PyCharm)
```
py -m pip install -r requirements.txt
```
Hoặc nếu `py` không nhận:
```
python -m pip install -r requirements.txt
```

### Bước 4 — Cài ODBC Driver (nếu chưa có)
Tải tại: https://aka.ms/odbc17  (ODBC Driver 17 for SQL Server)

### Bước 5 — Chạy
```
python app.py
```
Truy cập: http://127.0.0.1:5000

## Tài khoản demo
| Vai trò      | Email               | Mật khẩu |
|--------------|---------------------|-----------|
| Super Admin  | admin@edu.vn        | admin123  |
| Admin ĐV     | truongkhoa@edu.vn   | khoa123   |
| Cán bộ       | nguyenvana@edu.vn   | gv123     |

(Tài khoản demo tự tạo nếu DB trống, hoặc dùng seed data từ file SQL)

## Luồng sử dụng
1. **Admin** tạo Đơn vị → Học phần → Cán bộ
2. **Admin Đơn vị** vào từng học phần → phân công Cán bộ hiệu chỉnh
3. **Cán bộ** đăng nhập → thấy danh sách học phần được phân công → hiệu chỉnh đề cương
