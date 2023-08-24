import os
import requests

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


def get_citycode(city):
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "city": city,
        "key": WEATHER_API_KEY,
        "address": city
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        citycode = data["geocodes"][0]["adcode"]
        print(f"{city}: {citycode}")
        return citycode
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during GET request: {e}")
        return None


def _get_current_weather(city):
    citycode = get_citycode(city)
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "city": citycode,
        "key": WEATHER_API_KEY,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        w = data["lives"][0]
        weather = f"今天{w['province']}{w['city']}天气{w['weather']}，温度{w['temperature']}°C，湿度{w['humidity']}%，风向{w['winddirection']}，风力{w['windpower']}。"
        return weather
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during GET request: {e}")
        return None


def _get_n_day_weather_forecast(city, num_days):
    if num_days > 3 or num_days < 0:
        return "最多查询未来3天的预报"

    citycode = get_citycode(city)
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "city": citycode,
        "key": WEATHER_API_KEY,
        "extensions": "all"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        forecast = data["forecasts"][0]["casts"][num_days]
        date = forecast["date"]
        day_weather = forecast["dayweather"]
        night_weather = forecast["nightweather"]
        day_temp = forecast["daytemp"]
        night_temp = forecast["nighttemp"]
        day_wind = forecast["daywind"]
        night_wind = forecast["nightwind"]
        day_power = forecast["daypower"]
        night_power = forecast["nightpower"]

        weather = f"{date}，白天天气{day_weather}，夜晚天气{night_weather}，白天温度{day_temp}°C，夜晚温度{night_temp}°C，白天风向{day_wind}，夜晚风向{night_wind}，白天风力{day_power}，夜晚风力{night_power}。"

        return weather
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during GET request: {e}")
        return None


def test():
    city = "上海"
    num_days = 2
    weather_info = _get_current_weather(city)
    print(weather_info)

    weather_forecast = _get_n_day_weather_forecast(city, num_days)
    print(weather_forecast)


if __name__ == "__main__":
    test()
