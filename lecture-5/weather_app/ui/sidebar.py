import flet as ft
from api.jma_api import get_area_data


def build_sidebar(on_select):
    area_json = get_area_data()
    centers = area_json["centers"]
    offices = area_json["offices"]

    # 地方ごとに都道府県をまとめる
    center_map = {}
    for code, office in offices.items():
        parent = office["parent"]
        center_map.setdefault(parent, []).append(
            ft.ListTile(
                title=ft.Text(office["name"]),
                subtitle=ft.Text(code),
                on_click=lambda e, c=code: on_select(c)
            )
        )

    tiles = []
    for center_code, center in centers.items():
        if center_code in center_map:
            tiles.append(
                ft.ExpansionTile(
                    title=ft.Text(center["name"], weight="bold"),
                    controls=center_map[center_code]
                )
            )

    return ft.Container(
        width=280,
        bgcolor="#6f8893",
        padding=10,
        content=ft.Column(
            controls=tiles,
            scroll=ft.ScrollMode.AUTO
        )
    )
