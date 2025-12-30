import flet as ft
import datetime
from api.jma_api import get_forecast


# 気温表示用（未発表対策）
def format_temp(t):
    return f"{t}℃" if t else "未発表"


# 天気アイコン簡易判定
def weather_icon(weather):
    if "雨" in weather:
        return "🌧"
    if "雪" in weather:
        return "❄"
    if "曇" in weather:
        return "☁"
    return "☀"


# 天気カード1枚
def weather_card(date, weather, tmin, tmax):
    today = datetime.date.today().isoformat()
    is_today = date == today

    return ft.Container(
        width=200,
        height=240,
        bgcolor=ft.Colors.WHITE,
        border_radius=16,
        padding=15,
        border=ft.border.all(
            2 if is_today else 1,
            ft.Colors.BLUE if is_today else ft.Colors.BLACK12
        ),
        shadow=ft.BoxShadow(
            blur_radius=8,
            color=ft.Colors.BLACK12
        ),
        content=ft.Column(
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(date, weight="bold"),
                ft.Text(weather_icon(weather), size=40),
                ft.Text(weather, size=12, text_align="center"),
                ft.Divider(),
                ft.Text(
                    f"{format_temp(tmin)} / {format_temp(tmax)}",
                    size=16,
                    color=ft.Colors.BLUE,
                    weight="bold"
                )
            ]
        )
    )


# 天気表示エリア（Grid）
def build_weather_view():
    return ft.GridView(
        expand=True,
        max_extent=220,
        spacing=20,
        run_spacing=20,
    )


# 地域選択時に天気を更新
def update_weather(view, area_code):
    view.controls.clear()

    data = get_forecast(area_code)
    ts = data[0]["timeSeries"][0]
    area = ts["areas"][0]

    dates = ts["timeDefines"]
    weathers = area["weathers"]
    tmin = area.get("tempsMin", [])
    tmax = area.get("tempsMax", [])

    for i in range(len(dates)):
        view.controls.append(
            weather_card(
                dates[i][:10],
                weathers[i],
                tmin[i] if i < len(tmin) else None,
                tmax[i] if i < len(tmax) else None,
            )
        )
