from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import CanBoHocPhan, HocPhan, DeCuong, LichSuHieuChinh, ThongBao
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


# ==========================================
# CÔNG TẮC BƠM DỮ LIỆU THÔNG BÁO LÊN MỌI TRANG
# ==========================================
@giaovien_bp.context_processor
def inject_notifications():
    if current_user.is_authenticated and current_user.is_can_bo():
        thong_baos = ThongBao.query.filter_by(idCanBo=current_user.idCanBo, daDoc=False).order_by(
            ThongBao.idThongBao.desc()).limit(5).all()
        so_luong = ThongBao.query.filter_by(idCanBo=current_user.idCanBo, daDoc=False).count()
        return dict(chuong_thong_bao=thong_baos, so_luong_thong_bao=so_luong)
    return dict(chuong_thong_bao=[], so_luong_thong_bao=0)


# ==========================================
# XỬ LÝ KHI BẤM VÀO THÔNG BÁO
# ==========================================
@giaovien_bp.route('/thong-bao/<int:tb_id>')
@login_required
@can_bo_required
def doc_thong_bao(tb_id):
    tb = ThongBao.query.get_or_404(tb_id)
    if tb.idCanBo != current_user.idCanBo:
        flash('Lỗi truy cập.', 'danger')
        return redirect(url_for('giaovien.dashboard'))

    tb.daDoc = True  # Đánh dấu đã đọc để mất chấm đỏ
    db.session.commit()

    if tb.link_url:
        return redirect(tb.link_url)
    return redirect(url_for('giaovien.dashboard'))


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
    lich_su = LichSuHieuChinh.query.filter_by(idDeCuong=dc.idDeCuong) \
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

    dc.mucTieu = request.form.get('mucTieu', dc.mucTieu)
    dc.noiDung = request.form.get('noiDung', dc.noiDung)
    dc.taiLieu = request.form.get('taiLieu', dc.taiLieu)
    dc.ppGiangDay = request.form.get('ppGiangDay', dc.ppGiangDay)
    dc.ppDanhGia = request.form.get('ppDanhGia', dc.ppDanhGia)
    dc.trangThai = 'dang_hieu_chinh'

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