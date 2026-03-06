import datetime
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, DropdownList, DropdownItem

dropdowns_bp = Blueprint('dropdowns', __name__)

# صفحة إدارة القوائم المنسدلة
@dropdowns_bp.route('/dropdowns')
@login_required
def dropdowns_management():
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))
    
    # الحصول على جميع القوائم المنسدلة
    dropdowns = DropdownList.query.all()
    
    return render_template('dropdowns_management.html',
                           dropdowns=dropdowns,
                           current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

# إضافة قائمة منسدلة جديدة
@dropdowns_bp.route('/dropdowns/add', methods=['POST'])
@login_required
def add_dropdown():
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))
    
    name = request.form.get('name')
    display_name = request.form.get('display_name')
    field_type = request.form.get('field_type')
    visibility = request.form.get('visibility', 'all')
    description = request.form.get('description', '')
    
    # التحقق من عدم وجود قائمة بنفس الاسم
    existing_dropdown = DropdownList.query.filter_by(name=name).first()
    if existing_dropdown:
        flash(f'القائمة المنسدلة {name} موجودة بالفعل', 'danger')
        return redirect(url_for('dropdowns.dropdowns_management'))
    
    # إنشاء قائمة منسدلة جديدة
    dropdown = DropdownList(
        name=name,
        display_name=display_name,
        field_type=field_type,
        visibility=visibility,
        description=description,
        is_active=True,
        created_at=datetime.datetime.now()
    )
    
    db.session.add(dropdown)
    db.session.commit()
    
    flash(f'تم إضافة القائمة المنسدلة {display_name} بنجاح', 'success')
    return redirect(url_for('dropdowns.dropdowns_management'))

# تعديل قائمة منسدلة
@dropdowns_bp.route('/dropdowns/<int:dropdown_id>/edit', methods=['POST'])
@login_required
def edit_dropdown(dropdown_id):
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))
    
    dropdown = DropdownList.query.get_or_404(dropdown_id)
    
    name = request.form.get('name')
    display_name = request.form.get('display_name')
    field_type = request.form.get('field_type')
    visibility = request.form.get('visibility', 'all')
    description = request.form.get('description', '')
    
    # التحقق من عدم وجود قائمة أخرى بنفس الاسم
    existing_dropdown = DropdownList.query.filter(
        DropdownList.id != dropdown_id,
        DropdownList.name == name
    ).first()
    
    if existing_dropdown:
        flash(f'القائمة المنسدلة {name} موجودة بالفعل', 'danger')
        return redirect(url_for('dropdowns.dropdowns_management'))
    
    # تحديث بيانات القائمة
    dropdown.name = name
    dropdown.display_name = display_name
    dropdown.field_type = field_type
    dropdown.visibility = visibility
    dropdown.description = description
    dropdown.updated_at = datetime.datetime.now()
    
    db.session.commit()
    
    flash(f'تم تحديث القائمة المنسدلة {display_name} بنجاح', 'success')
    return redirect(url_for('dropdowns.dropdowns_management'))

# تفعيل/تعطيل قائمة منسدلة
@dropdowns_bp.route('/dropdowns/<int:dropdown_id>/toggle')
@login_required
def toggle_dropdown(dropdown_id):
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))
    
    dropdown = DropdownList.query.get_or_404(dropdown_id)
    
    dropdown.is_active = not dropdown.is_active
    dropdown.updated_at = datetime.datetime.now()
    
    db.session.commit()
    
    status = 'تفعيل' if dropdown.is_active else 'تعطيل'
    flash(f'تم {status} القائمة المنسدلة {dropdown.display_name} بنجاح', 'success')
    return redirect(url_for('dropdowns.dropdowns_management'))

# الحصول على عناصر قائمة منسدلة
@dropdowns_bp.route('/dropdowns/<int:dropdown_id>/items')
@login_required
def get_dropdown_items(dropdown_id):
    dropdown = DropdownList.query.get_or_404(dropdown_id)
    
    items = DropdownItem.query.filter_by(dropdown_id=dropdown_id).order_by(DropdownItem.order).all()
    
    items_data = [{
        'id': item.id,
        'value': item.value,
        'display_text': item.display_text,
        'order': item.order,
        'is_active': item.is_active
    } for item in items]
    
    return jsonify({'items': items_data})

# إضافة عنصر إلى قائمة منسدلة
@dropdowns_bp.route('/dropdowns/<int:dropdown_id>/items/add', methods=['POST'])
@login_required
def add_dropdown_item(dropdown_id):
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))
    
    dropdown = DropdownList.query.get_or_404(dropdown_id)
    
    value = request.form.get('value')
    display_text = request.form.get('display_text')
    order = int(request.form.get('order', 0))
    
    # التحقق من عدم وجود عنصر بنفس القيمة في نفس القائمة
    existing_item = DropdownItem.query.filter_by(dropdown_id=dropdown_id, value=value).first()
    if existing_item:
        flash(f'العنصر بالقيمة {value} موجود بالفعل في هذه القائمة', 'danger')
        return redirect(url_for('dropdowns.dropdowns_management'))
    
    # إنشاء عنصر جديد
    item = DropdownItem(
        dropdown_id=dropdown_id,
        value=value,
        display_text=display_text,
        order=order,
        is_active=True,
        created_at=datetime.datetime.now()
    )
    
    db.session.add(item)
    db.session.commit()
    
    flash(f'تم إضافة العنصر {display_text} إلى القائمة {dropdown.display_name} بنجاح', 'success')
    return redirect(url_for('dropdowns.dropdowns_management'))

# تعديل عنصر في قائمة منسدلة
@dropdowns_bp.route('/dropdowns/items/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_dropdown_item(item_id):
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))
    
    item = DropdownItem.query.get_or_404(item_id)
    dropdown = DropdownList.query.get_or_404(item.dropdown_id)
    
    value = request.form.get('value')
    display_text = request.form.get('display_text')
    order = int(request.form.get('order', 0))
    
    # التحقق من عدم وجود عنصر آخر بنفس القيمة في نفس القائمة
    existing_item = DropdownItem.query.filter(
        DropdownItem.id != item_id,
        DropdownItem.dropdown_id == item.dropdown_id,
        DropdownItem.value == value
    ).first()
    
    if existing_item:
        flash(f'العنصر بالقيمة {value} موجود بالفعل في هذه القائمة', 'danger')
        return redirect(url_for('dropdowns.dropdowns_management'))
    
    # تحديث بيانات العنصر
    item.value = value
    item.display_text = display_text
    item.order = order
    
    db.session.commit()
    
    flash(f'تم تحديث العنصر {display_text} في القائمة {dropdown.display_name} بنجاح', 'success')
    return redirect(url_for('dropdowns.dropdowns_management'))

# تفعيل/تعطيل عنصر في قائمة منسدلة
@dropdowns_bp.route('/dropdowns/items/<int:item_id>/toggle')
@login_required
def toggle_dropdown_item(item_id):
    # التحقق من أن المستخدم ليس مقاول
    if current_user.role == 'contractor':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('contractor_dashboard'))
    
    item = DropdownItem.query.get_or_404(item_id)
    dropdown = DropdownList.query.get_or_404(item.dropdown_id)
    
    item.is_active = not item.is_active
    
    db.session.commit()
    
    status = 'تفعيل' if item.is_active else 'تعطيل'
    flash(f'تم {status} العنصر {item.display_text} في القائمة {dropdown.display_name} بنجاح', 'success')
    return redirect(url_for('dropdowns.dropdowns_management'))

# الحصول على القوائم المنسدلة حسب نوع الحقل
@dropdowns_bp.route('/dropdowns/by-field-type/<field_type>')
@login_required
def get_dropdowns_by_field_type(field_type):
    # تحديد القوائم المنسدلة التي يمكن للمستخدم رؤيتها
    if current_user.role == 'admin':
        visibility_options = ['all', 'admin']
    elif current_user.role == 'contractor':
        visibility_options = ['all', 'contractor']
    else:
        visibility_options = ['all']
    
    dropdowns = DropdownList.query.filter(
        DropdownList.field_type == field_type,
        DropdownList.is_active == True,
        DropdownList.visibility.in_(visibility_options)
    ).all()
    
    dropdowns_data = []
    for dropdown in dropdowns:
        items = DropdownItem.query.filter_by(
            dropdown_id=dropdown.id,
            is_active=True
        ).order_by(DropdownItem.order).all()
        
        items_data = [{
            'id': item.id,
            'value': item.value,
            'display_text': item.display_text,
            'order': item.order
        } for item in items]
        
        dropdowns_data.append({
            'id': dropdown.id,
            'name': dropdown.name,
            'display_name': dropdown.display_name,
            'items': items_data
        })
    
    return jsonify(dropdowns_data)
