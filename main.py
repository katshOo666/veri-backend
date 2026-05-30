import os
import re
import requests
import base64
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ВСТАВЬ СВОИ ДАННЫЕ СЮДА (лучше через переменные окружения):
SIGHTENGINE_USER = "145435152"
SIGHTENGINE_SECRET = "wa4ykGt9ezK2MUZuTCURcfL2wDjYXpi8"
API_URL = "https://api.sightengine.com/1.0/check.json"

@app.get("/")
def home():
    return {"status": "Live", "message": "AI Detector работает"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        raw_url = body.get("imageUrl", "")
        image_base64 = body.get("imageBase64", "")
        
        print(f"📥 Получен URL: {raw_url[:100] if raw_url else 'None'}")
        
        # --- ЕСЛИ ПРИСЛАЛИ BASE64 (НАДЁЖНЫЙ СПОСОБ) ---
        if image_base64:
            print(f"🔧 Получено base64 изображение, длина: {len(image_base64)} символов")
            # Отправляем файл напрямую в Sightengine (POST с файлом)
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            
            img_bytes = base64.b64decode(image_base64)
            
            params = {
                'models': 'genai',
                'api_use': SIGHTENGINE_USER,
                'api_secret': SIGHTENGINE_SECRET,
            }
            
            files = {
                'media': ('image.jpg', img_bytes, 'image/jpeg')
            }
            
            print(f"🔄 Отправляю файл в Sightengine...")
            response = requests.post(API_URL, params=params, files=files, timeout=30)
            data = response.json()
            print(f"📊 Ответ Sightengine: {data}")
            
            # Обрабатываем ответ
            if data.get('status') == 'failure':
                error_msg = data.get('error', {}).get('message', 'Неизвестная ошибка')
                return {"error": True, "message": f"Sightengine: {error_msg}"}
            
            ai_prob = data.get('genai', {}).get('prob', 0)
            
            return {
                "is_ai": ai_prob > 0.5,
                "percentage": round(ai_prob * 100, 1),
                "raw_score": round(ai_prob, 3),
                "error": False,
                "method": "base64"
            }
        
        # --- ЕСЛИ ПРИСЛАЛИ URL ---
        if not raw_url:
            return {"error": True, "message": "URL изображения не предоставлен"}
        
        # --- УЛУЧШЕННАЯ ОБРАБОТКА Wix ССЫЛОК ---
        final_url = None
        
        # Случай 1: Обычная ссылка на Wix static
        if "wixstatic.com" in raw_url:
            final_url = raw_url
            print(f"✅ Обычная Wix static ссылка")
        
        # Случай 2: Специальный формат wix:image
        elif "wix:image" in raw_url:
            print(f"🔧 Обнаружен формат wix:image, обрабатываю...")
            # Метод 1: разбиваем по слешам (как в примере с форума Wix)
            try:
                parts = raw_url.split('/')
                if len(parts) > 3:
                    img_id = parts[3]  # ID изображения
                    final_url = f"https://static.wixstatic.com/media/{img_id}"
                    print(f"✅ Извлечен ID через split: {img_id}")
            except:
                pass
            
            # Метод 2: регулярные выражения (резервный)
            if not final_url:
                patterns = [
                    r'wix:image://v1/([^/?#]+)',
                    r'wix:image://([^/?#]+)',
                    r'v1/([a-f0-9_~]+)',
                    r'media/([a-f0-9_~]+)'
                ]
                for pattern in patterns:
                    match = re.search(pattern, raw_url)
                    if match:
                        img_id = match.group(1)
                        final_url = f"https://static.wixstatic.com/media/{img_id}"
                        print(f"✅ Извлечен ID через regex: {img_id}")
                        break
        
        # Случай 3: Обычный HTTP/HTTPS URL
        elif raw_url.startswith("http"):
            final_url = raw_url
            print(f"✅ Обычная HTTP ссылка")
        
        # Если не удалось обработать
        if not final_url:
            print(f"❌ Не удалось обработать ссылку")
            return {"error": True, "message": f"Не удалось обработать ссылку. Формат: {raw_url[:100]}"}
        
        print(f"📸 Финальный URL: {final_url}")
        
        # --- ПРОВЕРКА ДОСТУПНОСТИ ИЗОБРАЖЕНИЯ ---
        try:
            test_response = requests.head(final_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if test_response.status_code != 200:
                print(f"⚠️ Изображение не доступно, статус: {test_response.status_code}")
                # Пробуем скачать через GET
                test_response = requests.get(final_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if test_response.status_code != 200:
                    return {"error": True, "message": f"Изображение не найдено (статус: {test_response.status_code})"}
            print(f"✅ Изображение доступно")
        except Exception as e:
            print(f"⚠️ Не удалось проверить доступность: {e}")
        
        # --- ЗАПРОС К SIGHTENGINE (через URL) ---
        params = {
            'models': 'genai',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
            'url': final_url
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"🔄 Отправляю запрос в Sightengine...")
        response = requests.get(API_URL, params=params, headers=headers, timeout=30)
        data = response.json()
        
        print(f"📊 Ответ Sightengine: {data}")
        
        # Проверка на ошибки
        if data.get('status') == 'failure':
            error_msg = data.get('error', {}).get('message', 'Неизвестная ошибка')
            print(f"❌ Ошибка Sightengine: {error_msg}")
            return {"error": True, "message": f"Sightengine: {error_msg}"}
        
        # Получаем вероятность AI
        ai_prob = 0
        if 'genai' in data:
            ai_prob = data['genai'].get('prob', 0)
            print(f"🤖 Вероятность AI из genai: {ai_prob}")
        elif 'type' in data and 'ai' in data['type']:
            ai_prob = data['type']['ai']
            print(f"🤖 Вероятность AI из type.ai: {ai_prob}")
        else:
            print(f"⚠️ Не найден ключ 'genai' или 'type.ai' в ответе")
            print(f"📋 Полный ответ: {data}")
        
        # Определяем результат
        is_ai = ai_prob > 0.5
        result_text = "AI" if is_ai else "Real"
        
        print(f"🎯 Результат: {result_text} ({round(ai_prob * 100, 1)}%)")
        
        return {
            "is_ai": is_ai,
            "percentage": round(ai_prob * 100, 1),
            "raw_score": round(ai_prob, 3),
            "error": False,
            "method": "url"
        }
        
    except requests.exceptions.Timeout:
        print(f"❌ Таймаут")
        return {"error": True, "message": "Превышено время ожидания. Попробуйте еще раз."}
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return {"error": True, "message": f"Ошибка соединения: {str(e)}"}
    except Exception as e:
        print(f"❌ Общая ошибка: {str(e)}")
        return {"error": True, "message": "Ошибка сервера. Попробуйте еще раз."}

# ТЕСТОВЫЙ ENDPOINT для отладки
@app.post("/test-url")
async def test_url(request: Request):
    """Тестовый endpoint для проверки обработки URL и Sightengine"""
    try:
        body = await request.json()
        raw_url = body.get("imageUrl", "")
        image_base64 = body.get("imageBase64", "")
        
        print(f"🧪 ТЕСТ: Получен URL: {raw_url[:100] if raw_url else 'None'}")
        if image_base64:
            print(f"🧪 ТЕСТ: Получено base64, длина: {len(image_base64)} символов")
        
        result = {
            "original_url": raw_url,
            "has_base64": bool(image_base64)
        }
        
        # Если есть base64, проверяем его
        if image_base64:
            try:
                if "," in image_base64:
                    image_base64 = image_base64.split(",")[1]
                img_bytes = base64.b64decode(image_base64)
                result["base64_valid"] = True
                result["base64_size"] = len(img_bytes)
            except Exception as e:
                result["base64_valid"] = False
                result["base64_error"] = str(e)
        
        # Обработка URL
        if raw_url:
            final_url = raw_url
            if "wix:image" in raw_url:
                try:
                    parts = raw_url.split('/')
                    if len(parts) > 3:
                        img_id = parts[3]
                        final_url = f"https://static.wixstatic.com/media/{img_id}"
                except:
                    pass
            
            result["processed_url"] = final_url
            
            # Проверяем доступность
            try:
                test_resp = requests.head(final_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                result["url_status"] = test_resp.status_code
            except Exception as e:
                result["url_error"] = str(e)
            
            # Прямой запрос к Sightengine
            params = {
                'models': 'genai',
                'api_user': SIGHTENGINE_USER,
                'api_secret': SIGHTENGINE_SECRET,
                'url': final_url
            }
            
            response = requests.get(API_URL, params=params, timeout=30)
            result["sightengine_response"] = response.json()
            result["status_code"] = response.status_code
        
        return result
    except Exception as e:
        return {"error": str(e)}

# ПРОСТОЙ ТЕСТ Sightengine (без изображения)
@app.get("/test-sightengine")
async def test_sightengine():
    """Проверяет, работает ли API ключ Sightengine"""
    try:
        params = {
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET
        }
        response = requests.get("https://api.sightengine.com/1.0/account.json", params=params)
        return response.json()
    except Exception as e:
        return {"error": str(e)}
