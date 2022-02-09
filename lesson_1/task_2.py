import requests
from decouple import config


WEATHER_SECRET = config("WEATHER_SECRET")
CITY = input("Enter the city where you want to check weather: ")


def get_coord(city):
    res = requests.get(
        f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={WEATHER_SECRET}"
    )
    if not res.json():
        print(f"City {city} does not exist.")
        return None
    coordinates = (res.json()[0]["lat"], res.json()[0]["lon"])
    return coordinates


def get_weather(city):
    coordinates = get_coord(city)
    if not coordinates:
        return None
    lat, lon = coordinates[0], coordinates[1]
    res = requests.get(
        f"http://api.openweathermap.org/data/2.5/weather?"
        f"units=metric&lat={lat}&lon={lon}&appid={WEATHER_SECRET}"
    )
    temp = res.json()["main"]["temp"]
    weather_type = res.json()["weather"][0]["main"]
    weather_desc = res.json()["weather"][0]["description"]
    print(
        f"Today in {city} is {temp}\u2103\n{weather_type}, more precisely - {weather_desc}"
    )


def main():
    get_weather(CITY)


if __name__ == "__main__":
    main()
