from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Самая стабильная модель для детекции ИИ
API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"

@app.get("/")
def home():
    return {"status": "System Online"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        
        # Скачиваем изображение
        img_data = requests.get(image_url).content
        
        # 5 попыток достучаться до нейросети
        for i in range(5):
            response = requests.post(API_URL, data=img_data)
            result = response.json()
            
            # Если модель загружается, ждем
            if isinstance(result, dict) and ("estimated_time" in result or "loading" in str(result)):
                time.sleep(6)
                continue
            
            # Если получили результат
            if isinstance(result, list):
                ai_score = 0
                for item in result:
                    if item['label'].lower() in ['artificial', 'ai', 'fake']:
                        ai_score = item['score']
                
                return {
                    "is_ai": ai_score > 0.5,
                    "percentage": round(ai_score * 100, 2),
                    "error": False
                }
        
        return {"error": True, "message": "Нейросеть просыпается... Нажми еще раз через 5 сек"}
    except Exception:
        return {"error": True, "message": "Нажми кнопку еще раз для активации"}
