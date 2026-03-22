from flask import Blueprint, request, jsonify
from models import DonVi, CanBo, HocPhan
from extensions import db
from routes.api_auth import token_required, role_required

api_donvi_bp = Blueprint('api_donvi', __name__)


def _dv_to_dict(dv: DonVi, include_stats: bool = False) -> dict:
    d = {
        'id':        dv.idDonVi,
        'maDonVi':   dv.maDonVi,
        'tenDonVi':  dv.tenDonVi,
        'loaiDonVi': dv.loaiDonVi,
        'moTa':      dv.moTa if hasattr(dv, 'moTa') else None,
        'ngayTao':   dv.ngayTao.isoformat() if hasattr(dv, 'ngayTao') and dv.ngayTao else None,
    }
    if include_stats:
        d['soCanBo']    = CanBo.query.filter_by(idDonVi=dv.idDonVi).count()
        d['soHocPhan']  = HocPhan.query.filter_by(idDonVi=dv.idDonVi).count()
    return d


# ─────────────────────────────────────────────
# GET /api/don-vi/           – Danh sách đơn vị
# ─────────────────────────────────────────────
@api_donvi_bp.route('/', methods=['GET'])
@token_required
def get_list(current_cb):
    """
    Query params:
      - loai  (khoa | phong | bo_mon ...)
      - q     (tìm theo tên/mã)
      - stats (true → thêm số cán bộ, học phần)
    """
    loai       = request.args.get('loai')
    q          = request.args.get('q', '').strip()
    with_stats = request.args.get('stats', '').lower() == 'true'

    query = DonVi.query

    if loai:
        query = query.filter_by(loaiDonVi=loai)
    if q:
        like = f'%{q}%'
        query = query.filter(
            (DonVi.tenDonVi.ilike(like)) | (DonVi.maDonVi.ilike(like))
        )

    don_vis = query.order_by(DonVi.tenDonVi).all()
    return jsonify({
        'success': True,
        'data': [_dv_to_dict(dv, include_stats=with_stats) for dv in don_vis],
        'total': len(don_vis),
    })


# ─────────────────────────────────────────────
# GET /api/don-vi/<id>       – Chi tiết đơn vị
# ─────────────────────────────────────────────
@api_donvi_bp.route('/<int:dv_id>', methods=['GET'])
@token_required
def get_one(current_cb, dv_id):
    dv = DonVi.query.get_or_404(dv_id)
    return jsonify({'success': True, 'data': _dv_to_dict(dv, include_stats=True)})


# ─────────────────────────────────────────────
# GET /api/don-vi/<id>/can-bo – Cán bộ trong đơn vị
# ─────────────────────────────────────────────
@api_donvi_bp.route('/<int:dv_id>/can-bo', methods=['GET'])
@token_required
def get_can_bo(current_cb, dv_id):
    DonVi.query.get_or_404(dv_id)
    can_bos = CanBo.query.filter_by(idDonVi=dv_id).order_by(CanBo.hoTen).all()
    return jsonify({
        'success': True,
        'data': [
            {
                'id':     cb.idCanBo,
                'maCB':   cb.maCB,
                'hoTen':  cb.hoTen,
                'email':  cb.email,
                'vaiTro': cb.vaiTro,
            }
            for cb in can_bos
        ],
        'total': len(can_bos),
    })


# ─────────────────────────────────────────────
# GET /api/don-vi/<id>/hoc-phan – Học phần của đơn vị
# ─────────────────────────────────────────────
@api_donvi_bp.route('/<int:dv_id>/hoc-phan', methods=['GET'])
@token_required
def get_hoc_phan(current_cb, dv_id):
    DonVi.query.get_or_404(dv_id)
    hoc_phans = HocPhan.query.filter_by(idDonVi=dv_id).order_by(HocPhan.tenHP).all()
    return jsonify({
        'success': True,
        'data': [
            {
                'id':       hp.idHocPhan,
                'maHP':     hp.maHP,
                'tenHP':    hp.tenHP,
                'soTinChi': hp.soTinChi,
                'trangThai': getattr(hp, 'trangThai', None),
            }
            for hp in hoc_phans
        ],
        'total': len(hoc_phans),
    })


# ─────────────────────────────────────────────
# POST /api/don-vi/          – Tạo đơn vị mới
# ─────────────────────────────────────────────
@api_donvi_bp.route('/', methods=['POST'])
@token_required
@role_required('admin')
def create(current_cb):
    """
    Body JSON:
    {
      "maDonVi": "CNTT",
      "tenDonVi": "Khoa Công nghệ thông tin",
      "loaiDonVi": "khoa",   // khoa | phong | bo_mon
      "moTa": "..."          // tuỳ chọn
    }
    """
    data = request.get_json(silent=True) or {}

    for field in ['maDonVi', 'tenDonVi', 'loaiDonVi']:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'Thiếu trường: {field}'}), 400

    if DonVi.query.filter_by(maDonVi=data['maDonVi']).first():
        return jsonify({'success': False, 'message': 'Mã đơn vị đã tồn tại.'}), 409

    dv = DonVi(
        maDonVi=data['maDonVi'],
        tenDonVi=data['tenDonVi'],
        loaiDonVi=data['loaiDonVi'],
    )
    if hasattr(dv, 'moTa') and data.get('moTa'):
        dv.moTa = data['moTa']

    db.session.add(dv)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Tạo đơn vị thành công.', 'data': _dv_to_dict(dv)}), 201


# ─────────────────────────────────────────────
# PUT /api/don-vi/<id>       – Cập nhật đơn vị
# ─────────────────────────────────────────────
@api_donvi_bp.route('/<int:dv_id>', methods=['PUT'])
@token_required
@role_required('admin')
def update(current_cb, dv_id):
    dv = DonVi.query.get_or_404(dv_id)
    data = request.get_json(silent=True) or {}

    for field in ['tenDonVi', 'loaiDonVi']:
        if field in data:
            setattr(dv, field, data[field])
    if hasattr(dv, 'moTa') and 'moTa' in data:
        dv.moTa = data['moTa']

    db.session.commit()
    return jsonify({'success': True, 'message': 'Cập nhật đơn vị thành công.', 'data': _dv_to_dict(dv)})


# ─────────────────────────────────────────────
# DELETE /api/don-vi/<id>    – Xoá đơn vị
# ─────────────────────────────────────────────
@api_donvi_bp.route('/<int:dv_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete(current_cb, dv_id):
    dv = DonVi.query.get_or_404(dv_id)

    # Kiểm tra còn cán bộ/học phần không
    if CanBo.query.filter_by(idDonVi=dv_id).count() > 0:
        return jsonify({
            'success': False,
            'message': 'Không thể xoá đơn vị còn cán bộ. Hãy chuyển cán bộ trước.'
        }), 400

    if HocPhan.query.filter_by(idDonVi=dv_id).count() > 0:
        return jsonify({
            'success': False,
            'message': 'Không thể xoá đơn vị còn học phần. Hãy xoá học phần trước.'
        }), 400

    db.session.delete(dv)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Đã xoá đơn vị {dv.tenDonVi}.'})