import openai
import json
import requests
from datetime import datetime, timedelta
from flask import current_app
from mdb_dashboard.database import db
from mdb_dashboard.models.trip_models import AIModel, AITripPlanner, TripPackage, CustomTrip
from mdb_dashboard.models.smart_city_models import PilgrimageLocation
import uuid

class AIAssistant:
    """مساعد الذكاء الاصطناعي الرئيسي"""
    
    def __init__(self):
        self.active_models = {}
        self.load_active_models()
    
    def load_active_models(self):
        """تحميل النماذج النشطة"""
        try:
            models = AIModel.query.filter_by(is_active=True).all()
            for model in models:
                self.active_models[model.model_type] = {
                    'id': model.id,
                    'name': model.model_name,
                    'provider': model.api_provider,
                    'api_key': model.api_key,
                    'model_version': model.model_version,
                    'temperature': model.temperature,
                    'max_tokens': model.max_tokens,
                    'system_prompt': model.system_prompt
                }
        except Exception as e:
            print(f"خطأ في تحميل النماذج: {e}")
    
    def get_model_config(self, model_type):
        """الحصول على إعدادات النموذج"""
        return self.active_models.get(model_type)
    
    def call_openai_api(self, model_config, messages, user_input=""):
        """استدعاء OpenAI API"""
        try:
            openai.api_key = model_config['api_key']
            
            # إعداد الرسائل
            if model_config.get('system_prompt'):
                messages.insert(0, {"role": "system", "content": model_config['system_prompt']})
            
            response = openai.ChatCompletion.create(
                model=model_config.get('model_version', 'gpt-3.5-turbo'),
                messages=messages,
                temperature=model_config.get('temperature', 0.7),
                max_tokens=model_config.get('max_tokens', 1000)
            )
            
            return {
                'success': True,
                'response': response.choices[0].message.content,
                'usage': response.usage
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def call_anthropic_api(self, model_config, messages, user_input=""):
        """استدعاء Anthropic Claude API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': model_config['api_key'],
                'anthropic-version': '2023-06-01'
            }
            
            # تحويل الرسائل لتنسيق Claude
            prompt = ""
            for msg in messages:
                if msg['role'] == 'system':
                    prompt += f"System: {msg['content']}\n\n"
                elif msg['role'] == 'user':
                    prompt += f"Human: {msg['content']}\n\n"
                elif msg['role'] == 'assistant':
                    prompt += f"Assistant: {msg['content']}\n\n"
            
            prompt += "Assistant:"
            
            data = {
                'model': model_config.get('model_version', 'claude-3-sonnet-20240229'),
                'max_tokens': model_config.get('max_tokens', 1000),
                'messages': [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result['content'][0]['text'],
                    'usage': result.get('usage', {})
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_response(self, model_type, user_input, context=None):
        """توليد استجابة من الذكاء الاصطناعي"""
        model_config = self.get_model_config(model_type)
        if not model_config:
            return {
                'success': False,
                'error': f'لا يوجد نموذج نشط من نوع {model_type}'
            }
        
        # إعداد الرسائل
        messages = []
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": user_input})
        
        # استدعاء API حسب المزود
        if model_config['provider'] == 'openai':
            return self.call_openai_api(model_config, messages, user_input)
        elif model_config['provider'] == 'anthropic':
            return self.call_anthropic_api(model_config, messages, user_input)
        else:
            return {
                'success': False,
                'error': f'مزود غير مدعوم: {model_config["provider"]}'
            }

class TripPlannerAI:
    """مخطط الرحلات بالذكاء الاصطناعي"""
    
    def __init__(self):
        self.ai_assistant = AIAssistant()
    
    def plan_trip(self, user_request, user_preferences=None):
        """تخطيط رحلة بالذكاء الاصطناعي"""
        try:
            # إعداد السياق
            context = self.build_trip_context(user_preferences)
            
            # إعداد الطلب
            enhanced_request = self.enhance_trip_request(user_request, user_preferences)
            
            # توليد الاستجابة
            response = self.ai_assistant.generate_response(
                'trip_planner', 
                enhanced_request, 
                context
            )
            
            if response['success']:
                # معالجة الاستجابة
                processed_response = self.process_trip_response(response['response'])
                
                # حفظ في قاعدة البيانات
                session_id = str(uuid.uuid4())
                trip_plan = AITripPlanner(
                    session_id=session_id,
                    user_input=user_request,
                    user_preferences=json.dumps(user_preferences) if user_preferences else None,
                    ai_response=response['response'],
                    suggested_packages=json.dumps(processed_response.get('packages', [])),
                    estimated_costs=json.dumps(processed_response.get('costs', {})),
                    recommended_dates=json.dumps(processed_response.get('dates', []))
                )
                
                db.session.add(trip_plan)
                db.session.commit()
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'response': response['response'],
                    'processed_data': processed_response
                }
            else:
                return response
                
        except Exception as e:
            return {
                'success': False,
                'error': f'خطأ في تخطيط الرحلة: {str(e)}'
            }
    
    def build_trip_context(self, user_preferences):
        """بناء سياق الرحلة"""
        context = []
        
        # إضافة معلومات عن الحزم المتاحة
        packages = TripPackage.query.filter_by(is_active=True).limit(10).all()
        packages_info = []
        for package in packages:
            packages_info.append({
                'name': package.package_name,
                'type': package.package_type,
                'duration': package.duration_days,
                'price': package.price_per_person,
                'description': package.description
            })
        
        context.append({
            "role": "system",
            "content": f"الحزم المتاحة: {json.dumps(packages_info, ensure_ascii=False)}"
        })
        
        # إضافة معلومات عن المواقع
        locations = PilgrimageLocation.query.filter_by(is_featured=True).limit(20).all()
        locations_info = []
        for location in locations:
            locations_info.append({
                'name': location.location_name,
                'type': location.location_type,
                'description': location.description,
                'rating': location.safety_rating
            })
        
        context.append({
            "role": "system", 
            "content": f"المواقع المتاحة: {json.dumps(locations_info, ensure_ascii=False)}"
        })
        
        return context
    
    def enhance_trip_request(self, user_request, user_preferences):
        """تحسين طلب الرحلة"""
        enhanced = f"طلب الرحلة: {user_request}\n\n"
        
        if user_preferences:
            enhanced += "التفضيلات:\n"
            for key, value in user_preferences.items():
                enhanced += f"- {key}: {value}\n"
        
        enhanced += "\nيرجى تقديم:\n"
        enhanced += "1. اقتراحات للحزم المناسبة\n"
        enhanced += "2. تقدير التكاليف\n"
        enhanced += "3. أفضل الأوقات للسفر\n"
        enhanced += "4. برنامج مقترح للرحلة\n"
        enhanced += "5. نصائح مهمة\n"
        
        return enhanced
    
    def process_trip_response(self, ai_response):
        """معالجة استجابة الذكاء الاصطناعي"""
        try:
            # محاولة استخراج البيانات المنظمة من الاستجابة
            processed = {
                'packages': [],
                'costs': {},
                'dates': [],
                'itinerary': [],
                'tips': []
            }
            
            # يمكن تحسين هذا باستخدام regex أو NLP
            lines = ai_response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if 'حزم' in line or 'packages' in line.lower():
                    current_section = 'packages'
                elif 'تكلفة' in line or 'cost' in line.lower():
                    current_section = 'costs'
                elif 'تاريخ' in line or 'date' in line.lower():
                    current_section = 'dates'
                elif 'برنامج' in line or 'itinerary' in line.lower():
                    current_section = 'itinerary'
                elif 'نصائح' in line or 'tips' in line.lower():
                    current_section = 'tips'
                elif line and current_section:
                    if current_section == 'packages':
                        processed['packages'].append(line)
                    elif current_section == 'costs':
                        processed['costs'][len(processed['costs'])] = line
                    elif current_section == 'dates':
                        processed['dates'].append(line)
                    elif current_section == 'itinerary':
                        processed['itinerary'].append(line)
                    elif current_section == 'tips':
                        processed['tips'].append(line)
            
            return processed
            
        except Exception as e:
            print(f"خطأ في معالجة الاستجابة: {e}")
            return {}

class ChatBot:
    """شات بوت ذكي للموقع"""
    
    def __init__(self):
        self.ai_assistant = AIAssistant()
        self.conversation_history = {}
    
    def chat(self, user_message, session_id=None, context_type='general'):
        """محادثة مع الشات بوت"""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # الحصول على تاريخ المحادثة
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            # إضافة السياق حسب النوع
            context = self.build_chat_context(context_type)
            context.extend(self.conversation_history[session_id])
            
            # توليد الاستجابة
            response = self.ai_assistant.generate_response(
                'chatbot',
                user_message,
                context
            )
            
            if response['success']:
                # حفظ المحادثة
                self.conversation_history[session_id].append({
                    "role": "user",
                    "content": user_message
                })
                self.conversation_history[session_id].append({
                    "role": "assistant", 
                    "content": response['response']
                })
                
                # الحفاظ على آخر 10 رسائل فقط
                if len(self.conversation_history[session_id]) > 20:
                    self.conversation_history[session_id] = self.conversation_history[session_id][-20:]
                
                return {
                    'success': True,
                    'response': response['response'],
                    'session_id': session_id
                }
            else:
                return response
                
        except Exception as e:
            return {
                'success': False,
                'error': f'خطأ في الشات بوت: {str(e)}'
            }
    
    def build_chat_context(self, context_type):
        """بناء سياق المحادثة"""
        context = []
        
        base_prompt = """أنت مساعد ذكي لموقع الحج والعمرة والسياحة الدينية. 
        يمكنك مساعدة المستخدمين في:
        - التخطيط للرحلات
        - معلومات عن المواقع المقدسة
        - الحجوزات والأسعار
        - النصائح والإرشادات
        - الإجابة على الأسئلة العامة
        
        كن مفيداً ومهذباً واستخدم اللغة العربية بشكل أساسي."""
        
        if context_type == 'trip_planning':
            base_prompt += "\n\nأنت متخصص في تخطيط الرحلات. ساعد المستخدم في إنشاء رحلة مثالية."
        elif context_type == 'locations':
            base_prompt += "\n\nأنت خبير في المواقع المقدسة والسياحية. قدم معلومات مفصلة ومفيدة."
        elif context_type == 'bookings':
            base_prompt += "\n\nأنت متخصص في الحجوزات والأسعار. ساعد المستخدم في العثور على أفضل العروض."
        
        context.append({"role": "system", "content": base_prompt})
        
        return context

# إنشاء مثيلات عامة
ai_assistant = AIAssistant()
trip_planner = TripPlannerAI()
chatbot = ChatBot()
