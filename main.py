from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        
        # Используем самую базовую и быструю модель
        api_url = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"
        img_data = requests.get(image_url).content
        
        response = requests.post(api_url, data=img_data)
        data = response.json()

        # Если нейросеть прислала ошибку или еще грузится
        if isinstance(data, dict) and ("error" in data or "detail" in data):
            return {"error": True, "message": "Нейросеть просыпается... Нажми еще раз через 5 сек"}

        # Ищем результат
        ai_score = 0
        if isinstance(data, list) and len(data) > 0:
            for item in data:
                if item.get('label', '').lower() in ['artificial', 'ai', 'fake', 'label_1']:
                    ai_score = item.get('score', 0)
        
        return {
            "is_ai": ai_score > 0.5,
            "percentage": round(ai_score * 100, 1),
            "error": False
        }
    except Exception:
        return {"error": True, "message": "Жми кнопку еще раз!"}
