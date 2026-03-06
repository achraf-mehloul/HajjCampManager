import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, MeasurementUnit, DropdownList, DropdownItem

units_bp = Blueprint('units', __name__)

# صفحة إدارة وحدات القياس
@units_bp.route('/units')
@login_required
def units_management():
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))

    # الحصول على جميع وحدات القياس
    units = MeasurementUnit.query.all()

    return render_template('units_management.html',
                           units=units,
                           current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

# إضافة وحدة قياس جديدة
@units_bp.route('/units/add', methods=['POST'])
@login_required
def add_unit():
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))

    try:
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        category = request.form.get('category')
        conversion_factor = float(request.form.get('conversion_factor', 1.0))
        is_default = 'is_default' in request.form

        # إضافة دعم للفئات المخصصة
        if category == 'other':
            custom_category = request.form.get('custom_category')
            if custom_category and custom_category.strip():
                category = custom_category.strip()

        # التحقق من عدم وجود وحدة بنفس الاسم والفئة
        existing_unit = MeasurementUnit.query.filter_by(name=name, category=category).first()
        if existing_unit:
            flash(f'وحدة القياس {name} موجودة بالفعل في فئة {category}', 'danger')
            return redirect(url_for('units.units_management'))

        # إذا كانت الوحدة افتراضية، قم بإلغاء تعيين الوحدة الافتراضية الحالية
        if is_default:
            default_units = MeasurementUnit.query.filter_by(category=category, is_default=True).all()
            for unit in default_units:
                unit.is_default = False
                db.session.add(unit)

        # إنشاء وحدة قياس جديدة
        unit = MeasurementUnit(
            name=name,
            display_name=display_name,
            category=category,
            conversion_factor=conversion_factor,
            is_default=is_default,
            is_active=True,
            created_at=datetime.datetime.now()
        )

        db.session.add(unit)
        db.session.commit()

        flash(f'تم إضافة وحدة القياس {name} بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء إضافة وحدة القياس: {str(e)}', 'danger')

    return redirect(url_for('units.units_management'))

# تعديل وحدة قياس
@units_bp.route('/units/<int:unit_id>/edit', methods=['POST'])
@login_required
def edit_unit(unit_id):
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))

    try:
        unit = MeasurementUnit.query.get_or_404(unit_id)

        name = request.form.get('name')
        display_name = request.form.get('display_name')
        category = request.form.get('category')
        conversion_factor = float(request.form.get('conversion_factor', 1.0))
        is_default = 'is_default' in request.form

        # إضافة دعم للفئات المخصصة
        if category == 'other':
            custom_category = request.form.get('custom_category')
            if custom_category and custom_category.strip():
                category = custom_category.strip()

        # التحقق من عدم وجود وحدة أخرى بنفس الاسم والفئة
        existing_unit = MeasurementUnit.query.filter(
            MeasurementUnit.id != unit_id,
            MeasurementUnit.name == name,
            MeasurementUnit.category == category
        ).first()

        if existing_unit:
            flash(f'وحدة القياس {name} موجودة بالفعل في فئة {category}', 'danger')
            return redirect(url_for('units.units_management'))

        # إذا تم تغيير الفئة وكانت الوحدة افتراضية، قم بإلغاء تعيين الوحدة الافتراضية في الفئة القديمة
        if unit.category != category and unit.is_default:
            unit.is_default = False

        # إذا كانت الوحدة افتراضية، قم بإلغاء تعيين الوحدة الافتراضية الحالية في الفئة الجديدة
        if is_default and not unit.is_default:
            default_units = MeasurementUnit.query.filter_by(category=category, is_default=True).all()
            for default_unit in default_units:
                default_unit.is_default = False
                db.session.add(default_unit)

        # تحديث بيانات الوحدة
        unit.name = name
        unit.display_name = display_name
        unit.category = category
        unit.conversion_factor = conversion_factor
        unit.is_default = is_default
        unit.updated_at = datetime.datetime.now()

        db.session.commit()

        flash(f'تم تحديث وحدة القياس {name} بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث وحدة القياس: {str(e)}', 'danger')

    return redirect(url_for('units.units_management'))

# تفعيل/تعطيل وحدة قياس
@units_bp.route('/units/<int:unit_id>/toggle')
@login_required
def toggle_unit(unit_id):
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))

    unit = MeasurementUnit.query.get_or_404(unit_id)

    # لا يمكن تعطيل الوحدة الافتراضية
    if unit.is_default and unit.is_active:
        flash('لا يمكن تعطيل الوحدة الافتراضية. يرجى تعيين وحدة افتراضية أخرى أولاً.', 'danger')
        return redirect(url_for('units.units_management'))

    unit.is_active = not unit.is_active
    unit.updated_at = datetime.datetime.now()

    db.session.commit()

    status = 'تفعيل' if unit.is_active else 'تعطيل'
    flash(f'تم {status} وحدة القياس {unit.name} بنجاح', 'success')
    return redirect(url_for('units.units_management'))

# تعيين وحدة قياس كافتراضية
@units_bp.route('/units/<int:unit_id>/set-default')
@login_required
def set_default_unit(unit_id):
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))

    unit = MeasurementUnit.query.get_or_404(unit_id)

    # لا يمكن تعيين وحدة غير نشطة كافتراضية
    if not unit.is_active:
        flash('لا يمكن تعيين وحدة غير نشطة كافتراضية. يرجى تفعيل الوحدة أولاً.', 'danger')
        return redirect(url_for('units.units_management'))

    # إلغاء تعيين الوحدة الافتراضية الحالية
    default_units = MeasurementUnit.query.filter_by(category=unit.category, is_default=True).all()
    for default_unit in default_units:
        default_unit.is_default = False

    # تعيين الوحدة الجديدة كافتراضية
    unit.is_default = True
    unit.updated_at = datetime.datetime.now()

    db.session.commit()

    flash(f'تم تعيين وحدة القياس {unit.name} كوحدة افتراضية لفئة {unit.category}', 'success')
    return redirect(url_for('units.units_management'))

# الحصول على وحدات القياس حسب الفئة
@units_bp.route('/units/by-category/<category>')
@login_required
def get_units_by_category(category):
    units = MeasurementUnit.query.filter_by(category=category, is_active=True).all()

    units_data = [{
        'id': unit.id,
        'name': unit.name,
        'display_name': unit.display_name,
        'conversion_factor': unit.conversion_factor,
        'is_default': unit.is_default
    } for unit in units]

    return jsonify(units_data)
