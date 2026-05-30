import os
import base64
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI()

# Разрешаем CORS-запросы от твоего сайта Wix
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Считываем API-ключ OpenAI из настроек Render (Environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

@app.get("/")
def home():
    return {"status": "Live", "model": "FastAPI GPT-4o-mini Detector"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_b64 = body.get("image", "")

        if not image_b64:
            return {"error": True, "message": "Изображение не передано в бэкенд."}

        # Очищаем base64 строку от метаданных веб-заголовков, если они есть
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]

        # Декодируем для проверки корректности структуры base64
        try:
            base64.b64decode(image_b64)
        except Exception:
            return {"error": True, "message": "Передан некорректный формат Base64."}

        # Проверяем, настроен ли ключ API на Render
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return {"error": True, "message": "Ключ OPENAI_API_KEY не найден в переменных окружения Render."}

        # Инициализируем клиент OpenAI непосредственно перед запросом
        client = OpenAI(api_key=api_key)

        # Детальная промпт-инструкция для экспертной визуальной оценки
        prompt_instruction = (
            "Проанализируй это изображение как эксперт по распознаванию графики искусственного интеллекта. "
            "Изучи мелкие детали, текстуру кожи/шерсти, фон, тени, физику света, анатомические аномалии, "
            "смазанные текстуры или идеальные цифровые размытия, "
            "характерные для Midjourney, Stable Diffusion (включая SDXL), DALL-E, Flux или Nano Banana. "
            "Особое внимание обрати на аниме, стилизованные арты, 3D иллюстрации и фотореалистичные портреты. "
            "Ответь СТРОГО в формате JSON с тремя полями (и больше ничего не пиши, без разметки markdown):\n"
            "{\n"
            "  \"is_ai\": true или false (выстави true, если это генерация ИИ, и false, если реальное фото или рисунок человека),\n"
            "  \"confidence\": число от 0 до 100 (процент уверенности, например 95),\n"
            "  \"reason\": \"короткое объяснение на русском языке, почему ты так считаешь, буквально 1-2 предложения\"\n"
            "}"
        )

        # Вызываем gpt-4o-mini (поддерживает зрение, работает быстро и очень дешево)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},  # Гарантирует получение строгого JSON
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_instruction},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )

        # Парсим полученный JSON-ответ от нейросети
        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        # Возвращаем результат со всеми возможными полями для совместимости с Wix
        return {
            "is_ai": result.get("is_ai", False),
            "confidence": result.get("confidence", 0),
            "percentage": result.get("confidence", 0),  # Поле 'percentage' нужно для старой версии Wix-кода
            "reason": result.get("reason", "Анализ успешно завершен."),
            "error": False
        }

    except Exception as e:
        return {"error": True, "message": f"Ошибка на сервере OpenAI: {str(e)[:50]}"}
