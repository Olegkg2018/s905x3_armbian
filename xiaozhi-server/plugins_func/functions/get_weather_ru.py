import requests
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

GET_WEATHER_RU_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_weather_ru",
        "description": "Получить текущую погоду для указанного города или населенного пункта. Вызывай этот инструмент, когда пользователь спрашивает о погоде.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Название города или населенного пункта на русском языке, например: Москва, Екатеринбург.",
                }
            },
            "required": ["location"],
        },
    },
}

# Weather codes from Open-Meteo (WMO)
WEATHER_CODES = {
    0: "ясно",
    1: "преимущественно ясно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман",
    48: "изморозь",
    51: "легкая морось",
    53: "умеренная морось",
    55: "плотная морось",
    56: "ледяная морось",
    57: "плотная ледяная морось",
    61: "слабый дождь",
    63: "умеренный дождь",
    65: "сильный дождь",
    66: "слабый ледяной дождь",
    67: "сильный ледяной дождь",
    71: "слабый снегопад",
    73: "умеренный снегопад",
    75: "сильный снегопад",
    77: "снежные зерна",
    80: "слабый ливневый дождь",
    81: "умеренный ливневый дождь",
    82: "сильный ливневый дождь",
    85: "слабый ливневый снегопад",
    86: "сильный ливневый снегопад",
    95: "гроза",
    96: "гроза со слабым градом",
    99: "гроза с сильным градом",
}

@register_function("get_weather_ru", GET_WEATHER_RU_FUNCTION_DESC, ToolType.WAIT)
def get_weather_ru(conn: "ConnectionHandler", location: str = "Москва"):
    logger.bind(tag=TAG).info(f"get_weather_ru вызван для: {location}")
    if not location:
        location = "Москва"
        
    try:
        # 1. Geocoding to get lat/lon
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=ru"
        geo_resp = requests.get(geo_url, timeout=10)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        
        if not geo_data.get("results"):
            return ActionResponse(
                action=Action.REQLLM,
                result=f"Не удалось найти географические координаты для города '{location}'.",
                response=None
            )
            
        city_info = geo_data["results"][0]
        lat = city_info["latitude"]
        lon = city_info["longitude"]
        city_name = city_info.get("name", location)
        country = city_info.get("country", "")
        
        # 2. Weather forecast
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=auto"
        weather_resp = requests.get(weather_url, timeout=10)
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()
        
        current = weather_data.get("current", {})
        temp = current.get("temperature_2m", 0)
        apparent_temp = current.get("apparent_temperature", temp)
        humidity = current.get("relative_humidity_2m", 0)
        code = current.get("weather_code", 0)
        wind_speed = current.get("wind_speed_10m", 0)
        
        weather_desc = WEATHER_CODES.get(code, "неизвестные погодные условия")
        
        result_text = (
            f"Погода в городе {city_name} ({country}): сейчас там {weather_desc}, "
            f"температура воздуха составляет {temp}°C (ощущается как {apparent_temp}°C), "
            f"относительная влажность {humidity}%, скорость ветра {wind_speed} м/с."
        )
        logger.bind(tag=TAG).info(f"get_weather_ru успешный результат: {result_text}")
        return ActionResponse(action=Action.REQLLM, result=result_text, response=None)
        
    except Exception as e:
        logger.bind(tag=TAG).error(f"Ошибка получения погоды: {e}")
        return ActionResponse(
            action=Action.REQLLM,
            result=f"Не удалось получить погоду для '{location}' из-за ошибки сети или сервера.",
            response=None
        )
