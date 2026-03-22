from flask import Blueprint, request, jsonify
from models import CanBo, DonVi
from extensions import db
from routes.api_auth import token_required, role_required

api_canbo_bp = Blueprint('api_canbo', __name__)


def _cb_to_dict(cb: CanBo) -> dict:
    return {
        'id':        cb.idCanBo,
        'maCB':      cb.maCB,
        'hoTen':     cb.hoTen,
        'gioiTinh':  cb.gioiTinh,
        'ngaySinh':  cb.ngaySinh.isoformat() if cb.ngaySinh else None,
        'email':     cb.email,
        'soDienThoai': getattr(cb, 'soDienThoai', None),
        'hocVi':     getattr(cb, 'hocVi', None),
        'chuyenNganh': getattr(cb, 'chuyenNganh', None),
        'vaiTro':    cb.vaiTro,
        'idDonVi':   cb.idDonVi,
        'tenDonVi':  cb.don_vi.tenDonVi if cb.don_vi else None,
    }


# ─────────────────────────────────────────────
# GET /api/can-bo/          – Danh sách cán bộ
# ─────────────────────────────────────────────
@api_canbo_bp.route('/', methods=['GET'])
@token_required
@role_required('admin', 'admin_donvi')
def get_list(current_cb):
    """
    Query params:
      - page  (default 1)
      - per_page (default 20)
      - don_vi  (lọc theo idDonVi)
      - vai_tro (lọc theo vaiTro)
      - q       (tìm theo tên hoặc mã)
    """
    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    don_vi   = request.args.get('don_vi')
    vai_tro  = request.args.get('vai_tro')
    q        = request.args.get('q', '').strip()

    query = CanBo.query

    # Admin đơn vị chỉ xem được đơn vị mình
    if current_cb.vaiTro == 'admin_donvi':
        query = query.filter_by(idDonVi=current_cb.idDonVi)
    elif don_vi:
        query = query.filter_by(idDonVi=int(don_vi))

    if vai_tro:
        query = query.filter_by(vaiTro=vai_tro)
    if q:
        like = f'%{q}%'
        query = query.filter(
            (CanBo.hoTen.ilike(like)) | (CanBo.maCB.ilike(like)) | (CanBo.email.ilike(like))
        )

    pagination = query.order_by(CanBo.hoTen).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data': [_cb_to_dict(cb) for cb in pagination.items],
        'pagination': {
            'page':       pagination.page,
            'per_page':   pagination.per_page,
            'total':      pagination.total,
            'total_pages': pagination.pages,
        }
    })


# ─────────────────────────────────────────────
# GET /api/can-bo/<id>      – Chi tiết cán bộ
# ─────────────────────────────────────────────
@api_canbo_bp.route('/<int:cb_id>', methods=['GET'])
@token_required
def get_one(current_cb, cb_id):
    # Cán bộ thường chỉ xem được chính mình
    if current_cb.vaiTro == 'can_bo' and current_cb.idCanBo != cb_id:
        return jsonify({'success': False, 'message': 'Không có quyền truy cập.'}), 403

    cb = CanBo.query.get_or_404(cb_id)
    return jsonify({'success': True, 'data': _cb_to_dict(cb)})


# ─────────────────────────────────────────────
# POST /api/can-bo/         – Tạo cán bộ mới
# ─────────────────────────────────────────────
@api_canbo_bp.route('/', methods=['POST'])
@token_required
@role_required('admin', 'admin_donvi')
def create(current_cb):
    """
    Body JSON:
    {
      "maCB": "CB010",
      "hoTen": "Nguyễn Văn X",
      "email": "x@edu.vn",
      "password": "abc123",
      "vaiTro": "can_bo",       // admin | admin_donvi | can_bo
      "idDonVi": 1,
      "gioiTinh": "Nam",        // tuỳ chọn
      "ngaySinh": "1990-01-15", // tuỳ chọn
      "hocVi": "Thạc sĩ",       // tuỳ chọn
      "chuyenNganh": "CNTT"     // tuỳ chọn
    }
    """
    data = request.get_json(silent=True) or {}

    required = ['maCB', 'hoTen', 'email', 'password', 'vaiTro', 'idDonVi']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'Thiếu trường bắt buộc: {field}'}), 400

    # Admin đơn vị không được tạo admin hệ thống
    if current_cb.vaiTro == 'admin_donvi' and data['vaiTro'] == 'admin':
        return jsonify({'success': False, 'message': 'Không có quyền tạo tài khoản admin.'}), 403

    if CanBo.query.filter_by(maCB=data['maCB']).first():
        return jsonify({'success': False, 'message': 'Mã cán bộ đã tồn tại.'}), 409
    if CanBo.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email đã được sử dụng.'}), 409
    if not DonVi.query.get(data['idDonVi']):
        return jsonify({'success': False, 'message': 'Đơn vị không tồn tại.'}), 400

    cb = CanBo(
        maCB=data['maCB'],
        hoTen=data['hoTen'],
        email=data['email'],
        vaiTro=data['vaiTro'],
        idDonVi=data['idDonVi'],
        gioiTinh=data.get('gioiTinh', 'Nam'),
    )
    if data.get('ngaySinh'):
        from datetime import date
        cb.ngaySinh = date.fromisoformat(data['ngaySinh'])
    for field in ('hocVi', 'chuyenNganh', 'soDienThoai'):
        if data.get(field):
            setattr(cb, field, data[field])

    cb.set_password(data['password'])
    db.session.add(cb)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Tạo cán bộ thành công.', 'data': _cb_to_dict(cb)}), 201


# ─────────────────────────────────────────────
# PUT /api/can-bo/<id>      – Cập nhật cán bộ
# ─────────────────────────────────────────────
@api_canbo_bp.route('/<int:cb_id>', methods=['PUT'])
@token_required
def update(current_cb, cb_id):
    cb = CanBo.query.get_or_404(cb_id)

    # Cán bộ thường chỉ sửa được chính mình, và không sửa được vaiTro / idDonVi
    if current_cb.vaiTro == 'can_bo' and current_cb.idCanBo != cb_id:
        return jsonify({'success': False, 'message': 'Không có quyền chỉnh sửa.'}), 403

    data = request.get_json(silent=True) or {}

    updatable = ['hoTen', 'gioiTinh', 'hocVi', 'chuyenNganh', 'soDienThoai']
    if current_cb.vaiTro in ('admin', 'admin_donvi'):
        updatable += ['email', 'vaiTro', 'idDonVi']

    for field in updatable:
        if field in data:
            setattr(cb, field, data[field])

    if 'ngaySinh' in data and data['ngaySinh']:
        from datetime import date
        cb.ngaySinh = date.fromisoformat(data['ngaySinh'])

    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return jsonify({'success': False, 'message': 'Mật khẩu phải có ít nhất 6 ký tự.'}), 400
        cb.set_password(data['password'])

    db.session.commit()
    return jsonify({'success': True, 'message': 'Cập nhật thành công.', 'data': _cb_to_dict(cb)})


# ─────────────────────────────────────────────
# DELETE /api/can-bo/<id>   – Xoá cán bộ
# ─────────────────────────────────────────────
@api_canbo_bp.route('/<int:cb_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete(current_cb, cb_id):
    if current_cb.idCanBo == cb_id:
        return jsonify({'success': False, 'message': 'Không thể xoá chính mình.'}), 400

    cb = CanBo.query.get_or_404(cb_id)
    db.session.delete(cb)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Đã xoá cán bộ {cb.hoTen}.'})