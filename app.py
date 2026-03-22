from flask import Flask, jsonify
from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    # ── REST API Blueprints ───────────────────────────────────────────────
    from routes.api_auth    import api_auth_bp
    from routes.api_canbo   import api_canbo_bp
    from routes.api_hocphan import api_hocphan_bp
    from routes.api_donvi   import api_donvi_bp

    app.register_blueprint(api_auth_bp,    url_prefix='/api/auth')
    app.register_blueprint(api_canbo_bp,   url_prefix='/api/can-bo')
    app.register_blueprint(api_hocphan_bp, url_prefix='/api/hoc-phan')
    app.register_blueprint(api_donvi_bp,   url_prefix='/api/don-vi')

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Không tìm thấy tài nguyên.'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'success': False, 'message': 'Phương thức không được hỗ trợ.'}), 405

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Lỗi máy chủ nội bộ.'}), 500

    @app.route('/api')
    def api_index():
        return jsonify({
            'name':    'Hệ thống Quản lý Đề cương API',
            'version': '1.0',
            'endpoints': {
                'auth': {
                    'POST /api/auth/login':           'Đăng nhập, nhận JWT token',
                    'GET  /api/auth/me':              'Thông tin tài khoản đang đăng nhập',
                    'POST /api/auth/change-password': 'Đổi mật khẩu',
                },
                'can_bo': {
                    'GET    /api/can-bo/':     'Danh sách cán bộ',
                    'GET    /api/can-bo/<id>': 'Chi tiết cán bộ',
                    'POST   /api/can-bo/':     'Tạo cán bộ mới',
                    'PUT    /api/can-bo/<id>': 'Cập nhật cán bộ',
                    'DELETE /api/can-bo/<id>': 'Xoá cán bộ',
                },
                'hoc_phan': {
                    'GET    /api/hoc-phan/':                       'Danh sách học phần',
                    'GET    /api/hoc-phan/<id>':                   'Chi tiết học phần',
                    'POST   /api/hoc-phan/':                       'Tạo học phần mới',
                    'PUT    /api/hoc-phan/<id>':                   'Cập nhật học phần',
                    'DELETE /api/hoc-phan/<id>':                   'Xoá học phần',
                    'POST   /api/hoc-phan/<id>/phan-cong':         'Phân công cán bộ',
                    'DELETE /api/hoc-phan/<id>/phan-cong/<cb_id>': 'Huỷ phân công',
                },
                'don_vi': {
                    'GET    /api/don-vi/':              'Danh sách đơn vị',
                    'GET    /api/don-vi/<id>':          'Chi tiết đơn vị',
                    'GET    /api/don-vi/<id>/can-bo':   'Cán bộ trong đơn vị',
                    'GET    /api/don-vi/<id>/hoc-phan': 'Học phần của đơn vị',
                    'POST   /api/don-vi/':              'Tạo đơn vị mới',
                    'PUT    /api/don-vi/<id>':          'Cập nhật đơn vị',
                    'DELETE /api/don-vi/<id>':          'Xoá đơn vị',
                },
            },
            'auth_note': 'Thêm header: Authorization: Bearer <token> cho mọi request (trừ /api/auth/login)',
        })

    with app.app_context():
        try:
            _seed_data()
        except Exception as e:
            print(f'[seed] Bỏ qua: {e}')

    return app


def _seed_data():
    from models import CanBo, DonVi, HocPhan

    if CanBo.query.count() > 0:
        return

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