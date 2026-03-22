from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models import CanBo
        return CanBo.query.get(int(user_id))

    from routes.auth     import auth_bp
    from routes.admin    import admin_bp
    from routes.donvi    import donvi_bp
    from routes.giaovien import giaovien_bp

    app.register_blueprint(auth_bp,     url_prefix='/auth')
    app.register_blueprint(admin_bp,    url_prefix='/admin')
    app.register_blueprint(donvi_bp,    url_prefix='/donvi')
    app.register_blueprint(giaovien_bp, url_prefix='/giaovien')

    # Route gốc → tự chuyển về trang đăng nhập
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    with app.app_context():
        try:
            _seed_data()
        except Exception as e:
            print(f'[seed] Bỏ qua: {e}')

    return app


def _seed_data():
    from models import CanBo, DonVi, HocPhan
    from extensions import db

    if CanBo.query.count() > 0:
        return  # DB đã có dữ liệu từ SQL script

    dv1 = DonVi(tenDonVi='Khoa Công nghệ thông tin', maDonVi='CNTT', loaiDonVi='khoa')
    dv2 = DonVi(tenDonVi='Khoa Kinh tế', maDonVi='KT', loaiDonVi='khoa')
    db.session.add_all([dv1, dv2])
    db.session.flush()

    admin = CanBo(maCB='CB001', hoTen='Nguyễn Quản Trị',
                  email='admin@edu.vn', vaiTro='admin', idDonVi=dv1.idDonVi)
    admin.set_password('admin123')

    tk = CanBo(maCB='CB002', hoTen='Trần Thị Khoa',
               email='truongkhoa@edu.vn', vaiTro='admin_donvi', idDonVi=dv1.idDonVi)
    tk.set_password('khoa123')

    gv = CanBo(maCB='CB003', hoTen='Nguyễn Văn An',
               email='nguyenvana@edu.vn', vaiTro='can_bo', idDonVi=dv1.idDonVi)
    gv.set_password('gv123')

    db.session.add_all([admin, tk, gv])
    db.session.flush()

    hp = HocPhan(maHP='CS101', tenHP='Nhập môn lập trình', soTinChi=3, idDonVi=dv1.idDonVi)
    db.session.add(hp)
    db.session.commit()
    print('[seed] Tạo dữ liệu mẫu thành công.')


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)