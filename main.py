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
    return {"status": "Server is Live"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        
        # --- ТА САМАЯ МАГИЯ ДЛЯ WIX ---
        # Превращаем внутреннюю ссылку Wix во внешнюю публичную
        if image_url and image_url.startswith("wix:image://v1/"):
            img_id = image_url.split('/')[3]
            image_url = f"https://static.wixstatic.com/media/{img_id}"
        # ------------------------------
        
        img_data = requests.get(image_url).content
        
        for i in range(3):
            response = requests.post(API_URL, data=img_data)
            result = response.json()
            
            if isinstance(result, dict) and "estimated_time" in result:
                time.sleep(5)
                continue
            
            if isinstance(result, list):
                ai_score = next((item['score'] for item in result if item.get('label', '').lower() in ['artificial', 'ai', 'fake']), 0)
                return {
                    "is_ai": ai_score > 0.5,
                    "percentage": round(ai_score * 100, 1),
                    "error": False
                }
        
        return {"error": True, "message": "Нейросеть просыпается... Нажми еще раз!"}
    except Exception as e:
        return {"error": True, "message": "Нажми кнопку еще раз!"}
    except:
        return {"error": True, "message": "Нажми кнопку еще раз"}
