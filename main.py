import { fetch } from 'wix-fetch';

$w.onReady(function () {
    // Убедись, что ID кнопки в редакторе именно 'checkButton'
    $w('#checkButton').onClick(async () => {
        
        // 1. Проверка: выбрал ли пользователь файл?
        if ($w('#uploadButton').value.length > 0) {
            
            $w('#resultText').text = "Загрузка изображения...";
            $w('#resultText').style.color = "#000000"; 

            try {
                // 2. Загружаем файл на сервер Wix
                let uploadedFile = await $w('#uploadButton').uploadFiles();
                let fileUrl = uploadedFile[0].fileUrl;

                // 3. ПАУЗА (Критически важно!)
                // Даем Wix 2 секунды, чтобы файл стал доступен по ссылке
                $w('#resultText').text = "Анализируем нейросетью...";
                await new Promise(resolve => setTimeout(resolve, 2000));

                // Твой адрес на Render
                const backendUrl = "https://veri-backend-d0dj.onrender.com/analyze"; 

                // 4. Отправка запроса
                const response = await fetch(backendUrl, {
                    method: 'POST',
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ "imageUrl": fileUrl })
                });

                const data = await response.json();

                // 5. Обработка вердикта
                if (data.error) {
                    $w('#resultText').text = "Ошибка: " + data.message;
                    $w('#resultText').style.color = "#FF0000";
                } else {
                    // Если вероятность ИИ выше 50%
                    if (data.is_ai) {
                        $w('#resultText').text = ⚠️ Это ИИ (Вероятность: ${data.percentage}%);
                        $w('#resultText').style.color = "#FF0000"; // Красный для ИИ
                    } else {
                        $w('#resultText').text = ✅ Это человек (Вероятность ИИ: ${data.percentage}%);
                        $w('#resultText').style.color = "#008000"; // Зеленый для фото
                    }
                }

            } catch (err) {
                $w('#resultText').text = "Сервер не отвечает. Попробуйте еще раз.";
                $w('#resultText').style.color = "#FF0000";
                console.error("Ошибка запроса:", err);
            }
        } else {
            $w('#resultText').text = "Пожалуйста, сначала выберите фото!";
            $w('#resultText').style.color = "#FF8C00"; // Оранжевый
        }
    });
});
