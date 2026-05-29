import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import base64
import re
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env (рекомендуется для безопасности)
load_dotenv()

app = FastAPI()

# Настройка CORS для работы с вашим Wix-сайтом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- КОНФИГУРАЦИЯ SIGHTENGINE (БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ДАННЫХ) ----
# Для работы с Sightengine нужны две вещи: API User и API Secret[citation:4][citation:7].
# Получить их можно, создав бесплатный аккаунт на https://sightengine.com и зайдя в раздел "API keys".

# !!! ВАЖНО: Никогда не зашивайте эти данные прямо в код. Используйте переменные окружения !!!
SIGHTENGINE_USER = os.getenv("SIGHTENGINE_USER")
SIGHTENGINE_SECRET = os.getenv("SIGHTENGINE_SECRET")

# Проверяем, что переменные окружения загружены правильно
if not SIGHTENGINE_USER or not SIGHTENGINE_SECRET:
    print("ОШИБКА: Не найдены учетные данные Sightengine!")
    print("Пожалуйста, создайте файл .env в корне проекта и добавьте в него:")
    print("SIGHTENGINE_USER=ваш_api_user")
    print("SIGHTENGINE_SECRET=ваш_api_secret")
    # В режиме разработки можно выбросить исключение, в проде — лучше корректно завершиться.
    # raise ValueError("Missing Sightengine credentials")

# URL и параметры API Sightengine
SIGHTENGINE_API_URL = "https://api.sightengine.com/1.0/check.json"

# Модель для определения AI-контента. У Sightengine это 'genai'[citation:2][citation:5].
# Если нужно проверить еще что-то (например, nudity, gore), можно добавить через запятую:
# 'genai,nudity,gore'
DETECTION_MODELS = 'genai'

# Рекомендованный порог для определения AI (0.5 - хорошая отправная точка)[citation:5]
AI_THRESHOLD = 0.5

# --------------------------------------------------------------

@app.get("/")
def home():
    return {"status": "OK", "message": "AI Image Detector (Sightengine) работает"}

@app.post("/analyze")
async def analyze(request: Request):
    """
    Основной endpoint для анализа изображения.
    Принимает JSON с полем imageUrl или imageBase64.
    """
    try:
        body = await request.json()
        
        # Определяем, откуда брать картинку: по URL или из base64-строки
        image_url = body.get("imageUrl", "")
        image_base64 = body.get("imageBase64", "")
        
        img_data_for_sightengine = None
        
        # СЛУЧАЙ 1: Изображение пришло как base64 (самый надежный способ для Wix)
        if image_base64:
            # Очищаем строку от префикса "data:image/...;base64,"
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            # Декодируем base64 в байты
            img_bytes = base64.b64decode(image_base64)
            # Для Sightengine мы будем отправлять файл напрямую, а не через URL
            img_data_for_sightengine = ('media', ('image.jpg', img_bytes, 'image/jpeg'))
        
        # СЛУЧАЙ 2: Изображение пришло как URL
        elif image_url:
            final_url = image_url
            
            # Обработка специальных ссылок из Wix
            if "wix:image" in image_url:
                match = re.search(r'wix:image://v1/([^/?#]+)', image_url)
                if match:
                    final_url = f"https://static.wixstatic.com/media/{match.group(1)}"
                else:
                    match = re.search(r'wix:image://([^/?#]+)', image_url)
                    if match:
                        final_url = f"https://static.wixstatic.com/media/{match.group(1)}"
            
            # Для URL-адресов мы будем отправлять ссылку, а не сам файл
            # Это удобно, если картинка уже лежит в открытом доступе
            pass
        
        else:
            return {"error": True, "message": "Не удалось получить изображение: ни URL, ни base64 не предоставлены"}
        
        # --- ОТПРАВКА ЗАПРОСА В SIGHTENGINE ---
        # Документация: https://sightengine.com/docs/reference
        # Используем два подхода в зависимости от того, что у нас есть: файл или URL.
        
        params = {
            'models': DETECTION_MODELS,
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
        }
        
        files = None
        if img_data_for_sightengine:
            # Отправляем файл напрямую (метод POST с multipart/form-data)[citation:6][citation:9]
            response = requests.post(
                SIGHTENGINE_API_URL,
                params=params,
                files={'media': img_data_for_sightengine[1]}
            )
        elif image_url:
            # Отправляем URL (метод GET с параметрами в строке запроса)[citation:5]
            params['url'] = final_url
            response = requests.get(SIGHTENGINE_API_URL, params=params)
        else:
            return {"error": True, "message": "Нет данных для отправки в Sightengine"}
        
        # --- ОБРАБОТКА ОТВЕТА ОТ SIGHTENGINE ---
        if response.status_code != 200:
            # Пробуем получить более детальную ошибку от API
            try:
                error_detail = response.json()
                error_message = error_detail.get('error', {}).get('message', 'Неизвестная ошибка')
            except:
                error_message = f"HTTP {response.status_code}"
            return {"error": True, "message": f"Ошибка при обращении к Sightengine: {error_message}"}
        
        result = response.json()
        
        # Проверяем, есть ли в ответе данные о модели 'genai'
        if result.get('status') != 'success':
            return {"error": True, "message": f"Sightengine вернул ошибку: {result.get('error', {}).get('message', 'Unknown error')}"}
        
        # Извлекаем вероятность того, что изображение сгенерировано AI.
        # В ответе Sightengine это поле `result.genai.prob`[citation:5].
        genai_data = result.get('genai')
        if genai_data is None:
            return {"error": True, "message": "Модель 'genai' не была применена или не поддерживается вашим тарифом."}
        
        ai_probability = genai_data.get('prob', 0)
        is_ai = ai_probability > AI_THRESHOLD
        
        # Формируем ответ для клиента (вашего Wix-бота)
        return {
            "is_ai": is_ai,
            "percentage": round(ai_probability * 100, 1),
            "confidence": round(ai_probability, 3),
            "error": False,
            "source": "sightengine"
        }
        
    except Exception as e:
        # Логирование ошибки на сервере для отладки
        print(f"Критическая ошибка в /analyze: {str(e)}")
        return {"error": True, "message": f"Внутренняя ошибка сервера: {str(e)}"}

# Точка входа для локального запуска
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
