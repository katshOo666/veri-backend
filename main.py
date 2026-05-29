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

# Модель для детекции
API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"

@app.get("/")
def home():
    return {"status": "Veri is Live and Ready"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        image_data = requests.get(image_url).content
        
        # Делаем 5 попыток достучаться до нейросети
        for i in range(5):
            response = requests.post(API_URL, data=image_data)
            result = response.json()
            
            # Если модель загружается, она вернет 'estimated_time'
            if isinstance(result, dict) and "estimated_time" in result:
                wait_time = result.get("estimated_time", 10)
                time.sleep(min(wait_time, 15)) # Ждем, но не больше 15 сек за раз
                continue
            
            # Если получили результат в виде списка
            if isinstance(result, list):
                ai_score = 0
                for item in result:
                    if item['label'].lower() in ['artificial', 'ai', 'fake']:
                        ai_score = item['score']
                
                percentage = round(ai_score * 100, 2)
                return {
                    "is_ai": percentage > 50,
                    "percentage": percentage,
                    "error": False
                }
            
            # Если ошибка в формате словаря
            if isinstance(result, dict) and "error" in result:
                time.sleep(5)
                continue

        return {"error": True, "message": "Нейросеть просыпается. Подождите 10 секунд и нажмите кнопку еще раз."}
        
    except Exception as e:
        return {"error": True, "message": "Попробуйте еще раз через пару секунд."}
