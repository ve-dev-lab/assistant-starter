import json
import httpx
import asyncio
from datetime import datetime

async def fetch_async(url: str) -> str:
    print(f'Start  {url}')
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
        response.raise_for_status()
        print(f'Завершили запрос  {url}, статус {response.status_code}')
        body_text = response.text
        print(f'Длина тела ответа {len(body_text)} символов')
        return body_text
    except httpx.HTTPError as error:
        print(f'Произошла ошибка {error}')
        return ''

# Сводка по IP, включая координаты и код валюты
# https://ipapi.co/json

async def fetch_location(url: str) -> dict:
    result = await fetch_async(url)
    geodata = json.loads(result)
    return geodata

# Метео-данные по координатам
# https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&hourly=temperature_2m
# Курс валюты к биткойну
# https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd

async def fetch_services():
    geodata = await fetch_location("https://ipapi.co/json")
    latitude = geodata["latitude"]
    longitude = geodata["longitude"]
    currency = geodata["currency"]
    location = "{}/{}".format(geodata["city"], geodata["country_name"])

    weather_url = "https://api.open-meteo.com/v1/forecast?latitude={}&longitude={}&hourly=temperature_2m".format(latitude, longitude)
    currency_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies={}".format(currency)
    services = {
        'Service_Currency': currency_url,
        'Service_Weather': weather_url
    }
    print(f"\n# Данные по Geo-IP\nШирота: {latitude}\nДолгота: {longitude}\nРасположение: {location}\nВалюта: {currency}")
    tasks = [fetch_async(url=url) for url in services.values()]
    print(f'\n===== Началась асинхронная обработка HTTP =====\n')
    start = asyncio.get_event_loop().time()
    responses = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    total_time = end_time - start
    print(f'\n===== Все запросы выполнились за  {total_time:.2f}')
    result = {}
    for service_name, response_body in zip(services.keys(), responses):
        result[service_name] = response_body
        if service_name == 'Service_Currency':
            data_currency = json.loads(result[service_name])
            coin = next(iter(data_currency))
            inner = data_currency[coin]
            currency = next(iter(inner))
            rate = inner[currency]
            print(f"\n# Данные сервиса курсов валют\nКурс: {rate} {currency}/{coin}")
        if service_name == 'Service_Weather':
            data_weather = json.loads(result[service_name])

            hourly = data_weather['hourly']
            times = hourly['time']
            temps = hourly['temperature_2m']

            # Текущий час (сегодняшний)
            now = datetime.now()
            current_hour = now.strftime('%Y-%m-%dT%H:00')
            if current_hour in times:
                idx = times.index(current_hour)
                temp = temps[idx]
                print(f"\n# Данные сервиса погоды\nТемпература сейчас: {temp}°C (координаты: {data_weather['latitude']}, {data_weather['longitude']})")
            else:
                # Ближайший час
                nearest_idx = 0
                print(f"Прогноз на ближайший час: {temps[0]}°C")
    return result

async def async_main() -> None:
    print(f'\n===== Начало обработки. Получение данных GeoIP =====\n')
    summary = await fetch_services()
    print(f'\n===== Завершилась асинхронная обработка HTTP =====\n')
    if not summary:
        print('Пустой ответ')

if __name__ == '__main__':
    asyncio.run(async_main())