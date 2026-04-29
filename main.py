import os
import httpx
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Only the essential keys
LINQ_TOKEN = os.getenv("LINQ_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.linqapp.com/api/partner/v3"

async def get_weather(city: str):
    """Fetches real-time weather data from OpenWeatherMap"""
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=imperial"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                return f"The current weather in {city.title()} is {temp}°F with {desc}. ☀️"
            return f"I couldn't find weather data for '{city}'. Check the spelling! ☁️"
        except Exception:
            return "Weather service is currently unavailable. 🛠️"

@app.post("/webhook")
async def handle_linq_message(request: Request):
    try:
        data = await request.json()
        event_type = data.get("event_type")

        if event_type == "message.received" and data["data"]["direction"] == "inbound":
            chat_id = data["data"]["chat"]["id"]
            user_text = data["data"]["parts"][0]["value"].strip()
            
            print(f"DEBUG: User said: {user_text}")

            # Back to deterministic logic: User text = City Name
            weather_report = await get_weather(user_text)
            
            await send_linq_reply(chat_id, weather_report)
            
        return {"status": "ok"}
    except Exception as e:
        print(f"ERROR: {e}")
        return {"status": "error", "detail": str(e)}

async def send_linq_reply(chat_id: str, message: str):
    url = f"{BASE_URL}/chats/{chat_id}/messages"
    headers = {
        "Authorization": f"Bearer {LINQ_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": {
            "parts": [{"type": "text", "value": message}]
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        print(f"LINQ RESPONSE: {response.status_code}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)