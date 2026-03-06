from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import datetime

# إنشاء Blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # التحقق من وجود البيانات
        if not username or not password:
            flash('يرجى إدخال اسم المستخدم وكلمة المرور', 'danger')
            return render_template('login.html', current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

        try:
            user = User.query.filter_by(username=username).first()

            # استخدام الدالة الجديدة check_password للتحقق من كلمة المرور المشفرة
            if user and user.check_password(password):
                if not user.is_active:
                    flash('حسابك غير نشط. يرجى التواصل مع المسؤول', 'danger')
                    return render_template('login.html', current_date=datetime.datetime.now().strftime("%Y-%m-%d"))
                
                login_user(user)
                user.last_login = datetime.datetime.now()
                db.session.commit()

                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                # رسالة خطأ باللغتين العربية والإنجليزية
                if request.headers.get('Accept-Language', '').startswith('en'):
                    flash('Invalid username or password', 'danger')
                else:
                    flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
        except Exception as e:
            flash('حدث خطأ أثناء تسجيل الدخول', 'danger')
            print(f"Login error: {e}")

    return render_template('login.html', current_date=datetime.datetime.now().strftime("%Y-%m-%d"))


@auth_bp.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """تغيير كلمة المرور"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # التحقق من البيانات
        if not all([current_password, new_password, confirm_password]):
            flash('يرجى ملء جميع الحقول', 'danger')
            return render_template('change_password.html')

        # التحقق من كلمة المرور الحالية
        if not current_user.check_password(current_password):
            flash('كلمة المرور الحالية غير صحيحة', 'danger')
            return render_template('change_password.html')

        # التحقق من تطابق كلمة المرور الجديدة
        if new_password != confirm_password:
            flash('كلمة المرور الجديدة غير متطابقة', 'danger')
            return render_template('change_password.html')

        # التحقق من طول كلمة المرور
        if len(new_password) < 6:
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'danger')
            return render_template('change_password.html')

        try:
            # تحديث كلمة المرور
            current_user.set_password(new_password)
            db.session.commit()
            flash('تم تغيير كلمة المرور بنجاح', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تغيير كلمة المرور', 'danger')
            print(f"Password change error: {e}")

    return render_template('change_password.html')
