from flask import Blueprint, request, jsonify
from models import HocPhan, CanBoHocPhan, CanBo, DonVi
from extensions import db
from routes.api_auth import token_required, role_required

api_hocphan_bp = Blueprint('api_hocphan', __name__)


def _hp_to_dict(hp: HocPhan, include_canbo: bool = False) -> dict:
    d = {
        'id':         hp.idHocPhan,
        'maHP':       hp.maHP,
        'tenHP':      hp.tenHP,
        'soTinChi':   hp.soTinChi,
        'moTa':       hp.moTa,
        'idDonVi':    hp.idDonVi,
        'tenDonVi':   hp.don_vi.tenDonVi if hp.don_vi else None,
        'trangThai':  getattr(hp, 'trangThai', 'dang_su_dung'),
        'ngayTao':    hp.ngayTao.isoformat() if hp.ngayTao else None,
    }
    if include_canbo:
        d['canBo'] = [
            {
                'idCanBo': cbhp.can_bo.idCanBo,
                'hoTen':   cbhp.can_bo.hoTen,
                'maCB':    cbhp.can_bo.maCB,
                'email':   cbhp.can_bo.email,
            }
            for cbhp in hp.can_bo_hoc_phan
            if cbhp.can_bo
        ]
    return d


# ─────────────────────────────────────────────
# GET /api/hoc-phan/         – Danh sách học phần
# ─────────────────────────────────────────────
@api_hocphan_bp.route('/', methods=['GET'])
@token_required
def get_list(current_cb):
    """
    Query params:
      - page, per_page
      - don_vi   (idDonVi)
      - trang_thai
      - q        (tìm theo tên/mã)
      - my        (true → chỉ HP được phân công cho mình)
    """
    page       = int(request.args.get('page', 1))
    per_page   = int(request.args.get('per_page', 20))
    don_vi     = request.args.get('don_vi')
    trang_thai = request.args.get('trang_thai')
    q          = request.args.get('q', '').strip()
    only_mine  = request.args.get('my', '').lower() == 'true'

    query = HocPhan.query

    if only_mine or current_cb.vaiTro == 'can_bo':
        # Lấy danh sách HP được phân công
        hp_ids = [cbhp.idHocPhan for cbhp in current_cb.can_bo_hoc_phan]
        query = query.filter(HocPhan.idHocPhan.in_(hp_ids))
    elif current_cb.vaiTro == 'admin_donvi':
        query = query.filter_by(idDonVi=current_cb.idDonVi)
    elif don_vi:
        query = query.filter_by(idDonVi=int(don_vi))

    if trang_thai:
        query = query.filter_by(trangThai=trang_thai)
    if q:
        like = f'%{q}%'
        query = query.filter(
            (HocPhan.tenHP.ilike(like)) | (HocPhan.maHP.ilike(like))
        )

    pagination = query.order_by(HocPhan.tenHP).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data': [_hp_to_dict(hp) for hp in pagination.items],
        'pagination': {
            'page':        pagination.page,
            'per_page':    pagination.per_page,
            'total':       pagination.total,
            'total_pages': pagination.pages,
        }
    })


# ─────────────────────────────────────────────
# GET /api/hoc-phan/<id>     – Chi tiết + danh sách cán bộ
# ─────────────────────────────────────────────
@api_hocphan_bp.route('/<int:hp_id>', methods=['GET'])
@token_required
def get_one(current_cb, hp_id):
    hp = HocPhan.query.get_or_404(hp_id)

    # Cán bộ thường chỉ xem HP của mình
    if current_cb.vaiTro == 'can_bo':
        ids = [cbhp.idHocPhan for cbhp in current_cb.can_bo_hoc_phan]
        if hp_id not in ids:
            return jsonify({'success': False, 'message': 'Không có quyền truy cập.'}), 403

    return jsonify({'success': True, 'data': _hp_to_dict(hp, include_canbo=True)})


# ─────────────────────────────────────────────
# POST /api/hoc-phan/        – Tạo học phần mới
# ─────────────────────────────────────────────
@api_hocphan_bp.route('/', methods=['POST'])
@token_required
@role_required('admin', 'admin_donvi')
def create(current_cb):
    """
    Body JSON:
    {
      "maHP": "CS301",
      "tenHP": "Lập trình Web",
      "soTinChi": 3,
      "idDonVi": 1,
      "moTa": "...",        // tuỳ chọn
      "trangThai": "dang_su_dung"  // tuỳ chọn
    }
    """
    data = request.get_json(silent=True) or {}

    for field in ['maHP', 'tenHP', 'soTinChi', 'idDonVi']:
        if data.get(field) is None:
            return jsonify({'success': False, 'message': f'Thiếu trường: {field}'}), 400

    if HocPhan.query.filter_by(maHP=data['maHP']).first():
        return jsonify({'success': False, 'message': 'Mã học phần đã tồn tại.'}), 409

    if not DonVi.query.get(data['idDonVi']):
        return jsonify({'success': False, 'message': 'Đơn vị không tồn tại.'}), 400

    try:
        so_tin_chi = int(data['soTinChi'])
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'soTinChi phải là số nguyên.'}), 400

    hp = HocPhan(
        maHP=data['maHP'],
        tenHP=data['tenHP'],
        soTinChi=so_tin_chi,
        idDonVi=data['idDonVi'],
        moTa=data.get('moTa'),
    )
    if hasattr(hp, 'trangThai'):
        hp.trangThai = data.get('trangThai', 'dang_su_dung')

    db.session.add(hp)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Tạo học phần thành công.', 'data': _hp_to_dict(hp)}), 201


# ─────────────────────────────────────────────
# PUT /api/hoc-phan/<id>     – Cập nhật học phần
# ─────────────────────────────────────────────
@api_hocphan_bp.route('/<int:hp_id>', methods=['PUT'])
@token_required
@role_required('admin', 'admin_donvi')
def update(current_cb, hp_id):
    hp = HocPhan.query.get_or_404(hp_id)

    if current_cb.vaiTro == 'admin_donvi' and hp.idDonVi != current_cb.idDonVi:
        return jsonify({'success': False, 'message': 'Không có quyền sửa học phần của đơn vị khác.'}), 403

    data = request.get_json(silent=True) or {}

    for field in ['tenHP', 'moTa', 'trangThai']:
        if field in data:
            setattr(hp, field, data[field])

    if 'soTinChi' in data:
        try:
            hp.soTinChi = int(data['soTinChi'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'soTinChi phải là số nguyên.'}), 400

    db.session.commit()
    return jsonify({'success': True, 'message': 'Cập nhật học phần thành công.', 'data': _hp_to_dict(hp)})


# ─────────────────────────────────────────────
# DELETE /api/hoc-phan/<id>  – Xoá học phần
# ─────────────────────────────────────────────
@api_hocphan_bp.route('/<int:hp_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete(current_cb, hp_id):
    hp = HocPhan.query.get_or_404(hp_id)
    db.session.delete(hp)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Đã xoá học phần {hp.tenHP}.'})


# ─────────────────────────────────────────────
# POST /api/hoc-phan/<id>/phan-cong  – Phân công cán bộ
# ─────────────────────────────────────────────
@api_hocphan_bp.route('/<int:hp_id>/phan-cong', methods=['POST'])
@token_required
@role_required('admin', 'admin_donvi')
def assign_can_bo(current_cb, hp_id):
    """
    Body JSON: { "idCanBo": 5 }
    Phân công một cán bộ vào học phần.
    """
    hp = HocPhan.query.get_or_404(hp_id)

    if current_cb.vaiTro == 'admin_donvi' and hp.idDonVi != current_cb.idDonVi:
        return jsonify({'success': False, 'message': 'Không có quyền.'}), 403

    data = request.get_json(silent=True) or {}
    id_can_bo = data.get('idCanBo')
    if not id_can_bo:
        return jsonify({'success': False, 'message': 'Thiếu idCanBo.'}), 400

    cb = CanBo.query.get_or_404(id_can_bo)

    # Kiểm tra đã phân công chưa
    existing = CanBoHocPhan.query.filter_by(
        idCanBo=id_can_bo, idHocPhan=hp_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': 'Cán bộ đã được phân công vào học phần này.'}), 409

    cbhp = CanBoHocPhan(idCanBo=id_can_bo, idHocPhan=hp_id)
    db.session.add(cbhp)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Đã phân công {cb.hoTen} vào học phần {hp.tenHP}.'
    }), 201


# ─────────────────────────────────────────────
# DELETE /api/hoc-phan/<id>/phan-cong/<cb_id>  – Huỷ phân công
# ─────────────────────────────────────────────
@api_hocphan_bp.route('/<int:hp_id>/phan-cong/<int:cb_id>', methods=['DELETE'])
@token_required
@role_required('admin', 'admin_donvi')
def remove_can_bo(current_cb, hp_id, cb_id):
    hp = HocPhan.query.get_or_404(hp_id)

    if current_cb.vaiTro == 'admin_donvi' and hp.idDonVi != current_cb.idDonVi:
        return jsonify({'success': False, 'message': 'Không có quyền.'}), 403

    cbhp = CanBoHocPhan.query.filter_by(idCanBo=cb_id, idHocPhan=hp_id).first()
    if not cbhp:
        return jsonify({'success': False, 'message': 'Không tìm thấy phân công.'}), 404

    db.session.delete(cbhp)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Đã huỷ phân công.'})