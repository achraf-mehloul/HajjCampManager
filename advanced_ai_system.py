"""
نظام الذكاء الاصطناعي المتقدم
يدعم مزودين متعددين: Gemini, OpenAI, OpenRouter, AI/ML API
"""

try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

import json
import datetime
import os
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any
import logging
import random

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedAISystem:
    """نظام الذكاء الاصطناعي المتقدم"""
    
    def __init__(self):
        self.models = {}
        self._loaded = False
        self._last_load_time = None  # وقت آخر تحميل للنماذج
        self._load_interval = 60  # إعادة تحميل كل 60 ثانية تلقائياً
        # لا نحمّل النماذج هنا - app context غير متاح وقت الاستيراد
    
    def load_models(self):
        """تحميل النماذج من قاعدة البيانات"""
        try:
            from models import AIModel
            active_models = AIModel.query.filter_by(is_active=True).all()
            
            # تصفير القائمة لتجنب النماذج القديمة (نحتفظ فقط بالنماذج السالبة من .env)
            old_env_models = {k: v for k, v in self.models.items() if isinstance(k, int) and k < 0}
            self.models = old_env_models
            
            for model in active_models:
                self.models[model.id] = {
                    'id': model.id,
                    'name': model.model_name,
                    'type': model.model_type,
                    'provider': model.api_provider,
                    'api_key': model.api_key,
                    'model_version': model.model_version,
                    'temperature': model.temperature,
                    'max_tokens': model.max_tokens,
                    'system_prompt': model.system_prompt,
                    'is_default': model.is_default,
                    'model_obj': model
                }
            
            self._loaded = True
            self._last_load_time = datetime.datetime.now()
            logger.info(f"تم تحميل {len([k for k in self.models if k > 0])} نموذج من قاعدة البيانات")
            
        except RuntimeError:
            # خارج app context - سيتم التحميل لاحقاً تلقائياً
            pass
        except Exception as e:
            logger.error(f"خطأ في تحميل النماذج: {e}")
            print(f"DEBUG load_models error: {e}")

    def _ensure_loaded(self):
        """تحميل كسول مع تحديث دوري - يُحمَّل عند أول طلب، ويُجدَّد كل دقيقة"""
        now = datetime.datetime.now()
        should_reload = (
            not self._loaded or
            self._last_load_time is None or
            (now - self._last_load_time).total_seconds() > self._load_interval
        )
        if should_reload:
            self.load_models()
            # تحميل نماذج البيئة كاحتياطي لتغطية الأنواع الناقصة
            self._load_from_env()

    def _load_from_env(self):
        """تحميل نماذج AI مؤقتة من .env إذا لم تكن DB مضبوطة"""
        # 1. OpenRouter (شامل وصوت)
        o_key = os.environ.get('OPENROUTER_API_KEY', '')
        if o_key and len(o_key) > 10:
            self.models[-1] = {
                'id': -1, 'name': 'OpenRouter Omni', 'type': 'chatbot', 'provider': 'openrouter',
                'api_key': o_key, 'model_version': 'openai/gpt-4o-mini', 'temperature': 0.7, 'max_tokens': 1500,
                'system_prompt': 'أنت مساعد ذكي لإدارة مخيمات الحج. أجب بالعربية باحترافية.', 'is_default': False, 'model_obj': None
            }
            self.models[-4] = {
                'id': -4, 'name': 'OpenRouter Voice', 'type': 'voice_assistant', 'provider': 'openrouter',
                'api_key': o_key, 'model_version': 'openai/gpt-4o-mini-audio', 'temperature': 0.7, 'max_tokens': 1500,
                'system_prompt': 'أنت مساعد صوتي سريع. أجب بالعربية باختصار شديد.', 'is_default': False, 'model_obj': None
            }

        # 2. AI/ML API (تحليل بيانات)
        a_key = os.environ.get('AIML_API_KEY', '')
        if a_key and len(a_key) > 5:
            self.models[-2] = {
                'id': -2, 'name': 'AIML Analyzer', 'type': 'issue_analyzer', 'provider': 'aimlapi',
                'api_key': a_key, 'model_version': 'gpt-4o-mini', 'temperature': 0.3, 'max_tokens': 1500,
                'system_prompt': 'أنت محلل بيانات متخصص في بلاغات الكهرباء. حلل الأرقام بدقة وأجب بالعربية.', 'is_default': False, 'model_obj': None
            }

        # 3. Gemini (تخطيط رحلات)
        g_key = os.environ.get('GEMINI_API_KEY', '')
        if g_key and len(g_key) > 10:
            self.models[-3] = {
                'id': -3, 'name': 'Gemini Planner', 'type': 'trip_planner', 'provider': 'google',
                'api_key': g_key, 'model_version': 'gemini-1.5-flash', 'temperature': 0.7, 'max_tokens': 2000,
                'system_prompt': 'أنت خبير سياحي لتخطيط رحلات الحج والعمرة. صمم جداول رائعة بالعربية.', 'is_default': False, 'model_obj': None
            }
        
        logger.info(f"تم تحميل نماذج افتراضية ذكية من .env")
    
    def get_default_model(self, model_type: str = 'chatbot') -> Optional[Dict]:
        """الحصول على النموذج الافتراضي لنوع معين"""
        self._ensure_loaded()
        
        # 1. البحث عن موجه افتراضي محدد لهذا النوع
        for model_id, model_data in self.models.items():
            if model_data['type'] == model_type and model_data['is_default']:
                return model_data
                
        # 2. إذا لم يوجد افتراضي، خذ أو نموذج من نفس النوع
        for model_id, model_data in self.models.items():
            if model_data['type'] == model_type:
                return model_data
        
        # 3. إذا لم يوجد أي نموذج من هذا النوع، استخدم الشات بوت العام كـ fallback
        if model_type != 'chatbot':
            return self.get_default_model('chatbot')
            
        return None
    
    def generate_response(self, prompt: str, model_type: str = 'chatbot', model_id: Optional[int] = None, is_failover: bool = False) -> Dict[str, Any]:
        """توليد استجابة باستخدام الذكاء الاصطناعي"""
        try:
            # اختيار النموذج
            if model_id and model_id in self.models:
                model = self.models[model_id]
            else:
                model = self.get_default_model(model_type)
            
            if not model:
                if is_failover:
                    raise Exception("لا يوجد نموذج بديل متاح")
                db_models_count = len([k for k in self.models if isinstance(k, int) and k > 0])
                print(f"DEBUG: لا يوجد نموذج من نوع '{model_type}' - إجمالي النماذج: {db_models_count} - أنواع مُحمَّلة: {set(v['type'] for v in self.models.values())}")
                return {
                    'success': False,
                    'response': f'⚠️ لم يتم العثور على نموذج ذكاء اصطناعي من نوع ({model_type}). يرجى التحقق من إعدادات النماذج في لوحة التحكم.',
                    'model_used': 'لا يوجد نموذج'
                }
            
            # محاولة استدعاء النموذج الحقيقي
            try:
                provider = model['provider']
                if provider == 'openai':
                    return self._call_openai(model, prompt)
                elif provider == 'anthropic':
                    return self._call_anthropic(model, prompt)
                elif provider == 'google':
                    return self._call_google(model, prompt)
                elif provider in ('openrouter', 'open_router'):
                    return self._call_openrouter(model, prompt)
                elif provider in ('aimlapi', 'aiml', 'ai_ml'):
                    return self._call_aiml(model, prompt)
                else:
                    if is_failover:
                        raise Exception("مزود غير معروف")
                    return {
                        'success': True,
                        'response': self._get_smart_response(prompt, model_type),
                        'model_used': model['name'] + ' (محاكاة)'
                    }
            except Exception as api_error:
                print(f"DEBUG: AI API Error ({model.get('name')} - {provider}): {api_error}")
                logger.warning(f"فشل في استدعاء API: {api_error}")
                
                # إذا كنا أصلاً في حالة فشل محاولة أخرى، ارفع الخطأ للأعلى بدلاً من الرد بالاحتياطي
                if is_failover:
                    raise api_error

                # فشل هذا النموذج؟ جرّب أي نموذج آخر متاح (failover)
                if not hasattr(self, '_trying_failover'): self._trying_failover = set()
                current_id = model_id or model.get('id')
                self._trying_failover.add(current_id)
                
                for other_id, other_model in self.models.items():
                    if other_id not in self._trying_failover and other_model['type'] == model_type:
                        try:
                            print(f"DEBUG: Trying failover to {other_model['name']}...")
                            resp = self.generate_response(prompt, model_type, other_id, is_failover=True)
                            self._trying_failover.remove(current_id)
                            return resp
                        except Exception as inner_e:
                            print(f"DEBUG: Failover to {other_model['name']} failed: {inner_e}")
                            continue
                
                if current_id in self._trying_failover: self._trying_failover.remove(current_id)

                # إرجاع رسالة خطأ حقيقية بدلاً من الردود الافتراضية المضللة
                error_msg = str(api_error)
                print(f"DEBUG: All models failed. Last error: {error_msg}")
                return {
                    'success': False,
                    'response': f'⚠️ فشل الاتصال بنموذج الذكاء الاصطناعي: {error_msg[:200]}\n\nيرجى التحقق من مفتاح API وحالة الاتصال.',
                    'model_used': model['name'] + ' (فشل)'
                }
                
        except Exception as e:
            logger.error(f"خطأ في توليد الاستجابة: {e}")
            if is_failover:
                raise e
            return {
                'success': False,
                'response': f'⚠️ خطأ في نظام الذكاء الاصطناعي: {str(e)[:200]}',
                'model_used': 'خطأ في النظام'
            }
    
    def _call_openai(self, model: Dict, prompt: str) -> Dict[str, Any]:
        """استدعاء OpenAI API"""
        try:
            api_key = model['api_key']
            if not api_key or api_key in ('', 'demo-key', 'your-key-here'):
                raise Exception("OpenAI API key غير مضبوط")

            if openai:
                # استخدام مكتبة openai الرسمية (v1+)
                try:
                    client = openai.OpenAI(api_key=api_key)
                    messages = []
                    if model['system_prompt']:
                        messages.append({"role": "system", "content": model['system_prompt']})
                    messages.append({"role": "user", "content": prompt})
                    response = client.chat.completions.create(
                        model=model['model_version'] or 'gpt-3.5-turbo',
                        messages=messages,
                        temperature=model['temperature'],
                        max_tokens=model['max_tokens']
                    )
                    text = response.choices[0].message.content
                except AttributeError:
                    # openai v0.x
                    openai.api_key = api_key
                    messages = []
                    if model['system_prompt']:
                        messages.append({"role": "system", "content": model['system_prompt']})
                    messages.append({"role": "user", "content": prompt})
                    response = openai.ChatCompletion.create(
                        model=model['model_version'] or 'gpt-3.5-turbo',
                        messages=messages,
                        temperature=model['temperature'],
                        max_tokens=model['max_tokens']
                    )
                    text = response.choices[0].message.content
            else:
                # HTTP مباشر بدون مكتبة
                payload = json.dumps({
                    "model": model['model_version'] or 'gpt-3.5-turbo',
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": model['temperature'],
                    "max_tokens": model['max_tokens']
                }).encode('utf-8')
                req = urllib.request.Request(
                    'https://api.openai.com/v1/chat/completions',
                    data=payload,
                    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + api_key}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read())
                text = result['choices'][0]['message']['content']

            self._update_usage_stats(model['model_obj'])
            return {'success': True, 'response': text, 'model_used': model['name']}

        except Exception as e:
            logger.error(f"خطأ في OpenAI API: {e}")
            raise e
    
    def _call_anthropic(self, model: Dict, prompt: str) -> Dict[str, Any]:
        """Anthropic - غير مدعوم حالياً"""
        raise Exception("Anthropic API غير متاح حالياً")

    def _call_google(self, model: Dict, prompt: str) -> Dict[str, Any]:
        """استدعاء Google Gemini API"""
        api_key = model['api_key']
        if not api_key or api_key in ('', 'demo-key', 'your-key-here'):
            raise Exception("Gemini API key غير مضبوط")

        model_name = model['model_version'] or 'gemini-1.5-flash'
        system_prompt = model.get('system_prompt', '')
        full_prompt = (system_prompt + '\n\n' + prompt).strip() if system_prompt else prompt

        if genai:
            # استخدام مكتبة google-generativeai الرسمية
            genai.configure(api_key=api_key)
            gmodel = genai.GenerativeModel(model_name)
            response = gmodel.generate_content(full_prompt)
            text = response.text
        else:
            # HTTP مباشر بدون مكتبة
            payload = json.dumps({
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": model['temperature'],
                    "maxOutputTokens": model['max_tokens']
                }
            }).encode('utf-8')
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}'
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            text = result['candidates'][0]['content']['parts'][0]['text']

        self._update_usage_stats(model.get('model_obj'))
        return {'success': True, 'response': text, 'model_used': model['name']}

    def _call_openai_compatible(self, model: Dict, prompt: str, base_url: str, extra_headers: dict = None) -> Dict[str, Any]:
        """استدعاء أي API متوافق مع OpenAI (OpenRouter, AIML, إلخ)"""
        api_key = model['api_key']
        messages = []
        if model.get('system_prompt'):
            messages.append({'role': 'system', 'content': model['system_prompt']})
        messages.append({'role': 'user', 'content': prompt})

        payload = json.dumps({
            'model': model.get('model_version') or 'gpt-4o-mini',
            'messages': messages,
            'temperature': model.get('temperature', 0.7),
            'max_tokens': model.get('max_tokens', 1500)
        }).encode('utf-8')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'MDB-Dashboard-Client/1.0'
        }
        if extra_headers:
            headers.update(extra_headers)

        req = urllib.request.Request(base_url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        text = result['choices'][0]['message']['content']
        self._update_usage_stats(model.get('model_obj'))
        return {'success': True, 'response': text, 'model_used': model['name']}

    def _call_openrouter(self, model: Dict, prompt: str) -> Dict[str, Any]:
        """استدعاء OpenRouter API"""
        return self._call_openai_compatible(
            model, prompt,
            'https://openrouter.ai/api/v1/chat/completions',
            extra_headers={
                'HTTP-Referer': 'https://mdb-dashboard.local',
                'X-Title': 'MDB Dashboard'
            }
        )

    def _call_aiml(self, model: Dict, prompt: str) -> Dict[str, Any]:
        """استدعاء AI/ML API"""
        return self._call_openai_compatible(
            model, prompt,
            'https://api.aimlapi.com/v1/chat/completions'
        )
    
    def _update_usage_stats(self, model_obj):
        """تحديث إحصائيات الاستخدام"""
        if not model_obj:
            return
        try:
            from app import db
            model_obj.usage_count = (model_obj.usage_count or 0) + 1
            model_obj.last_used = datetime.datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logger.error(f"خطأ في تحديث الإحصائيات: {e}")
    
    def _get_smart_response(self, prompt: str, model_type: str) -> str:
        """نظام استجابة ذكي احتياطي"""
        prompt_lower = prompt.lower()
        
        # استجابات للرحلات والحج والعمرة (تجنب التفعيل إذا كان السياق يتحدث عن بلاغات كهربائية)
        if (model_type == 'trip_planner' or any(word in prompt_lower for word in ['رحلة', 'عمرة', 'سفر', 'trip'])) and 'بلاغ' not in prompt_lower:
            return self._get_trip_response(prompt_lower)
        
        # استجابة للحج فقط لو مفيش سيرة بلاغات أو كهرباء
        if 'حج' in prompt_lower and not any(w in prompt_lower for w in ['بلاغ', 'كهرباء', 'لوحة', 'مقاول']):
            return self._get_trip_response(prompt_lower)
        
        # استجابات للشات بوت العام
        elif model_type == 'chatbot':
            return self._get_chatbot_response(prompt_lower)
        
        # استجابات للمواقف والنقل
        elif any(word in prompt_lower for word in ['موقف', 'سيارة', 'نقل', 'parking']):
            return self._get_parking_response(prompt_lower)
        
        # استجابات للسكن
        elif any(word in prompt_lower for word in ['سكن', 'شقة', 'فندق', 'إقامة', 'housing']):
            return self._get_housing_response(prompt_lower)
        
        # استجابة عامة
        else:
            return self._get_general_response(prompt_lower)
    
    def _get_trip_response(self, prompt: str) -> str:
        """استجابات ذكية للرحلات"""
        if 'حج' in prompt or 'hajj' in prompt:
            return """🕋 **رحلة الحج - اقتراحات مخصصة**

📅 **أفضل التوقيتات**: حسب التواريخ الشرعية (ذو الحجة)
💰 **تقدير التكاليف**:
- حزمة اقتصادية: 8,000 - 12,000 ريال
- حزمة متوسطة: 12,000 - 18,000 ريال  
- حزمة مميزة: 18,000+ ريال

📍 **البرنامج المقترح** (14 يوم):
- أيام 1-3: الوصول والتأقلم في مكة
- أيام 4-8: أداء مناسك الحج (منى، عرفات، مزدلفة)
- أيام 9-12: طواف الإفاضة والسعي
- أيام 13-14: زيارة المدينة المنورة

✅ **نصائح مهمة**:
- احجز مبكراً (6-12 شهر)
- تأكد من اللياقة البدنية
- احضر الوثائق المطلوبة
- اتبع إرشادات السلامة"""

        elif 'عمرة' in prompt or 'umrah' in prompt:
            return """🕌 **رحلة العمرة - خطة مثالية**

📅 **أفضل الأوقات**:
- شهر رمضان (أجر مضاعف)
- الأشهر الباردة (نوفمبر - مارس)
- تجنب موسم الحج

💰 **تقدير التكاليف**:
- حزمة اقتصادية: 2,500 - 4,000 ريال
- حزمة متوسطة: 4,000 - 6,500 ريال
- حزمة مميزة: 6,500+ ريال

📍 **البرنامج المقترح** (7 أيام):
- يوم 1: الوصول والاستقرار
- أيام 2-4: أداء العمرة والطواف
- أيام 5-6: زيارة المدينة المنورة
- يوم 7: المغادرة

🎯 **مميزات خاصة**:
- إمكانية الأداء في أي وقت
- مرونة في التوقيت
- فرصة لزيارة المعالم التاريخية"""

        else:
            return """✈️ **مخطط الرحلات الذكي**

يمكنني مساعدتك في تخطيط:
🕋 رحلات الحج الشاملة
🕌 رحلات العمرة المميزة
🏛️ السياحة الدينية والتاريخية
🎯 الرحلات المخصصة

📋 **لتخطيط أفضل، أخبرني عن**:
- نوع الرحلة المطلوبة
- عدد المسافرين
- المدة المفضلة  
- الميزانية المتاحة
- أي متطلبات خاصة

💡 **نصيحة**: كلما كانت التفاصيل أكثر، كانت الاقتراحات أدق!"""
    
    def _get_chatbot_response(self, prompt: str) -> str:
        """استجابات الشات بوت العام"""
        greetings = ['مرحبا', 'السلام', 'أهلا', 'hello', 'hi']
        questions = ['كيف', 'ماذا', 'متى', 'أين', 'لماذا', 'how', 'what', 'when', 'where']
        
        if any(word in prompt for word in greetings):
            if 'بلاغ' in prompt:
                return """مرحباً! يبدو أنك تسأل عن تحليل البلاغات.
كحل مؤقت (بسبب عطل في الاتصال بالمزود)، إليك نظرة سريعة:
- النظام يعمل حالياً على معالجة البيانات.
- يمكنك مراجعة لوحة الإحصائيات في الأعلى للحصول على الأرقام الدقيقة.
- جاري إصلاح الاتصال بالذكاء الاصطناعي..."""
            
            return """مرحباً بك! 👋

أنا مساعدك الذكي لخدمات الحج والعمرة. يمكنني مساعدتك في:

🕋 تخطيط رحلات الحج والعمرة
🏨 البحث عن أفضل أماكن الإقامة  
🚗 ترتيب المواصلات والمواقف
📍 معلومات عن المواقع المقدسة
💰 مقارنة الأسعار والحزم

كيف يمكنني مساعدتك اليوم؟"""

        elif any(word in prompt for word in questions):
            return """يسعدني الإجابة على استفساراتك! 

🤔 **أسئلة شائعة يمكنني الإجابة عليها**:
- متى أفضل وقت للحج أو العمرة؟
- كم تكلفة الرحلة تقريباً؟
- ما المستندات المطلوبة؟
- أين أفضل أماكن الإقامة؟
- كيف أحجز موقف سيارة؟

اطرح سؤالك وسأقدم لك إجابة مفصلة! 💭"""

        else:
            return """شكراً لتواصلك معي! 

أنا هنا لمساعدتك في جميع احتياجاتك المتعلقة بالحج والعمرة والسياحة الدينية.

🔍 **يمكنك أن تسأل عن**:
- تخطيط الرحلات
- الحجوزات والأسعار  
- المعلومات والإرشادات
- النصائح والتوجيهات

لا تتردد في طرح أي سؤال! 😊"""
    
    def _get_parking_response(self, prompt: str) -> str:
        """استجابات المواقف والنقل"""
        return """🚗 **خدمات المواقف والنقل**

📍 **مواقف متاحة**:
- موقف الحرم الشمالي (2000 موقف)
- موقف الحرم الجنوبي (1500 موقف)  
- موقف المسجد النبوي (1000 موقف)

💰 **الأسعار**:
- ساعة واحدة: 5 ريال
- يوم كامل: 50 ريال (مكة) / 30 ريال (المدينة)

🚌 **خدمات إضافية**:
- نقل مجاني للحرم
- مواقف مخصصة لذوي الاحتياجات الخاصة
- أمان على مدار الساعة

📱 **للحجز**: استخدم التطبيق أو اتصل بخدمة العملاء"""
    
    def _get_housing_response(self, prompt: str) -> str:
        """استجابات السكن والإقامة"""
        return """🏨 **خيارات الإقامة المتاحة**

🏢 **أنواع السكن**:
- فنادق فاخرة (5 نجوم): 500-1500 ريال/ليلة
- فنادق متوسطة (3-4 نجوم): 200-500 ريال/ليلة
- شقق مفروشة: 150-400 ريال/ليلة
- بيوت الضيافة: 100-250 ريال/ليلة

📍 **المواقع المميزة**:
- قريب من الحرم (أقل من 500م)
- وسط المدينة (سهولة المواصلات)
- المناطق الهادئة (للعائلات)

✨ **المرافق المتوفرة**:
- واي فاي مجاني
- مواقف سيارات
- خدمة الغرف
- مطاعم حلال

📞 **للحجز والاستفسار**: تواصل معنا الآن!"""
    
    def _get_general_response(self, prompt: str) -> str:
        """استجابة عامة"""
        return """مرحباً! أنا مساعدك الذكي 🤖

🌟 **خدماتي تشمل**:
- تخطيط رحلات الحج والعمرة
- معلومات عن المواقع المقدسة
- حجز الإقامة والمواصلات
- نصائح وإرشادات مفيدة

💬 **كيف يمكنني مساعدتك؟**
اكتب سؤالك أو طلبك وسأقدم لك أفضل الحلول!

🔄 **نصيحة**: كن محدداً في سؤالك للحصول على إجابة أكثر دقة."""

# إنشاء مثيل عام من النظام
advanced_ai = AdvancedAISystem()

def get_ai_response(prompt: str, model_type: str = 'chatbot', model_id: Optional[int] = None) -> Dict[str, Any]:
    """دالة مساعدة للحصول على استجابة الذكاء الاصطناعي"""
    return advanced_ai.generate_response(prompt, model_type, model_id)

def reload_ai_models():
    """إعادة تحميل النماذج"""
    global advanced_ai
    advanced_ai.load_models()
