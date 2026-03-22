from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from models import CanBo
from extensions import db
import jwt
import datetime
from functools import wraps
from flask import current_app

api_auth_bp = Blueprint('api_auth', __name__)


def generate_token(user_id: int) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8),
        'iat': datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def token_required(f):
    """Decorator: bảo vệ endpoint bằng JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]

        if not token:
            return jsonify({'success': False, 'message': 'Thiếu token xác thực.'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_cb = CanBo.query.get(data['user_id'])
            if not current_cb:
                return jsonify({'success': False, 'message': 'Người dùng không tồn tại.'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token đã hết hạn.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token không hợp lệ.'}), 401

        return f(current_cb, *args, **kwargs)
    return decorated


def role_required(*roles):
    """Decorator: kiểm tra vai trò người dùng."""
    def decorator(f):
        @wraps(f)
        def decorated(current_cb, *args, **kwargs):
            if current_cb.vaiTro not in roles:
                return jsonify({'success': False, 'message': 'Không có quyền truy cập.'}), 403
            return f(current_cb, *args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────
# POST /api/auth/login
# ─────────────────────────────────────────────
@api_auth_bp.route('/login', methods=['POST'])
def login():
    """
    Body JSON: { "email": "...", "password": "..." }
    Trả về JWT token khi đăng nhập thành công.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Body phải là JSON.'}), 400

    email    = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Vui lòng nhập email và mật khẩu.'}), 400

    cb = CanBo.query.filter_by(email=email).first()
    if not cb or not cb.check_password(password):
        return jsonify({'success': False, 'message': 'Email hoặc mật khẩu không đúng.'}), 401

    token = generate_token(cb.idCanBo)
    return jsonify({
        'success': True,
        'message': 'Đăng nhập thành công.',
        'token': token,
        'user': {
            'id':      cb.idCanBo,
            'maCB':    cb.maCB,
            'hoTen':   cb.hoTen,
            'email':   cb.email,
            'vaiTro':  cb.vaiTro,
            'idDonVi': cb.idDonVi,
        }
    })


# ─────────────────────────────────────────────
# GET /api/auth/me
# ─────────────────────────────────────────────
@api_auth_bp.route('/me', methods=['GET'])
@token_required
def me(current_cb):
    """Trả về thông tin cán bộ đang đăng nhập."""
    return jsonify({
        'success': True,
        'user': {
            'id':      current_cb.idCanBo,
            'maCB':    current_cb.maCB,
            'hoTen':   current_cb.hoTen,
            'email':   current_cb.email,
            'vaiTro':  current_cb.vaiTro,
            'idDonVi': current_cb.idDonVi,
        }
    })


# ─────────────────────────────────────────────
# POST /api/auth/change-password
# ─────────────────────────────────────────────
@api_auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_cb):
    """
    Body JSON: { "old_password": "...", "new_password": "..." }
    """
    data = request.get_json(silent=True) or {}
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')

    if not old_pw or not new_pw:
        return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin.'}), 400

    if not current_cb.check_password(old_pw):
        return jsonify({'success': False, 'message': 'Mật khẩu cũ không đúng.'}), 400

    if len(new_pw) < 6:
        return jsonify({'success': False, 'message': 'Mật khẩu mới phải có ít nhất 6 ký tự.'}), 400

    current_cb.set_password(new_pw)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Đổi mật khẩu thành công.'})