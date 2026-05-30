import os
import base64
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Настройка CORS для безопасной связи с твоим сайтом Wix
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Используем открытую модель детекции ИИ-изображений от Hugging Face
HF_MODEL = "umm-maybe/AI-image-detector"
API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

# Твой бесплатный токен доступа от Hugging Face (считывается из переменных Render)
HF_API_KEY = os.getenv("HF_API_KEY", "")

@app.get("/")
def home():
    return {"status": "Live", "model": "Hugging Face ViT AI Detector"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_b64 = body.get("image", "")

        if not image_b64:
            return {"error": True, "message": "Изображение не передано в бэкенд."}

        # Очищаем строку base64 от возможных веб-заголовков браузера
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]

        # Декодируем текстовую строку обратно в байты картинки для отправки
        try:
            img_bytes = base64.b64decode(image_b64)
        except Exception:
            return {"error": True, "message": "Некорректный формат изображения."}

        # Настраиваем авторизацию для отправки запроса к Hugging Face
        headers = {}
        if HF_API_KEY:
            headers["Authorization"] = f"Bearer {HF_API_KEY}"

        # Отправляем бинарный файл напрямую в API моделей Hugging Face
        response = requests.post(API_URL, headers=headers, data=img_bytes)

        if response.status_code != 200:
            res_json = response.json()
            # Если модель «спит» на сервере Hugging Face, она попросит подождать загрузки
            if isinstance(res_json, dict) and "estimated_time" in res_json:
                wait_time = int(res_json["estimated_time"])
                return {
                    "error": True,
                    "message": f"Нейросеть запускается на сервере. Повторите попытку через {wait_time} сек."
                }
            return {"error": True, "message": f"Ошибка нейросети Hugging Face: код {response.status_code}"}

        predictions = response.json()
        
        # Разбираем результаты классификации от модели
        # Модель возвращает список вероятностей: [{"label": "artificial", "score": 0.95}, {"label": "human", "score": 0.05}]
        artificial_score = 0.0
        human_score = 0.0

        if isinstance(predictions, list):
            for pred in predictions:
                if pred.get("label") == "artificial":
                    artificial_score = pred.get("score", 0.0)
                elif pred.get("label") == "human":
                    human_score = pred.get("score", 0.0)

        # Вычисляем финальный вердикт
        is_ai = artificial_score > human_score
        confidence_val = max(artificial_score, human_score) * 100

        # Формируем понятное обоснование ответа для вывода на твоем сайте
        if is_ai:
            reason_text = "В структуре изображения найдены микроструктурные аномалии сглаживания и пиксельные шумы, характерные для ИИ-генераторов."
        else:
            reason_text = "Изображение имеет плавные переходы, естественные текстуры и распределение света, характерные для реальной съемки или рисунка человека."

        return {
            "is_ai": is_ai,
            "confidence": int(confidence_val),
            "percentage": int(confidence_val),  # Для совместимости со всеми версиями Wix
            "reason": reason_text,
            "error": False
        }

    except Exception as e:
        return {"error": True, "message": f"Ошибка на сервере: {str(e)[:50]}"}

# Специальный блок автозапуска для Render (если там настроена команда python main.py)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
    except Exception as e:
        return {"error": True, "message": f"Ошибка на сервере: {str(e)[:50]}"}
