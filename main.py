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

# Ссылка на бесплатную модель детекции ИИ на Hugging Face
API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"

@app.get("/")
def home():
    return {"status": "Veri is Live via HuggingFace"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        
        # Скачиваем картинку, чтобы отправить её в нейросеть
        image_data = requests.get(image_url).content
        
        # Запрос к нейросети
        response = requests.post(API_URL, data=image_data)
        result = response.json()

        # Парсим результат (ищем вероятность 'ai')
        # Обычно приходит список: [{'label': 'artificial', 'score': 0.99}, ...]
        ai_score = 0
        for item in result:
            if item['label'] in ['artificial', 'ai', 'fake']:
                ai_score = item['score']
        
        percentage = round(ai_score * 100, 2)
        
        return {
            "is_ai": percentage > 50,
            "percentage": percentage,
            "error": False
        }
        
    except Exception as e:
        return {"error": True, "message": "Нейросеть занята, попробуйте еще раз через 10 секунд"}
