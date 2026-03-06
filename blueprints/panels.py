"""
Blueprint لإدارة اللوحات الكهربائية
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, MDBPanel, ElectricalReading, Alert, Camp, Company, Country
from utils import paginate_query, get_pagination_info, admin_required
from sqlalchemy.orm import joinedload
import datetime

# إنشاء Blueprint
panels_bp = Blueprint('panels', __name__, url_prefix='/panels')


@panels_bp.route('/')
@login_required
def list_panels():
    """قائمة اللوحات مع Pagination"""
    # الحصول على معايير البحث
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    area = request.args.get('area', '')
    
    # بناء الاستعلام
    query = MDBPanel.query.options(
        joinedload(MDBPanel.camp),
        joinedload(MDBPanel.company),
        joinedload(MDBPanel.country)
    )
    
    # تطبيق الفلاتر
    if search:
        query = query.filter(
            db.or_(
                MDBPanel.mdb.contains(search),
                MDBPanel.maximo_tag.contains(search),
                MDBPanel.area_name.contains(search)
            )
        )
    
    if status:
        query = query.filter(MDBPanel.status == status)
    
    if area:
        query = query.filter(MDBPanel.area_name == area)
    
    # تطبيق Pagination
    pagination = paginate_query(query.order_by(MDBPanel.id.desc()))
    
    # الحصول على قائمة المناطق للفلتر
    areas = db.session.query(MDBPanel.area_name).distinct().filter(
        MDBPanel.area_name.isnot(None)
    ).all()
    areas = [area[0] for area in areas if area[0]]
    
    return render_template('panels/list.html',
                         panels=pagination.items,
                         pagination=pagination,
                         areas=areas,
                         search=search,
                         status=status,
                         area=area,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))


@panels_bp.route('/<int:panel_id>')
@login_required
def panel_details(panel_id):
    """تفاصيل لوحة كهربائية"""
    panel = MDBPanel.query.options(
        joinedload(MDBPanel.camp),
        joinedload(MDBPanel.company),
        joinedload(MDBPanel.country),
        joinedload(MDBPanel.responsible_contractor)
    ).get_or_404(panel_id)
    
    # الحصول على آخر القراءات
    latest_readings = ElectricalReading.query.filter_by(
        panel_id=panel_id
    ).order_by(
        ElectricalReading.timestamp.desc()
    ).limit(10).all()
    
    # الحصول على التنبيهات النشطة
    active_alerts = Alert.query.filter_by(
        panel_id=panel_id,
        is_resolved=False
    ).order_by(
        Alert.timestamp.desc()
    ).all()
    
    return render_template('panels/details.html',
                         panel=panel,
                         latest_readings=latest_readings,
                         active_alerts=active_alerts,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))


@panels_bp.route('/<int:panel_id>/readings')
@login_required
def panel_readings(panel_id):
    """قراءات اللوحة مع Pagination"""
    panel = MDBPanel.query.get_or_404(panel_id)
    
    # بناء الاستعلام
    query = ElectricalReading.query.filter_by(panel_id=panel_id).order_by(
        ElectricalReading.timestamp.desc()
    )
    
    # تطبيق Pagination
    pagination = paginate_query(query, per_page=100)
    
    return render_template('panels/readings.html',
                         panel=panel,
                         readings=pagination.items,
                         pagination=pagination,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))


@panels_bp.route('/<int:panel_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_panel_status(panel_id):
    """تحديث حالة اللوحة"""
    panel = MDBPanel.query.get_or_404(panel_id)
    
    try:
        status = request.form.get('status')
        notes = request.form.get('notes', '')
        
        if status:
            panel.status = status
            if notes:
                panel.notes = notes
            
            panel.last_maintenance_date = datetime.datetime.now()
            db.session.commit()
            
            flash('تم تحديث حالة اللوحة بنجاح', 'success')
        else:
            flash('يرجى اختيار الحالة', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء تحديث الحالة', 'danger')
        print(f"Update status error: {e}")
    
    return redirect(url_for('panels.panel_details', panel_id=panel_id))


@panels_bp.route('/api/stats')
@login_required
def api_panel_stats():
    """API للحصول على إحصائيات اللوحات"""
    try:
        total = MDBPanel.query.count()
        active = MDBPanel.query.filter_by(status='عامل').count()
        inactive = MDBPanel.query.filter_by(status='معطل').count()
        maintenance = MDBPanel.query.filter_by(status='تحت الصيانة').count()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'active': active,
                'inactive': inactive,
                'maintenance': maintenance,
                'active_percentage': round((active / total * 100), 2) if total > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@panels_bp.route('/export')
@login_required
@admin_required
def export_panels():
    """تصدير اللوحات إلى Excel"""
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    
    try:
        # الحصول على جميع اللوحات
        panels = MDBPanel.query.all()
        
        # تحويل إلى DataFrame
        data = []
        for panel in panels:
            data.append({
                'MDB': panel.mdb,
                'Maximo Tag': panel.maximo_tag,
                'المنطقة': panel.area_name,
                'الحالة': panel.status,
                'النوع': panel.panel_type,
                'X': panel.x_coordinate,
                'Y': panel.y_coordinate,
                'المخيم': panel.camp.camp_number if panel.camp else '',
                'الشركة': panel.company.name if panel.company else '',
                'الدولة': panel.country.name if panel.country else '',
            })
        
        df = pd.DataFrame(data)
        
        # إنشاء ملف Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='اللوحات')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'panels_{datetime.datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    except Exception as e:
        flash('حدث خطأ أثناء التصدير', 'danger')
        print(f"Export error: {e}")
        return redirect(url_for('panels.list_panels'))
