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

API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"

@app.get("/")
def home():
    return {"status": "OK"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        raw_url = body.get("imageUrl", "")
        
        # --- МАГИЯ ВОССТАНОВЛЕНИЯ ССЫЛКИ ---
        if "wix:image" in raw_url:
            # Если это внутренняя ссылка Wix
            img_id = raw_url.split('/')[3]
            if '#' in img_id: img_id = img_id.split('#')[0]
            final_url = f"https://static.wixstatic.com/media/{img_id}"
        elif raw_url.startswith("https") and "//" not in raw_url:
            # Если пришло "https:..." без слешей (редкий глюк Wix)
            final_url = raw_url.replace("https:", "https://")
        else:
            final_url = raw_url

        # Проверяем, что ссылка вообще похожа на правду
        if len(final_url) < 10:
            return {"error": True, "message": "Картинка не загрузилась. Попробуй еще раз."}

        img_data = requests.get(final_url, timeout=10).content
        
        # Попытки пробуждения нейросети
        for i in range(4):
            response = requests.post(API_URL, data=img_data)
            result = response.json()
            if isinstance(result, dict) and "estimated_time" in result:
                time.sleep(5)
                continue
            if isinstance(result, list):
                ai_score = next((item['score'] for item in result if item['label'].lower() in ['artificial', 'ai', 'fake', 'label_1']), 0)
                return {"is_ai": ai_score > 0.5, "percentage": round(ai_score * 100, 1), "error": False}
        
        return {"error": True, "message": "Нейросеть просыпается... Жми кнопку!"}
    except Exception as e:
        return {"error": True, "message": "Жми кнопку еще раз!"}
