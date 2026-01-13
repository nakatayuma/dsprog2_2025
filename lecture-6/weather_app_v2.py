import flet as ft
import requests
import sqlite3
from datetime import datetime, timedelta

# --- 設定値とエンドポイント ---
JMA_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/"
REGION_CONF_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
DB_NAME = "weather_intelligence.db"

# 観測地点（ID, 地域コード, 表示名, Y座標, X座標）
# 初期データとしてDBに登録します
INITIAL_MONITOR_POINTS = [
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

# --- データベース管理クラス ---
class WeatherDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """テーブルの作成"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 地域マスタ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS areas (
                area_code TEXT PRIMARY KEY,
                office_code TEXT,
                name TEXT,
                pos_y INTEGER,
                pos_x INTEGER
            )
        ''')

        # 予報データ
        # target_date: 予報対象日, fetched_at: データ取得日時
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                area_code TEXT,
                target_date TEXT,
                weather_code TEXT,
                weather_text TEXT,
                temp_max TEXT,
                temp_min TEXT,
                pop TEXT,
                fetched_at TEXT,
                FOREIGN KEY (area_code) REFERENCES areas (area_code),
                UNIQUE(area_code, target_date)
            )
        ''')
        conn.commit()
        conn.close()

    def upsert_area(self, area_data):
        """地域の登録・更新"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR REPLACE INTO areas (office_code, area_code, name, pos_y, pos_x)
            VALUES (?, ?, ?, ?, ?)
        ''', area_data)
        conn.commit()
        conn.close()

    def upsert_forecast(self, area_code, target_date, w_code, w_text, t_max, t_min, pop):
        """予報データの保存（既存の日付データがあれば上書き）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO forecasts 
            (area_code, target_date, weather_code, weather_text, temp_max, temp_min, pop, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (area_code, target_date, w_code, w_text, t_max, t_min, pop, now))
        conn.commit()
        conn.close()

    def get_forecasts_by_date(self, target_date_str):
        """指定した日付の予報データを全地域分取得"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, a.office_code, a.name, a.pos_x, a.pos_y
            FROM areas a
            LEFT JOIN forecasts f ON a.area_code = f.area_code AND f.target_date = ?
        ''', (target_date_str,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_areas(self):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM areas')
        rows = cursor.fetchall()
        conn.close()
        return rows

# --- 天気予報ロジック ---

def fetch_visual_style(condition_text):
    if not condition_text: return "❓", "#CBD5E1", ft.LinearGradient(["#F8FAFC", "#F1F5F9"])
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

def main(page: ft.Page):
    # DB初期化
    db = WeatherDatabase(DB_NAME)
    db.upsert_area(INITIAL_MONITOR_POINTS) # マスタデータの投入

    page.title = "Weather Intelligence Dashboard (DB Integrated)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F1F5F9"
    page.window_width = 1300
    page.window_height = 920
    page.padding = 0

    # 状態管理
    current_date = datetime.now().strftime("%Y-%m-%d")
    selected_date_text = ft.Text(f"表示中のデータ: {current_date}", size=14, weight="bold")

    weather_canvas = ft.Stack(width=1100, height=850)
    nav_panel = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # 詳細ダイアログ表示 (APIから直接取得のまま維持 - 週間予報のため)
    def open_detailed_report(office_id, area_id, area_name):
        try:
            # 週間予報等はAPIから直接取得（今回はDB保存対象外とする）
            raw_data = requests.get(f"{JMA_BASE_URL}{office_id}.json").json()
            
            weekly_box = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=12)
            if len(raw_data) > 1:
                week_ts = raw_data[1]["timeSeries"]
                w_weather = next((a for a in week_ts[0]["areas"] if a["area"]["code"] == area_id), week_ts[0]["areas"][0])
                w_temp = next((a for a in week_ts[1]["areas"] if a["area"]["code"] == area_id), week_ts[1]["areas"][0])

                for i, date_raw in enumerate(week_ts[0]["timeDefines"]):
                    day_obj = datetime.fromisoformat(date_raw.replace('Z','+00:00'))
                    
                    code = w_weather.get("weatherCodes", ["100"] * 10)[i]
                    # 簡易的な天気判定ロジック
                    if code.startswith("1"): w_text = "晴"
                    elif code.startswith("2"): w_text = "雨" if code in ["202","203"] else "曇"
                    elif code.startswith("3"): w_text = "雨"
                    elif code.startswith("4"): w_text = "雪"
                    else: w_text = "曇"

                    w_emoji, _, _ = fetch_visual_style(w_text)
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
                    ft.Text("🗓️ 7日間の予報推移 (API直接取得)", size=14, weight="bold"), 
                    weekly_box
                ], tight=True, spacing=15)
            ))
        except Exception as e:
            print(f"Detail Fetch Error: {e}")

    # UI描画関数：DBからデータを読み込んで表示
    def render_map_from_db(target_date_str):
        weather_canvas.controls.clear()
        
        # DBから指定日のデータを取得
        rows = db.get_forecasts_by_date(target_date_str)
        
        for row in rows:
            # データがない場合（過去の日付で保存がない場合など）は「--」表示
            name = row["name"]
            w_text = row["weather_text"] if row["weather_text"] else ""
            t_max = row["temp_max"] if row["temp_max"] else "--"
            t_min = row["temp_min"] if row["temp_min"] else "--"
            pop = row["pop"] if row["pop"] else "--"
            
            emoji, _, _ = fetch_visual_style(w_text)
            
            # DBにデータがない場合はグレーアウトさせるスタイル
            bg_color = "white" if row["weather_code"] else "#F1F5F9"
            
            weather_canvas.controls.append(
                ft.Container(
                    top=row["pos_y"],
                    left=row["pos_x"],
                    width=110,
                    bgcolor=bg_color,
                    border_radius=12,
                    padding=8,
                    shadow=ft.BoxShadow(blur_radius=8, color="#1E293B20"),
                    content=ft.Column(
                        [
                            ft.Text(name, size=10, weight="bold"),
                            ft.Text(emoji, size=22),
                            ft.Row(
                                [
                                    ft.Text(f"↑{t_max}°", size=10, color="#EF4444"),
                                    ft.Text(f"↓{t_min}°", size=10, color="#3B82F6"),
                                ],
                                alignment="center", spacing=4,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.WATER_DROP, size=10, color="#3B82F6"),
                                    ft.Text(f"{pop}%", size=9, color="#64748B"),
                                ],
                                alignment="center", spacing=2,
                            ),
                        ],
                        horizontal_alignment="center", spacing=2,
                    ),
                    on_click=lambda e, oid=row["office_code"], rid=row["area_code"], rname=name:
                        open_detailed_report(oid, rid, rname),
                )
            )
        page.update()

    # データ同期：APIから取得してDBに保存し、画面を更新
    def sync_data_api_to_db(e=None):
        page.overlay.append(ft.SnackBar(ft.Text("最新の予報を取得しDBを更新中...")))
        page.update()
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        areas = db.get_all_areas() # DBのマスタから取得
        
        for area in areas:
            oid = area["office_code"]
            rid = area["area_code"]
            
            try:
                data = requests.get(f"{JMA_BASE_URL}{oid}.json").json()
                ts_base = data[0]["timeSeries"]
                
                # エリアデータを特定
                area_w = next((a for a in ts_base[0]["areas"] if a["area"]["code"] == rid), ts_base[0]["areas"][0])
                area_p = next((a for a in ts_base[1]["areas"] if a["area"]["code"] == rid), ts_base[1]["areas"][0])
                
                # 気温データの処理
                temp_max, temp_min = "--", "--"
                if len(ts_base) > 2:
                    area_t = next((a for a in ts_base[2]["areas"] if a["area"]["code"] == rid), ts_base[2]["areas"][0])
                    temps = area_t.get("temps", [])
                    # 今日の気温を取得（配列のindexに注意が必要だが簡易的に実装）
                    if len(temps) >= 2:
                        temp_max = temps[1]
                        temp_min = temps[0]
                    elif len(temps) == 1: # 朝取得した場合などはMaxしかない場合がある
                         temp_max = temps[0]

                # 天気と降水確率
                w_code = area_w["weatherCodes"][0]
                w_text = area_w["weathers"][0]
                pop_now = area_p.get("pops", ["0"])[0]

                # DBに保存 (Upsert)
                db.upsert_forecast(rid, today_str, w_code, w_text, temp_max, temp_min, pop_now)

            except Exception as e:
                print(f"Fetch Error {area['name']}: {e}")

        # 今日の日付を選択状態にして再描画
        nonlocal current_date
        current_date = today_str
        selected_date_text.value = f"表示中のデータ: {current_date}"
        render_map_from_db(current_date)
        page.overlay.clear()
        page.update()

    # 日付変更時の処理
    def change_date(e):
        nonlocal current_date
        if e.control.value:
            date_obj = e.control.value
            current_date = date_obj.strftime("%Y-%m-%d")
            selected_date_text.value = f"表示中のデータ: {current_date}"
            render_map_from_db(current_date)

    # ナビゲーション構築
    def build_navigation():
        try:
            config = requests.get(REGION_CONF_URL).json()
            for c_id, c_data in config["centers"].items():
                subs = []
                for o_id in c_data.get("children", []):
                    office = config["offices"][o_id]
                    # ここではクリック時の詳細表示のみ設定
                    regions = [ft.ListTile(title=ft.Text(config["class10s"][r]["name"], size=12), 
                               on_click=lambda e, oid=o_id, rid=r, rname=config["class10s"][r]["name"]: open_detailed_report(oid, rid, rname))
                               for r in office.get("children", []) if r in config["class10s"]]
                    subs.append(ft.ExpansionTile(title=ft.Text(office["name"], size=13, weight="w600"), controls=regions))
                nav_panel.controls.append(ft.ExpansionTile(title=ft.Text(c_data["name"], size=14, weight="bold"), controls=subs))
            page.update()
        except Exception as e:
            print(f"Nav Build Error: {e}")

    # --- レイアウト ---
    
    # 日付選択ピッカー
    date_picker = ft.DatePicker(
        on_change=change_date,
        first_date=datetime(2023,1,1),
        last_date=datetime(2030,12,31)
    )
    # page.overlay.append(date_picker)

    control_bar = ft.Container(
        padding=10, bgcolor="white", border_radius=10,
        content=ft.Row([
            ft.ElevatedButton(
                "データの更新 (API→DB)", 
                icon=ft.Icons.CLOUD_SYNC, 
                on_click=sync_data_api_to_db,
                bgcolor="#3B82F6", color="white"
            ),
            ft.VerticalDivider(width=20),
            ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, on_click=lambda _: page.open(date_picker), tooltip="過去の予報を見る"),
            selected_date_text
        ], alignment="center")
    )

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
                        control_bar,
                        ft.Divider(height=20, color="transparent"),
                        ft.Row(scroll=ft.ScrollMode.AUTO, controls=[weather_canvas])
                    ]
                )
            )
        ], expand=True, spacing=0)
    )

    build_navigation()
    # 初回起動時はAPIからデータを取得してDBに入れる
    sync_data_api_to_db()

ft.app(target=main)