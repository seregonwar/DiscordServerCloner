import flet as ft
from datetime import datetime
import os

class DebugView(ft.Container):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(expand=True, padding=20, **kwargs)
        self.main_page = page
        
        # Log Storage
        self.logs = []
        
        # UI Components
        self.log_list = ft.ListView(
            expand=True,
            spacing=5,
            padding=10,
            auto_scroll=True
        )
        
        self.toolbar = ft.Row([
            ft.Text("Log History", size=20, weight="bold"),
            ft.Row([
                ft.IconButton(ft.icons.DELETE_SWEEP_OUTLINED, tooltip="Clear Logs", on_click=self.clear_logs),
                ft.IconButton(ft.icons.SAVE_ALT_OUTLINED, tooltip="Save to File", on_click=self.save_logs),
            ])
        ], alignment="spaceBetween")

        self.content = ft.Column([
            self.toolbar,
            ft.Divider(),
            ft.Container(
                content=self.log_list,
                bgcolor=ft.colors.BLACK45,
                border_radius=10,
                expand=True,
                padding=10
            )
        ])

    def log(self, message, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        colors = {
            "ERROR": ft.colors.RED_400,
            "SUCCESS": ft.colors.GREEN_400,
            "WARNING": ft.colors.ORANGE_400,
            "INFO": ft.colors.BLUE_GREY_200
        }
        
        log_entry = ft.Text(
            f"[{ts}] [{level}] {message}",
            color=colors.get(level, ft.colors.WHITE),
            font_family="Consolas",
            size=12
        )
        
        self.log_list.controls.append(log_entry)
        self.logs.append(f"[{ts}] [{level}] {message}")
        
        # Limit log size for performance
        if len(self.log_list.controls) > 500:
            self.log_list.controls.pop(0)
            
        self.main_page.update()

    def clear_logs(self, e):
        self.log_list.controls.clear()
        self.logs.clear()
        self.log("Logs cleared", "INFO")
        self.main_page.update()

    def save_logs(self, e):
        try:
            os.makedirs("logs", exist_ok=True)
            filename = f"logs/debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(self.logs))
            self.log(f"Logs saved to {filename}", "SUCCESS")
        except Exception as ex:
            self.log(f"Failed to save logs: {str(ex)}", "ERROR")
