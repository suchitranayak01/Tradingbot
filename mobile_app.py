import flet as ft
import yaml
from pathlib import Path
from datetime import datetime
import sys
from src.strategies.non_directional_strangle import NonDirectionalStrangleStrategy
from src.brokers.angelone import AngelOneClient

class AlgoTradingApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Algo Trading Mobile"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        
        self.bot_running = False
        self.logs = []
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        self.status_text = ft.Text("Bot Status: STOPPED", color=ft.colors.RED, weight=ft.FontWeight.BOLD)
        self.status_icon = ft.Icon(ft.icons.STOP_CIRCLE, color=ft.colors.RED)
        
        # Connection Status Card
        self.conn_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.ACCOUNT_BALANCE),
                        title=ft.Text("Broker Connection"),
                        subtitle=ft.Text("Not Connected"),
                    ),
                ]),
                padding=10,
            )
        )

        # Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Control", icon=ft.icons.PLAY_ARROW, content=self.control_tab()),
                ft.Tab(text="Signals", icon=ft.icons.SHOW_CHART, content=self.signals_tab()),
                ft.Tab(text="Logs", icon=ft.icons.LIST_ALT, content=self.logs_tab()),
            ],
            expand=1
        )

        self.page.add(
            ft.Row([self.status_icon, self.status_text], alignment=ft.MainAxisAlignment.CENTER),
            self.conn_card,
            self.tabs
        )

    def control_tab(self):
        return ft.Column([
            ft.Divider(),
            ft.ElevatedButton(
                "START BOT",
                icon=ft.icons.PLAY_ARROW,
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN,
                on_click=self.toggle_bot,
                height=50,
                width=400
            ),
            ft.ElevatedButton(
                "STOP BOT",
                icon=ft.icons.STOP,
                color=ft.colors.WHITE,
                bgcolor=ft.colors.RED,
                on_click=self.toggle_bot,
                height=50,
                width=400,
                disabled=True
            ),
            ft.Text("Trading Parameters", size=20, weight=ft.FontWeight.BOLD),
            ft.TextField(label="Lot Size", value="50", keyboard_type=ft.KeyboardType.NUMBER),
            ft.Switch(label="Dry Run Mode", value=True),
        ], scroll=ft.ScrollMode.AUTO)

    def signals_tab(self):
        self.signals_list = ft.ListView(expand=1, spacing=10, padding=10)
        return self.signals_list

    def logs_tab(self):
        self.logs_view = ft.ListView(expand=1, spacing=5, padding=10)
        return self.logs_view

    def toggle_bot(self, e):
        self.bot_running = not self.bot_running
        self.status_text.value = "Bot Status: RUNNING" if self.bot_running else "Bot Status: STOPPED"
        self.status_text.color = ft.colors.GREEN if self.bot_running else ft.colors.RED
        self.status_icon.color = ft.colors.GREEN if self.bot_running else ft.colors.RED
        self.status_icon.name = ft.icons.PLAY_CIRCLE if self.bot_running else ft.icons.STOP_CIRCLE
        
        self.add_log(f"Bot {'started' if self.bot_running else 'stopped'}")
        self.page.update()

    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_view.controls.insert(0, ft.Text(f"[{timestamp}] {message}"))
        self.page.update()

def main(page: ft.Page):
    AlgoTradingApp(page)

if __name__ == "__main__":
    ft.app(target=main)
