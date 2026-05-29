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

# НОВАЯ БЫСТРАЯ МОДЕЛЬ
API_URL = "https://api-inference.huggingface.co/models/linkiway/ai-content-detector"

@app.get("/")
def home():
    return {"status": "Work"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        image_data = requests.get(image_url).content
        
        # Делаем запрос к нейросети
        for i in range(5):
            response = requests.post(API_URL, data=image_data)
            result = response.json()
            
            # Если модель еще грузится
            if isinstance(result, dict) and "estimated_time" in result:
                time.sleep(4)
                continue
            
            # Обработка результата
            if isinstance(result, list):
                # Находим оценку для лейбла 'ai' или 'fake'
                ai_score = 0
                for item in result:
                    if item['label'].lower() in ['ai', 'fake', 'artificial']:
                        ai_score = item['score']
                    # Если модель выдает только 'label': 'LABEL_1' (часто для ИИ)
                    elif item['label'] == 'LABEL_1':
                        ai_score = item['score']
                
                percentage = round(ai_score * 100, 1)
                return {
                    "is_ai": percentage > 50,
                    "percentage": percentage,
                    "error": False
                }
        
        return {"error": True, "message": "Нейросеть почти проснулась, нажмите еще раз через 3 секунды"}
        
    except Exception as e:
        return {"error": True, "message": "Ошибка. Попробуйте еще раз."}
