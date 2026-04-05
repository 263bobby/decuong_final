from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import CanBo, HocPhan, DeCuong, CanBoHocPhan, ThongBao
from extensions import db
from datetime import datetime
from sqlalchemy import or_

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
    # Thêm tính năng Tìm kiếm cho Trưởng Khoa
    q = request.args.get('q', '').strip()
    query = HocPhan.query.filter_by(idDonVi=current_user.idDonVi)

    if q:
        query = query.filter(or_(
            HocPhan.tenHP.ilike(f"%{q}%"),
            HocPhan.maHP.ilike(f"%{q}%")
        ))

    hoc_phans = query.all()
    return render_template('donvi/dashboard.html', hoc_phans=hoc_phans, search_query=q)


@donvi_bp.route('/hoc-phan/<int:hp_id>')
@login_required
@admin_donvi_required
def chi_tiet_hoc_phan(hp_id):
    hp = HocPhan.query.get_or_404(hp_id)
    if hp.idDonVi != current_user.idDonVi:
        flash('Bạn không có quyền xem học phần này.', 'danger')
        return redirect(url_for('donvi.dashboard'))

    tat_ca_cb = CanBo.query.filter_by(vaiTro='can_bo', idDonVi=current_user.idDonVi).all()
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

    # 1. Bắt lấy Deadline từ Giao diện
    ngay_ket_thuc_str = request.form.get('ngayKetThuc')
    ngay_ket_thuc = None
    if ngay_ket_thuc_str:
        ngay_ket_thuc = datetime.strptime(ngay_ket_thuc_str, '%Y-%m-%d').date()

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
            # Lưu dữ liệu phân công kèm Deadline
            pq = CanBoHocPhan(
                idCanBo=cb_id, idHocPhan=hp_id,
                quyenHieuChinh=True,
                quyenDuyetDC=bool(request.form.get(f'duyet_{cb_id}')),
                nguoiPhanQuyen=current_user.idCanBo,
                trangThai='hoat_dong',
                ngayKetThuc=ngay_ket_thuc,  # Lắp ráp Deadline
                ghiChu=f'Phân công bởi {current_user.hoTen}'
            )
            db.session.add(pq)

            # 2. CÔNG TẮC BẮN THÔNG BÁO CHO GIẢNG VIÊN
            noi_dung_tb = f"Bạn vừa được Trưởng khoa {current_user.hoTen} phân công biên soạn đề cương môn: {hp.tenHP} ({hp.maHP})."
            if ngay_ket_thuc:
                noi_dung_tb += f" Hạn chót hoàn thành: {ngay_ket_thuc.strftime('%d/%m/%Y')}."

            tb = ThongBao(
                idCanBo=cb_id,
                tieuDe="🔔 Nhiệm vụ mới: Soạn đề cương",
                noiDung=noi_dung_tb,
                loai='phan_cong',
                link_url='/giaovien/dashboard'  # Gắn link để GV bấm vào nhảy luôn tới chỗ làm
            )
            db.session.add(tb)
        else:
            # Cập nhật lại deadline cho GV cũ (nếu Trưởng khoa đổi ý lùi ngày hạn chót)
            pq_cu = CanBoHocPhan.query.filter_by(idHocPhan=hp_id, idCanBo=cb_id).first()
            if pq_cu:
                pq_cu.quyenDuyetDC = bool(request.form.get(f'duyet_{cb_id}'))
                if ngay_ket_thuc:
                    pq_cu.ngayKetThuc = ngay_ket_thuc

    db.session.commit()
    flash(f'Đã cập nhật phân quyền và gửi thông báo thành công!', 'success')
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


@donvi_bp.route('/hoc-phan/<int:hp_id>/phe-duyet', methods=['POST'])
@login_required
@admin_donvi_required
def phe_duyet_de_cuong(hp_id):
    hp = HocPhan.query.get_or_404(hp_id)

    # Kiểm tra bảo mật
    if hp.idDonVi != current_user.idDonVi:
        flash('Bạn không có quyền thao tác trên học phần này.', 'danger')
        return redirect(url_for('donvi.dashboard'))

    if not hp.de_cuong:
        flash('Học phần này chưa có đề cương để duyệt.', 'warning')
        return redirect(url_for('donvi.chi_tiet_hoc_phan', hp_id=hp_id))

    # Cấp "quyền lực tối cao" chốt hạ
    hp.de_cuong.trangThai = 'hoan_thanh'
    db.session.commit()

    flash('Đã phê duyệt và chốt Đề cương thành công!', 'success')
    return redirect(url_for('donvi.chi_tiet_hoc_phan', hp_id=hp_id))


