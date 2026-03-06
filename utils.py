"""
دوال مساعدة للتطبيق
"""
from flask import request, url_for
from functools import wraps
from flask_login import current_user
from flask import flash, redirect, abort

# إعدادات Pagination
ITEMS_PER_PAGE = 50


def get_page_number():
    """الحصول على رقم الصفحة من الطلب"""
    return request.args.get('page', 1, type=int)


def get_per_page():
    """الحصول على عدد العناصر في الصفحة"""
    return request.args.get('per_page', ITEMS_PER_PAGE, type=int)


def paginate_query(query, page=None, per_page=None):
    """
    تطبيق pagination على استعلام SQLAlchemy
    
    Args:
        query: استعلام SQLAlchemy
        page: رقم الصفحة (اختياري)
        per_page: عدد العناصر في الصفحة (اختياري)
    
    Returns:
        Pagination object
    """
    if page is None:
        page = get_page_number()
    if per_page is None:
        per_page = get_per_page()
    
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_pagination_info(pagination):
    """
    الحصول على معلومات Pagination للعرض في القالب
    
    Args:
        pagination: Pagination object
    
    Returns:
        dict: معلومات Pagination
    """
    return {
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_num': pagination.prev_num,
        'next_num': pagination.next_num,
        'items': pagination.items
    }


# Decorators للصلاحيات
def admin_required(f):
    """التحقق من أن المستخدم مدير"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def contractor_or_admin_required(f):
    """التحقق من أن المستخدم مقاول أو مدير"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role not in ['admin', 'contractor']:
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def active_user_required(f):
    """التحقق من أن المستخدم نشط"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_active:
            flash('حسابك غير نشط', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# دوال مساعدة للبيانات
def safe_int(value, default=0):
    """تحويل آمن إلى integer"""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """تحويل آمن إلى float"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default


def safe_str(value, default=''):
    """تحويل آمن إلى string"""
    try:
        return str(value).strip() if value else default
    except (ValueError, TypeError):
        return default


# دوال مساعدة للتواريخ
def format_datetime(dt, format='%Y-%m-%d %H:%M'):
    """تنسيق التاريخ والوقت"""
    if dt:
        return dt.strftime(format)
    return ''


def format_date(dt, format='%Y-%m-%d'):
    """تنسيق التاريخ"""
    if dt:
        return dt.strftime(format)
    return ''


# دوال مساعدة للملفات
def allowed_file(filename, allowed_extensions):
    """التحقق من امتداد الملف"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_file_extension(filename):
    """الحصول على امتداد الملف"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


# دوال مساعدة للـ JSON
def parse_json_field(field_value, default=None):
    """تحليل حقل JSON بشكل آمن"""
    import json
    if not field_value:
        return default or []
    
    try:
        if isinstance(field_value, str):
            return json.loads(field_value)
        return field_value
    except (json.JSONDecodeError, TypeError):
        return default or []


def to_json_field(data):
    """تحويل البيانات إلى JSON"""
    import json
    if data is None:
        return None
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return None


# دوال مساعدة للإحصائيات
def calculate_percentage(part, total):
    """حساب النسبة المئوية"""
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def get_status_color(status):
    """الحصول على لون الحالة"""
    status_colors = {
        'عامل': 'success',
        'معطل': 'danger',
        'تحت الصيانة': 'warning',
        'مفصول': 'secondary',
        'جديد': 'info',
        'قيد التنفيذ': 'primary',
        'مكتمل': 'success',
        'ملغي': 'secondary',
        'مفتوح': 'warning',
        'مغلق': 'success'
    }
    return status_colors.get(status, 'secondary')


def get_priority_color(priority):
    """الحصول على لون الأولوية"""
    priority_colors = {
        'منخفض': 'info',
        'متوسط': 'warning',
        'عالي': 'danger',
        'عاجل': 'danger'
    }
    return priority_colors.get(priority, 'secondary')
