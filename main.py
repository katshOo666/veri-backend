import os
# ВАЖНО: Установка зеркала (если нужно - раскомментируйте)
# os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
import base64
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ЗАМЕНИТЕ ЭТОТ ТОКЕН
HUGGINGFACE_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# НОВЫЙ РАБОЧИЙ URL (исправлено!)
API_URL = "https://router.huggingface.co/hf-inference/models/umm-maybe/AI-image-detector"
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

@app.get("/")
def home():
    return {"status": "OK", "message": "AI Image Detector работает"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        
        image_url = body.get("imageUrl", "")
        image_base64 = body.get("imageBase64", "")
        
        img_data = None
        
        if image_base64:
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            img_data = base64.b64decode(image_base64)
        
        elif image_url:
            final_url = image_url
            
            if "wix:image" in image_url:
                match = re.search(r'wix:image://v1/([^/?#]+)', image_url)
                if match:
                    final_url = f"https://static.wixstatic.com/media/{match.group(1)}"
                else:
                    match = re.search(r'wix:image://([^/?#]+)', image_url)
                    if match:
                        final_url = f"https://static.wixstatic.com/media/{match.group(1)}"
            
            response = requests.get(final_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            img_data = response.content
        
        if not img_data:
            return {"error": True, "message": "Не удалось получить изображение"}
        
        for attempt in range(3):
            try:
                response = requests.post(API_URL, headers=HEADERS, data=img_data, timeout=30)
                
                if response.status_code == 503:
                    time.sleep(5)
                    continue
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if isinstance(result, list) and len(result) > 0:
                        ai_score = 0
                        for item in result:
                            label = item.get('label', '').lower()
                            score = item.get('score', 0)
                            if label in ['artificial', 'ai', 'fake', 'AI']:
                                ai_score = score
                                break
                            elif label in ['real', 'human']:
                                ai_score = 1 - score
                                break
                        
                        if ai_score == 0:
                            ai_score = result[0].get('score', 0)
                        
                        return {
                            "is_ai": ai_score > 0.5,
                            "percentage": round(ai_score * 100, 1),
                            "confidence": round(ai_score, 3),
                            "error": False
                        }
                
                return {"error": True, "message": f"Ошибка API: {response.status_code}"}
                
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error attempt {attempt + 1}: {e}")
                if attempt == 2:
                    return {"error": True, "message": "Ошибка соединения с Hugging Face. Проверьте интернет или попробуйте использовать зеркало."}
                time.sleep(2)
                
    except Exception as e:
        return {"error": True, "message": f"Ошибка: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
