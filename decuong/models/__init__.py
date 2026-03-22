from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from sqlalchemy import SmallInteger


class DonVi(db.Model):
    __tablename__ = 'DonVi'
    idDonVi   = db.Column(db.Integer, primary_key=True)
    tenDonVi  = db.Column(db.String(200), nullable=False)
    maDonVi   = db.Column(db.String(20),  nullable=False, unique=True)
    loaiDonVi = db.Column(db.String(20),  nullable=False, default='khoa')
    moTa      = db.Column(db.Text, nullable=True)
    ngayTao   = db.Column(db.DateTime, server_default=db.func.now())

    can_bo   = db.relationship('CanBo',   foreign_keys='CanBo.idDonVi', backref='don_vi', lazy='dynamic')
    hoc_phan = db.relationship('HocPhan', backref='don_vi', lazy='dynamic')

    def __repr__(self):
        return f'<DonVi {self.maDonVi}>'


class CanBo(UserMixin, db.Model):
    __tablename__ = 'CanBo'
    idCanBo     = db.Column(db.Integer, primary_key=True)
    maCB        = db.Column(db.String(20),  nullable=False, unique=True)
    hoTen       = db.Column(db.String(150), nullable=False)
    gioiTinh    = db.Column(db.String(10),  nullable=False, default='Nam')
    ngaySinh    = db.Column(db.Date, nullable=True)
    email       = db.Column(db.String(150), nullable=False, unique=True)
    dienThoai   = db.Column(db.String(20),  nullable=True)
    hocVi       = db.Column(db.String(20),  nullable=True)
    chucVu      = db.Column(db.String(100), nullable=True)
    idDonVi     = db.Column(db.Integer, db.ForeignKey('DonVi.idDonVi'), nullable=False)
    matKhau     = db.Column(db.String(256), nullable=False)
    vaiTro      = db.Column(db.String(20),  nullable=False, default='can_bo')
    trangThai   = db.Column(db.Boolean, nullable=False, default=True)
    ngayTao     = db.Column(db.DateTime, server_default=db.func.now())
    ngayCapNhat = db.Column(db.DateTime, server_default=db.func.now())

    def get_id(self):
        return str(self.idCanBo)

    def set_password(self, password):
        self.matKhau = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.matKhau, password)

    def is_admin(self):
        return self.vaiTro == 'admin'

    def is_admin_donvi(self):
        return self.vaiTro == 'admin_donvi'

    def is_can_bo(self):
        return self.vaiTro == 'can_bo'

    @property
    def is_active(self):
        return bool(self.trangThai)

    def __repr__(self):
        return f'<CanBo {self.maCB} {self.hoTen}>'


class HocPhan(db.Model):
    __tablename__ = 'HocPhan'
    idHocPhan  = db.Column(db.Integer, primary_key=True)
    maHP       = db.Column(db.String(20),  nullable=False, unique=True)
    tenHP      = db.Column(db.String(200), nullable=False)
    soTinChi   = db.Column(db.SmallInteger, nullable=False, default=3)
    idDonVi    = db.Column(db.Integer, db.ForeignKey('DonVi.idDonVi'), nullable=False)
    moTa       = db.Column(db.Text, nullable=True)
    trangThai  = db.Column(db.String(20),  nullable=False, default='dang_su_dung')
    ngayTao    = db.Column(db.DateTime, server_default=db.func.now())

    de_cuong   = db.relationship('DeCuong', backref='hoc_phan', uselist=False, cascade='all, delete-orphan')
    phan_quyen = db.relationship('CanBoHocPhan', backref='hoc_phan', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<HocPhan {self.maHP}>'


class CanBoHocPhan(db.Model):
    __tablename__ = 'CanBo_HocPhan'
    idPhanQuyen    = db.Column(db.Integer, primary_key=True)
    idCanBo        = db.Column(db.Integer, db.ForeignKey('CanBo.idCanBo'),     nullable=False)
    idHocPhan      = db.Column(db.Integer, db.ForeignKey('HocPhan.idHocPhan'), nullable=False)
    quyenHieuChinh = db.Column(db.Boolean, nullable=False, default=True)
    quyenDuyetDC   = db.Column(db.Boolean, nullable=False, default=False)
    ngayPhanQuyen  = db.Column(db.DateTime, server_default=db.func.now())
    ngayBatDau     = db.Column(db.Date, nullable=True)
    ngayKetThuc    = db.Column(db.Date, nullable=True)
    nguoiPhanQuyen = db.Column(db.Integer, db.ForeignKey('CanBo.idCanBo'), nullable=False)
    trangThai      = db.Column(db.String(20), nullable=False, default='hoat_dong')
    ghiChu         = db.Column(db.String(500), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('idCanBo', 'idHocPhan', name='uq_canbo_hocphan'),
    )

    can_bo   = db.relationship('CanBo', foreign_keys=[idCanBo], backref='phan_quyen_list')
    nguoi_pq = db.relationship('CanBo', foreign_keys=[nguoiPhanQuyen])

    @property
    def con_hieu_luc(self):
        if self.trangThai != 'hoat_dong':
            return False
        today = date.today()
        if self.ngayBatDau and self.ngayBatDau > today:
            return False
        if self.ngayKetThuc and self.ngayKetThuc < today:
            return False
        return True

    def __repr__(self):
        return f'<PhanQuyen CB={self.idCanBo} HP={self.idHocPhan}>'


class DeCuong(db.Model):
    __tablename__ = 'DeCuong'

    # Dùng __mapper_args__ để báo SQLAlchemy KHÔNG tự include ngayCapNhat khi UPDATE
    idDeCuong   = db.Column(db.Integer, primary_key=True)
    idHocPhan   = db.Column(db.Integer, db.ForeignKey('HocPhan.idHocPhan'), nullable=False, unique=True)
    phienBan    = db.Column(db.String(10), nullable=False, default='1.0')
    mucTieu     = db.Column(db.Text, nullable=True)
    noiDung     = db.Column(db.Text, nullable=True)
    taiLieu     = db.Column(db.Text, nullable=True)
    ppGiangDay  = db.Column(db.Text, nullable=True)
    ppDanhGia   = db.Column(db.Text, nullable=True)
    trangThai   = db.Column(db.String(30), nullable=False, default='nhap')
    ngayTao     = db.Column(db.DateTime, server_default=db.func.now())
    # ngayCapNhat: để SQL Server tự quản lý, KHÔNG map vào model
    # để tránh lỗi pyodbc precision khi truyền datetime Python xuống

    lich_su = db.relationship('LichSuHieuChinh', backref='de_cuong', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DeCuong HP={self.idHocPhan}>'


class LichSuHieuChinh(db.Model):
    __tablename__ = 'LichSuHieuChinh'
    idLichSu      = db.Column(db.Integer, primary_key=True)
    idDeCuong     = db.Column(db.Integer, db.ForeignKey('DeCuong.idDeCuong'), nullable=False)
    idCanBo       = db.Column(db.Integer, db.ForeignKey('CanBo.idCanBo'),     nullable=False)
    noiDungCu     = db.Column(db.Text, nullable=True)
    noiDungMoi    = db.Column(db.Text, nullable=True)
    truongThayDoi = db.Column(db.String(100), nullable=True)
    ghiChu        = db.Column(db.String(500), nullable=True)
    thoiGian      = db.Column(db.DateTime, server_default=db.func.now())

    can_bo = db.relationship('CanBo', backref='lich_su_hieu_chinh')

    def __repr__(self):
        return f'<LichSu DC={self.idDeCuong}>'