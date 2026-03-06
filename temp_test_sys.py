import sys
import os

# إضافة مسار المشروع حتى نقدر نستورد app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from advanced_ai_system import AdvancedAISystem

with app.app_context():
    ai = AdvancedAISystem()
    ai._ensure_loaded()
    print("Loaded Models:")
    for mid, m in ai.models.items():
        print(f"[{mid}] {m['name']} ({m['type']} - {m['provider']}) - Default: {m['is_default']}")
        
    print("\nTesting Chatbot:")
    resp = ai.generate_response("مرحبا", model_type="chatbot")
    print(resp)

    print("\nTesting Report Analyzer:")
    resp = ai.generate_response("حلل البيانات", model_type="issue_analyzer")
    print(resp)
