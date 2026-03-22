from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import CanBo, DonVi, HocPhan
from extensions import db
from services.external_api import ExternalAPIService

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Bạn không có quyền truy cập.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    tong_cb = CanBo.query.count()
    tong_dv = DonVi.query.count()
    tong_hp = HocPhan.query.count()
    return render_template('admin/dashboard.html', tong_cb=tong_cb, tong_dv=tong_dv, tong_hp=tong_hp)

# ── Cán bộ ──────────────────────────────────────────────────
@admin_bp.route('/can-bo')
@login_required
@admin_required
def can_bo():
    ds_cb = CanBo.query.all()
    ds_dv = DonVi.query.all()
    return render_template('admin/can_bo.html', ds_cb=ds_cb, ds_dv=ds_dv)

@admin_bp.route('/can-bo/them', methods=['POST'])
@login_required
@admin_required
def them_can_bo():
    f = request.form
    if CanBo.query.filter_by(email=f['email']).first():
        flash('Email đã tồn tại.', 'danger')
        return redirect(url_for('admin.can_bo'))
    cb = CanBo(maCB=f['maCB'].strip(), hoTen=f['hoTen'].strip(),
               email=f['email'].strip(), vaiTro=f.get('vaiTro','can_bo'),
               idDonVi=int(f['idDonVi']),
               hocVi=f.get('hocVi') or None,
               chucVu=f.get('chucVu','').strip() or None)
    cb.set_password(f['matKhau'])
    db.session.add(cb)
    db.session.commit()
    flash(f'Đã thêm cán bộ {cb.hoTen}.', 'success')
    return redirect(url_for('admin.can_bo'))

@admin_bp.route('/can-bo/<int:cb_id>/cap-nhat', methods=['POST'])
@login_required
@admin_required
def cap_nhat_can_bo(cb_id):
    cb = CanBo.query.get_or_404(cb_id)
    f  = request.form
    cb.hoTen    = f.get('hoTen', cb.hoTen).strip()
    cb.vaiTro   = f.get('vaiTro', cb.vaiTro)
    cb.idDonVi  = int(f.get('idDonVi', cb.idDonVi))
    cb.hocVi    = f.get('hocVi') or None
    cb.chucVu   = f.get('chucVu','').strip() or None
    cb.trangThai= bool(f.get('trangThai'))
    if f.get('matKhauMoi'):
        cb.set_password(f['matKhauMoi'])
    db.session.commit()
    flash('Đã cập nhật cán bộ.', 'success')
    return redirect(url_for('admin.can_bo'))

@admin_bp.route('/can-bo/<int:cb_id>/xoa', methods=['POST'])
@login_required
@admin_required
def xoa_can_bo(cb_id):
    cb = CanBo.query.get_or_404(cb_id)
    db.session.delete(cb)
    db.session.commit()
    flash('Đã xóa cán bộ.', 'success')
    return redirect(url_for('admin.can_bo'))

# ── Đơn vị ──────────────────────────────────────────────────
@admin_bp.route('/don-vi')
@login_required
@admin_required
def don_vi():
    ds_dv = DonVi.query.all()
    return render_template('admin/don_vi.html', ds_dv=ds_dv)

@admin_bp.route('/don-vi/them', methods=['POST'])
@login_required
@admin_required
def them_don_vi():
    f  = request.form
    ma = f['maDonVi'].strip().upper()
    if DonVi.query.filter_by(maDonVi=ma).first():
        flash('Mã đơn vị đã tồn tại.', 'danger')
        return redirect(url_for('admin.don_vi'))
    dv = DonVi(tenDonVi=f['tenDonVi'].strip(), maDonVi=ma,
               loaiDonVi=f.get('loaiDonVi','khoa'))
    db.session.add(dv)
    db.session.commit()
    flash('Đã thêm đơn vị.', 'success')
    return redirect(url_for('admin.don_vi'))

# ── Học phần ────────────────────────────────────────────────
@admin_bp.route('/hoc-phan')
@login_required
@admin_required
def hoc_phan():
    ds_hp = HocPhan.query.all()
    ds_dv = DonVi.query.all()
    return render_template('admin/hoc_phan.html', ds_hp=ds_hp, ds_dv=ds_dv)

@admin_bp.route('/hoc-phan/them', methods=['POST'])
@login_required
@admin_required
def them_hoc_phan():
    f  = request.form
    ma = f['maHP'].strip().upper()
    if HocPhan.query.filter_by(maHP=ma).first():
        flash('Mã học phần đã tồn tại.', 'danger')
        return redirect(url_for('admin.hoc_phan'))
    hp = HocPhan(maHP=ma, tenHP=f['tenHP'].strip(),
                 soTinChi=int(f.get('soTinChi', 3)),
                 idDonVi=int(f['idDonVi']))
    db.session.add(hp)
    db.session.commit()
    flash('Đã thêm học phần.', 'success')
    return redirect(url_for('admin.hoc_phan'))

# ── Đồng bộ API ngoài ───────────────────────────────────────
@admin_bp.route('/dong-bo-api')
@login_required
@admin_required
def dong_bo_api():
    ket_qua = ExternalAPIService.lay_danh_sach_giang_vien()
    if ket_qua:
        flash(f'Đồng bộ thành công: {len(ket_qua)} cán bộ.', 'success')
    else:
        flash('Không thể kết nối API ngoài.', 'warning')
    return redirect(url_for('admin.dashboard'))
