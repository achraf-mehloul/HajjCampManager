import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import get_setting, SystemSettings, Contractor, ContractorTeamMember, MDBPanel, Alert
import datetime
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('notifications')

def send_email_notification(recipient_email, subject, html_content):
    """
    إرسال بريد إلكتروني باستخدام SMTP

    Args:
        recipient_email (str): عنوان البريد الإلكتروني للمستلم
        subject (str): عنوان البريد الإلكتروني
        html_content (str): محتوى البريد الإلكتروني بتنسيق HTML

    Returns:
        bool: نجاح أو فشل إرسال البريد الإلكتروني
    """
    try:
        # الحصول على إعدادات البريد الإلكتروني من قاعدة البيانات
        smtp_server = get_setting('smtp_server', '')
        smtp_port = int(get_setting('smtp_port', '587'))
        smtp_username = get_setting('smtp_username', '')
        smtp_password = get_setting('smtp_password', '')
        sender_email = get_setting('sender_email', '')

        # التحقق من وجود الإعدادات المطلوبة
        if not all([smtp_server, smtp_port, smtp_username, smtp_password, sender_email]):
            logger.error("إعدادات البريد الإلكتروني غير مكتملة")
            return False

        # إنشاء رسالة البريد الإلكتروني
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = recipient_email

        # إضافة محتوى HTML
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

        # إنشاء اتصال آمن
        context = ssl.create_default_context()

        # إرسال البريد الإلكتروني
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        logger.info(f"تم إرسال البريد الإلكتروني بنجاح إلى {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"خطأ في إرسال البريد الإلكتروني: {str(e)}")
        return False

def send_sms_notification(phone_number, message):
    """
    إرسال رسالة نصية (SMS)

    Args:
        phone_number (str): رقم الهاتف المستلم
        message (str): نص الرسالة

    Returns:
        bool: نجاح أو فشل إرسال الرسالة
    """
    # هذه الدالة تحتاج إلى تكامل مع خدمة إرسال الرسائل النصية
    # يمكن استخدام خدمات مثل Twilio أو Vonage (Nexmo) أو غيرها

    # مثال على استخدام Twilio (يتطلب تثبيت مكتبة twilio)
    try:
        # الحصول على إعدادات خدمة الرسائل النصية
        sms_provider = get_setting('sms_provider', 'none')

        if sms_provider == 'none':
            logger.warning("لم يتم تكوين خدمة إرسال الرسائل النصية")
            return False

        # هنا يمكن إضافة كود للتكامل مع خدمة الرسائل النصية المختارة
        logger.info(f"محاولة إرسال رسالة نصية إلى {phone_number}")

        # تنفيذ وهمي للتوضيح فقط
        logger.info(f"تم إرسال رسالة نصية بنجاح إلى {phone_number}")
        return True

    except Exception as e:
        logger.error(f"خطأ في إرسال الرسالة النصية: {str(e)}")
        return False

def notify_contractor(contractor, subject, html_content, plain_text=None):
    """
    إرسال إشعار للمقاول وأعضاء مجموعته وفرقه باستخدام الطريقة المفضلة

    Args:
        contractor (Contractor): كائن المقاول
        subject (str): عنوان الإشعار
        html_content (str): محتوى الإشعار بتنسيق HTML
        plain_text (str, optional): نص عادي للرسائل النصية

    Returns:
        bool: نجاح أو فشل إرسال الإشعار
    """
    # تحديد طريقة الإشعار
    notification_method = get_setting('notification_method', 'email')

    success = False

    # إرسال إشعار للمقاول الرئيسي
    if notification_method == 'email' or notification_method == 'both':
        if contractor.email:
            success = send_email_notification(contractor.email, subject, html_content)
        else:
            logger.warning(f"المقاول {contractor.name} ليس لديه بريد إلكتروني")

    if notification_method == 'sms' or notification_method == 'both':
        if contractor.phone:
            # استخدام النص العادي للرسائل النصية إذا تم توفيره
            sms_text = plain_text if plain_text else f"{subject}: يرجى مراجعة البريد الإلكتروني للتفاصيل"
            sms_success = send_sms_notification(contractor.phone, sms_text)
            success = success or sms_success
        else:
            logger.warning(f"المقاول {contractor.name} ليس لديه رقم هاتف")

    # إرسال إشعارات لأعضاء مجموعة المقاول (الأعضاء غير المرتبطين بفرق)
    try:
        # الحصول على أعضاء المجموعة النشطين غير المرتبطين بفرق
        team_members = ContractorTeamMember.query.filter_by(contractor_id=contractor.id, is_active=True, team_id=None).all()

        for member in team_members:
            # إرسال بريد إلكتروني
            if notification_method == 'email' or notification_method == 'both':
                if member.email:
                    member_email_success = send_email_notification(member.email, subject, html_content)
                    success = success or member_email_success
                    logger.info(f"تم إرسال إشعار بريد إلكتروني إلى عضو المجموعة {member.name}")

            # إرسال رسالة نصية
            if notification_method == 'sms' or notification_method == 'both':
                if member.phone:
                    sms_text = plain_text if plain_text else f"{subject}: يرجى مراجعة البريد الإلكتروني للتفاصيل"
                    member_sms_success = send_sms_notification(member.phone, sms_text)
                    success = success or member_sms_success
                    logger.info(f"تم إرسال إشعار رسالة نصية إلى عضو المجموعة {member.name}")

    except Exception as e:
        logger.error(f"خطأ في إرسال الإشعارات لأعضاء مجموعة المقاول: {str(e)}")

    # إرسال إشعارات لأعضاء فرق المقاول
    try:
        # الحصول على فرق المقاول النشطة
        teams = ContractorTeam.query.filter_by(contractor_id=contractor.id, is_active=True).all()

        for team in teams:
            # الحصول على أعضاء الفريق النشطين
            team_members = ContractorTeamMember.query.filter_by(team_id=team.id, is_active=True).all()

            for member in team_members:
                # إرسال بريد إلكتروني
                if notification_method == 'email' or notification_method == 'both':
                    if member.email:
                        member_email_success = send_email_notification(member.email, subject, html_content)
                        success = success or member_email_success
                        logger.info(f"تم إرسال إشعار بريد إلكتروني إلى عضو الفريق {member.name} في فريق {team.name}")

                # إرسال رسالة نصية
                if notification_method == 'sms' or notification_method == 'both':
                    if member.phone:
                        sms_text = plain_text if plain_text else f"{subject}: يرجى مراجعة البريد الإلكتروني للتفاصيل"
                        member_sms_success = send_sms_notification(member.phone, sms_text)
                        success = success or member_sms_success
                        logger.info(f"تم إرسال إشعار رسالة نصية إلى عضو الفريق {member.name} في فريق {team.name}")

    except Exception as e:
        logger.error(f"خطأ في إرسال الإشعارات لأعضاء فرق المقاول: {str(e)}")

    return success

def create_google_maps_url(x_coordinate, y_coordinate):
    """
    إنشاء رابط خرائط Google من الإحداثيات

    Args:
        x_coordinate (float): خط الطول
        y_coordinate (float): خط العرض

    Returns:
        str: رابط خرائط Google
    """
    if x_coordinate and y_coordinate:
        return f"https://www.google.com/maps?q={y_coordinate},{x_coordinate}"
    return None
