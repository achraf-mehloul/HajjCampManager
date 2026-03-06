from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user
try:
    from flask_wtf.csrf import csrf_exempt
except ImportError:
    def csrf_exempt(f): return f
import datetime
import json
import os
import uuid
import random
import urllib.request
import urllib.parse
import urllib.error
from advanced_ai_system import get_ai_response, reload_ai_models

# نظام ذكاء اصطناعي مبسط للتجربة
class SimpleAI:
    def __init__(self):
        self.responses = {
            'hajj': [
                "رحلة الحج تتطلب تخطيطاً مسبقاً. أنصح بحجز الحزمة قبل 6 أشهر على الأقل.",
                "للحج، ستحتاج إلى تأشيرة حج وشهادة تطعيم. الحزم تتراوح من 8000 إلى 25000 ريال حسب مستوى الخدمة.",
                "أفضل أوقات الحج هي في الأشهر المحددة شرعياً. يمكنني اقتراح حزم مناسبة لميزانيتك."
            ],
            'umrah': [
                "العمرة يمكن أداؤها في أي وقت. أنصح بتجنب موسم الحج للحصول على أسعار أفضل.",
                "حزم العمرة تبدأ من 2500 ريال للشخص الواحد لمدة 5 أيام. تشمل الإقامة والنقل.",
                "أفضل أوقات العمرة هي في رمضان أو الأشهر الباردة. يمكنني ترتيب رحلة مخصصة لك."
            ],
            'tourism': [
                "السياحة الدينية تشمل زيارة المعالم التاريخية والمساجد المهمة.",
                "يمكنك زيارة مكة والمدينة والطائف في رحلة واحدة. المدة المثلى 7-10 أيام.",
                "الجولات السياحية تتضمن مرشدين متخصصين ونقل مريح بين المواقع."
            ],
            'general': [
                "مرحباً! يمكنني مساعدتك في تخطيط رحلة مثالية للحج أو العمرة أو السياحة الدينية.",
                "أخبرني عن تفضيلاتك: نوع الرحلة، عدد الأشخاص، الميزانية، والمدة المفضلة.",
                "لدينا حزم متنوعة تناسب جميع الميزانيات والاحتياجات. ما نوع الرحلة التي تفكر فيها؟"
            ]
        }

    def generate_response(self, user_input, context_type='general'):
        """توليد رد بسيط بناءً على الكلمات المفتاحية"""
        user_input_lower = user_input.lower()

        # تحديد نوع الاستفسار
        if any(word in user_input_lower for word in ['حج', 'hajj']):
            response_type = 'hajj'
        elif any(word in user_input_lower for word in ['عمرة', 'umrah']):
            response_type = 'umrah'
        elif any(word in user_input_lower for word in ['سياحة', 'tourism', 'جولة']):
            response_type = 'tourism'
        else:
            response_type = context_type if context_type in self.responses else 'general'

        # اختيار رد عشوائي من النوع المحدد
        responses = self.responses.get(response_type, self.responses['general'])
        base_response = random.choice(responses)

        # إضافة معلومات إضافية بناءً على السياق
        if 'ميزانية' in user_input_lower or 'سعر' in user_input_lower or 'تكلفة' in user_input_lower:
            base_response += "\n\nبخصوص الأسعار:\n- حزم اقتصادية: 3000-8000 ريال\n- حزم متوسطة: 8000-15000 ريال\n- حزم مميزة: 15000+ ريال"

        if any(word in user_input_lower for word in ['وقت', 'تاريخ', 'موعد']):
            base_response += "\n\nأفضل الأوقات:\n- العمرة: أي وقت (تجنب موسم الحج)\n- الحج: حسب التواريخ الشرعية\n- السياحة: الأشهر الباردة (نوفمبر-مارس)"

        return {
            'success': True,
            'response': base_response,
            'session_id': str(uuid.uuid4())
        }

# إنشاء مثيل من النظام المبسط
simple_ai = SimpleAI()

# إنشاء Blueprint
trips_ai_bp = Blueprint('trips_ai', __name__, url_prefix='/trips-ai')

@trips_ai_bp.route('/')
def index():
    """الصفحة الرئيسية للرحلات والذكاء الاصطناعي"""
    # بيانات تجريبية مؤقتة
    featured_packages = []
    recent_bookings = []
    total_packages = 3
    total_bookings = 15
    active_trips = 8
    featured_locations = []

    return render_template('trips_ai/index.html',
                         featured_packages=featured_packages,
                         recent_bookings=recent_bookings,
                         total_packages=total_packages,
                         total_bookings=total_bookings,
                         active_trips=active_trips,
                         featured_locations=featured_locations,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@trips_ai_bp.route('/packages')
def packages():
    """صفحة عرض جميع الحزم"""
    # بيانات تجريبية مؤقتة
    packages = []
    package_types = ['hajj', 'umrah', 'tourism']
    durations = [5, 7, 14]

    # الفلاتر
    package_type = request.args.get('type', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    duration = request.args.get('duration', type=int)

    return render_template('trips_ai/packages.html',
                         packages=packages,
                         package_types=package_types,
                         durations=durations,
                         current_filters={
                             'type': package_type,
                             'min_price': min_price,
                             'max_price': max_price,
                             'duration': duration
                         },
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@trips_ai_bp.route('/package/<int:package_id>')
def package_detail(package_id):
    """تفاصيل الحزمة"""
    # بيانات تجريبية مؤقتة
    package = None
    itinerary = []
    reviews = []
    similar_packages = []

    return render_template('trips_ai/package_detail.html',
                         package=package,
                         itinerary=itinerary,
                         reviews=reviews,
                         similar_packages=similar_packages,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@trips_ai_bp.route('/ai-planner')
def ai_planner():
    """مخطط الرحلات بالذكاء الاصطناعي"""
    return render_template('trips_ai/ai_planner.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@trips_ai_bp.route('/api/plan-trip', methods=['POST'])
def api_plan_trip():
    """API لتخطيط الرحلة بالذكاء الاصطناعي"""
    try:
        data = request.get_json()
        user_request = data.get('request', '')
        user_preferences = data.get('preferences', {})

        if not user_request:
            return jsonify({
                'success': False,
                'error': 'يرجى إدخال طلب الرحلة'
            })

        # استخدام النظام المتقدم
        ai_response = get_ai_response(user_request, 'trip_planner')

        # إعداد النتيجة
        result = {
            'success': True,
            'response': ai_response['response'],
            'model_used': ai_response.get('model_used', 'غير محدد')
        }

        # إضافة معلومات إضافية
        suggested_packages = [
            'حج اقتصادي - 14 يوم - 8,000 ريال',
            'عمرة مميزة - 7 أيام - 4,500 ريال',
            'جولة سياحية دينية - 5 أيام - 2,800 ريال'
        ]

        result['processed_data'] = {
            'packages': suggested_packages,
            'costs': {
                'اقتصادي': '3000-8000 ريال للشخص',
                'متوسط': '8000-15000 ريال للشخص',
                'مميز': '15000+ ريال للشخص'
            },
            'dates': ['أفضل الأوقات: نوفمبر - مارس', 'تجنب موسم الحج للعمرة'],
            'tips': ['احجز مبكراً للحصول على أفضل الأسعار', 'تأكد من صحة الوثائق المطلوبة']
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'خطأ في الخادم: {str(e)}'
        })

@trips_ai_bp.route('/chatbot')
def chatbot_page():
    """صفحة الشات بوت"""
    return render_template('trips_ai/chatbot.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@trips_ai_bp.route('/api/chat', methods=['POST'])
def api_chat():
    """API للشات بوت"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id')
        context_type = data.get('context_type', 'general')

        if not message:
            return jsonify({
                'success': False,
                'error': 'يرجى إدخال رسالة'
            })

        # إعادة تحميل النماذج للتأكد من أن النماذج الجديدة متاحة
        reload_ai_models()

        # استخدام النظام المتقدم
        ai_response = get_ai_response(message, 'chatbot')

        result = {
            'success': ai_response.get('success', True),
            'response': ai_response['response'],
            'model_used': ai_response.get('model_used', 'غير محدد'),
            'timestamp': datetime.datetime.now().isoformat()
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'خطأ في الخادم: {str(e)}'
        })

@trips_ai_bp.route('/ai-models')
@login_required
def ai_models():
    """إدارة نماذج الذكاء الاصطناعي"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    try:
        # استيراد النموذج محلياً
        from models import AIModel
        models = AIModel.query.order_by(AIModel.created_at.desc()).all()
    except Exception as e:
        print(f"خطأ في جلب النماذج: {e}")
        models = []

    return render_template('trips_ai/ai_models.html',
                         models=models,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@trips_ai_bp.route('/add-ai-model', methods=['GET', 'POST'])
@login_required
def add_ai_model():
    """إضافة نموذج ذكاء اصطناعي جديد"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # استيراد النموذج محلياً لتجنب مشاكل الاستيراد
            from app import db
            from models import AIModel

            # إنشاء النموذج الجديد
            model = AIModel(
                model_name=request.form['model_name'],
                model_type=request.form['model_type'],
                api_provider=request.form['api_provider'],
                api_key=request.form['api_key'],
                model_version=request.form.get('model_version', ''),
                temperature=float(request.form.get('temperature', 0.7)),
                max_tokens=int(request.form.get('max_tokens', 1000)),
                system_prompt=request.form.get('system_prompt', ''),
                is_active=bool(request.form.get('is_active')),
                is_default=bool(request.form.get('is_default'))
            )

            # إذا كان هذا النموذج افتراضي، إلغاء الافتراضية من النماذج الأخرى من نفس النوع
            if model.is_default:
                existing_defaults = AIModel.query.filter_by(model_type=model.model_type, is_default=True).all()
                for existing in existing_defaults:
                    existing.is_default = False

            db.session.add(model)
            db.session.commit()

            # إعادة تحميل النماذج في النظام
            reload_ai_models()

            flash('تم إضافة النموذج بنجاح', 'success')
            return redirect(url_for('trips_ai.ai_models'))

        except Exception as e:
            try:
                db.session.rollback()
            except:
                pass
            flash(f'خطأ في إضافة النموذج: {str(e)}', 'error')

    return render_template('trips_ai/add_ai_model.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@trips_ai_bp.route('/edit-ai-model/<int:model_id>', methods=['GET', 'POST'])
@login_required
def edit_ai_model(model_id):
    """تعديل نموذج ذكاء اصطناعي موجود"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return redirect(url_for('index'))

    try:
        from app import db
        from models import AIModel
        model = AIModel.query.get_or_404(model_id)

        if request.method == 'POST':
            # تحديث بيانات النموذج
            model.model_name = request.form['model_name']
            model.model_type = request.form['model_type']
            model.api_provider = request.form['api_provider']
            model.api_key = request.form['api_key']
            model.model_version = request.form.get('model_version', '')
            model.temperature = float(request.form.get('temperature', 0.7))
            model.max_tokens = int(request.form.get('max_tokens', 1000))
            model.system_prompt = request.form.get('system_prompt', '')
            model.is_active = bool(request.form.get('is_active'))
            
            new_is_default = bool(request.form.get('is_default'))
            
            # إذا تم تحديد هذا النموذج كافتراضي، إلغاء الافتراضية من النماذج الأخرى من نفس النوع
            if new_is_default and not model.is_default:
                AIModel.query.filter_by(model_type=model.model_type, is_default=True).update({'is_default': False})
            
            model.is_default = new_is_default

            db.session.commit()
            
            # إعادة تحميل النماذج
            reload_ai_models()
            
            flash('تم تحديث النموذج بنجاح', 'success')
            return redirect(url_for('trips_ai.ai_models'))

        return render_template('trips_ai/edit_ai_model.html',
                             model=model,
                             current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        flash(f'خطأ في تعديل النموذج: {str(e)}', 'error')
        return redirect(url_for('trips_ai.ai_models'))

@trips_ai_bp.route('/delete-ai-model/<int:model_id>')
@login_required
def delete_ai_model(model_id):
    """حذف نموذج ذكاء اصطناعي"""
    if current_user.role != 'admin':
        flash('غير مصرح لك بهذا الإجراء', 'error')
        return redirect(url_for('index'))

    try:
        from app import db
        from models import AIModel
        model = AIModel.query.get_or_404(model_id)
        
        db.session.delete(model)
        db.session.commit()
        
        # إعادة تحميل النماذج
        reload_ai_models()
        
        flash('تم حذف النموذج بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ في حذف النموذج: {str(e)}', 'error')

    return redirect(url_for('trips_ai.ai_models'))

@trips_ai_bp.route('/api/test-ai-model', methods=['POST'])
@login_required
def api_test_ai_model():
    """اختبار نموذج ذكاء اصطناعي"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'غير مصرح'}), 403

    try:
        data = request.get_json()
        model_id = data.get('model_id')
        test_prompt = data.get('test_prompt') or data.get('test_message') or 'مرحباً، كيف يمكنك مساعدتي في تخطيط رحلة حج؟'

        if not model_id:
            return jsonify({'success': False, 'error': 'معرف النموذج مطلوب'}), 400

        # إعادة تحميل النماذج للتأكد من أحدث البيانات
        reload_ai_models()

        # اختبار النموذج
        ai_response = get_ai_response(test_prompt, 'chatbot', int(model_id))

        return jsonify({
            'success': True,
            'response': ai_response['response'],
            'model_used': ai_response.get('model_used', 'غير محدد'),
            'test_prompt': test_prompt,
            'timestamp': datetime.datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'خطأ في اختبار النموذج: {str(e)}'
        }), 500

@trips_ai_bp.route('/custom-trip', methods=['GET', 'POST'])
def custom_trip():
    """طلب رحلة مخصصة"""
    if request.method == 'POST':
        # إنشاء رقم الرحلة تجريبي
        trip_number = f"CT-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        flash(f'تم إرسال طلبك بنجاح. رقم الطلب: {trip_number} (تجريبي)', 'success')
        return redirect(url_for('trips_ai.custom_trip_status', trip_number=trip_number))

    return render_template('trips_ai/custom_trip.html',
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

@trips_ai_bp.route('/smart-guide')
def smart_guide_page():
    """صفحة الإرشاد المكاني الذكي - خريطة تفاعلية مع صوت وتوجيه للمشاة"""
    return render_template('trips_ai/smart_guide.html')

@trips_ai_bp.route('/custom-trip-status/<trip_number>')
def custom_trip_status(trip_number):
    """حالة الرحلة المخصصة"""
    # بيانات تجريبية مؤقتة
    custom_trip = {
        'trip_number': trip_number,
        'status': 'pending',
        'customer_name': 'عميل تجريبي',
        'trip_type': 'umrah',
        'number_of_travelers': 2,
        'request_date': datetime.datetime.now()
    }

    return render_template('trips_ai/custom_trip_status.html',
                         custom_trip=custom_trip,
                         current_date=datetime.datetime.now().strftime("%Y-%m-%d"))

def _call_ai_extract_destination(user_message):
    """استخدام النظام المتقدم لاستخراج اسم الوجهة من نص المستخدم."""
    prompt = (
        'أنت خبير إرشاد مكاني. استخرج اسم المكان أو الوجهة الوحيد من هذا الطلب. '
        'أعد كلمة أو عبارة قصيرة جداً فقط (مثال: المسجد الحرام، جمرة العقبة، مكة). '
        'لا تضف شرحاً أو جمل إضافية. النص:\n' + (user_message or '').strip()
    )
    try:
        from advanced_ai_system import get_ai_response
        resp = get_ai_response(prompt, 'voice_assistant')
        
        # إذا استخدم النظام الاحتياطي الذكي أو المحاكاة، فهذا يعني أن النماذج معطلة
        # والنظام الاحتياطي سيرجع نصاً طويلاً للمحادثة بدلاً من كلمة واحدة!
        model_used = resp.get('model_used', '')
        if 'احتياطي' in model_used or 'محاكاة' in model_used:
            print(f"DEBUG: AI failed to extract destination, falling back to raw input.")
            return user_message.strip()

        if resp.get('success'):
            text = resp['response'].strip()
            # تنظيف أي علامات تنصيص زائدة
            text = text.replace('"', '').replace("'", "").replace('.', '')
            return text
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"Error in extract destination text: {e}")
        
    return user_message.strip()


def _geocode_nominatim(query):
    """جيو-كود عبر Nominatim."""
    q = urllib.parse.quote(query)
    url = f'https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1'
    req = urllib.request.Request(url, headers={'User-Agent': 'MDB-SmartGuide/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        results = json.loads(resp.read().decode())
    if not results:
        return None, None, query
    p = results[0]
    return float(p['lat']), float(p['lon']), p.get('display_name', query)


def _translate_maneuver(stype, mod):
    """ترجمة نوع المناورة واتجاهها من OSRM إلى اللغة العربية."""
    types = {
        'depart': 'ابدأ السير',
        'turn': 'انعطف',
        'continue': 'استمر في السير',
        'new name': 'اتجه نحو',
        'merge': 'اندمج في الطريق',
        'on ramp': 'ادخل المنحدر',
        'off ramp': 'اخرج من المنحدر',
        'fork': 'مفترق طرق',
        'end of road': 'نهاية الطريق',
        'use lane': 'التزم الحارة',
        'rotary': 'دوار',
        'roundabout': 'دوار',
        'arrive': 'وصلت إلى وجهتك'
    }
    
    modifiers = {
        'uturn': 'للدوران للخلف',
        'sharp right': 'يميناً حاداً',
        'right': 'يميناً',
        'slight right': 'يميناً قليلاً',
        'straight': 'للأمام',
        'slight left': 'يساراً قليلاً',
        'left': 'يساراً',
        'sharp left': 'يساراً حاداً'
    }
    
    t = types.get(stype, stype)
    m = modifiers.get(mod, '')
    
    if stype == 'depart':
        return "ابدأ السير"
    if stype == 'arrive':
        return "وصلت إلى وجهتك"
    if m:
        return f"{t} {m}"
    return t


def _get_osrm_walking_route(orig_lat, orig_lng, dest_lat, dest_lng):
    """الحصول على مسار مشاة من OSRM."""
    coords = f'{orig_lng},{orig_lat};{dest_lng},{dest_lat}'
    url = f'https://router.project-osrm.org/route/v1/foot/{coords}?overview=full&geometries=geojson&steps=true'
    req = urllib.request.Request(url, headers={'User-Agent': 'MDB-SmartGuide/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data.get('code') != 'Ok':
            return None, []
        
        route = data.get('routes', [{}])[0]
        geojson = route.get('geometry', {})
        steps = []
        for leg in route.get('legs', []):
            for s in leg.get('steps', []):
                mani = s.get('maneuver', {})
                stype = mani.get('type', '')
                mod = mani.get('modifier', '')
                # محاولة الحصول على تعليمات جاهزة أو ترجمتها يدوياً
                instr = mani.get('instruction', '')
                if not instr:
                    instr = _translate_maneuver(stype, mod)
                
                dist = s.get('distance', 0)
                maneuver_loc = mani.get('location', [0, 0])
                name = s.get('name', '')
                
                if instr or name:
                    steps.append({
                        'instruction': instr or f"اتجه نحو {name}" if name else "استمر",
                        'distance': dist,
                        'name': name,
                        'lat': maneuver_loc[1],
                        'lng': maneuver_loc[0]
                    })
        return geojson, steps
    except Exception as e:
        print(f"DEBUG OSRM Error: {e}")
        return None, []


@trips_ai_bp.route('/api/smart-spatial-guide', methods=['POST'])
@csrf_exempt
def api_smart_spatial_guide():
    """
    إرشاد مكاني ذكي: يفهم كلام المستخدم، يعرض مسار مشاة على الخريطة، مع إرشادات صوتية.
    يدعم OpenRouter و AI/ML API لاستخراج الوجهة من النص.
    """
    try:
        data = request.get_json() or {}
        message = (data.get('message') or data.get('destination') or '').strip()
        if not message:
            return jsonify({
                'success': False,
                'error': 'يرجى التحدث أو كتابة المكان الذي تريد الوصول إليه (مثال: وجهني للمسجد الحرام)'
            }), 400

        origin_lat = data.get('origin_lat')
        origin_lng = data.get('origin_lng')
        if origin_lat is None or origin_lng is None:
            origin_lat, origin_lng = 21.4225, 39.8262

        # استخراج الوجهة بالذكاء الاصطناعي أو استخدام النص كما هو
        destination_query = _call_ai_extract_destination(message)
        if not destination_query:
            destination_query = message

        dest_lat, dest_lng, display_name = _geocode_nominatim(destination_query)
        if dest_lat is None:
            return jsonify({
                'success': False,
                'error': f'لم يتم العثور على موقع "{destination_query}". جرّب اسماً أوضح.'
            }), 404

        route_geojson, steps = _get_osrm_walking_route(origin_lat, origin_lng, dest_lat, dest_lng)
        
        # إضافة خطوة افتراضية إذا لم توجد خطوات ولكن يوجد مسار (للمسافات الطويلة)
        if route_geojson and not steps:
            steps.append({
                'instruction': f'اتجه نحو {display_name}',
                'distance': 0,
                'name': display_name,
                'lat': dest_lat,
                'lng': dest_lng
            })

        if not route_geojson:
            return jsonify({
                'success': True,
                'destination': destination_query,
                'display_name': display_name,
                'lat': dest_lat,
                'lng': dest_lng,
                'route_geojson': None,
                'steps': [],
                'ai_message': f'الوجهة: {display_name}. لم يتم العثور على مسار مشاة مباشر.',
                'directions_url': (
                    f'https://www.google.com/maps/dir/?api=1'
                    f'&destination={dest_lat},{dest_lng}'
                    f'&origin={origin_lat},{origin_lng}'
                    '&travelmode=walking'
                ),
            })

        ai_msg_parts = [f'اتبع المسار للمشي حتى {display_name}.']
        for i, s in enumerate(steps[:8], 1):
            ai_msg_parts.append(f'{i}. {s.get("instruction", "")}')
        ai_message = '\n'.join(ai_msg_parts)

        dir_url = (
            f'https://www.google.com/maps/dir/?api=1'
            f'&destination={dest_lat},{dest_lng}'
            f'&origin={origin_lat},{origin_lng}'
            '&travelmode=walking'
        )

        return jsonify({
            'success': True,
            'destination': destination_query,
            'display_name': display_name,
            'lat': dest_lat,
            'lng': dest_lng,
            'route_geojson': route_geojson,
            'steps': steps,
            'ai_message': ai_message,
            'directions_url': dir_url,
        })
    except urllib.error.HTTPError as e:
        return jsonify({'success': False, 'error': f'خطأ في خدمة الخرائط: {e.code}'}), 502
    except urllib.error.URLError as e:
        return jsonify({'success': False, 'error': 'تعذّر الاتصال. تحقق من الإنترنت.'}), 502
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trips_ai_bp.route('/api/spatial-guide', methods=['POST'])
@csrf_exempt
def api_spatial_guide():
    """
    إرشاد مكاني: جيو-كود الوجهة وإرجاع رابط الخريطة والاتجاهات.
    يستخدم Nominatim (OpenStreetMap) مجاناً ولا يحتاج مفتاح API.
    """
    try:
        data = request.get_json() or {}
        destination_query = (data.get('destination') or '').strip()
        if not destination_query:
            return jsonify({
                'success': False,
                'error': 'يرجى تحديد المكان الذي تريد الوصول إليه (مثال: المسجد الحرام، جمرة العقبة)'
            }), 400

        origin_lat = data.get('origin_lat')
        origin_lng = data.get('origin_lng')
        # افتراضي: مكة المكرمة إذا لم يُرسل موقع المستخدم
        if origin_lat is None or origin_lng is None:
            origin_lat, origin_lng = 21.4225, 39.8262  # مكة

        # جيو-كود عبر Nominatim (يطلب User-Agent)
        q = urllib.parse.quote(destination_query)
        url = f'https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'MDB-Dashboard-SpatialGuide/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode())

        if not results:
            return jsonify({
                'success': False,
                'error': f'لم يتم العثور على موقع مطابق لـ "{destination_query}". جرّب صياغة أخرى أو اسم مكان أوضح.'
            }), 404

        place = results[0]
        dest_lat = float(place['lat'])
        dest_lng = float(place['lon'])
        display_name = place.get('display_name', destination_query)

        # رابط Google Maps للاتجاهات (يعمل بدون مفتاح API)
        dir_url = (
            'https://www.google.com/maps/dir/?api=1'
            f'&destination={dest_lat},{dest_lng}'
            f'&origin={origin_lat},{origin_lng}'
            '&travelmode=walking'
        )
        # رابط فتح الوجهة فقط على الخريطة
        map_url = f'https://www.google.com/maps?q={dest_lat},{dest_lng}'

        return jsonify({
            'success': True,
            'destination': destination_query,
            'display_name': display_name,
            'lat': dest_lat,
            'lng': dest_lng,
            'directions_url': dir_url,
            'map_url': map_url,
            'origin_used': bool(data.get('origin_lat') is not None),
        })
    except urllib.error.HTTPError as e:
        return jsonify({'success': False, 'error': f'خطأ في خدمة الخرائط: {e.code}'}), 502
    except urllib.error.URLError as e:
        return jsonify({'success': False, 'error': 'تعذّر الاتصال بخدمة المواقع. تحقق من الإنترنت.'}), 502
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




