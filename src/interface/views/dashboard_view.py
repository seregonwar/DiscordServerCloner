import flet as ft
import aiohttp
import asyncio
from datetime import datetime

class DashboardView(ft.Container):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(expand=True, padding=0, **kwargs) # Zero padding for full-width header
        self.main_page = page
        
        # Stats State
        self.server_count = ft.Text("0", size=32, weight="bold", color="white")
        self.active_clones = ft.Text("0", size=32, weight="bold", color="white")
        self.total_backups = ft.Text("0", size=32, weight="bold", color="white")
        self.health_score = ft.Text("100%", size=32, weight="bold", color="white")
        
        self.profile_name = ft.Text("Loading Manager...", size=28, weight="bold", color="white")
        self.profile_tag = ft.Text("@---", size=16, color="white70")
        
        # Recent Activity List
        self.activity_list = ft.ListView(expand=True, spacing=10, padding=10)
        
        # Dashboard Content
        self.content = ft.Column([
            # 1. Gradient Hero Header
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.DASHBOARD_ROUNDED, size=40, color="white"),
                        ft.Column([
                            self.profile_name,
                            self.profile_tag,
                        ], spacing=0),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.icons.REFRESH_ROUNDED, 
                            icon_color="white", 
                            tooltip="Refresh Data", 
                            on_click=lambda _: self.main_page.run_task(self.refresh_data)
                        ),
                    ], alignment="start"),
                    ft.Text("Manage your Discord empire with precision and ease.", color="white70", size=14),
                ], spacing=10),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[ft.colors.BLUE_700, ft.colors.INDIGO_900],
                ),
                padding=40,
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
                shadow=ft.BoxShadow(blur_radius=15, color="black45", offset=ft.Offset(0, 5))
            ),
            
            # 2. Stats Grid
            ft.Container(
                content=ft.Column([
                    ft.Text("Live Overview", size=20, weight="bold", color="grey400"),
                    ft.ResponsiveRow([
                        ft.Column([self._create_stat_card("Servers", self.server_count, ft.icons.DNS_ROUNDED, ft.colors.BLUE_400)], col={"sm": 6, "md": 3}),
                        ft.Column([self._create_stat_card("Active Clones", self.active_clones, ft.icons.REPLAY_CIRCLE_FILLED_ROUNDED, ft.colors.GREEN_400)], col={"sm": 6, "md": 3}),
                        ft.Column([self._create_stat_card("Total Backups", self.total_backups, ft.icons.CLOUDY_SNOWING, ft.colors.AMBER_400)], col={"sm": 6, "md": 3}),
                        ft.Column([self._create_stat_card("Health Score", self.health_score, ft.icons.FAVORITE_ROUNDED, ft.colors.RED_400)], col={"sm": 6, "md": 3}),
                    ], spacing=20),
                ], spacing=15),
                padding=ft.padding.only(left=30, right=30, top=20)
            ),
            
            # 3. Two-Column Layout (Recent Activity & Quick Actions)
            ft.Container(
                content=ft.ResponsiveRow([
                    # Quick Actions
                    ft.Column([
                        ft.Text("Command Center", size=20, weight="bold", color="grey400"),
                        ft.Container(
                            content=ft.Column([
                                self._create_action_button("Start Cloning Engine", "Launch the cloner to replicate servers", ft.icons.ROCKET_LAUNCH, ft.colors.BLUE_ACCENT, 1),
                                self._create_action_button("Manage Snapshots", "Access your offline server backups", ft.icons.CAMERA_ALT, ft.colors.AMBER_ACCENT, 3),
                                self._create_action_button("System Settings", "Configure local app preferences", ft.icons.SETTINGS, ft.colors.GREY_400, 6),
                            ], spacing=15),
                            padding=10
                        )
                    ], col={"sm": 12, "md": 5}),
                    
                    # Recent Activity
                    ft.Column([
                        ft.Text("Recent Activity", size=20, weight="bold", color="grey400"),
                        ft.Container(
                            content=self.activity_list,
                            bgcolor="black12",
                            border_radius=15,
                            height=300,
                            padding=10,
                            border=ft.border.all(1, "white10")
                        )
                    ], col={"sm": 12, "md": 7}),
                ], spacing=40),
                padding=ft.padding.only(left=30, right=30, top=20, bottom=40)
            )
            
        ], scroll="auto", spacing=0)

    def _create_stat_card(self, title, value_control, icon, accent_color):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=24, color=accent_color),
                    ft.Text(title, color="grey500", size=14, weight="w500"),
                ], alignment="spaceBetween"),
                ft.Container(height=5),
                value_control,
                ft.Container(
                    width=float("inf"),
                    height=3,
                    bgcolor=accent_color,
                    border_radius=5,
                    opacity=0.3
                )
            ], spacing=5),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=25,
            border_radius=20,
            border=ft.border.all(1, "white10"),
        )

    def _create_action_button(self, title, subtitle, icon, color, nav_index):
        return ft.Container(
            content=ft.ListTile(
                leading=ft.Icon(icon, color=color, size=30),
                title=ft.Text(title, weight="bold"),
                subtitle=ft.Text(subtitle, size=12, color="grey400"),
                on_click=lambda _: self._nav_to(nav_index),
            ),
            bgcolor="white10",
            border_radius=15,
            ink=True,
            on_hover=lambda e: self._btn_hover(e)
        )

    def _btn_hover(self, e):
        e.control.bgcolor = "white24" if e.data == "true" else "white10"
        e.control.update()

    def _nav_to(self, index):
        # Find the NavigationRail in the page
        for control in self.main_page.controls:
            if isinstance(control, ft.Row):
                for sub in control.controls:
                    if isinstance(sub, ft.NavigationRail):
                        sub.selected_index = index
                        sub.on_change(ft.ControlEvent(target=sub.uid, name="change", data=str(index), control=sub, page=self.main_page))
                        return

    def add_activity(self, message, type="INFO"):
        icon = ft.icons.INFO_OUTLINE
        color = ft.colors.BLUE_400
        if type == "SUCCESS":
            icon = ft.icons.CHECK_CIRCLE_OUTLINE
            color = ft.colors.GREEN_400
        elif type == "WARNING":
            icon = ft.icons.WARNING_AMBER_OUTLINED
            color = ft.colors.ORANGE_400
            
        self.activity_list.controls.insert(0, 
            ft.Row([
                ft.Icon(icon, size=16, color=color),
                ft.Text(f"{datetime.now().strftime('%H:%M')} - {message}", size=13, color="grey300")
            ], spacing=10)
        )
        if len(self.activity_list.controls) > 10:
            self.activity_list.controls.pop()
        self.main_page.update()

    async def refresh_data(self):
        token = self.main_page.session.get("discord_token")
        user_data = self.main_page.session.get("user_data")
        
        if not token or not user_data:
            return
            
        self.profile_name.value = f"Welcome, {user_data.get('global_name') or user_data.get('username')}"
        self.profile_tag.value = f"@{user_data.get('username')} • Verified Manager"
        
        # Update Backups Count
        try:
            import os
            if os.path.exists("snapshots"):
                backup_files = [f for f in os.listdir("snapshots") if f.endswith(".json")]
                self.total_backups.value = str(len(backup_files))
        except Exception as e:
            print(f"Error updating backup count: {e}")

        self.add_activity(f"Logged in as {user_data.get('username')}", "SUCCESS")
        
        async with aiohttp.ClientSession(headers={"Authorization": token}) as session:
            try:
                async with session.get("https://discord.com/api/v10/users/@me/guilds", timeout=10) as resp:
                    if resp.status == 200:
                        guilds = await resp.json()
                        self.server_count.value = str(len(guilds))
                        self.server_count.color = "white"
                        self.add_activity(f"Fetched {len(guilds)} servers from Discord", "INFO")
                    elif resp.status == 429:
                        self.server_count.value = "!!"
                        self.server_count.color = "orange"
                        self.add_activity("Rate limited by Discord. Try again in a minute.", "WARNING")
                    else:
                        self.server_count.value = "ERR"
                        self.server_count.color = "red"
                        self.add_activity(f"Discord API error: HTTP {resp.status}", "ERROR")
            except Exception as e:
                self.server_count.value = "???"
                self.server_count.color = "red"
                self.add_activity(f"Connection failed: {str(e)}", "WARNING")
        
        self.main_page.update()
