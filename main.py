import os
import re
import base64
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from io import BytesIO
import logging

# Логирование для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Максимально широкие CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SIGHTENGINE_USER = os.getenv("SIGHTENGINE_USER", "145435152")
SIGHTENGINE_SECRET = os.getenv("SIGHTENGINE_SECRET", "wa4ykGt9ezK2MUZuTCURcfL2wDjYXpi8")
API_URL = "https://api.sightengine.com/1.0/check.json"

# Пороги для более точного определения
AI_THRESHOLD_HIGH = 0.75  # Высокая уверенность - это AI
AI_THRESHOLD_LOW = 0.25   # Низкая уверенность - это реально

def validate_and_optimize_image(img_data: bytes) -> bytes:
    """Валидация и оптимизация изображения для лучшей обработки"""
    try:
        # Открываем изображение
        img = Image.open(BytesIO(img_data))
        
        # Проверяем размер (не менее 100x100)
        if img.width < 100 or img.height < 100:
            logger.warning(f"Изображение слишком маленькое: {img.width}x{img.height}")
        
        # Конвертируем в RGB если нужно (для RGBA, P, etc.)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Сохраняем с оптимизацией качества (90%)
        output = BytesIO()
        img.save(output, format='JPEG', quality=90, optimize=True)
        return output.getvalue()
    
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}")
        raise ValueError(f"Невалидное изображение: {str(e)}")

@app.get("/")
def home():
    return {"status": "Live", "message": "AI Detector работает", "version": "2.0"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_base64 = body.get("imageBase64", "")
        image_url = body.get("imageUrl", "")

        img_data = None

        # Приоритет: base64 (самый надёжный)
        if image_base64:
            try:
                # Удаляем data URI префикс если есть
                if "," in image_base64:
                    image_base64 = image_base64.split(",")[1]
                
                # Декодируем base64
                img_data = base64.b64decode(image_base64)
            except Exception as e:
                logger.error(f"Ошибка декодирования base64: {e}")
                return JSONResponse(
                    content={"error": True, "message": "Невалидный base64 формат"},
                    status_code=400
                )
        
        elif image_url:
            try:
                # Обработка Wix URL
                final_url = image_url
                if "wix:image" in image_url:
                    parts = image_url.split('/')
                    if len(parts) > 3:
                        final_url = f"https://static.wixstatic.com/media/{parts[3]}"
                
                logger.info(f"Загрузка изображения с URL: {final_url}")
                
                # Скачиваем картинку с корректными headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                resp = requests.get(final_url, timeout=15, headers=headers)
                resp.raise_for_status()
                img_data = resp.content
                
                if not img_data:
                    return JSONResponse(
                        content={"error": True, "message": "URL вернул пустые данные"},
                        status_code=400
                    )
            except requests.RequestException as e:
                logger.error(f"Ошибка загрузки URL: {e}")
                return JSONResponse(
                    content={"error": True, "message": f"Не удалось загрузить изображение с URL: {str(e)}"},
                    status_code=400
                )

        if not img_data:
            return JSONResponse(
                content={"error": True, "message": "Не передано ни base64, ни URL"},
                status_code=400
            )

        # Валидируем и оптимизируем изображение
        try:
            img_data = validate_and_optimize_image(img_data)
        except ValueError as e:
            return JSONResponse(
                content={"error": True, "message": str(e)},
                status_code=400
            )

        # Отправляем в Sightengine с корректными параметрами
        params = {
            'models': 'genai',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
            'version': '2.0'  # Используем последнюю версию API
        }
        
        files = {'media': ('image.jpg', img_data, 'image/jpeg')}
        
        logger.info(f"Отправка запроса в Sightengine API")
        response = requests.post(API_URL, params=params, files=files, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Ответ Sightengine: {data}")

        # Проверяем статус ответа
        if data.get('status') == 'failure':
            error_msg = data.get('error', {}).get('message', 'Неизвестная ошибка API')
            logger.error(f"API ошибка: {error_msg}")
            return JSONResponse(
                content={"error": True, "message": f"API ошибка: {error_msg}"},
                status_code=400
            )

        # Извлекаем вероятность AI
        ai_prob = data.get('genai', {}).get('prob', 0)
        
        # Логируем для отладки
        logger.info(f"AI вероятность: {ai_prob}")

        # Определяем результат с использованием пороговых значений
        if ai_prob >= AI_THRESHOLD_HIGH:
            is_ai = True
            confidence = "high"
        elif ai_prob <= AI_THRESHOLD_LOW:
            is_ai = False
            confidence = "high"
        else:
            # Неопределённость - используем середину
            is_ai = ai_prob > 0.5
            confidence = "low"

        return {
            "is_ai": is_ai,
            "probability": round(ai_prob, 3),
            "percentage": round(ai_prob * 100, 1),
            "confidence": confidence,
            "threshold_high": AI_THRESHOLD_HIGH,
            "threshold_low": AI_THRESHOLD_LOW,
            "error": False,
            "raw_response": data.get('genai', {})  # Для отладки
        }

    except requests.Timeout:
        logger.error("Timeout при запросе к API")
        return JSONResponse(
            content={"error": True, "message": "Timeout при обработке изображения"},
            status_code=504
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
        return JSONResponse(
            content={"error": True, "message": f"Ошибка сервера: {str(e)}"},
            status_code=500
        )

@app.post("/health")
def health():
    """Проверка здоровья сервиса"""
    return {"status": "ok"}

