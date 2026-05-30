import os
import base64
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)  # Разрешаем запросы со стороны Wix

# 1. Настраиваем API-ключ OpenAI
# Рекомендуется добавить переменную OPENAI_API_KEY в настройках Render (Environment Variables)
# Или для теста временно вставьте свой ключ прямо в код ниже
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Инициализируем клиент OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def home():
    return "Python OpenAI GPT-4o-mini Detector is Running!"

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": True, "message": "Нет данных изображения в запросе"}), 400

        base64_image = data['image']
        
        # Очищаем base64 строку от метаданных веб-заголовков, если они есть
        if "," in base64_image:
            base64_image = base64_image.split(",")[1]

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

        # 2. Вызываем GPT-4o-mini (самая быстрая и дешевая модель с поддержкой зрения)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},  # Гарантирует получение строгого JSON без лишнего текста
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_instruction},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
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

        # Возвращаем результат в формате, который ожидает твой код на Wix
        return jsonify({
            "is_ai": result.get("is_ai", False),
            "confidence": result.get("confidence", 0),
            "reason": result.get("reason", "Анализ завершен успешно."),
            "error": False
        })

    except Exception as e:
        return jsonify({"error": True, "message": f"Ошибка на сервере OpenAI: {str(e)[:50]}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
