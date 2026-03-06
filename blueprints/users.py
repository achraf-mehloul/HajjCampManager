from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Contractor, ContractorTeam
from utils import paginate_query, admin_required, safe_str
import datetime

# إنشاء Blueprint
users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('/')
@login_required
@admin_required
def list_users():
    """قائمة المستخدمين مع Pagination"""
    # الحصول على معايير البحث
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    
    # بناء الاستعلام
    query = User.query
    
    # تطبيق الفلاتر
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.name.contains(search),
                User.email.contains(search)
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status == 'active':
        query = query.filter(User.is_active == True)
    elif status == 'inactive':
        query = query.filter(User.is_active == False)
    
    # تطبيق Pagination
    pagination = paginate_query(query.order_by(User.created_at.desc()))
    
    # الحصول على قوائم للفلاتر
    contractors = Contractor.query.all()
    teams = ContractorTeam.query.all()
    
    return render_template('users/list.html',
                         users=pagination.items,
                         pagination=pagination,
                         contractors=contractors,
                         teams=teams,
                         search=search,
                         role=role,
                         status=status,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))


@users_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    """إضافة مستخدم جديد"""
    try:
        username = safe_str(request.form.get('username'))
        name = safe_str(request.form.get('name'))
        email = safe_str(request.form.get('email'))
        password = request.form.get('password', '')
        role = request.form.get('role', 'user')
        
        # التحقق من البيانات
        if not all([username, password]):
            flash('اسم المستخدم وكلمة المرور مطلوبان', 'danger')
            return redirect(url_for('users.list_users'))
        
        # التحقق من عدم وجود مستخدم بنفس الاسم
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('users.list_users'))
        
        # التحقق من طول كلمة المرور
        if len(password) < 6:
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'danger')
            return redirect(url_for('users.list_users'))
        
        # إنشاء المستخدم
        user = User(
            username=username,
            name=name,
            email=email,
            role=role,
            is_active=True,
            created_at=datetime.datetime.now()
        )
        user.set_password(password)
        
        # المناطق المخصصة
        selected_areas = request.form.getlist('assigned_areas')
        if selected_areas:
            user.set_assigned_areas(selected_areas)
        
        db.session.add(user)
        db.session.commit()
        
        flash('تم إضافة المستخدم بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء إضافة المستخدم', 'danger')
        print(f"Add user error: {e}")
    
    return redirect(url_for('users.list_users'))


@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """تعديل مستخدم"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            user.name = safe_str(request.form.get('name'))
            user.email = safe_str(request.form.get('email'))
            user.role = request.form.get('role', user.role)
            
            # المناطق المخصصة
            selected_areas = request.form.getlist('assigned_areas')
            if selected_areas:
                user.set_assigned_areas(selected_areas)
            
            db.session.commit()
            flash('تم تحديث المستخدم بنجاح', 'success')
            return redirect(url_for('users.list_users'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء تحديث المستخدم', 'danger')
            print(f"Edit user error: {e}")
    
    return render_template('users/edit.html',
                         user=user,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))


@users_bp.route('/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_password(user_id):
    """إعادة تعيين كلمة المرور"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            new_password = request.form.get('new_password', '')
            
            if len(new_password) < 6:
                flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'danger')
                return render_template('users/reset_password.html', user=user)
            
            user.set_password(new_password)
            db.session.commit()
            
            flash('تم إعادة تعيين كلمة المرور بنجاح', 'success')
            return redirect(url_for('users.list_users'))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إعادة تعيين كلمة المرور', 'danger')
            print(f"Reset password error: {e}")
    
    return render_template('users/reset_password.html',
                         user=user,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))


@users_bp.route('/<int:user_id>/toggle')
@login_required
@admin_required
def toggle_user(user_id):
    """تفعيل/تعطيل مستخدم"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('لا يمكنك تعطيل حسابك الخاص', 'danger')
        return redirect(url_for('users.list_users'))
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'تم تفعيل' if user.is_active else 'تم تعطيل'
        flash(f'{status} المستخدم بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء تغيير حالة المستخدم', 'danger')
        print(f"Toggle user error: {e}")
    
    return redirect(url_for('users.list_users'))


@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """حذف مستخدم"""
    user = User.query.get_or_404(user_id)
    
    # منع المستخدم من حذف نفسه
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'danger')
        return redirect(url_for('users.list_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('تم حذف المستخدم بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف المستخدم', 'danger')
        print(f"Delete user error: {e}")
    
    return redirect(url_for('users.list_users'))
