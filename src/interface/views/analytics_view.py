import flet as ft
from src.core.utils.stats_manager import load_all_stats
from datetime import datetime

class AnalyticsView(ft.Container):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(expand=True, padding=20, **kwargs)
        self.main_page = page
        self.stats_history = []
        
        # UI Elements
        self.summary_cards = ft.Row(spacing=20)
        self.history_list = ft.ListView(expand=True, spacing=10)
        self.chart_container = ft.Container(
            content=ft.Text("No data available for charts", color="grey500"),
            height=300,
            alignment=ft.alignment.center,
            bgcolor="black12",
            border_radius=15,
            padding=20
        )
        
        self.content = ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Analytics Dashboard", size=32, weight="bold"),
                    ft.Text("Performance metrics and historical data for your operations.", color="grey500"),
                ]),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.icons.REFRESH_ROUNDED,
                    on_click=lambda _: self.main_page.run_task(self.refresh_data),
                    tooltip="Refresh Analytics"
                )
            ]),
            ft.Divider(),
            
            # Summary Cards
            self.summary_cards,
            
            ft.Text("Operation Trends", size=20, weight="bold", color="grey400"),
            self.chart_container,
            
            ft.Text("Recent History", size=20, weight="bold", color="grey400"),
            ft.Container(
                content=self.history_list,
                expand=True,
                bgcolor="black12",
                border_radius=15,
                padding=10,
                border=ft.border.all(1, "white10")
            )
        ], spacing=20)

    async def initialize_data(self):
        await self.refresh_data()

    async def refresh_data(self):
        self.stats_history = load_all_stats()
        self.update_summary()
        self.update_history_list()
        self.update_charts()
        self.update()

    def update_summary(self):
        total_ops = len(self.stats_history)
        total_success = len([s for s in self.stats_history if s.get("success")])
        total_messages = sum([s.get("messages_cloned", 0) for s in self.stats_history])
        
        self.summary_cards.controls = [
            self._create_summary_card("Total Operations", str(total_ops), ft.icons.HISTORY, ft.colors.BLUE_400),
            self._create_summary_card("Success Rate", f"{(total_success/total_ops*100 if total_ops > 0 else 0):.1f}%", ft.icons.CHECK_CIRCLE, ft.colors.GREEN_400),
            self._create_summary_card("Messages Cloned", str(total_messages), ft.icons.MESSAGE, ft.colors.AMBER_400),
        ]

    def _create_summary_card(self, title, value, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon, color=color, size=20), ft.Text(title, size=14, color="grey400")]),
                ft.Text(value, size=24, weight="bold"),
            ], spacing=5),
            bgcolor="white10",
            padding=20,
            border_radius=15,
            expand=True,
            border=ft.border.all(1, "white10")
        )

    def update_history_list(self):
        self.history_list.controls.clear()
        if not self.stats_history:
            self.history_list.controls.append(ft.Text("No operations logged yet.", color="grey500", text_align="center"))
            return
            
        # Show newest first
        for stat in reversed(self.stats_history):
            ts = stat.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M")
            except:
                dt = ts
                
            op_type = stat.get("type", "unknown").capitalize()
            success = stat.get("success", False)
            
            self.history_list.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(
                            ft.icons.COPY_ALL_ROUNDED if op_type == "Cloning" else ft.icons.SETTINGS_BACKUP_RESTORE_ROUNDED,
                            color=ft.colors.GREEN_400 if success else ft.colors.RED_400
                        ),
                        title=ft.Text(f"{op_type}: {stat.get('source')} → {stat.get('destination')}", weight="bold"),
                        subtitle=ft.Text(f"{dt} • Roles: {stat.get('roles_created', 0)} • Channels: {stat.get('channels_created', 0)} • Messages: {stat.get('messages_cloned', 0)}"),
                        trailing=ft.Text("SUCCESS" if success else "FAILED", color="green" if success else "red", size=12, weight="bold")
                    ),
                    bgcolor="white05",
                    border_radius=10,
                )
            )

    def update_charts(self):
        if not self.stats_history or len(self.stats_history) < 2:
            return

        # Prepare data for a simple line chart of messages cloned over time
        data_points = []
        for i, stat in enumerate(self.stats_history[-10:]): # Last 10 operations
            data_points.append(
                ft.LineChartDataPoint(i, stat.get("messages_cloned", 0))
            )
            
        self.chart_container.content = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=data_points,
                    stroke_width=4,
                    color=ft.colors.BLUE_400,
                    curved=True,
                    below_line_bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE_400),
                    below_line_gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=[ft.colors.with_opacity(0.2, ft.colors.BLUE_400), ft.colors.TRANSPARENT]
                    ),
                )
            ],
            border=ft.border.all(1, "white10"),
            horizontal_grid_lines=ft.ChartGridLines(interval=10, color="white10", width=1),
            vertical_grid_lines=ft.ChartGridLines(interval=1, color="white10", width=1),
            left_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=0, label=ft.Text("0", size=10)),
                    ft.ChartAxisLabel(value=50, label=ft.Text("50", size=10)),
                    ft.ChartAxisLabel(value=100, label=ft.Text("100", size=10)),
                ],
                labels_size=30,
            ),
            bottom_axis=ft.ChartAxis(
                labels=[ft.ChartAxisLabel(value=i, label=ft.Text(str(i+1), size=10)) for i in range(len(data_points))],
                labels_size=30,
            ),
            expand=True,
        )
