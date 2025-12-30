import flet as ft
from ui.sidebar import build_sidebar
from ui.weather_view import build_weather_view, update_weather


def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.bgcolor = "#e3e9ec"
    page.padding = 0

    weather_view = build_weather_view()

    def on_area_selected(code):
        update_weather(weather_view, code)
        page.update()

    sidebar = build_sidebar(on_area_selected)

    page.add(
        ft.Row(
            expand=True,
            controls=[
                sidebar,
                ft.Container(
                    expand=True,
                    padding=30,
                    content=weather_view
                )
            ]
        )
    )


ft.app(target=main)
