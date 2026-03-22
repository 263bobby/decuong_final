from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import CanBo

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        cb = CanBo.query.filter_by(email=email).first()
        if not cb or not cb.check_password(password):
            flash('Email hoặc mật khẩu không đúng.', 'danger')
            return render_template('auth/login.html')
        if not cb.is_active:
            flash('Tài khoản đã bị vô hiệu hóa.', 'warning')
            return render_template('auth/login.html')

        login_user(cb, remember=remember)
        return _redirect_by_role(cb)

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công.', 'success')
    return redirect(url_for('auth.login'))

def _redirect_by_role(cb):
    if cb.vaiTro == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif cb.vaiTro == 'admin_donvi':
        return redirect(url_for('donvi.dashboard'))
    else:
        return redirect(url_for('giaovien.dashboard'))
