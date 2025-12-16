import flet as ft
import math  # 計算のためのライブラリをインポート


class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text


class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.Colors.WHITE24
        self.color = ft.Colors.WHITE


class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.ORANGE
        self.color = ft.Colors.WHITE


class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.color = ft.Colors.BLACK


class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()
        
        self.angle_mode = "DEG"  # 三角関数の角度モード

        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=20)
        self.width = 350
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment=ft.MainAxisAlignment.END),
                ft.Row(
                    controls=[
                        ExtraActionButton(text="DEG", button_clicked=self.button_clicked),  # 角度モード切替ボタン
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
                # 三角関数とその他の計算ボタンを追加
                ft.Row(
                    controls=[
                        ActionButton(text="sin", button_clicked=self.button_clicked),
                        ActionButton(text="cos", button_clicked=self.button_clicked),
                        ActionButton(text="tan", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        ActionButton(text="√", button_clicked=self.button_clicked),
                        ActionButton(text="x²", button_clicked=self.button_clicked),
                        ActionButton(text="!", button_clicked=self.button_clicked),
                    ]
                ),
            ]
        )

    # 角度をラジアンに変換するメソッド
    def to_radian(self, x):
        if self.angle_mode == "DEG":
            return math.radians(x)
        return x

    def button_clicked(self, e):
        data = e.control.data
        print(f"Button clicked with data = {data, type(data)}")
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()

        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand == True:
                self.result.value = data
                self.new_operand = False
            else:
                self.result.value = str(self.result.value) + str(data)

        elif data in ("+", "-", "*", "/"):
            self.result.value = str(self.calculate(self.operand1, float(str(self.result.value)), self.operator))
            self.operator = data
            if self.result.value == "Error":
                self.operand1 = "0"
            else:
                self.operand1 = float(self.result.value)
            self.new_operand = True

        elif data in ("="):
            self.result.value = str(self.calculate(self.operand1, float(str(self.result.value)), self.operator))
            self.reset()

        elif data in ("%"):
            self.result.value = str(float(str(self.result.value)) / 100)
            self.reset()

        elif data in ("+/-"):
            if float(str(self.result.value)) > 0:
                self.result.value = "-" + str(self.result.value)
            elif float(str(self.result.value)) < 0:
                self.result.value = str(self.format_number(abs(float(str(self.result.value)))))

        # 角度モード切り替えと三角関数、平方根、二乗、階乗の処理を追加
        elif data == "DEG":
            self.angle_mode = "RAD"
            e.control.text = "RAD"
            e.control.data = "RAD"

        elif data == "RAD":
            self.angle_mode = "DEG"
            e.control.text = "DEG"
            e.control.data = "DEG"

        elif data == "sin":
            x = self.to_radian(float(self.result.value))
            self.result.value = str(round(math.sin(x), 10))
            self.reset()

        elif data == "cos":
            x = self.to_radian(float(self.result.value))
            self.result.value = str(round(math.cos(x), 10))
            self.reset()

        elif data == "tan":
            x = self.to_radian(float(self.result.value))
            self.result.value = str(round(math.tan(x), 10))
            self.reset()

        elif data == "√":
            self.result.value = str(round(math.sqrt(float(self.result.value)), 10))
            self.reset()

        elif data == "x²":
            x = float(self.result.value)
            self.result.value = str(round(x * x, 10))
            self.reset()

        elif data == "!":
            n = int(float(self.result.value))
            self.result.value = str(math.factorial(n))
            self.reset()

        self.update()

    def format_number(self, num):
        if num % 1 == 0:
            return int(num)
        else:
            return num

    def calculate(self, operand1, operand2, operator):
        if operator == "+":
            return self.format_number(operand1 + operand2)

        elif operator == "-":
            return self.format_number(operand1 - operand2)

        elif operator == "*":
            return self.format_number(operand1 * operand2)

        elif operator == "/":
            if operand2 == 0:
                return "Error"
            else:
                return self.format_number(operand1 / operand2)

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "Simple Calculator"
    calc = CalculatorApp()
    page.add(calc)


ft.app(main)