#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
وحدة تجربة الحجاج والسياح 360°
360° Pilgrimage & Tourism Experience Module

صفحة مستقلة للتجربة التفاعلية 360 درجة للحجاج والسياح
"""

import os
import datetime
import json
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
from sqlalchemy import and_, or_
import os
from PIL import Image

# استيراد النماذج
from models import (
    db, User,
    PilgrimageLocation, PilgrimageReport, VirtualTourInteraction,
    ServiceCategory, InteractiveLocation, LocationConnection
)

# إنشاء Blueprint
pilgrimage_bp = Blueprint('pilgrimage_360', __name__, url_prefix='/pilgrimage-360')

@pilgrimage_bp.route('/')
def index():
    """الصفحة الرئيسية لتجربة الحجاج والسياح 360°"""
    # الحصول على المواقع المميزة
    featured_locations = PilgrimageLocation.query.filter_by(is_featured=True).order_by(PilgrimageLocation.display_order).all()
    
    # الحصول على جميع المواقع مرتبة حسب النوع
    holy_sites = PilgrimageLocation.query.filter_by(location_type='holy_site').order_by(PilgrimageLocation.display_order).all()
    services = PilgrimageLocation.query.filter_by(location_type='service').order_by(PilgrimageLocation.display_order).all()
    shopping = PilgrimageLocation.query.filter_by(location_type='shopping').order_by(PilgrimageLocation.display_order).all()
    transport = PilgrimageLocation.query.filter_by(location_type='transport').order_by(PilgrimageLocation.display_order).all()
    emergency = PilgrimageLocation.query.filter_by(location_type='emergency').order_by(PilgrimageLocation.display_order).all()
    
    # إحصائيات
    total_locations = PilgrimageLocation.query.count()
    total_reports = PilgrimageReport.query.count()
    active_reports = PilgrimageReport.query.filter(PilgrimageReport.status.in_(['reported', 'investigating'])).count()
    
    return render_template('pilgrimage_360/index.html',
                         featured_locations=featured_locations,
                         holy_sites=holy_sites,
                         services=services,
                         shopping=shopping,
                         transport=transport,
                         emergency=emergency,
                         total_locations=total_locations,
                         total_reports=total_reports,
                         active_reports=active_reports,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/location/<int:location_id>')
def location_detail(location_id):
    """عرض تفاصيل موقع معين مع التجربة 360°"""
    location = PilgrimageLocation.query.get_or_404(location_id)
    
    # تسجيل التفاعل
    session_id = session.get('tour_session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['tour_session_id'] = session_id
    
    interaction = VirtualTourInteraction(
        session_id=session_id,
        location_id=location_id,
        user_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        language=request.headers.get('Accept-Language', 'ar')[:2],
        interaction_type='view'
    )
    db.session.add(interaction)
    db.session.commit()
    
    # الحصول على المواقع القريبة
    nearby_locations = PilgrimageLocation.query.filter(
        PilgrimageLocation.id != location_id
    ).limit(6).all()
    
    # الحصول على التقارير الحديثة لهذا الموقع
    recent_reports = PilgrimageReport.query.filter_by(
        location_id=location_id
    ).order_by(PilgrimageReport.report_date.desc()).limit(5).all()
    
    return render_template('pilgrimage_360/location_detail.html',
                         location=location,
                         nearby_locations=nearby_locations,
                         recent_reports=recent_reports,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/virtual-tour')
def virtual_tour():
    """الجولة الافتراضية الكاملة"""
    # استخدام البيانات التجريبية مباشرة بدلاً من قاعدة البيانات

    # استخدام البيانات التجريبية مباشرة كقواميس
    demo_locations = [
        {
            'id': 1,
            'location_name': 'المسجد الحرام',
            'location_name_en': 'Masjid al-Haram',
            'location_type': 'holy_site',
            'type': 'holy_site',
            'description': 'أقدس مكان في الإسلام، يحتوي على الكعبة المشرفة',
            'center_lat': 21.4225,
            'center_lng': 39.8262,
            'virtual_tour_url': '/static/360_images/masjid_360.jpg',
            'panorama_images': '["/static/360_images/masjid_360.jpg"]',
            'visit_duration': 180,
            'best_visit_time': 'بعد صلاة الفجر أو قبل المغرب',
            'crowd_level': 'high',
            'operating_hours': '24/7',
            'amenities': '["مصاعد", "مكيفات", "مياه زمزم", "مصليات منفصلة"]',
            'is_featured': True,
            'display_order': 1
        },
        {
            'id': 2,
            'location_name': 'الكعبة المشرفة',
            'location_name_en': 'Holy Kaaba',
            'location_type': 'holy_site',
            'type': 'holy_site',
            'description': 'قبلة المسلمين في جميع أنحاء العالم، البيت الحرام',
            'center_lat': 21.4225,
            'center_lng': 39.8262,
            'virtual_tour_url': '/static/360_images/kaaba_360.jpg',
            'panorama_images': '["/static/360_images/kaaba_360.jpg"]',
            'visit_duration': 120,
            'best_visit_time': 'بعد صلاة الفجر أو العصر',
            'crowd_level': 'very_high',
            'operating_hours': '24/7',
            'amenities': '["طواف", "صلاة", "دعاء", "تصوير"]',
            'is_featured': True,
            'display_order': 2
        },
        {
            'id': 3,
            'location_name': 'منى',
            'location_name_en': 'Mina',
            'location_type': 'holy_site',
            'type': 'holy_site',
            'description': 'مدينة الخيام، حيث يقيم الحجاج أيام التشريق',
            'center_lat': 21.4125,
            'center_lng': 39.8875,
            'virtual_tour_url': '/static/360_images/mina_360.jpg',
            'panorama_images': '["/static/360_images/mina_360.jpg"]',
            'visit_duration': 240,
            'best_visit_time': 'أيام الحج',
            'crowd_level': 'very_high',
            'operating_hours': 'موسم الحج',
            'amenities': '["خيام", "مطاعم", "مراحيض", "عيادات طبية"]',
            'is_featured': True,
            'display_order': 3
        },
        {
            'id': 4,
            'location_name': 'عرفات',
            'location_name_en': 'Arafat',
            'location_type': 'holy_site',
            'type': 'holy_site',
            'description': 'جبل الرحمة، حيث يقف الحجاج يوم عرفة',
            'center_lat': 21.3544,
            'center_lng': 39.9844,
            'virtual_tour_url': '/static/360_images/arafat_360.jpg',
            'panorama_images': '["/static/360_images/arafat_360.jpg"]',
            'visit_duration': 480,
            'best_visit_time': 'يوم عرفة',
            'crowd_level': 'very_high',
            'operating_hours': 'موسم الحج',
            'amenities': '["مياه", "مظلات", "مراحيض", "إسعافات أولية"]',
            'is_featured': True,
            'display_order': 4
        },
        {
            'id': 5,
            'location_name': 'مزدلفة',
            'location_name_en': 'Muzdalifah',
            'location_type': 'holy_site',
            'type': 'holy_site',
            'description': 'المشعر الحرام، حيث يبيت الحجاج ليلة النحر',
            'center_lat': 21.3964,
            'center_lng': 39.9364,
            'virtual_tour_url': '/static/360_images/muzdalifah_360.jpg',
            'panorama_images': '["/static/360_images/muzdalifah_360.jpg"]',
            'visit_duration': 360,
            'best_visit_time': 'ليلة النحر',
            'crowd_level': 'very_high',
            'operating_hours': 'موسم الحج',
            'amenities': '["مياه", "مراحيض", "إضاءة", "أمن"]',
            'is_featured': True,
            'display_order': 5
        },
        {
            'id': 6,
            'location_name': 'الجمرات',
            'location_name_en': 'Jamarat',
            'location_type': 'holy_site',
            'type': 'holy_site',
            'description': 'جسر الجمرات، حيث يرمي الحجاج الجمرات',
            'center_lat': 21.4194,
            'center_lng': 39.8844,
            'virtual_tour_url': '/static/360_images/jamarat_360.jpg',
            'panorama_images': '["/static/360_images/jamarat_360.jpg"]',
            'visit_duration': 60,
            'best_visit_time': 'أيام التشريق',
            'crowd_level': 'very_high',
            'operating_hours': 'موسم الحج',
            'amenities': '["جسر متعدد الطوابق", "مكيفات", "مراحيض", "إسعافات أولية"]',
            'is_featured': True,
            'display_order': 6
        },
        {
            'id': 7,
            'location_name': 'الصفا والمروة',
            'location_name_en': 'Safa and Marwa',
            'location_type': 'holy_site',
            'type': 'holy_site',
            'description': 'مسعى الحجاج والمعتمرين، حيث يتم السعي بين الصفا والمروة',
            'center_lat': 21.4225,
            'center_lng': 39.8262,
            'virtual_tour_url': '/static/360_images/safa_marwa_360.jpg',
            'panorama_images': '["/static/360_images/safa_marwa_360.jpg"]',
            'visit_duration': 45,
            'best_visit_time': 'بعد الطواف',
            'crowd_level': 'high',
            'operating_hours': '24/7',
            'amenities': '["مسارات مكيفة", "مياه زمزم", "كراسي متحركة", "مصاعد"]',
            'is_featured': True,
            'display_order': 7
        },
        {
            'id': 8,
            'location_name': 'فندق الحجاج',
            'location_name_en': 'Pilgrims Hotel',
            'location_type': 'service',
            'type': 'service',
            'description': 'فندق مخصص لإقامة الحجاج والمعتمرين',
            'center_lat': 21.4125,
            'center_lng': 39.8175,
            'virtual_tour_url': '/static/360_images/hotel_360.jpg',
            'panorama_images': '["/static/360_images/hotel_360.jpg"]',
            'visit_duration': 30,
            'best_visit_time': 'أي وقت',
            'crowd_level': 'medium',
            'operating_hours': '24/7',
            'amenities': '["غرف مكيفة", "مطعم", "مصلى", "خدمة الغرف"]',
            'is_featured': False,
            'display_order': 8
        },
        {
            'id': 9,
            'location_name': 'محطة النقل',
            'location_name_en': 'Transport Station',
            'location_type': 'transport',
            'type': 'transport',
            'description': 'محطة نقل الحجاج بين المشاعر المقدسة',
            'center_lat': 21.4025,
            'center_lng': 39.8575,
            'virtual_tour_url': '/static/360_images/transport_360.jpg',
            'panorama_images': '["/static/360_images/transport_360.jpg"]',
            'visit_duration': 15,
            'best_visit_time': 'حسب مواعيد النقل',
            'crowd_level': 'high',
            'operating_hours': '5:00 - 23:00',
            'amenities': '["حافلات مكيفة", "مناطق انتظار", "معلومات", "أمن"]',
            'is_featured': False,
            'display_order': 9
        }
    ]

    # تجميع المواقع حسب النوع للجولة المنظمة
    tour_sequence = {
        'holy_sites': [loc for loc in demo_locations if loc['type'] == 'holy_site'],
        'historical_sites': [loc for loc in demo_locations if loc['type'] == 'historical_site'],
        'services': [loc for loc in demo_locations if loc['type'] == 'service'],
        'shopping': [loc for loc in demo_locations if loc['type'] == 'shopping'],
        'transport': [loc for loc in demo_locations if loc['type'] == 'transport'],
        'emergency': [loc for loc in demo_locations if loc['type'] == 'emergency']
    }

    return render_template('pilgrimage_360/virtual_tour.html',
                         tour_sequence=tour_sequence,
                         all_locations=demo_locations,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))



@pilgrimage_bp.route('/report-issue', methods=['GET', 'POST'])
def report_issue():
    """تقديم بلاغ أو استفسار"""
    if request.method == 'POST':
        # إنشاء رقم البلاغ
        report_number = f"PIL{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        report = PilgrimageReport(
            report_number=report_number,
            location_id=int(request.form['location_id']) if request.form['location_id'] else None,
            report_type=request.form['report_type'],
            coordinates=request.form['coordinates'] if request.form['coordinates'] else None,
            description=request.form['description'],
            description_en=request.form['description_en'] if request.form['description_en'] else None,
            urgency=request.form['urgency'],
            reported_by_name=request.form['reported_by_name'],
            reported_by_nationality=request.form['reported_by_nationality'],
            contact_info=request.form['contact_info'],
            preferred_language=request.form['preferred_language']
        )
        
        db.session.add(report)
        db.session.commit()
        
        # إرسال رد تلقائي بناءً على نوع البلاغ
        ai_response = generate_ai_response(report)
        report.ai_response = ai_response
        db.session.commit()
        
        flash(f'تم تسجيل البلاغ بنجاح. رقم البلاغ: {report_number}', 'success')
        return redirect(url_for('pilgrimage_360.report_status', report_number=report_number))
    
    # الحصول على المواقع للقائمة المنسدلة
    locations = PilgrimageLocation.query.order_by(PilgrimageLocation.location_name).all()
    
    return render_template('pilgrimage_360/report_issue.html',
                         locations=locations,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/report-status/<report_number>')
def report_status(report_number):
    """عرض حالة البلاغ"""
    report = PilgrimageReport.query.filter_by(report_number=report_number).first_or_404()
    
    return render_template('pilgrimage_360/report_status.html',
                         report=report,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/interactive-map')
def interactive_map():
    """الخريطة التفاعلية الشاملة"""
    try:
        # إنشاء البيانات التجريبية إذا لم تكن موجودة
        if InteractiveLocation.query.count() == 0:
            create_demo_categories_and_locations()

        # جلب المواقع من قاعدة البيانات
        locations = InteractiveLocation.query.filter_by(is_active=True).all()

        # تحويل البيانات للخريطة
        map_data = []
        for location in locations:
            # تحليل صور 360°
            has_360 = bool(location.panorama_360_images)

            # تحديد نوع الموقع حسب الفئة
            location_type = 'service'  # افتراضي
            if location.category:
                if 'مسجد' in location.category.name:
                    location_type = 'holy_site'
                elif 'مطعم' in location.category.name:
                    location_type = 'service'
                elif 'تسوق' in location.category.name:
                    location_type = 'shopping'
                elif 'مواصلات' in location.category.name:
                    location_type = 'transport'
                elif 'طبية' in location.category.name:
                    location_type = 'emergency'

            map_data.append({
                'id': location.id,
                'name': location.name,
                'name_en': location.name_en,
                'type': location_type,
                'lat': location.latitude,
                'lng': location.longitude,
                'description': location.description,
                'crowd_level': 'normal',  # يمكن إضافة هذا الحقل لاحقاً
                'safety_rating': int(location.rating) if location.rating else 4,
                'cleanliness_rating': int(location.rating) if location.rating else 4,
                'operating_hours': location.operating_hours,
                'amenities': [],
                'has_360': has_360,
                'virtual_tour_url': location.virtual_tour_url,
                'address': location.address,
                'phone': location.phone,
                'price_range': location.price_range
            })

        # إضافة بيانات تجريبية إضافية إذا كانت القائمة فارغة
        if not map_data:
            map_data = [
            {
                'id': 1,
                'name': 'المسجد الحرام',
                'name_en': 'Masjid al-Haram',
                'type': 'holy_site',
                'lat': 21.4225,
                'lng': 39.8262,
                'description': 'أقدس مكان في الإسلام، يحتوي على الكعبة المشرفة',
                'crowd_level': 'high',
                'safety_rating': 5,
                'cleanliness_rating': 5,
                'amenities': ['مصاعد', 'مكيفات', 'مياه زمزم', 'مصليات منفصلة'],
                'operating_hours': '24/7',
                'has_360': True
            },
            {
                'id': 2,
                'name': 'المسجد النبوي',
                'name_en': 'Prophet\'s Mosque',
                'type': 'holy_site',
                'lat': 24.4672,
                'lng': 39.6117,
                'description': 'ثاني أقدس مسجد في الإسلام، يحتوي على قبر النبي محمد صلى الله عليه وسلم',
                'crowd_level': 'medium',
                'safety_rating': 5,
                'cleanliness_rating': 5,
                'amenities': ['مكتبة', 'مكيفات', 'مياه باردة', 'مصليات منفصلة'],
                'operating_hours': '24/7',
                'has_360': True
            },
            {
                'id': 3,
                'name': 'موقف الحرم الشريف - الشمالي',
                'name_en': 'Haram Parking - North',
                'type': 'parking',
                'lat': 21.4235,
                'lng': 39.8255,
                'description': 'موقف سيارات كبير شمال المسجد الحرام',
                'crowd_level': 'medium',
                'safety_rating': 4,
                'cleanliness_rating': 4,
                'amenities': ['أمن', 'كاميرات', 'إضاءة', 'مظلات'],
                'operating_hours': '24/7',
                'has_360': False
            },
            {
                'id': 4,
                'name': 'فندق مكة الملكي',
                'name_en': 'Makkah Royal Hotel',
                'type': 'accommodation',
                'lat': 21.4188,
                'lng': 39.8258,
                'description': 'فندق فاخر قريب من المسجد الحرام',
                'crowd_level': 'medium',
                'safety_rating': 5,
                'cleanliness_rating': 5,
                'amenities': ['مطعم', 'مسبح', 'واي فاي', 'خدمة الغرف'],
                'operating_hours': '24/7',
                'has_360': True
            },
            {
                'id': 5,
                'name': 'جبل النور - غار حراء',
                'name_en': 'Mount of Light - Cave of Hira',
                'type': 'historical_site',
                'lat': 21.4594,
                'lng': 39.8578,
                'description': 'الجبل الذي يحتوي على غار حراء حيث نزل الوحي على النبي محمد',
                'crowd_level': 'low',
                'safety_rating': 3,
                'cleanliness_rating': 4,
                'amenities': ['مسارات مشي', 'لوحات إرشادية'],
                'operating_hours': 'طوال اليوم',
                'has_360': True
            }
        ]

    except Exception as e:
        print(f"خطأ في تحميل الخريطة التفاعلية: {str(e)}")
        # إنشاء بيانات تجريبية في حالة الخطأ
        map_data = [
            {
                'id': 1,
                'name': 'المسجد الحرام',
                'name_en': 'Masjid al-Haram',
                'type': 'holy_site',
                'lat': 21.4225,
                'lng': 39.8262,
                'description': 'أقدس مكان في الإسلام',
                'crowd_level': 'high',
                'safety_rating': 5,
                'cleanliness_rating': 5,
                'amenities': ['مصاعد', 'مكيفات', 'مياه زمزم'],
                'operating_hours': '24/7',
                'has_360': True
            }
        ]

    return render_template('pilgrimage_360/interactive_map_simple.html',
                         map_data=map_data,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/help-center')
def help_center():
    """مركز المساعدة والأسئلة الشائعة"""
    # الأسئلة الشائعة
    faqs = [
        {
            'question': 'كيف يمكنني استخدام الجولة الافتراضية؟',
            'question_en': 'How can I use the virtual tour?',
            'answer': 'يمكنك النقر على أي موقع في الخريطة أو اختيار موقع من القائمة لبدء الجولة الافتراضية 360 درجة.',
            'answer_en': 'You can click on any location on the map or choose a location from the list to start the 360-degree virtual tour.'
        },
        {
            'question': 'كيف أبلغ عن مشكلة أو استفسار؟',
            'question_en': 'How do I report an issue or inquiry?',
            'answer': 'استخدم نموذج "تقديم بلاغ" وحدد نوع المشكلة والموقع، وسيتم الرد عليك في أقرب وقت.',
            'answer_en': 'Use the "Report Issue" form and specify the type of problem and location, and you will receive a response as soon as possible.'
        },
        {
            'question': 'هل يمكنني استخدام النظام بلغات متعددة؟',
            'question_en': 'Can I use the system in multiple languages?',
            'answer': 'نعم، النظام يدعم العربية والإنجليزية، ويمكن إضافة لغات أخرى حسب الحاجة.',
            'answer_en': 'Yes, the system supports Arabic and English, and other languages can be added as needed.'
        }
    ]
    
    return render_template('pilgrimage_360/help_center.html',
                         faqs=faqs,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/test-tour')
def test_tour():
    """صفحة اختبار الجولة الافتراضية"""
    return render_template('pilgrimage_360/test_tour.html')

@pilgrimage_bp.route('/3d-viewer')
@pilgrimage_bp.route('/3d-viewer/<int:location_id>')
def viewer_3d(location_id=None):
    """عارض النماذج ثلاثية الأبعاد"""
    if location_id:
        location = PilgrimageLocation.query.get_or_404(location_id)
    else:
        # استخدام الكعبة كموقع افتراضي
        location = PilgrimageLocation.query.filter_by(location_name='المسجد الحرام').first()
        if not location:
            # إنشاء موقع افتراضي إذا لم يوجد
            location = type('Location', (), {
                'id': 1,
                'location_name': 'المسجد الحرام',
                'location_name_en': 'Masjid al-Haram',
                'description': 'أقدس مكان في الإسلام، يحتوي على الكعبة المشرفة'
            })()

    return render_template('pilgrimage_360/3d_viewer.html',
                         location=location,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

# ===== Admin Routes =====

@pilgrimage_bp.route('/admin/locations')
@login_required
def admin_locations():
    """لوحة تحكم إدارة المواقع التفاعلية"""
    # التحقق من صلاحيات الإدارة
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('pilgrimage_360.index'))

    # الحصول على الفئات
    categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.display_order).all()

    # الحصول على المواقع
    locations = InteractiveLocation.query.filter_by(is_active=True).order_by(InteractiveLocation.created_at.desc()).all()

    # إحصائيات
    total_locations = InteractiveLocation.query.filter_by(is_active=True).count()
    restaurants_count = InteractiveLocation.query.join(ServiceCategory).filter(
        ServiceCategory.name.like('%مطعم%'), InteractiveLocation.is_active == True
    ).count()
    mosques_count = InteractiveLocation.query.join(ServiceCategory).filter(
        ServiceCategory.name.like('%مسجد%'), InteractiveLocation.is_active == True
    ).count()
    services_count = InteractiveLocation.query.join(ServiceCategory).filter(
        ServiceCategory.name.like('%خدمة%'), InteractiveLocation.is_active == True
    ).count()

    return render_template('pilgrimage_360/admin_locations.html',
                         categories=categories,
                         locations=locations,
                         total_locations=total_locations,
                         restaurants_count=restaurants_count,
                         mosques_count=mosques_count,
                         services_count=services_count,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/admin/locations/add', methods=['POST'])
@login_required
def admin_add_location():
    """إضافة موقع جديد"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'})

    try:
        # الحصول على البيانات
        name = request.form.get('name')
        name_en = request.form.get('name_en')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        phone = request.form.get('phone')
        address = request.form.get('address')
        operating_hours = request.form.get('operating_hours')
        price_range = request.form.get('price_range')
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))

        # إنشاء الموقع الجديد
        location = InteractiveLocation(
            name=name,
            name_en=name_en,
            category_id=int(category_id),
            description=description,
            phone=phone,
            address=address,
            operating_hours=operating_hours,
            price_range=price_range,
            latitude=latitude,
            longitude=longitude,
            added_by=current_user.id,
            verified=True,
            verification_date=datetime.datetime.now()
        )

        # معالجة رفع الصور
        main_image = request.files.get('main_image')
        if main_image and main_image.filename:
            main_image_path = save_uploaded_image(main_image, 'main')
            location.main_image = main_image_path

        # معالجة صور 360°
        panorama_images = request.files.getlist('panorama_images')
        if panorama_images:
            panorama_paths = []
            for img in panorama_images:
                if img and img.filename:
                    path = save_uploaded_image(img, '360')
                    panorama_paths.append(path)
            if panorama_paths:
                location.panorama_360_images = json.dumps(panorama_paths)

        db.session.add(location)
        db.session.commit()

        return jsonify({'success': True, 'message': 'تم إضافة الموقع بنجاح'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@pilgrimage_bp.route('/admin/locations/<int:location_id>', methods=['DELETE'])
@login_required
def admin_delete_location(location_id):
    """حذف موقع"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'})

    try:
        location = InteractiveLocation.query.get_or_404(location_id)
        location.is_active = False  # حذف منطقي
        db.session.commit()

        return jsonify({'success': True, 'message': 'تم حذف الموقع بنجاح'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

def save_uploaded_image(file, image_type):
    """حفظ الصورة المرفوعة"""
    if not file or not file.filename:
        return None

    # إنشاء اسم ملف آمن
    filename = secure_filename(file.filename)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"

    # تحديد مجلد الحفظ
    if image_type == '360':
        upload_folder = os.path.join('static', '360_images', 'uploaded')
    else:
        upload_folder = os.path.join('static', 'images', 'uploaded')

    # إنشاء المجلد إذا لم يكن موجوداً
    os.makedirs(upload_folder, exist_ok=True)

    # حفظ الملف
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    # تحسين الصورة إذا كانت كبيرة
    try:
        with Image.open(file_path) as img:
            # تحديد الحد الأقصى للحجم
            max_size = (2048, 2048) if image_type == '360' else (800, 600)

            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=85)
    except Exception as e:
        print(f"خطأ في تحسين الصورة: {e}")

    return f"/{file_path.replace(os.sep, '/')}"



@pilgrimage_bp.route('/api/locations')
def api_locations():
    """API للحصول على المواقع التفاعلية"""
    try:
        # الحصول على المعاملات
        category_filter = request.args.get('category')
        search_query = request.args.get('search', '').strip()
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 10, type=float)  # نصف قطر البحث بالكيلومتر

        # بناء الاستعلام
        query = InteractiveLocation.query.filter_by(is_active=True)

        # تصفية حسب الفئة
        if category_filter:
            query = query.join(ServiceCategory).filter(ServiceCategory.name.like(f'%{category_filter}%'))

        # البحث النصي
        if search_query:
            query = query.filter(
                or_(
                    InteractiveLocation.name.like(f'%{search_query}%'),
                    InteractiveLocation.name_en.like(f'%{search_query}%'),
                    InteractiveLocation.address.like(f'%{search_query}%'),
                    InteractiveLocation.description.like(f'%{search_query}%')
                )
            )

        locations = query.all()

        # تحويل إلى JSON مع حساب المسافات
        result = []
        for location in locations:
            location_data = {
                'id': location.id,
                'name': location.name,
                'name_en': location.name_en,
                'category': location.category.name if location.category else 'غير مصنف',
                'category_icon': location.category.icon if location.category else 'fa-map-marker',
                'category_color': location.category.color if location.category else '#6c757d',
                'latitude': location.latitude,
                'longitude': location.longitude,
                'address': location.address,
                'phone': location.phone,
                'description': location.description,
                'rating': location.rating,
                'price_range': location.price_range,
                'operating_hours': location.operating_hours,
                'main_image': location.main_image,
                'has_360': bool(location.panorama_360_images),
                'is_featured': location.is_featured,
                'verified': location.verified
            }

            # حساب المسافة إذا تم توفير الإحداثيات
            if lat and lng:
                distance = calculate_distance(lat, lng, location.latitude, location.longitude)
                location_data['distance'] = round(distance, 2)

                # تصفية حسب نصف القطر
                if distance <= radius:
                    result.append(location_data)
            else:
                result.append(location_data)

        # ترتيب حسب المسافة إذا كانت متوفرة
        if lat and lng:
            result.sort(key=lambda x: x.get('distance', float('inf')))

        return jsonify({
            'success': True,
            'locations': result,
            'total': len(result)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب المواقع: {str(e)}'
        })

def calculate_distance(lat1, lng1, lat2, lng2):
    """حساب المسافة بين نقطتين بالكيلومتر"""
    from math import radians, cos, sin, asin, sqrt

    # تحويل إلى راديان
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

    # صيغة هافرساين
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # نصف قطر الأرض بالكيلومتر

    return c * r

@pilgrimage_bp.route('/image-navigation')
def image_navigation():
    """التنقل بين الصور 360 درجة"""
    return render_template('pilgrimage_360/image_navigation.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/api/location-connections/<int:location_id>')
def api_location_connections(location_id):
    """API للحصول على الاتصالات بين المواقع"""
    try:
        location = InteractiveLocation.query.get_or_404(location_id)

        # الحصول على الاتصالات من هذا الموقع
        connections = LocationConnection.query.filter_by(
            from_location_id=location_id,
            is_active=True
        ).all()

        result = []
        for conn in connections:
            to_location = conn.to_location
            if to_location and to_location.is_active:
                result.append({
                    'id': conn.id,
                    'to_location_id': to_location.id,
                    'to_location_name': to_location.name,
                    'hotspot_position': conn.hotspot_position,
                    'hotspot_label': conn.hotspot_label,
                    'connection_type': conn.connection_type,
                    'distance': conn.distance_meters,
                    'category': to_location.category.name if to_location.category else 'غير مصنف',
                    'category_icon': to_location.category.icon if to_location.category else 'fa-map-marker'
                })

        return jsonify({
            'success': True,
            'location': {
                'id': location.id,
                'name': location.name,
                'panorama_images': json.loads(location.panorama_360_images) if location.panorama_360_images else []
            },
            'connections': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب الاتصالات: {str(e)}'
        })

@pilgrimage_bp.route('/test-map')
def test_map():
    """صفحة اختبار الخريطة البسيطة"""
    return render_template('pilgrimage_360/simple_map_test.html')

@pilgrimage_bp.route('/manage-3d-models')
@login_required
def manage_3d_models():
    """إدارة النماذج ثلاثية الأبعاد"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    # جلب جميع المواقع التي تحتوي على نماذج ثلاثية الأبعاد
    locations_with_3d = PilgrimageLocation.query.filter(
        PilgrimageLocation.model_3d_glb.isnot(None)
    ).all()

    return render_template('pilgrimage_360/manage_3d_models.html',
                         models=locations_with_3d,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/add-location', methods=['GET', 'POST'])
def add_location():
    """إضافة موقع جديد"""
    # السماح للجميع بإضافة المواقع للاختبار

    if request.method == 'POST':
        try:
            # الحصول على البيانات من النموذج
            location_name = request.form.get('location_name')
            location_name_en = request.form.get('location_name_en')
            location_type = request.form.get('location_type')
            description = request.form.get('description')
            center_lat = float(request.form.get('center_lat', 0))
            center_lng = float(request.form.get('center_lng', 0))
            virtual_tour_url = request.form.get('virtual_tour_url', '')
            panorama_images = request.form.get('panorama_images', '[]')
            operating_hours = request.form.get('operating_hours', '24/7')
            amenities = request.form.get('amenities', '[]')

            # إنشاء موقع جديد
            new_location = PilgrimageLocation(
                location_name=location_name,
                location_name_en=location_name_en,
                location_type=location_type,
                description=description,
                center_lat=center_lat,
                center_lng=center_lng,
                virtual_tour_url=virtual_tour_url,
                panorama_images=panorama_images,
                operating_hours=operating_hours,
                amenities=amenities,
                crowd_level='low',
                is_featured=False,
                display_order=0
            )

            from app import db
            db.session.add(new_location)
            db.session.commit()

            flash('تم إضافة الموقع بنجاح!', 'success')
            return redirect(url_for('pilgrimage_360.location_detail', location_id=new_location.id))

        except Exception as e:
            flash(f'حدث خطأ أثناء إضافة الموقع: {str(e)}', 'error')
            from app import db
            db.session.rollback()

    return render_template('pilgrimage_360/add_location.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

# ===== API Endpoints =====

@pilgrimage_bp.route('/api/pilgrimage-locations')
def api_pilgrimage_locations():
    """API للحصول على مواقع الحج والعمرة"""
    locations = PilgrimageLocation.query.all()
    data = []
    for location in locations:
        data.append({
            'id': location.id,
            'name': location.location_name,
            'name_en': location.location_name_en,
            'type': location.location_type,
            'lat': location.center_lat,
            'lng': location.center_lng,
            'description': location.description,
            'crowd_level': location.crowd_level,
            'safety_rating': location.safety_rating,
            'cleanliness_rating': location.cleanliness_rating,
            'operating_hours': location.operating_hours,
            'amenities': json.loads(location.amenities) if location.amenities else [],
            'panorama_images': json.loads(location.panorama_images) if location.panorama_images else [],
            'virtual_tour_url': location.virtual_tour_url
        })
    return jsonify(data)

@pilgrimage_bp.route('/api/location/<int:location_id>/interaction', methods=['POST'])
def api_record_interaction(location_id):
    """تسجيل تفاعل المستخدم مع الموقع"""
    data = request.get_json()
    
    session_id = session.get('tour_session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['tour_session_id'] = session_id
    
    interaction = VirtualTourInteraction(
        session_id=session_id,
        location_id=location_id,
        user_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        language=request.headers.get('Accept-Language', 'ar')[:2],
        interaction_type=data.get('type', 'unknown'),
        interaction_data=json.dumps(data.get('data', {})),
        duration_seconds=data.get('duration', 0)
    )
    
    db.session.add(interaction)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@pilgrimage_bp.route('/api/crowd-levels')
def api_crowd_levels():
    """API للحصول على مستويات الازدحام الحالية"""
    locations = PilgrimageLocation.query.filter(
        PilgrimageLocation.center_lat.isnot(None),
        PilgrimageLocation.center_lng.isnot(None)
    ).all()
    
    data = []
    for location in locations:
        data.append({
            'id': location.id,
            'name': location.location_name,
            'lat': location.center_lat,
            'lng': location.center_lng,
            'crowd_level': location.crowd_level,
            'capacity': location.capacity,
            'current_occupancy': location.current_occupancy
        })
    
    return jsonify(data)

# ===== Helper Functions =====

def generate_ai_response(report):
    """إنشاء رد تلقائي ذكي بناءً على نوع البلاغ"""
    responses = {
        'crowding': {
            'ar': 'شكراً لتقريركم عن الازدحام. تم إرسال التنبيه للفرق المختصة لاتخاذ الإجراءات اللازمة.',
            'en': 'Thank you for reporting crowding. An alert has been sent to the relevant teams to take necessary action.'
        },
        'cleanliness': {
            'ar': 'نشكركم على تقريركم. تم إرسال طلب تنظيف عاجل للموقع المحدد.',
            'en': 'Thank you for your report. An urgent cleaning request has been sent for the specified location.'
        },
        'accessibility': {
            'ar': 'تم استلام تقريركم حول إمكانية الوصول. سيتم مراجعة الموقع وتحسين الخدمات.',
            'en': 'Your accessibility report has been received. The location will be reviewed and services improved.'
        },
        'emergency': {
            'ar': 'تم تسجيل حالة الطوارئ. تم إرسال الفرق المختصة فوراً للموقع.',
            'en': 'Emergency has been logged. Specialized teams have been dispatched immediately to the location.'
        },
        'lost_person': {
            'ar': 'تم تسجيل بلاغ الشخص المفقود. تم تنبيه فرق الأمن والبحث.',
            'en': 'Lost person report has been registered. Security and search teams have been alerted.'
        }
    }
    
    response_type = report.report_type
    language = report.preferred_language or 'ar'
    
    if response_type in responses and language in responses[response_type]:
        return responses[response_type][language]
    else:
        return responses['crowding']['ar']  # Default response

# ===== Admin Routes =====

@pilgrimage_bp.route('/admin/locations')
def admin_locations():
    """صفحة إدارة المواقع التفاعلية"""
    try:
        # إحصائيات
        total_locations = InteractiveLocation.query.count()
        restaurants_count = InteractiveLocation.query.join(ServiceCategory).filter(
            ServiceCategory.name.like('%مطعم%')).count()
        mosques_count = InteractiveLocation.query.join(ServiceCategory).filter(
            ServiceCategory.name.like('%مسجد%')).count()
        services_count = InteractiveLocation.query.join(ServiceCategory).filter(
            ServiceCategory.name.like('%خدمة%')).count()

        # المواقع والفئات
        locations = InteractiveLocation.query.all()
        categories = ServiceCategory.query.all()

        return render_template('pilgrimage_360/admin_locations.html',
                             total_locations=total_locations,
                             restaurants_count=restaurants_count,
                             mosques_count=mosques_count,
                             services_count=services_count,
                             locations=locations,
                             categories=categories)
    except Exception as e:
        flash(f'خطأ في تحميل صفحة الإدارة: {str(e)}', 'error')
        return redirect(url_for('pilgrimage_360.index'))

@pilgrimage_bp.route('/admin/add-location', methods=['POST'])
def admin_add_location():
    """إضافة موقع جديد"""
    try:
        # الحصول على البيانات
        name = request.form.get('name')
        name_en = request.form.get('name_en')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        phone = request.form.get('phone')
        address = request.form.get('address')
        operating_hours = request.form.get('operating_hours')
        price_range = request.form.get('price_range')
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))

        # إنشاء الموقع الجديد
        location = InteractiveLocation(
            name=name,
            name_en=name_en,
            category_id=int(category_id) if category_id else None,
            description=description,
            phone=phone,
            address=address,
            operating_hours=operating_hours,
            price_range=price_range,
            latitude=latitude,
            longitude=longitude,
            is_active=True,
            verified=True
        )

        # معالجة رفع الصور
        main_image = request.files.get('main_image')
        if main_image and main_image.filename:
            # حفظ الصورة الرئيسية
            from werkzeug.utils import secure_filename
            filename = secure_filename(main_image.filename)
            image_path = os.path.join('static', 'images', 'locations', filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            main_image.save(image_path)
            location.main_image = f'/static/images/locations/{filename}'

        # معالجة صور 360°
        panorama_images = request.files.getlist('panorama_images')
        panorama_urls = []
        for img in panorama_images:
            if img and img.filename:
                from werkzeug.utils import secure_filename
                filename = secure_filename(img.filename)
                image_path = os.path.join('static', '360_images', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                img.save(image_path)
                panorama_urls.append(f'/static/360_images/{filename}')

        if panorama_urls:
            location.panorama_360_images = json.dumps(panorama_urls)

        # حفظ في قاعدة البيانات
        db.session.add(location)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم إضافة الموقع بنجاح',
            'location_id': location.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إضافة الموقع: {str(e)}'
        }), 500

@pilgrimage_bp.route('/admin/delete-location/<int:location_id>', methods=['DELETE'])
def admin_delete_location(location_id):
    """حذف موقع"""
    try:
        location = InteractiveLocation.query.get_or_404(location_id)

        # حذف الصور المرتبطة
        if location.main_image:
            try:
                os.remove(location.main_image.lstrip('/'))
            except:
                pass

        if location.panorama_360_images:
            try:
                images = json.loads(location.panorama_360_images)
                for img_url in images:
                    os.remove(img_url.lstrip('/'))
            except:
                pass

        # حذف من قاعدة البيانات
        db.session.delete(location)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم حذف الموقع بنجاح'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف الموقع: {str(e)}'
        }), 500

@pilgrimage_bp.route('/upload-panorama', methods=['POST'])
def upload_panorama_image():
    """رفع صورة بانورامية 360° لموقع"""
    try:
        location_id = request.form.get('location_id')
        if not location_id:
            return jsonify({'success': False, 'message': 'معرف الموقع مطلوب'}), 400

        location = InteractiveLocation.query.get_or_404(location_id)

        # التحقق من وجود الصورة
        if 'panorama_image' not in request.files:
            return jsonify({'success': False, 'message': 'لم يتم رفع أي صورة'}), 400

        file = request.files['panorama_image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400

        if file and allowed_file(file.filename):
            from werkzeug.utils import secure_filename
            import uuid

            # إنشاء اسم ملف فريد
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"

            # إنشاء مجلد الحفظ
            upload_folder = os.path.join('static', '360_images')
            os.makedirs(upload_folder, exist_ok=True)

            # حفظ الملف
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # تحديث قاعدة البيانات
            image_url = f'/static/360_images/{filename}'

            # إضافة الصورة للقائمة الموجودة أو إنشاء قائمة جديدة
            if location.panorama_360_images:
                try:
                    existing_images = json.loads(location.panorama_360_images)
                    existing_images.append(image_url)
                    location.panorama_360_images = json.dumps(existing_images)
                except:
                    location.panorama_360_images = json.dumps([image_url])
            else:
                location.panorama_360_images = json.dumps([image_url])

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'تم رفع الصورة بنجاح',
                'image_url': image_url
            })
        else:
            return jsonify({'success': False, 'message': 'نوع الملف غير مدعوم'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في رفع الصورة: {str(e)}'
        }), 500

@pilgrimage_bp.route('/add-quick-location', methods=['POST'])
def add_quick_location():
    """إضافة موقع سريع من الخريطة"""
    try:
        data = request.get_json()

        name = data.get('name')
        description = data.get('description', '')
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))

        if not name:
            return jsonify({'success': False, 'message': 'اسم الموقع مطلوب'}), 400

        # إنشاء الموقع الجديد
        location = InteractiveLocation(
            name=name,
            description=description,
            latitude=latitude,
            longitude=longitude,
            is_active=True,
            verified=False,  # يحتاج موافقة
            is_featured=False
        )

        db.session.add(location)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'تم إضافة الموقع بنجاح',
            'location_id': location.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إضافة الموقع: {str(e)}'
        }), 500

def allowed_file(filename):
    """التحقق من أن نوع الملف مسموح"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pilgrimage_bp.route('/enhanced-interactive-map')
def enhanced_interactive_map():
    """الخريطة التفاعلية المحسنة مع دعم 360°"""
    return render_template('pilgrimage_360/enhanced_interactive_map.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@pilgrimage_bp.route('/map')
def map_360():
    """خريطة 360 درجة مع إمكانية رفع الصور والتجول"""
    try:
        # إنشاء البيانات التجريبية إذا لم تكن موجودة
        if InteractiveLocation.query.count() == 0:
            create_demo_categories_and_locations()

        # جلب المواقع والفئات
        locations = InteractiveLocation.query.filter_by(is_active=True).all()
        categories = ServiceCategory.query.all()

        return render_template('pilgrimage_360/map_360.html',
                             locations=locations,
                             categories=categories,
                             current_date=datetime.datetime.now().strftime("%Y-%m-%d"))
    except Exception as e:
        flash(f'خطأ في تحميل الخريطة: {str(e)}', 'error')
        return redirect(url_for('pilgrimage_360.index'))

def create_demo_categories_and_locations():
    """إنشاء فئات ومواقع تجريبية"""
    try:
        # إنشاء الفئات
        categories_data = [
            {'name': 'مطاعم', 'name_en': 'Restaurants', 'icon': 'fa-utensils', 'color': '#28a745'},
            {'name': 'مساجد', 'name_en': 'Mosques', 'icon': 'fa-mosque', 'color': '#007bff'},
            {'name': 'خدمات طبية', 'name_en': 'Medical Services', 'icon': 'fa-hospital', 'color': '#dc3545'},
            {'name': 'مراكز تسوق', 'name_en': 'Shopping Centers', 'icon': 'fa-shopping-cart', 'color': '#ffc107'},
            {'name': 'فنادق', 'name_en': 'Hotels', 'icon': 'fa-bed', 'color': '#6f42c1'},
            {'name': 'مواصلات', 'name_en': 'Transportation', 'icon': 'fa-bus', 'color': '#fd7e14'},
        ]

        categories = {}
        for cat_data in categories_data:
            category = ServiceCategory.query.filter_by(name=cat_data['name']).first()
            if not category:
                category = ServiceCategory(**cat_data)
                db.session.add(category)
                db.session.flush()
            categories[cat_data['name']] = category

        # إنشاء المواقع التجريبية
        locations_data = [
            {
                'name': 'مطعم الحرمين',
                'name_en': 'Al Haramain Restaurant',
                'category': 'مطاعم',
                'description': 'مطعم يقدم الأطباق العربية التقليدية',
                'latitude': 21.4225,
                'longitude': 39.8262,
                'address': 'شارع الملك عبدالعزيز، مكة المكرمة',
                'phone': '+966 12 123 4567',
                'operating_hours': '6:00 ص - 12:00 م',
                'price_range': '$$',
                'rating': 4.5,
                'panorama_images': ['/static/360_images/restaurant_360.jpg']
            },
            {
                'name': 'مسجد الحرام',
                'name_en': 'Masjid al-Haram',
                'category': 'مساجد',
                'description': 'المسجد الحرام والكعبة المشرفة',
                'latitude': 21.4225,
                'longitude': 39.8262,
                'address': 'المسجد الحرام، مكة المكرمة',
                'operating_hours': '24 ساعة',
                'rating': 5.0,
                'panorama_images': ['/static/360_images/kaaba_360.jpg']
            },
            {
                'name': 'مستشفى الملك فيصل',
                'name_en': 'King Faisal Hospital',
                'category': 'خدمات طبية',
                'description': 'مستشفى متخصص في خدمة الحجاج والمعتمرين',
                'latitude': 21.4300,
                'longitude': 39.8200,
                'address': 'حي العزيزية، مكة المكرمة',
                'phone': '+966 12 987 6543',
                'operating_hours': '24 ساعة',
                'rating': 4.2,
                'panorama_images': ['/static/360_images/hospital_360.jpg']
            },
            {
                'name': 'مول الحرمين',
                'name_en': 'Al Haramain Mall',
                'category': 'مراكز تسوق',
                'description': 'مركز تسوق حديث بالقرب من الحرم',
                'latitude': 21.4180,
                'longitude': 39.8300,
                'address': 'شارع إبراهيم الخليل، مكة المكرمة',
                'phone': '+966 12 555 0123',
                'operating_hours': '10:00 ص - 12:00 م',
                'price_range': '$$$',
                'rating': 4.0,
                'panorama_images': ['/static/360_images/mall_360.jpg']
            },
            {
                'name': 'فندق دار التوحيد',
                'name_en': 'Dar Al Tawhid Hotel',
                'category': 'فنادق',
                'description': 'فندق فاخر مطل على الحرم المكي',
                'latitude': 21.4210,
                'longitude': 39.8280,
                'address': 'أبراج البيت، مكة المكرمة',
                'phone': '+966 12 777 8888',
                'operating_hours': '24 ساعة',
                'price_range': '$$$$',
                'rating': 4.8,
                'panorama_images': ['/static/360_images/hotel_360.jpg']
            },
            {
                'name': 'محطة الحافلات المركزية',
                'name_en': 'Central Bus Station',
                'category': 'مواصلات',
                'description': 'محطة الحافلات الرئيسية لنقل الحجاج',
                'latitude': 21.4100,
                'longitude': 39.8400,
                'address': 'طريق مكة جدة السريع، مكة المكرمة',
                'phone': '+966 12 333 2222',
                'operating_hours': '5:00 ص - 2:00 ص',
                'rating': 3.8,
                'panorama_images': ['/static/360_images/bus_station_360.jpg']
            }
        ]

        for loc_data in locations_data:
            location = InteractiveLocation.query.filter_by(name=loc_data['name']).first()
            if not location:
                category = categories.get(loc_data['category'])
                location = InteractiveLocation(
                    name=loc_data['name'],
                    name_en=loc_data['name_en'],
                    category_id=category.id if category else None,
                    description=loc_data['description'],
                    latitude=loc_data['latitude'],
                    longitude=loc_data['longitude'],
                    address=loc_data['address'],
                    phone=loc_data.get('phone'),
                    operating_hours=loc_data.get('operating_hours'),
                    price_range=loc_data.get('price_range'),
                    rating=loc_data.get('rating', 0.0),
                    is_active=True,
                    verified=True,
                    is_featured=True
                )

                # إضافة صور 360° إذا كانت متوفرة
                if 'panorama_images' in loc_data:
                    location.panorama_360_images = json.dumps(loc_data['panorama_images'])

                db.session.add(location)

        db.session.commit()
        print("تم إنشاء الفئات والمواقع التجريبية بنجاح!")

    except Exception as e:
        db.session.rollback()
        print(f"خطأ في إنشاء البيانات التجريبية: {str(e)}")
