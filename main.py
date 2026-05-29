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
        
        # Самая стабильная модель на данный момент
        api_url = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"
        image_data = requests.get(image_url).content
        
        response = requests.post(api_url, data=image_data)
        result = response.json()

        # Если нейросеть спит, мы вернем это Wix
        if isinstance(result, dict) and "error" in result:
             return {"error": True, "message": "Нейросеть просыпается, нажми еще раз через 5 сек"}

        # Извлекаем результат
        ai_score = 0
        if isinstance(result, list):
            for item in result:
                if item['label'].lower() in ['artificial', 'ai', 'fake']:
                    ai_score = item['score']
        
        return {
            "is_ai": ai_score > 0.5,
            "percentage": round(ai_score * 100, 2),
            "error": False
        }
    except Exception as e:
        return {"error": True, "message": "Нажми кнопку еще раз"}
