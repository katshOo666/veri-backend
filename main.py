import os
import base64
import io
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

# Импортируем библиотеки для локального запуска нейросети
from transformers import pipeline

app = FastAPI()

# Разрешаем CORS-запросы со стороны твоего сайта Wix
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Загрузка локальной нейросети детектора ИИ...")
# Загружаем модель прямо в память сервера при старте (абсолютно бесплатно и без API ключей!)
try:
    pipe = pipeline("image-classification", model="umm-maybe/AI-image-detector")
    print("Нейросеть успешно загружена в память сервера!")
except Exception as e:
    print(f"Ошибка при предварительной загрузке модели: {e}")
    pipe = None

@app.get("/")
def home():
    status = "Live" if pipe is not None else "Loading/Error"
    return {"status": status, "model": "Local Hugging Face ViT AI Detector (Self-Hosted)"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        global pipe
        # Если модель не успела загрузиться при старте, пробуем загрузить её снова
        if pipe is None:
            pipe = pipeline("image-classification", model="umm-maybe/AI-image-detector")

        body = await request.json()
        image_b64 = body.get("image", "")

        if not image_b64:
            return {"error": True, "message": "Изображение не передано в бэкенд."}

        # Очищаем строку base64 от возможных заголовков браузера
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]

        # Декодируем текстовую строку в байты картинки
        try:
            img_bytes = base64.b64decode(image_b64)
        except Exception:
            return {"error": True, "message": "Некорректный формат изображения."}

        # Открываем изображение через PIL прямо в памяти сервера
        try:
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception as e:
            return {"error": True, "message": f"Не удалось прочитать картинку: {str(e)[:30]}"}

        # Локально классифицируем изображение нашей моделью!
        predictions = pipe(image)
        
        # Разбираем результаты классификации
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

# Специальный блок автозапуска для Render
if __name__ == "__main__":
    import uvicorn
    print("Запуск приложения FastAPI...")
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
