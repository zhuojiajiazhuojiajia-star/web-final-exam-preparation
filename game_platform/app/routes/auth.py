from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '')
        password = data.get('password', '')
        remember = data.get('remember', False)

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(remember))
            user.last_login = datetime.now()
            db.session.commit()
            if request.is_json:
                return jsonify({'code': 200, 'msg': '登录成功', 'data': {'username': user.username, 'nickname': user.nickname}})
            flash('登录成功！', 'success')
            return redirect(url_for('main.index'))
        else:
            if request.is_json:
                return jsonify({'code': 400, 'msg': '用户名或密码错误'})
            flash('用户名或密码错误', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        nickname = data.get('nickname', '').strip() or username

        if not username or not email or not password:
            if request.is_json:
                return jsonify({'code': 400, 'msg': '请填写所有必填项'})
            flash('请填写所有必填项', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            if request.is_json:
                return jsonify({'code': 400, 'msg': '两次密码不一致'})
            flash('两次密码不一致', 'error')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            if request.is_json:
                return jsonify({'code': 400, 'msg': '密码长度至少6位'})
            flash('密码长度至少6位', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'code': 400, 'msg': '用户名已存在'})
            flash('用户名已存在', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'code': 400, 'msg': '邮箱已被注册'})
            flash('邮箱已被注册', 'error')
            return redirect(url_for('auth.register'))

        user = User(username=username, email=email, nickname=nickname)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if request.is_json:
            return jsonify({'code': 200, 'msg': '注册成功，请登录'})
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'success')
    return redirect(url_for('main.index'))
