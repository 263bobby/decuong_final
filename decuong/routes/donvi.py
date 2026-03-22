from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import CanBo, HocPhan, DeCuong, CanBoHocPhan
from extensions import db
from services.external_api import ExternalAPIService

donvi_bp = Blueprint('donvi', __name__)

def admin_donvi_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin_donvi():
            flash('Bạn không có quyền truy cập.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@donvi_bp.route('/dashboard')
@login_required
@admin_donvi_required
def dashboard():
    hoc_phans = HocPhan.query.filter_by(idDonVi=current_user.idDonVi).all()
    return render_template('donvi/dashboard.html', hoc_phans=hoc_phans)

@donvi_bp.route('/hoc-phan/<int:hp_id>')
@login_required
@admin_donvi_required
def chi_tiet_hoc_phan(hp_id):
    hp = HocPhan.query.get_or_404(hp_id)
    if hp.idDonVi != current_user.idDonVi:
        flash('Bạn không có quyền xem học phần này.', 'danger')
        return redirect(url_for('donvi.dashboard'))

    tat_ca_cb = CanBo.query.filter_by(vaiTro='can_bo').all()
    phan_quyen_hien_tai = {pq.idCanBo: pq for pq in
                           CanBoHocPhan.query.filter_by(idHocPhan=hp_id).all()}

    return render_template('donvi/chi_tiet_hoc_phan.html',
                           hp=hp, tat_ca_cb=tat_ca_cb,
                           phan_quyen_hien_tai=phan_quyen_hien_tai)

@donvi_bp.route('/hoc-phan/<int:hp_id>/phan-quyen', methods=['POST'])
@login_required
@admin_donvi_required
def phan_quyen(hp_id):
    hp = HocPhan.query.get_or_404(hp_id)
    if hp.idDonVi != current_user.idDonVi:
        flash('Không có quyền.', 'danger')
        return redirect(url_for('donvi.dashboard'))

    cb_ids_chon = set(int(x) for x in request.form.getlist('can_bo_ids'))

    # Xóa phân quyền không còn được chọn
    CanBoHocPhan.query.filter(
        CanBoHocPhan.idHocPhan == hp_id,
        CanBoHocPhan.idCanBo.notin_(cb_ids_chon)
    ).delete(synchronize_session=False)

    # Thêm phân quyền mới
    hien_tai_ids = {pq.idCanBo for pq in
                   CanBoHocPhan.query.filter_by(idHocPhan=hp_id).all()}
    for cb_id in cb_ids_chon:
        if cb_id not in hien_tai_ids:
            pq = CanBoHocPhan(
                idCanBo=cb_id, idHocPhan=hp_id,
                quyenHieuChinh=True,
                quyenDuyetDC=bool(request.form.get(f'duyet_{cb_id}')),
                nguoiPhanQuyen=current_user.idCanBo,
                trangThai='hoat_dong',
                ghiChu=f'Phân công bởi {current_user.hoTen}'
            )
            db.session.add(pq)
            cb = CanBo.query.get(cb_id)
            if cb:
                ExternalAPIService.gui_thong_bao_phan_cong(
                    cb.email, hp.tenHP, hp.don_vi.tenDonVi)

    db.session.commit()
    flash(f'Đã cập nhật phân quyền cho {hp.tenHP}.', 'success')
    return redirect(url_for('donvi.chi_tiet_hoc_phan', hp_id=hp_id))

@donvi_bp.route('/hoc-phan/<int:hp_id>/tao-de-cuong', methods=['POST'])
@login_required
@admin_donvi_required
def tao_de_cuong(hp_id):
    hp = HocPhan.query.get_or_404(hp_id)
    if hp.de_cuong:
        flash('Đề cương đã tồn tại.', 'warning')
        return redirect(url_for('donvi.chi_tiet_hoc_phan', hp_id=hp_id))
    dc = DeCuong(idHocPhan=hp_id)
    db.session.add(dc)
    db.session.commit()
    flash('Đã tạo đề cương mới.', 'success')
    return redirect(url_for('donvi.chi_tiet_hoc_phan', hp_id=hp_id))
