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

# Используем проверенную модель
API_URL = "https://api-inference.huggingface.co/models/linkiway/ai-content-detector"

@app.get("/")
def home():
    return {"status": "Live"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        
        # Скачиваем изображение
        img_resp = requests.get(image_url, timeout=10)
        
        # Пробуем достучаться до нейросети 5 раз
        for i in range(5):
            response = requests.post(API_URL, data=img_resp.content, timeout=20)
            result = response.json()
            
            # Если модель грузится - ждем
            if isinstance(result, dict) and "estimated_time" in result:
                time.sleep(5)
                continue
            
            # Если получили данные
            if isinstance(result, list) and len(result) > 0:
                # Берем самый высокий балл вероятности
                ai_score = 0
                for item in result:
                    if item['label'].lower() in ['ai', 'fake', 'artificial', 'label_1']:
                        ai_score = item['score']
                
                # Если модель выдала другие метки, берем первую
                if ai_score == 0:
                    ai_score = result[0]['score']

                return {
                    "is_ai": ai_score > 0.5,
                    "percentage": round(ai_score * 100, 1),
                    "error": False
                }
        
        return {"error": True, "message": "Нейросеть проснулась! Нажми еще раз."}

    except Exception:
        return {"error": True, "message": "Секунду... Нажми кнопку еще раз."}
