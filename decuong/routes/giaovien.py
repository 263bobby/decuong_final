from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import CanBoHocPhan, HocPhan, DeCuong, LichSuHieuChinh
from extensions import db

giaovien_bp = Blueprint('giaovien', __name__)

def can_bo_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_can_bo():
            flash('Bạn không có quyền truy cập.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def _get_phan_quyen(hp_id):
    pq = CanBoHocPhan.query.filter_by(
        idCanBo=current_user.idCanBo, idHocPhan=hp_id).first()
    return pq if (pq and pq.con_hieu_luc) else None

@giaovien_bp.route('/dashboard')
@login_required
@can_bo_required
def dashboard():
    ds_pq = [pq for pq in current_user.phan_quyen_list if pq.con_hieu_luc]
    return render_template('giaovien/dashboard.html', ds_pq=ds_pq)

@giaovien_bp.route('/de-cuong/<int:hp_id>')
@login_required
@can_bo_required
def xem_de_cuong(hp_id):
    pq = _get_phan_quyen(hp_id)
    if not pq:
        flash('Bạn không được phân quyền hiệu chỉnh học phần này.', 'danger')
        return redirect(url_for('giaovien.dashboard'))
    hp = HocPhan.query.get_or_404(hp_id)
    dc = hp.de_cuong
    if not dc:
        flash('Đề cương chưa được tạo. Liên hệ Admin Đơn vị.', 'warning')
        return redirect(url_for('giaovien.dashboard'))
    # Dùng idLichSu thay thoiGian vì thoiGian đã xóa khỏi model
    lich_su = LichSuHieuChinh.query.filter_by(idDeCuong=dc.idDeCuong)\
        .order_by(LichSuHieuChinh.idLichSu.desc()).limit(10).all()
    return render_template('giaovien/de_cuong.html', hp=hp, dc=dc, pq=pq, lich_su=lich_su)

@giaovien_bp.route('/de-cuong/<int:dc_id>/luu', methods=['POST'])
@login_required
@can_bo_required
def luu_de_cuong(dc_id):
    dc = DeCuong.query.get_or_404(dc_id)
    pq = _get_phan_quyen(dc.idHocPhan)
    if not pq:
        flash('Bạn không có quyền hiệu chỉnh.', 'danger')
        return redirect(url_for('giaovien.dashboard'))

    ls = LichSuHieuChinh(
        idDeCuong=dc.idDeCuong,
        idCanBo=current_user.idCanBo,
        noiDungCu=dc.noiDung,
        noiDungMoi=request.form.get('noiDung', ''),
        truongThayDoi='noiDung',
        ghiChu=request.form.get('ghiChu', '')
    )
    db.session.add(ls)

    dc.mucTieu    = request.form.get('mucTieu',    dc.mucTieu)
    dc.noiDung    = request.form.get('noiDung',    dc.noiDung)
    dc.taiLieu    = request.form.get('taiLieu',    dc.taiLieu)
    dc.ppGiangDay = request.form.get('ppGiangDay', dc.ppGiangDay)
    dc.ppDanhGia  = request.form.get('ppDanhGia',  dc.ppDanhGia)
    dc.trangThai  = 'dang_hieu_chinh'

    db.session.commit()
    flash('Đã lưu hiệu chỉnh thành công!', 'success')
    return redirect(url_for('giaovien.xem_de_cuong', hp_id=dc.idHocPhan))

@giaovien_bp.route('/de-cuong/<int:dc_id>/hoan-thanh', methods=['POST'])
@login_required
@can_bo_required
def hoan_thanh(dc_id):
    dc = DeCuong.query.get_or_404(dc_id)
    pq = _get_phan_quyen(dc.idHocPhan)
    if not pq or not pq.quyenDuyetDC:
        flash('Bạn không có quyền xác nhận hoàn thành.', 'danger')
        return redirect(url_for('giaovien.dashboard'))
    dc.trangThai = 'hoan_thanh'
    db.session.commit()
    flash('Đã đánh dấu đề cương hoàn thành.', 'success')
    return redirect(url_for('giaovien.xem_de_cuong', hp_id=dc.idHocPhan))