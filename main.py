import { fetch } from 'wix-fetch';

export async function button_click(event) {
    const imageUrl = $w("#imageField").src; // Убедись, что ID верный!
    const backendUrl = "https://veri-backend-d0dj.onrender.com/analyze";

    $w("#resultText").text = "Анализирую...";

    try {
        const response = await fetch(backendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ "imageUrl": imageUrl })
        });

        const data = await response.json();

        if (data.error) {
            $w("#resultText").text = data.message;
        } else {
            // Вот тут магия!
            $w("#resultText").text = "Вероятность ИИ: " + data.percentage + "%";
        }

    } catch (error) {
        $w("#resultText").text = "Ошибка соединения с сервером";
    }
}
                time.sleep(5)
                continue
            
            if isinstance(result, list):
                ai_score = next((item['score'] for item in result if item['label'].lower() in ['artificial', 'ai', 'fake']), 0)
                return {"is_ai": ai_score > 0.5, "percentage": round(ai_score * 100, 2), "error": False}
        
        return {"error": True, "message": "Нейросеть просыпается, нажми еще раз через 5 сек"}
    except:
        return {"error": True, "message": "Нажми кнопку еще раз"}
