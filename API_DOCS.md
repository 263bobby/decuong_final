# REST API – Hệ thống Quản lý Đề cương

## Cài đặt thêm
```bash
pip install PyJWT==2.8.0
```

## Base URL
```
http://127.0.0.1:5000/api
```

## Xác thực
Tất cả endpoint (trừ `/api/auth/login`) yêu cầu header:
```
Authorization: Bearer <token>
```

---

## 1. AUTH

### POST /api/auth/login
Đăng nhập, nhận JWT token (hết hạn sau 8 giờ).

**Request:**
```json
{
  "email": "admin@edu.vn",
  "password": "admin123"
}
```

**Response 200:**
```json
{
  "success": true,
  "token": "eyJhbGciOi...",
  "user": {
    "id": 1,
    "maCB": "CB001",
    "hoTen": "Nguyễn Quản Trị",
    "email": "admin@edu.vn",
    "vaiTro": "admin",
    "idDonVi": 1
  }
}
```

---

### GET /api/auth/me
Thông tin tài khoản đang đăng nhập.

---

### POST /api/auth/change-password
```json
{ "old_password": "admin123", "new_password": "newpass123" }
```

---

## 2. CÁN BỘ `/api/can-bo`

| Method | URL | Quyền | Mô tả |
|--------|-----|-------|-------|
| GET | `/api/can-bo/` | admin, admin_donvi | Danh sách (có phân trang) |
| GET | `/api/can-bo/<id>` | tất cả | Chi tiết |
| POST | `/api/can-bo/` | admin, admin_donvi | Tạo mới |
| PUT | `/api/can-bo/<id>` | tất cả* | Cập nhật |
| DELETE | `/api/can-bo/<id>` | admin | Xoá |

*Cán bộ thường chỉ sửa được chính mình.

### Query params GET /api/can-bo/
| Param | Ví dụ | Mô tả |
|-------|-------|-------|
| page | `?page=2` | Trang (mặc định 1) |
| per_page | `?per_page=10` | Số bản ghi/trang |
| don_vi | `?don_vi=1` | Lọc theo idDonVi |
| vai_tro | `?vai_tro=can_bo` | Lọc theo vai trò |
| q | `?q=nguyễn` | Tìm kiếm tên/mã/email |

### Body POST /api/can-bo/
```json
{
  "maCB": "CB010",
  "hoTen": "Nguyễn Văn X",
  "email": "x@edu.vn",
  "password": "abc123",
  "vaiTro": "can_bo",
  "idDonVi": 1,
  "gioiTinh": "Nam",
  "ngaySinh": "1990-01-15",
  "hocVi": "Thạc sĩ",
  "chuyenNganh": "CNTT"
}
```

---

## 3. HỌC PHẦN `/api/hoc-phan`

| Method | URL | Quyền | Mô tả |
|--------|-----|-------|-------|
| GET | `/api/hoc-phan/` | tất cả | Danh sách |
| GET | `/api/hoc-phan/<id>` | tất cả* | Chi tiết + cán bộ phân công |
| POST | `/api/hoc-phan/` | admin, admin_donvi | Tạo mới |
| PUT | `/api/hoc-phan/<id>` | admin, admin_donvi | Cập nhật |
| DELETE | `/api/hoc-phan/<id>` | admin | Xoá |
| POST | `/api/hoc-phan/<id>/phan-cong` | admin, admin_donvi | Phân công cán bộ |
| DELETE | `/api/hoc-phan/<id>/phan-cong/<cb_id>` | admin, admin_donvi | Huỷ phân công |

*Cán bộ thường chỉ thấy HP được phân công.

### Query params GET /api/hoc-phan/
| Param | Mô tả |
|-------|-------|
| `my=true` | Chỉ HP được phân công cho mình |
| `don_vi=<id>` | Lọc theo đơn vị |
| `trang_thai=dang_su_dung` | Lọc trạng thái |
| `q=<từ khoá>` | Tìm kiếm |

### Body POST /api/hoc-phan/phan-cong
```json
{ "idCanBo": 5 }
```

---

## 4. ĐƠN VỊ `/api/don-vi`

| Method | URL | Quyền | Mô tả |
|--------|-----|-------|-------|
| GET | `/api/don-vi/` | tất cả | Danh sách |
| GET | `/api/don-vi/<id>` | tất cả | Chi tiết + thống kê |
| GET | `/api/don-vi/<id>/can-bo` | tất cả | Cán bộ trong đơn vị |
| GET | `/api/don-vi/<id>/hoc-phan` | tất cả | Học phần của đơn vị |
| POST | `/api/don-vi/` | admin | Tạo mới |
| PUT | `/api/don-vi/<id>` | admin | Cập nhật |
| DELETE | `/api/don-vi/<id>` | admin | Xoá |

### Query params GET /api/don-vi/
| Param | Mô tả |
|-------|-------|
| `loai=khoa` | Lọc theo loại đơn vị |
| `q=<từ khoá>` | Tìm kiếm |
| `stats=true` | Thêm số cán bộ, học phần |

---

## Cấu trúc Response chuẩn

**Thành công:**
```json
{
  "success": true,
  "message": "...",
  "data": { ... }
}
```

**Lỗi:**
```json
{
  "success": false,
  "message": "Mô tả lỗi"
}
```

**Danh sách có phân trang:**
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

---

## HTTP Status Codes

| Code | Ý nghĩa |
|------|---------|
| 200 | Thành công |
| 201 | Tạo mới thành công |
| 400 | Dữ liệu đầu vào không hợp lệ |
| 401 | Chưa xác thực / Token hết hạn |
| 403 | Không có quyền |
| 404 | Không tìm thấy |
| 409 | Xung đột dữ liệu (trùng mã) |
| 500 | Lỗi máy chủ |

---

## Ví dụ dùng với curl

```bash
# 1. Đăng nhập
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@edu.vn","password":"admin123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 2. Lấy danh sách cán bộ
curl http://localhost:5000/api/can-bo/ \
  -H "Authorization: Bearer $TOKEN"

# 3. Tạo học phần
curl -X POST http://localhost:5000/api/hoc-phan/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"maHP":"CS999","tenHP":"Test","soTinChi":2,"idDonVi":1}'

# 4. Phân công cán bộ vào học phần
curl -X POST http://localhost:5000/api/hoc-phan/1/phan-cong \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"idCanBo":3}'
```