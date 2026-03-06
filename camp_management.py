"""
وحدة إدارة المخيمات والشركات
"""

import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Country, Company, Camp, PanelCampAssignment, MDBPanel
from shapely.geometry import Point, Polygon
import json

# إنشاء Blueprint
camps_bp = Blueprint('camps', __name__)

def allowed_file(filename, allowed_extensions=None):
    """فحص امتداد الملف"""
    if allowed_extensions is None:
        allowed_extensions = {'xlsx', 'xls', 'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def parse_coordinates(coord_string):
    """تحليل الإحداثيات من النص"""
    if not coord_string:
        return []

    try:
        points = []
        # تقسيم الإحداثيات بالمسافات
        coord_pairs = coord_string.strip().split(' ')

        for pair in coord_pairs:
            if ',' in pair:
                parts = pair.split(',')
                if len(parts) >= 2:
                    try:
                        lat = float(parts[0])
                        lng = float(parts[1])
                        points.append([lat, lng])
                    except ValueError:
                        continue

        return points
    except Exception as e:
        print(f"خطأ في تحليل الإحداثيات: {str(e)}")
        return []

def point_in_polygon(point_lat, point_lng, polygon_coords):
    """فحص ما إذا كانت النقطة داخل المضلع مع إصلاح ترتيب الإحداثيات"""
    try:
        if not polygon_coords or len(polygon_coords) < 3:
            return False

        # ملاحظة مهمة:
        # اللوحات: point_lng=X (خط الطول), point_lat=Y (خط العرض)
        # المخيمات: polygon_coords = [[خط العرض, خط الطول], ...]

        # الترتيب الصحيح: نحتاج مقارنة (خط العرض، خط الطول) مع (خط العرض، خط الطول)
        # لذلك: point_lat مع coord[0], point_lng مع coord[1]

        # طريقة 1: استخدام Shapely مع الترتيب الصحيح
        try:
            # إنشاء نقطة: (خط الطول، خط العرض) لـ Shapely
            point = Point(point_lng, point_lat)
            # إنشاء مضلع: تحويل من [lat, lng] إلى (lng, lat) لـ Shapely
            polygon_points = [(coord[1], coord[0]) for coord in polygon_coords]
            polygon = Polygon(polygon_points)

            if polygon.is_valid:
                # فحص ما إذا كانت النقطة داخل المضلع أو على الحدود
                if polygon.contains(point) or polygon.touches(point):
                    return True

                # فحص المسافة للنقاط القريبة جداً (تساهل إضافي)
                distance = polygon.distance(point)
                if distance < 0.0001:  # مسافة صغيرة جداً (حوالي 10 متر)
                    return True

        except Exception as e:
            print(f"خطأ في Shapely: {str(e)}")

        # طريقة 2: خوارزمية Ray Casting مع الترتيب الصحيح
        ray_result = ray_casting_algorithm(point_lat, point_lng, polygon_coords)

        # طريقة 3: إذا لم تنجح الطرق السابقة، فحص المسافة
        if not ray_result:
            distance = distance_to_polygon(point_lat, point_lng, polygon_coords)
            if distance < 0.0005:  # مسافة صغيرة جداً (حوالي 50 متر)
                return True

        return ray_result

    except Exception as e:
        print(f"خطأ في فحص النقطة داخل المضلع: {str(e)}")
        return False

def ray_casting_algorithm(point_lat, point_lng, polygon_coords):
    """خوارزمية Ray Casting للتحقق من وجود النقطة داخل المضلع مع الترتيب الصحيح"""
    try:
        n = len(polygon_coords)
        inside = False

        # polygon_coords = [[lat, lng], [lat, lng], ...]
        # point: lat=خط العرض, lng=خط الطول

        p1_lat, p1_lng = polygon_coords[0][0], polygon_coords[0][1]
        for i in range(1, n + 1):
            p2_lat, p2_lng = polygon_coords[i % n][0], polygon_coords[i % n][1]

            # استخدام خط الطول للفحص الأفقي
            if point_lng > min(p1_lng, p2_lng):
                if point_lng <= max(p1_lng, p2_lng):
                    if point_lat <= max(p1_lat, p2_lat):
                        if p1_lng != p2_lng:
                            # حساب نقطة التقاطع
                            lat_intersection = (point_lng - p1_lng) * (p2_lat - p1_lat) / (p2_lng - p1_lng) + p1_lat
                        if p1_lat == p2_lat or point_lat <= lat_intersection:
                            inside = not inside
            p1_lat, p1_lng = p2_lat, p2_lng

        return inside
    except Exception as e:
        print(f"خطأ في Ray Casting: {str(e)}")
        return False

def distance_to_polygon(point_lat, point_lng, polygon_coords):
    """حساب المسافة من النقطة إلى أقرب نقطة في المضلع مع الترتيب الصحيح"""
    try:
        if not polygon_coords:
            return float('inf')

        min_distance = float('inf')
        for coord in polygon_coords:
            # coord = [lat, lng]
            # point: lat=خط العرض, lng=خط الطول
            coord_lat, coord_lng = coord[0], coord[1]

            # حساب المسافة الإقليدية
            distance = ((point_lat - coord_lat) ** 2 + (point_lng - coord_lng) ** 2) ** 0.5
            min_distance = min(min_distance, distance)

        return min_distance
    except Exception as e:
        print(f"خطأ في حساب المسافة: {str(e)}")
        return float('inf')

def assign_panels_to_camps():
    """ربط اللوحات بالمخيمات بناءً على الإحداثيات مع خوارزمية محسنة"""
    try:
        from models import db, MDBPanel, Camp, PanelCampAssignment, Company, Country

        # الحصول على جميع اللوحات والمخيمات
        panels = MDBPanel.query.filter(
            MDBPanel.x_coordinate.isnot(None),
            MDBPanel.y_coordinate.isnot(None)
        ).all()

        camps = Camp.query.join(Company).join(Country).filter(
            Camp.coordinates.isnot(None)
        ).all()

        assignments_count = 0
        updated_panels = 0
        distance_assignments = 0

        print(f"🔍 العثور على {len(panels)} لوحة و {len(camps)} مخيم للربط...")

        # تحليل إحداثيات المخيمات مسبقاً
        valid_camps = []
        for camp in camps:
            polygon_coords = camp.get_coordinates_list()
            if len(polygon_coords) >= 3:
                valid_camps.append((camp, polygon_coords))
                print(f"📍 مخيم {camp.camp_number}: {len(polygon_coords)} نقطة إحداثية")

        print(f"✅ تم العثور على {len(valid_camps)} مخيم صالح للربط")

        for panel in panels:
            # حذف التخصيصات السابقة
            PanelCampAssignment.query.filter_by(panel_id=panel.id).delete()

            # إعادة تعيين معلومات اللوحة
            panel.camp_id = None
            panel.company_id = None
            panel.country_id = None

            panel_assigned = False
            closest_camp = None
            min_distance = float('inf')

            print(f"🔍 فحص اللوحة {panel.mdb} في الإحداثيات (lng={panel.x_coordinate}, lat={panel.y_coordinate})")

            # المرحلة 1: البحث عن تطابق مباشر داخل المضلع
            for camp, polygon_coords in valid_camps:
                try:
                    # تمرير الإحداثيات بالترتيب الصحيح: lat=Y, lng=X
                    if point_in_polygon(panel.y_coordinate, panel.x_coordinate, polygon_coords):
                        # إنشاء تخصيص جديد
                        assignment = PanelCampAssignment(
                            panel_id=panel.id,
                            camp_id=camp.id,
                            is_active=True
                        )
                        db.session.add(assignment)

                        # تحديث معلومات اللوحة
                        panel.camp_id = camp.id
                        panel.company_id = camp.company_id
                        panel.country_id = camp.company.country_id

                        assignments_count += 1
                        updated_panels += 1
                        print(f"✅ ربط مباشر: اللوحة {panel.mdb} -> مخيم {camp.camp_number} -> {camp.company.name} -> {camp.company.country.name}")
                        panel_assigned = True
                        break
                except Exception as e:
                    print(f"⚠️ خطأ في فحص المخيم {camp.camp_number}: {str(e)}")
                    continue

            # المرحلة 2: إذا لم يتم العثور على تطابق مباشر، ابحث عن أقرب مخيم
            if not panel_assigned:
                print(f"🔍 البحث عن أقرب مخيم للوحة {panel.mdb}...")
                for camp, polygon_coords in valid_camps:
                    try:
                        # تمرير الإحداثيات بالترتيب الصحيح: lat=Y, lng=X
                        distance = distance_to_polygon(panel.y_coordinate, panel.x_coordinate, polygon_coords)
                        if distance < min_distance:
                            min_distance = distance
                            closest_camp = camp
                    except Exception as e:
                        print(f"⚠️ خطأ في حساب المسافة للمخيم {camp.camp_number}: {str(e)}")
                        continue

                # ربط بأقرب مخيم إذا كانت المسافة معقولة (أقل من 0.02 درجة ≈ 2 كم)
                if closest_camp and min_distance < 0.02:
                    assignment = PanelCampAssignment(
                        panel_id=panel.id,
                        camp_id=closest_camp.id,
                        is_active=True
                    )
                    db.session.add(assignment)

                    # تحديث معلومات اللوحة
                    panel.camp_id = closest_camp.id
                    panel.company_id = closest_camp.company_id
                    panel.country_id = closest_camp.company.country_id

                    assignments_count += 1
                    updated_panels += 1
                    distance_assignments += 1
                    print(f"📏 ربط بالمسافة: اللوحة {panel.mdb} -> مخيم {closest_camp.camp_number} (مسافة: {min_distance:.6f})")
                    panel_assigned = True

            if not panel_assigned:
                print(f"❌ لم يتم العثور على مخيم مناسب للوحة {panel.mdb} في الإحداثيات ({panel.x_coordinate}, {panel.y_coordinate})")

        db.session.commit()
        print(f"\n🎉 نتائج الربط:")
        print(f"   📊 إجمالي اللوحات المرتبطة: {assignments_count}")
        print(f"   🎯 ربط مباشر (داخل المضلع): {assignments_count - distance_assignments}")
        print(f"   📏 ربط بالمسافة (أقرب مخيم): {distance_assignments}")
        print(f"   🔄 اللوحات المحدثة: {updated_panels}")

        return assignments_count

    except Exception as e:
        print(f"❌ خطأ في ربط اللوحات بالمخيمات: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return 0

@camps_bp.route('/camps')
@login_required
def camps_list():
    """صفحة قائمة المخيمات"""
    # التحقق من الصلاحيات
    if current_user.role not in ['admin', 'user']:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))

    # الحصول على المعاملات من الطلب
    country_filter = request.args.get('country', '')
    company_filter = request.args.get('company', '')
    search = request.args.get('search', '')

    # بناء الاستعلام
    query = Camp.query.join(Company).join(Country)

    # تطبيق الفلاتر
    if country_filter:
        query = query.filter(Country.id == country_filter)

    if company_filter:
        query = query.filter(Company.id == company_filter)

    if search:
        query = query.filter(
            db.or_(
                Camp.camp_number.contains(search),
                Camp.square_number.contains(search),
                Company.name.contains(search)
            )
        )

    # الحصول على النتائج
    camps = query.order_by(Camp.camp_number, Camp.square_number).all()

    # الحصول على قوائم الدول والشركات للفلاتر
    countries = Country.query.filter_by(is_active=True).order_by(Country.name).all()
    companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()

    # حساب الإحصائيات
    total_camps = len(camps)
    total_pilgrims = sum(camp.pilgrims_count or 0 for camp in camps)
    total_companies = len(set(camp.company_id for camp in camps))
    total_countries = len(set(camp.company.country_id for camp in camps))

    return render_template('camps/camps_list.html',
                         camps=camps,
                         countries=countries,
                         companies=companies,
                         country_filter=country_filter,
                         company_filter=company_filter,
                         search=search,
                         total_camps=total_camps,
                         total_pilgrims=total_pilgrims,
                         total_companies=total_companies,
                         total_countries=total_countries)

@camps_bp.route('/camps/import', methods=['GET', 'POST'])
@login_required
def import_camps():
    """استيراد بيانات المخيمات من Excel"""
    # التحقق من الصلاحيات
    if current_user.role not in ['admin']:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('camps.camps_list'))

    if request.method == 'POST':
        # التحقق من وجود الملف
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                # قراءة الملف
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file, engine='openpyxl')

                # التحقق من وجود الأعمدة المطلوبة
                required_columns = [
                    'رقم المربع', 'رقم المخيم', 'عدد الحجاج',
                    'اسم الشركة', 'الدولة', 'المساحة الإجمالية',
                    'الإحداثيات', 'Zone/Style'
                ]

                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    flash(f'الأعمدة التالية مفقودة: {", ".join(missing_columns)}', 'danger')
                    return redirect(request.url)

                # معالجة البيانات
                camps_added = 0
                countries_added = 0
                companies_added = 0

                for index, row in df.iterrows():
                    try:
                        # معالجة الدولة
                        country_name = str(row['الدولة']).strip()
                        country = Country.query.filter_by(name=country_name).first()
                        if not country:
                            country = Country(name=country_name, is_active=True)
                            db.session.add(country)
                            db.session.flush()  # للحصول على ID
                            countries_added += 1

                        # معالجة الشركة
                        company_name = str(row['اسم الشركة']).strip()

                        # استخراج معلومات الاتصال الاختيارية
                        contact_person = None
                        phone = None

                        if 'الشخص المسؤول' in row and pd.notna(row['الشخص المسؤول']):
                            contact_person = str(row['الشخص المسؤول']).strip()

                        if 'رقم التواصل' in row and pd.notna(row['رقم التواصل']):
                            phone = str(row['رقم التواصل']).strip()

                        company = Company.query.filter_by(
                            name=company_name,
                            country_id=country.id
                        ).first()

                        if not company:
                            company = Company(
                                name=company_name,
                                country_id=country.id,
                                contact_person=contact_person,
                                phone=phone,
                                is_active=True
                            )
                            db.session.add(company)
                            db.session.flush()  # للحصول على ID
                            companies_added += 1
                        else:
                            # تحديث معلومات الاتصال إذا كانت متوفرة
                            updated = False
                            if contact_person and not company.contact_person:
                                company.contact_person = contact_person
                                updated = True
                            if phone and not company.phone:
                                company.phone = phone
                                updated = True
                            if updated:
                                db.session.flush()

                        # معالجة المخيم
                        camp_number = str(row['رقم المخيم']).strip()
                        square_number = str(row['رقم المربع']).strip()

                        # التحقق من عدم وجود المخيم مسبقاً
                        existing_camp = Camp.query.filter_by(
                            camp_number=camp_number,
                            square_number=square_number,
                            company_id=company.id
                        ).first()

                        if not existing_camp:
                            # معالجة البيانات الرقمية
                            pilgrims_count = 0
                            try:
                                pilgrims_count = int(float(row['عدد الحجاج'])) if pd.notna(row['عدد الحجاج']) else 0
                            except (ValueError, TypeError):
                                pilgrims_count = 0

                            total_area = None
                            try:
                                total_area = float(row['المساحة الإجمالية']) if pd.notna(row['المساحة الإجمالية']) else None
                            except (ValueError, TypeError):
                                total_area = None

                            # معالجة الإحداثيات
                            coordinates = str(row['الإحداثيات']).strip() if pd.notna(row['الإحداثيات']) else ''

                            # معالجة Zone/Style
                            zone_style = str(row['Zone/Style']).strip() if pd.notna(row['Zone/Style']) else ''

                            # إنشاء المخيم
                            camp = Camp(
                                camp_number=camp_number,
                                square_number=square_number,
                                company_id=company.id,
                                pilgrims_count=pilgrims_count,
                                total_area=total_area,
                                zone_style=zone_style,
                                coordinates=coordinates,
                                is_active=True
                            )

                            db.session.add(camp)
                            camps_added += 1

                    except Exception as e:
                        print(f"خطأ في معالجة الصف {index + 1}: {str(e)}")
                        continue

                # حفظ التغييرات
                db.session.commit()

                # ربط اللوحات بالمخيمات
                assignments_count = assign_panels_to_camps()

                flash(f'تم استيراد {camps_added} مخيم، {companies_added} شركة، {countries_added} دولة، وربط {assignments_count} لوحة بالمخيمات', 'success')

            except Exception as e:
                db.session.rollback()
                flash(f'حدث خطأ أثناء استيراد البيانات: {str(e)}', 'danger')

        else:
            flash('نوع الملف غير مسموح به. يرجى استخدام ملفات Excel (.xlsx, .xls) أو CSV', 'danger')

        return redirect(url_for('camps.camps_list'))

    return render_template('camps/import_camps.html')

@camps_bp.route('/api/companies/<int:country_id>')
@login_required
def get_companies_by_country(country_id):
    """API للحصول على الشركات حسب الدولة"""
    companies = Company.query.filter_by(country_id=country_id, is_active=True).order_by(Company.name).all()
    return jsonify([{
        'id': company.id,
        'name': company.name
    } for company in companies])

@camps_bp.route('/camps/assign_panels')
@login_required
def assign_panels():
    """ربط اللوحات بالمخيمات يدوياً"""
    if current_user.role not in ['admin']:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('camps.camps_list'))

    try:
        assignments_count = assign_panels_to_camps()
        flash(f'تم ربط {assignments_count} لوحة بالمخيمات بنجاح', 'success')
    except Exception as e:
        flash(f'حدث خطأ أثناء ربط اللوحات: {str(e)}', 'danger')

    return redirect(url_for('camps.camps_list'))
