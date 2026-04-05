from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import CanBo, DonVi, HocPhan, CanBoHocPhan
from extensions import db
from datetime import date, timedelta
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

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

    # Thống kê tiến độ đề cương
    ds_hp = HocPhan.query.all()
    hoan_thanh = sum(1 for hp in ds_hp if hp.de_cuong and hp.de_cuong.trangThai == 'hoan_thanh')
    dang_hc = sum(1 for hp in ds_hp if hp.de_cuong and hp.de_cuong.trangThai == 'dang_hieu_chinh')
    nhap = sum(1 for hp in ds_hp if hp.de_cuong and hp.de_cuong.trangThai == 'nhap')
    chua_co = tong_hp - hoan_thanh - dang_hc - nhap

    # Phân quyền sắp hết hạn (trong 7 ngày)
    today = date.today()
    sap_het_han = CanBoHocPhan.query.filter(
        CanBoHocPhan.trangThai == 'hoat_dong',
        CanBoHocPhan.ngayKetThuc != None,
        CanBoHocPhan.ngayKetThuc >= today,
        CanBoHocPhan.ngayKetThuc <= today + timedelta(days=7)
    ).all()

    return render_template('admin/dashboard.html',
                           tong_cb=tong_cb, tong_dv=tong_dv, tong_hp=tong_hp,
                           hoan_thanh=hoan_thanh, dang_hc=dang_hc, nhap=nhap, chua_co=chua_co,
                           sap_het_han=sap_het_han)

# ── Cán bộ ──────────────────────────────────────────────────
@admin_bp.route('/can-bo')
@login_required
@admin_required
def can_bo():
    # LOGIC TÌM KIẾM CÁN BỘ
    q = request.args.get('q', '').strip()
    query = CanBo.query
    if q:
        query = query.filter(or_(
            CanBo.hoTen.ilike(f"%{q}%"),
            CanBo.maCB.ilike(f"%{q}%"),
            CanBo.email.ilike(f"%{q}%")
        ))

    ds_cb = query.all()
    ds_dv = DonVi.query.all()
    return render_template('admin/can_bo.html', ds_cb=ds_cb, ds_dv=ds_dv, search_query=q)

@admin_bp.route('/can-bo/them', methods=['POST'])
@login_required
@admin_required
def them_can_bo():
    f = request.form
    ma = f['maCB'].strip()
    email = f['email'].strip()

    # Bắt lỗi thủ công trước
    if CanBo.query.filter_by(maCB=ma).first():
        flash(f'Lỗi: Mã cán bộ {ma} đã tồn tại trong hệ thống.', 'danger')
        return redirect(url_for('admin.can_bo'))

    if CanBo.query.filter_by(email=email).first():
        flash(f'Lỗi: Email {email} đã được sử dụng.', 'danger')
        return redirect(url_for('admin.can_bo'))

    cb = CanBo(maCB=ma, hoTen=f['hoTen'].strip(),
               email=email, vaiTro=f.get('vaiTro', 'can_bo'),
               idDonVi=int(f['idDonVi']),
               hocVi=f.get('hocVi') or None,
               chucVu=f.get('chucVu', '').strip() or None)
    cb.set_password(f['matKhau'])

    # Bọc Try-Catch
    try:
        db.session.add(cb)
        db.session.commit()
        flash(f'Đã thêm cán bộ {cb.hoTen} thành công.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Lỗi hệ thống: Dữ liệu vi phạm ràng buộc (Trùng lặp).', 'danger')

    return redirect(url_for('admin.can_bo'))

@admin_bp.route('/can-bo/<int:cb_id>/cap-nhat', methods=['POST'])
@login_required
@admin_required
def cap_nhat_can_bo(cb_id):
    cb = CanBo.query.get_or_404(cb_id)
    f = request.form

    cb.hoTen = f.get('hoTen', cb.hoTen).strip()
    cb.vaiTro = f.get('vaiTro', cb.vaiTro)
    cb.idDonVi = int(f.get('idDonVi', cb.idDonVi))
    cb.hocVi = f.get('hocVi') or None
    cb.chucVu = f.get('chucVu', '').strip() or None
    cb.trangThai = bool(f.get('trangThai'))
    if f.get('matKhauMoi'):
        cb.set_password(f['matKhauMoi'])

    try:
        db.session.commit()
        flash('Đã cập nhật thông tin cán bộ.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Cập nhật thất bại: Thông tin bị trùng lặp với cán bộ khác.', 'danger')

    return redirect(url_for('admin.can_bo'))

@admin_bp.route('/can-bo/xoa/<int:id>', methods=['POST'])
@login_required
@admin_required
def xoa_can_bo(id):
    cb = CanBo.query.get_or_404(id)

    # Gỡ mìn lỗi khóa ngoại
    from models import CanBoHocPhan
    CanBoHocPhan.query.filter_by(idCanBo=id).delete()

    db.session.delete(cb)
    db.session.commit()
    flash('Đã xóa cán bộ thành công!', 'success')
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
    f = request.form
    ma = f['maDonVi'].strip().upper()

    if DonVi.query.filter_by(maDonVi=ma).first():
        flash(f'Lỗi: Mã đơn vị {ma} đã tồn tại.', 'danger')
        return redirect(url_for('admin.don_vi'))

    dv = DonVi(tenDonVi=f['tenDonVi'].strip(), maDonVi=ma,
               loaiDonVi=f.get('loaiDonVi', 'khoa'))

    try:
        db.session.add(dv)
        db.session.commit()
        flash('Đã thêm đơn vị mới thành công.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Lỗi CSDL: Vi phạm ràng buộc dữ liệu đơn vị.', 'danger')

    return redirect(url_for('admin.don_vi'))

# ── Học phần ────────────────────────────────────────────────
@admin_bp.route('/hoc-phan')
@login_required
@admin_required
def hoc_phan():
    # LOGIC TÌM KIẾM HỌC PHẦN
    q = request.args.get('q', '').strip()
    query = HocPhan.query
    if q:
        query = query.filter(or_(
            HocPhan.tenHP.ilike(f"%{q}%"),
            HocPhan.maHP.ilike(f"%{q}%")
        ))

    ds_hp = query.all()
    ds_dv = DonVi.query.all()
    return render_template('admin/hoc_phan.html', ds_hp=ds_hp, ds_dv=ds_dv, search_query=q)

@admin_bp.route('/hoc-phan/them', methods=['POST'])
@login_required
@admin_required
def them_hoc_phan():
    f = request.form
    ma = f['maHP'].strip().upper()

    if HocPhan.query.filter_by(maHP=ma).first():
        flash(f'Lỗi: Mã học phần {ma} đã tồn tại.', 'danger')
        return redirect(url_for('admin.hoc_phan'))

    hp = HocPhan(maHP=ma, tenHP=f['tenHP'].strip(),
                 soTinChi=int(f.get('soTinChi', 3)),
                 idDonVi=int(f['idDonVi']))

    try:
        db.session.add(hp)
        db.session.commit()
        flash('Đã thêm học phần mới thành công.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Lỗi CSDL: Vi phạm ràng buộc dữ liệu học phần.', 'danger')

    return redirect(url_for('admin.hoc_phan'))