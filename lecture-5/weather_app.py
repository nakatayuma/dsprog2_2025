import flet as ft
import requests
from datetime import datetime

# --- 設定値とエンドポイント ---
JMA_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/"
REGION_CONF_URL = "https://www.jma.go.jp/bosai/common/const/area.json"

# 観測地点（ID, 地域コード, 表示名, Y座標, X座標）
MONITOR_POINTS = [
    ("016000", "016010", "札幌", 40, 620),
    ("015000", "015010", "釧路", 70, 730),
    ("040000", "040010", "仙台", 230, 590),
    ("150000", "150010", "新潟", 250, 480),
    ("130000", "130010", "東京", 360, 560),
    ("230000", "230010", "名古屋", 390, 450),
    ("170000", "170010", "金沢", 290, 380),
    ("270000", "270000", "大阪", 410, 360),
    ("340000", "340010", "広島", 410, 240),
    ("390000", "390010", "高知", 520, 280),
    ("400000", "400010", "福岡", 410, 100),
    ("460100", "460100", "鹿児島", 530, 80),
    ("471000", "471010", "那覇", 630, 210),
]

def main(page: ft.Page):
    page.title = "Weather Intelligence Dashboard"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F1F5F9"
    page.window_width = 1250
    page.window_height = 920
    page.padding = 0


    def fetch_visual_style(condition_text):
        target = str(condition_text)
        if "雷" in target:
            return "⛈️", "#7C3AED", ft.LinearGradient(["#DDD6FE", "#A78BFA"], begin=ft.alignment.top_left)
        if "雪" in target:
            return "❄️", "#0891B2", ft.LinearGradient(["#CFFAFE", "#67E8F9"], begin=ft.alignment.top_left)
        if "雨" in target:
            return "🌧️", "#2563EB", ft.LinearGradient(["#DBEAFE", "#93C5FD"], begin=ft.alignment.top_left)
        if "晴" in target and ("曇" in target or "くもり" in target):
            return "🌤️", "#D97706", ft.LinearGradient(["#FEF3C7", "#FDE68A"], begin=ft.alignment.top_left)
        if "晴" in target:
            return "☀️", "#EA580C", ft.LinearGradient(["#FFEDD5", "#FED7AA"], begin=ft.alignment.top_left)
        return "☁️", "#475569", ft.LinearGradient(["#F1F5F9", "#E2E8F0"], begin=ft.alignment.top_left)

 
    def open_detailed_report(office_id, area_id, area_name):
        try:
            raw_data = requests.get(f"{JMA_BASE_URL}{office_id}.json").json()
            
            weekly_box = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=12)
            if len(raw_data) > 1:
                week_ts = raw_data[1]["timeSeries"]
                w_weather = next((a for a in week_ts[0]["areas"] if a["area"]["code"] == area_id), week_ts[0]["areas"][0])
                w_temp = next((a for a in week_ts[1]["areas"] if a["area"]["code"] == area_id), week_ts[1]["areas"][0])

                for i, date_raw in enumerate(week_ts[0]["timeDefines"]):
                    day_obj = datetime.fromisoformat(date_raw.replace('Z','+00:00'))
                    
                    
                    code = w_weather.get("weatherCodes", ["100"] * 10)[i]
                    
                    if code.startswith("4"):
                        weather_text = "雪"
                    elif code.startswith("3"):
                        weather_text = "雨"
                    elif code.startswith("2"):
                        
                        if code in ["204", "205", "206", "207", "208", "215", "216", "217", "218", "219", "224", "225", "226"]:
                            weather_text = "雪"
                        elif code in ["202", "203", "212", "213", "214", "222"]:
                            weather_text = "雨"
                        else:
                            weather_text = "曇"
                    elif code.startswith("1"):
                        weather_text = "晴"
                    else:
                        weather_text = "曇"
                    
                    w_emoji, _, _ = fetch_visual_style(weather_text)
                   

                    w_pop = w_weather.get("pops", ["--"]*10)[i]

                    weekly_box.controls.append(
                        ft.Container(
                            width=100, padding=15, bgcolor="#FFFFFF", border_radius=15, border=ft.border.all(1, "#F1F5F9"),
                            content=ft.Column([
                                ft.Text(day_obj.strftime("%m/%d"), size=11, weight="bold", color="#94A3B8"),
                                ft.Text(w_emoji, size=28),
                                ft.Container(
                                    content=ft.Text(f"{w_pop}%", size=10, weight="bold", color="#3B82F6"),
                                    bgcolor="#EFF6FF", padding=ft.padding.symmetric(4, 8), border_radius=6
                                ),
                                ft.Row([
                                    ft.Text(f"{w_temp.get('tempsMin',['--']*10)[i]}°", color="#3B82F6", size=10),
                                    ft.Text(f"{w_temp.get('tempsMax',['--']*10)[i]}°", color="#EF4444", size=10)
                                ], spacing=4, alignment="center")
                            ], horizontal_alignment="center", spacing=6)
                        )
                    )

            page.open(ft.AlertDialog(
                title=ft.Text(f"{area_name} の週間予報", size=16, weight="bold"),
                content=ft.Column([
                    ft.Text("🗓️ 7日間の予報推移", size=14, weight="bold"), 
                    weekly_box
                ], tight=True, spacing=15)
            ))
        except Exception as e:
            print(f"Detail Fetch Error: {e}")
            page.open(ft.SnackBar(ft.Text(f"エラーが発生しました: {e}")))
    
    nav_panel = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def build_navigation():
        try:
            config = requests.get(REGION_CONF_URL).json()
            for c_id, c_data in config["centers"].items():
                subs = []
                for o_id in c_data.get("children", []):
                    office = config["offices"][o_id]
                    regions = [ft.ListTile(title=ft.Text(config["class10s"][r]["name"], size=12), 
                               on_click=lambda e, oid=o_id, rid=r, rname=config["class10s"][r]["name"]: open_detailed_report(oid, rid, rname))
                               for r in office.get("children", []) if r in config["class10s"]]
                    subs.append(ft.ExpansionTile(title=ft.Text(office["name"], size=13, weight="w600"), controls=regions))
                nav_panel.controls.append(ft.ExpansionTile(title=ft.Text(c_data["name"], size=14, weight="bold"), controls=subs))
            page.update()
        except Exception as e:
            print(f"Nav Build Error: {e}")

 
    weather_canvas = ft.Stack(width=1100, height=850)

    def sync_map_data():
        for oid, rid, name, top, left in MONITOR_POINTS:
            try:
                data = requests.get(f"{JMA_BASE_URL}{oid}.json").json()
                ts_base = data[0]["timeSeries"]

                
                area_w = next(
                    (a for a in ts_base[0]["areas"] if a["area"]["code"] == rid),
                    ts_base[0]["areas"][0]
                )

               
                area_p = next(
                    (a for a in ts_base[1]["areas"] if a["area"]["code"] == rid),
                    ts_base[1]["areas"][0]
                )


                
                if len(ts_base) > 2:
                    area_t = ts_base[2]["areas"][0]
                    temps = area_t.get("temps", [])
                    
                    
                    temp_max = temps[1] if len(temps) > 1 else "--"
                    temp_min = temps[0] if len(temps) > 0 else "--"
                else:
                    temp_max = "--"
                    temp_min = "--"


                
                weather_text = area_w["weathers"][0]
                emoji, _, _ = fetch_visual_style(weather_text)

                
                

                pop_now = area_p.get("pops", ["0"])[0]

                weather_canvas.controls.append(
                    ft.Container(
                        top=top,
                        left=left,
                        width=110,
                        bgcolor="white",
                        border_radius=12,
                        padding=8,
                        shadow=ft.BoxShadow(blur_radius=8, color="#1E293B20"),
                        content=ft.Column(
                            [
                                ft.Text(name, size=10, weight="bold"),
                                ft.Text(emoji, size=22),

                                
                                ft.Row(
                                    [
                                        ft.Text(f"↑{temp_max}°", size=10, color="#EF4444"),
                                        ft.Text(f"↓{temp_min}°", size=10, color="#3B82F6"),
                                    ],
                                    alignment="center",
                                    spacing=4,
                                ),

                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.WATER_DROP, size=10, color="#3B82F6"),
                                        ft.Text(f"{pop_now}%", size=9, color="#64748B"),
                                    ],
                                    alignment="center",
                                    spacing=2,
                                ),
                            ],
                            horizontal_alignment="center",
                            spacing=2,
                        ),
                        on_click=lambda e, oid=oid, rid=rid, rname=name:
                            open_detailed_report(oid, rid, rname),
                    )
                )

            except Exception as e:
                print("Map fetch error:", e)

        page.update()


    page.add(
        ft.Row([
            ft.Container(
                width=300, bgcolor="white", padding=20,
                border=ft.border.only(right=ft.border.BorderSide(1, "#F1F5F9")),
                content=ft.Column([
                    ft.Text("Intelligence Map", size=18, weight="black", color="#1E293B"),
                    ft.Divider(height=20, color="#F1F5F9"),
                    nav_panel
                ], expand=True)
            ),
            ft.Container(
                expand=True, padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO, expand=True,
                    controls=[
                        ft.Row(scroll=ft.ScrollMode.AUTO, controls=[weather_canvas])
                    ]
                )
            )
        ], expand=True, spacing=0)
    )

    build_navigation()
    sync_map_data()

ft.app(target=main)