
import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

def test_openrouter():
    key = os.environ.get('OPENROUTER_API_KEY')
    print(f"Testing OpenRouter with key: {key[:10]}...")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = json.dumps({
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say hello in Arabic"}],
        "temperature": 0.7
    }).encode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "MDB Test",
        "User-Agent": "MDB-Dashboard-Client/1.0"
    }
    
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print("OpenRouter Success!")
            print("Response:", result['choices'][0]['message']['content'])
    except Exception as e:
        print("OpenRouter Failed:", e)

def test_aiml():
    key = os.environ.get('AIML_API_KEY')
    print(f"Testing AI/ML API with key: {key[:10]}...")
    
    url = "https://api.aimlapi.com/v1/chat/completions"
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say hello in Arabic"}],
    }).encode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "MDB-Dashboard-Client/1.0"
    }
    
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print("AI/ML API Success!")
            print("Response:", result['choices'][0]['message']['content'])
    except Exception as e:
        print("AI/ML API Failed:", e)

if __name__ == "__main__":
    test_openrouter()
    test_aiml()
