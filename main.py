from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"
HEADERS = {"Authorization": "Bearer YOUR_HUGGINGFACE_TOKEN"}  # Замените на ваш токен

@app.get("/")
def home():
    return {"status": "OK"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        raw_url = body.get("imageUrl", "")
        
        if not raw_url:
            return {"error": True, "message": "URL изображения не предоставлен"}
        
        # --- ИСПРАВЛЕННАЯ МАГИЯ ВОССТАНОВЛЕНИЯ ССЫЛКИ ---
        final_url = None
        
        # Обработка Wix ссылок
        if "wix:image" in raw_url:
            # Извлекаем ID изображения
            match = re.search(r'wix:image://v1/([^/?#]+)', raw_url)
            if match:
                img_id = match.group(1)
                final_url = f"https://static.wixstatic.com/media/{img_id}"
        elif "static.wixstatic.com" in raw_url:
            final_url = raw_url
        elif raw_url.startswith("https://") or raw_url.startswith("http://"):
            final_url = raw_url
        else:
            # Если ссылка кривая, пробуем её исправить
            if raw_url.startswith("https:") and "//" not in raw_url:
                final_url = raw_url.replace("https:", "https://")
            else:
                final_url = raw_url
        
        # Проверяем, что ссылка валидна
        if not final_url or len(final_url) < 10:
            return {"error": True, "message": "Не удалось получить ссылку на изображение"}
        
        # Скачиваем изображение
        try:
            img_response = requests.get(final_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            img_response.raise_for_status()
            img_data = img_response.content
        except requests.exceptions.RequestException as e:
            return {"error": True, "message": f"Не удалось загрузить изображение: {str(e)}"}
        
        # Отправляем в Hugging Face с авторизацией
        max_attempts = 4
        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    API_URL, 
                    headers=HEADERS,  # Добавляем заголовки авторизации
                    data=img_data,
                    timeout=30
                )
                
                # Проверяем статус ответа
                if response.status_code == 503:
                    result = response.json()
                    if "estimated_time" in result:
                        wait_time = min(result.get("estimated_time", 5), 10)
                        time.sleep(wait_time)
                        continue
                
                elif response.status_code == 200:
                    result = response.json()
                    
                    # Обрабатываем ответ
                    if isinstance(result, list) and len(result) > 0:
                        # Ищем метку AI/real
                        ai_score = 0
                        for item in result:
                            label = item.get('label', '').lower()
                            score = item.get('score', 0)
                            
                            # В зависимости от модели могут быть разные названия меток
                            if label in ['artificial', 'ai', 'fake', 'label_1', 'AI']:
                                ai_score = score
                                break
                            elif label in ['real', 'human', 'label_0']:
                                ai_score = 1 - score
                                break
                            else:
                                # Если метки нестандартные, используем первую
                                ai_score = score if 'artificial' in label else 1 - score
                        
                        is_ai = ai_score > 0.5
                        percentage = round(ai_score * 100, 1)
                        
                        return {
                            "is_ai": is_ai,
                            "percentage": percentage,
                            "confidence": ai_score,
                            "error": False
                        }
                    else:
                        return {"error": True, "message": "Неожиданный формат ответа от модели"}
                
                else:
                    # Другие ошибки
                    return {
                        "error": True, 
                        "message": f"Ошибка API: {response.status_code}"
                    }
                    
            except requests.exceptions.Timeout:
                if attempt == max_attempts - 1:
                    return {"error": True, "message": "Превышено время ожидания ответа от модели"}
                continue
            except Exception as e:
                if attempt == max_attempts - 1:
                    return {"error": True, "message": f"Ошибка при анализе: {str(e)}"}
                continue
        
        return {"error": True, "message": "Модель не отвечает. Попробуйте позже"}
        
    except Exception as e:
        return {"error": True, "message": f"Ошибка сервера: {str(e)}"}

# Добавляем endpoint для проверки статуса модели
@app.get("/model-status")
async def model_status():
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return {"status": "ready", "message": "Модель готова к работе"}
        else:
            return {"status": "loading", "message": "Модель загружается"}
    except:
        return {"status": "error", "message": "Не удалось проверить статус модели"}
