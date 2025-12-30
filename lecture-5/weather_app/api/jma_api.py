import requests

AREA_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"


def get_area_data():
    return requests.get(AREA_URL).json()


def get_forecast(area_code: str):
    url = FORECAST_URL.format(area_code)
    return requests.get(url).json()

