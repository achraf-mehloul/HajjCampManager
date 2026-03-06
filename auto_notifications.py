#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نظام الإشعارات التلقائية للمسؤولين
"""

import datetime
from models import db, User, Issue, InspectionRequest, Contractor
from notifications import notify_contractor

def notify_admins_new_issue(issue):
    """إرسال إشعار للمسؤولين عند إنشاء بلاغ جديد"""
    try:
        # الحصول على جميع المسؤولين النشطين
        admins = User.query.filter_by(role='admin', is_active=True).all()
        
        # إنشاء رسالة الإشعار
        message = f"""
        تم إنشاء بلاغ جديد:
        
        رقم البلاغ: {issue.id}
        العنوان: {issue.title}
        اللوحة: {issue.panel.mdb} ({issue.panel.maximo_tag})
        المنطقة: {issue.panel.area_name}
        الأولوية: {issue.priority}
        نوع المشكلة: {issue.issue_type}
        
        الوصف: {issue.description}
        
        تاريخ الإنشاء: {issue.created_at.strftime('%Y-%m-%d %H:%M')}
        المنشئ: {issue.created_by_user.name if issue.created_by_user else 'غير محدد'}
        """
        
        # إرسال الإشعار لكل مسؤول
        for admin in admins:
            # التحقق من أن المسؤول لديه صلاحية للوصول إلى هذه المنطقة
            if admin.has_area_access(issue.panel.area_name):
                try:
                    # يمكن إضافة إرسال إيميل أو رسالة SMS هنا
                    print(f"إشعار للمسؤول {admin.name}: بلاغ جديد رقم {issue.id}")
                    
                    # إضافة الإشعار إلى قاعدة البيانات (إذا كان هناك نموذج للإشعارات)
                    # notification = Notification(
                    #     user_id=admin.id,
                    #     title=f"بلاغ جديد رقم {issue.id}",
                    #     message=message,
                    #     type='new_issue',
                    #     related_id=issue.id
                    # )
                    # db.session.add(notification)
                    
                except Exception as e:
                    print(f"خطأ في إرسال الإشعار للمسؤول {admin.name}: {str(e)}")
        
        # حفظ التغييرات
        # db.session.commit()
        
    except Exception as e:
        print(f"خطأ في إرسال الإشعارات للمسؤولين: {str(e)}")

def notify_admins_new_inspection_request(inspection_request):
    """إرسال إشعار للمسؤولين عند إنشاء طلب فحص جديد"""
    try:
        # الحصول على جميع المسؤولين النشطين
        admins = User.query.filter_by(role='admin', is_active=True).all()
        
        # إنشاء رسالة الإشعار
        message = f"""
        تم إنشاء طلب فحص جديد:
        
        رقم الطلب: {inspection_request.request_number}
        العنوان: {inspection_request.title}
        اللوحة: {inspection_request.panel.mdb} ({inspection_request.panel.maximo_tag})
        المنطقة: {inspection_request.panel.area_name}
        الأولوية: {inspection_request.priority}
        نوع الطلب: {inspection_request.request_type.name if inspection_request.request_type else 'غير محدد'}
        
        الوصف: {inspection_request.description}
        
        تاريخ الإنشاء: {inspection_request.created_at.strftime('%Y-%m-%d %H:%M')}
        تاريخ الاستحقاق: {inspection_request.due_date.strftime('%Y-%m-%d') if inspection_request.due_date else 'غير محدد'}
        المنشئ: {inspection_request.created_by_user.name if inspection_request.created_by_user else 'غير محدد'}
        """
        
        # إرسال الإشعار لكل مسؤول
        for admin in admins:
            # التحقق من أن المسؤول لديه صلاحية للوصول إلى هذه المنطقة
            if admin.has_area_access(inspection_request.panel.area_name):
                try:
                    # يمكن إضافة إرسال إيميل أو رسالة SMS هنا
                    print(f"إشعار للمسؤول {admin.name}: طلب فحص جديد رقم {inspection_request.request_number}")
                    
                    # إضافة الإشعار إلى قاعدة البيانات (إذا كان هناك نموذج للإشعارات)
                    # notification = Notification(
                    #     user_id=admin.id,
                    #     title=f"طلب فحص جديد رقم {inspection_request.request_number}",
                    #     message=message,
                    #     type='new_inspection_request',
                    #     related_id=inspection_request.id
                    # )
                    # db.session.add(notification)
                    
                except Exception as e:
                    print(f"خطأ في إرسال الإشعار للمسؤول {admin.name}: {str(e)}")
        
        # حفظ التغييرات
        # db.session.commit()
        
    except Exception as e:
        print(f"خطأ في إرسال الإشعارات للمسؤولين: {str(e)}")

def notify_responsible_contractor(issue_or_request):
    """إرسال إشعار للمقاول المسؤول عن اللوحة"""
    try:
        panel = issue_or_request.panel
        
        # البحث عن المقاول المسؤول عن اللوحة
        responsible_contractor = None
        
        if panel.responsible_contractor_id:
            responsible_contractor = Contractor.query.get(panel.responsible_contractor_id)
        else:
            # البحث عن المقاول المسؤول عن المنطقة
            contractors = Contractor.query.filter_by(is_active=True).all()
            for contractor in contractors:
                from app import get_contractor_areas
                contractor_areas = get_contractor_areas(contractor.id, True)  # افتراض أنه مدير
                if panel.area_name in contractor_areas:
                    responsible_contractor = contractor
                    break
        
        if responsible_contractor:
            # إرسال الإشعار للمقاول
            if isinstance(issue_or_request, Issue):
                notify_contractor(issue_or_request.id, responsible_contractor.id, 'new_issue')
            else:  # InspectionRequest
                notify_contractor(issue_or_request.id, responsible_contractor.id, 'new_inspection_request')
                
    except Exception as e:
        print(f"خطأ في إرسال الإشعار للمقاول المسؤول: {str(e)}")

def send_priority_alerts(issue_or_request):
    """إرسال تنبيهات عاجلة للحالات عالية الأولوية"""
    try:
        if issue_or_request.priority == 'عالي':
            # الحصول على جميع المسؤولين والمقاولين
            admins = User.query.filter_by(role='admin', is_active=True).all()
            contractors = User.query.filter_by(role='contractor', is_active=True).all()
            
            urgent_message = f"""
            تنبيه عاجل - أولوية عالية!
            
            {'بلاغ' if isinstance(issue_or_request, Issue) else 'طلب فحص'} عالي الأولوية:
            
            الرقم: {issue_or_request.id if isinstance(issue_or_request, Issue) else issue_or_request.request_number}
            العنوان: {issue_or_request.title}
            اللوحة: {issue_or_request.panel.mdb}
            المنطقة: {issue_or_request.panel.area_name}
            
            يتطلب اهتماماً فورياً!
            """
            
            # إرسال للمسؤولين
            for admin in admins:
                if admin.has_area_access(issue_or_request.panel.area_name):
                    print(f"تنبيه عاجل للمسؤول {admin.name}")
            
            # إرسال للمقاولين المسؤولين عن المنطقة
            for contractor_user in contractors:
                if contractor_user.contractor_id:
                    from app import get_contractor_areas
                    contractor_areas = get_contractor_areas(contractor_user.contractor_id, contractor_user.is_manager)
                    if issue_or_request.panel.area_name in contractor_areas:
                        print(f"تنبيه عاجل للمقاول {contractor_user.name}")
                        
    except Exception as e:
        print(f"خطأ في إرسال التنبيهات العاجلة: {str(e)}")

def auto_assign_to_contractor(issue_or_request):
    """تخصيص تلقائي للمقاول المسؤول"""
    try:
        panel = issue_or_request.panel
        
        # البحث عن المقاول المسؤول
        if panel.responsible_contractor_id:
            if isinstance(issue_or_request, Issue):
                issue_or_request.contractor_id = panel.responsible_contractor_id
            else:  # InspectionRequest
                issue_or_request.assigned_contractor_id = panel.responsible_contractor_id
        else:
            # البحث عن المقاول المسؤول عن المنطقة
            contractors = Contractor.query.filter_by(is_active=True).all()
            for contractor in contractors:
                from app import get_contractor_areas
                contractor_areas = get_contractor_areas(contractor.id, True)
                if panel.area_name in contractor_areas:
                    if isinstance(issue_or_request, Issue):
                        issue_or_request.contractor_id = contractor.id
                    else:  # InspectionRequest
                        issue_or_request.assigned_contractor_id = contractor.id
                    break
        
        db.session.commit()
        
    except Exception as e:
        print(f"خطأ في التخصيص التلقائي: {str(e)}")

def process_new_issue(issue):
    """معالجة شاملة للبلاغ الجديد"""
    try:
        # إرسال إشعارات للمسؤولين
        notify_admins_new_issue(issue)
        
        # إرسال إشعار للمقاول المسؤول
        notify_responsible_contractor(issue)
        
        # إرسال تنبيهات عاجلة إذا كانت الأولوية عالية
        send_priority_alerts(issue)
        
        # تخصيص تلقائي للمقاول
        auto_assign_to_contractor(issue)
        
    except Exception as e:
        print(f"خطأ في معالجة البلاغ الجديد: {str(e)}")

def process_new_inspection_request(inspection_request):
    """معالجة شاملة لطلب الفحص الجديد"""
    try:
        # إرسال إشعارات للمسؤولين
        notify_admins_new_inspection_request(inspection_request)
        
        # إرسال إشعار للمقاول المسؤول
        notify_responsible_contractor(inspection_request)
        
        # إرسال تنبيهات عاجلة إذا كانت الأولوية عالية
        send_priority_alerts(inspection_request)
        
        # تخصيص تلقائي للمقاول
        auto_assign_to_contractor(inspection_request)
        
    except Exception as e:
        print(f"خطأ في معالجة طلب الفحص الجديد: {str(e)}")
