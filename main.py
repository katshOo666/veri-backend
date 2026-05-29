// Вставьте этот код в Wix Velo (на страницу с загрузчиком)
import {fetch} from 'wix-fetch';

// ID ваших элементов
const imageUploader = $w("#yourImageUploader");
const resultText = $w("#yourResultText");
const analyzeButton = $w("#yourButton");

// Ваш сервер (замените на реальный URL)
const SERVER_URL = "http://localhost:8000/analyze";

analyzeButton.onClick(async () => {
    const uploadedImage = imageUploader.value;
    
    if (!uploadedImage) {
        resultText.text = "Сначала загрузите изображение";
        return;
    }
    
    resultText.text = "🔍 Анализируем...";
    
    try {
        // Получаем файл и конвертируем в base64
        const imageUrl = uploadedImage[0].url;
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        
        const reader = new FileReader();
        
        const result = await new Promise((resolve) => {
            reader.onloadend = async function() {
                const base64Image = reader.result;
                
                const apiResponse = await fetch(SERVER_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ imageBase64: base64Image })
                });
                
                resolve(await apiResponse.json());
            };
            reader.readAsDataURL(blob);
        });
        
        if (result.error) {
            resultText.text = `❌ ${result.message}`;
        } else if (result.is_ai) {
            resultText.text = `🤖 Это AI изображение (${result.percentage}% уверенности)`;
        } else {
            resultText.text = `📸 Это реальное изображение (${result.percentage}% уверенности)`;
        }
        
    } catch (error) {
        resultText.text = "❌ Ошибка при анализе";
        console.error(error);
    }
});
