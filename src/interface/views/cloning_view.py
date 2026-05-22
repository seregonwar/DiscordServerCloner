import flet as ft
import asyncio
import aiohttp
import os
import json
from datetime import datetime
from src.core.utils.language_manager import LanguageManager
from src.operation_file.serverclone import Clone

class CloningView(ft.Container):
    def __init__(self, main_page: ft.Page, log_callback=None, explorer_callback=None, **kwargs):
        super().__init__(expand=True, padding=20, **kwargs)
        self.main_page = main_page
        self.lang = LanguageManager()
        self.log_callback = log_callback
        self.explorer_callback = explorer_callback
        self.cloner = Clone(debug_callback=self.on_debug_message)
        
        # State
        self.source_guild = None
        self.dest_guild = None
        self.all_guilds = []

        # UI Components
        self.title_text = ft.Text("Server Cloning Engine", size=32, weight="bold")
        
        self.source_card = self._create_guild_selection_card("Source Server", ft.icons.LOGIN_ROUNDED, True, ft.colors.BLUE_400)
        self.dest_card = self._create_guild_selection_card("Destination Server", ft.icons.LOGOUT_ROUNDED, False, ft.colors.GREEN_400)

        self.opt_roles = ft.Switch(label="Clone Roles", value=True, active_color=ft.colors.BLUE_400)
        self.opt_categories = ft.Switch(label="Clone Categories", value=True, active_color=ft.colors.BLUE_400)
        self.opt_text = ft.Switch(label="Clone Text Channels", value=True, active_color=ft.colors.BLUE_400)
        self.opt_voice = ft.Switch(label="Clone Voice Channels", value=True, active_color=ft.colors.BLUE_400)
        
        self.opt_clear_roles = ft.Switch(label="Clear Existing Roles", value=True, active_color=ft.colors.ORANGE_400)
        self.opt_clear_categories = ft.Switch(label="Clear Existing Categories", value=True, active_color=ft.colors.ORANGE_400)
        self.opt_clear_channels = ft.Switch(label="Clear Existing Channels", value=True, active_color=ft.colors.ORANGE_400)
        
        self.opt_name_icon = ft.Switch(label="Clone Name & Icon", value=False)
        self.opt_messages = ft.Switch(label="Clone Messages (REST)", value=False, on_change=self._toggle_msg_limit)
        self.opt_limit = ft.TextField(label="Limit", value="100", width=80, visible=False, border_radius=10)
        
        self.clone_btn = ft.ElevatedButton(
            text="Launch Cloning Engine",
            icon=ft.icons.ROCKET_LAUNCH,
            on_click=self.start_cloning,
            disabled=True,
            height=60,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.colors.PRIMARY, ft.ControlState.DISABLED: ft.colors.GREY_800},
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=15),
            )
        )

        self.progress_bar = ft.ProgressBar(value=0, visible=False, color=ft.colors.CYAN_400, height=10, border_radius=5)
        self.status_text = ft.Text("System Ready", color=ft.colors.GREY_400, italic=True)

        self.content = ft.Column([
            ft.Row([
                ft.Icon(ft.icons.ROCKET_LAUNCH, size=35, color=ft.colors.PRIMARY),
                self.title_text
            ], spacing=15),
            ft.Text("Configure and execute high-fidelity server replications.", color="grey500", size=14),
            ft.Divider(height=30),
            
            # Selection Section
            ft.ResponsiveRow([
                ft.Column([self.source_card], col={"sm": 12, "md": 6}),
                ft.Column([self.dest_card], col={"sm": 12, "md": 6}),
            ], spacing=20),
            
            # Options Cards
            ft.ResponsiveRow([
                # Cloning Options
                ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Cloning Parameters", size=18, weight="bold", color="blue400"),
                            ft.Divider(height=10, thickness=0.5),
                            ft.ResponsiveRow([
                                ft.Column([self.opt_roles, self.opt_categories], col={"sm": 6}),
                                ft.Column([self.opt_text, self.opt_voice], col={"sm": 6}),
                            ]),
                            self.opt_name_icon,
                        ], spacing=15),
                        bgcolor=ft.colors.BLACK12,
                        padding=20,
                        border_radius=20,
                        border=ft.border.all(1, "white10")
                    )
                ], col={"sm": 12, "md": 6}),

                # Cleanup & Messages
                ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Cleanup & Advanced", size=18, weight="bold", color="orange400"),
                            ft.Divider(height=10, thickness=0.5),
                            ft.Row([self.opt_clear_roles, self.opt_clear_categories, self.opt_clear_channels], wrap=True),
                            ft.Row([self.opt_messages, self.opt_limit], vertical_alignment="center"),
                        ], spacing=15),
                        bgcolor=ft.colors.BLACK12,
                        padding=20,
                        border_radius=20,
                        border=ft.border.all(1, "white10")
                    )
                ], col={"sm": 12, "md": 6}),
            ], spacing=20),

            # Progress Section
            ft.Container(
                content=ft.Column([
                    self.progress_bar,
                    ft.Row([
                        self.status_text,
                        self.clone_btn
                    ], alignment="spaceBetween")
                ], spacing=15),
                padding=ft.padding.only(top=20)
            )
        ], scroll="auto", spacing=25)

    def _create_guild_selection_card(self, title, icon, is_source, accent_color):
        return ft.Container(
            content=ft.Column([
                ft.ListTile(
                    leading=ft.Container(
                        content=ft.Icon(icon, color="white", size=24),
                        bgcolor=accent_color,
                        width=45, height=45,
                        border_radius=12,
                        alignment=ft.alignment.center
                    ),
                    title=ft.Text(title, weight="bold", size=18),
                    subtitle=ft.Text("Click to select target server", color=ft.colors.GREY_500),
                ),
                ft.Row([
                    ft.TextButton("Browse List", icon=ft.icons.LIST_ALT_ROUNDED, on_click=lambda _: self._open_guild_picker(is_source)),
                    ft.TextButton("Manual ID", icon=ft.icons.FINGERPRINT_ROUNDED, on_click=lambda _: self._open_manual_id_dialog(is_source)),
                    ft.ElevatedButton(
                        "Explorer", 
                        icon=ft.icons.EXPLORE_ROUNDED, 
                        on_click=lambda _: self._open_explorer(is_source), 
                        visible=False,
                        style=ft.ButtonStyle(bgcolor=ft.colors.GREY_900)
                    ),
                ], alignment="end", spacing=5)
            ], spacing=10),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=15,
            border_radius=20,
            border=ft.border.all(1, "white10"),
            on_hover=lambda e: self._btn_hover(e)
        )

    def _btn_hover(self, e):
        e.control.bgcolor = "white10" if e.data == "true" else ft.colors.SURFACE_VARIANT
        e.control.update()

    def update_ui(self):
        # Check if a template was selected from the Templates View
        template_file = self.main_page.session.get("selected_template")
        if template_file:
            self.load_template(template_file)
            self.main_page.session.set("selected_template", None) # Clear after loading
        self.main_page.update()

    def load_template(self, filename):
        try:
            filepath = os.path.join("snapshots", filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Create a mock guild object for the UI
            guild = {
                "id": f"TEMPLATE:{filename}", 
                "name": f"Template: {data['metadata']['guild_name']}", 
                "icon": None,
                "is_template": True,
                "data": data
            }
            self._select_guild(guild, True) # Select as source
        except Exception as e:
            print(f"Failed to load template into cloner: {e}")

    async def initialize_data(self):
        token = self.main_page.session.get("discord_token")
        if not token: return
        async with aiohttp.ClientSession(headers={"Authorization": token}) as session:
            try:
                async with session.get("https://discord.com/api/v10/users/@me/guilds") as resp:
                    if resp.status == 200:
                        self.all_guilds = await resp.json()
                        self.main_page.session.set("all_guilds", self.all_guilds) # Ensure session is updated
                        self.status_text.value = f"Core Ready - {len(self.all_guilds)} servers linked"
            except Exception as ex:
                self.status_text.value = f"Initialization Error"
        self.main_page.update()

    def _toggle_msg_limit(self, e):
        self.opt_limit.visible = e.control.value
        self.main_page.update()

    def _open_manual_id_dialog(self, is_source):
        id_input = ft.TextField(label="Input Server ID", hint_text="Enter snowflake ID...", border_radius=10)
        def close_dlg(_):
            dlg.open = False
            self.main_page.update()
        def confirm(_):
            if not id_input.value: return
            guild = {"id": id_input.value, "name": f"Manual ID", "icon": None}
            self._select_guild(guild, is_source)
            close_dlg(None)

        dlg = ft.AlertDialog(
            title=ft.Text("Target Identification"),
            content=id_input,
            actions=[ft.TextButton("Cancel", on_click=close_dlg), ft.ElevatedButton("Lock Target", on_click=confirm)]
        )
        self.main_page.open(dlg)

    def _open_guild_picker(self, is_source):
        if not self.all_guilds:
            self.main_page.run_task(self.initialize_data)
            return
        search_field = ft.TextField(hint_text="Search by name or ID...", prefix_icon=ft.icons.SEARCH, border_radius=10,
                                   on_change=lambda e: update_list(e.control.value))
        list_container = ft.Column(scroll="auto", height=400, spacing=5)
        def close_picker(_):
            dlg.open = False
            self.main_page.update()
        def update_list(search_term=""):
            list_container.controls.clear()
            term = search_term.lower()
            for g in self.all_guilds:
                if term in g['name'].lower() or term in g['id']:
                    icon_url = f"https://cdn.discordapp.com/icons/{g['id']}/{g['icon']}.png" if g['icon'] else ""
                    list_container.controls.append(
                        ft.ListTile(
                            leading=ft.Image(src=icon_url, width=32, height=32, border_radius=16) if icon_url else ft.Icon(ft.icons.GROUP),
                            title=ft.Text(g['name']),
                            subtitle=ft.Text(f"ID: {g['id']}"),
                            on_click=lambda _, guild=g: [self._select_guild(guild, is_source), close_picker(None)]
                        )
                    )
            self.main_page.update()
        update_list()
        dlg = ft.AlertDialog(title=ft.Text("Select Operational Target"), content=ft.Container(content=ft.Column([search_field, list_container], tight=True), width=450))
        self.main_page.open(dlg)

    def _select_guild(self, guild, is_source):
        card = self.source_card if is_source else self.dest_card
        if is_source: self.source_guild = guild
        else: self.dest_guild = guild
        card.content.controls[0].subtitle.value = f"{guild['name']} ({guild['id']})"
        card.content.controls[0].subtitle.color = ft.colors.BLUE_400 if is_source else ft.colors.GREEN_400
        card.content.controls[1].controls[2].visible = True
        self.clone_btn.disabled = not (self.source_guild and self.dest_guild)
        self.main_page.update()

    def _open_explorer(self, is_source):
        guild = self.source_guild if is_source else self.dest_guild
        if guild and self.explorer_callback:
            self.main_page.run_task(self.explorer_callback, guild)
        else:
            self.main_page.open(ft.SnackBar(content=ft.Text("Select a guild first!")))

    async def start_cloning(self, e):
        self.clone_btn.disabled = True
        self.progress_bar.visible = True
        self.progress_bar.value = 0
        self.status_text.value = "Engine Initializing..."
        self.main_page.update()
        
        options = {
            "clone_roles": self.opt_roles.value,
            "clone_categories": self.opt_categories.value,
            "clone_text_channels": self.opt_text.value,
            "clone_voice_channels": self.opt_voice.value,
            "clear_roles": self.opt_clear_roles.value,
            "clear_categories": self.opt_clear_categories.value,
            "clear_channels": self.opt_clear_channels.value,
            "clone_messages": self.opt_messages.value,
            "messages_limit": int(self.opt_limit.value) if self.opt_messages.value else 0,
            "clone_name_icon": self.opt_name_icon.value
        }
        
        token = self.main_page.session.get("discord_token")
        
        # Check if source is a template
        if self.source_guild.get("is_template"):
            from src.operation_file.restore_manager import RestoreManager
            restorer = RestoreManager(debug_callback=self.on_debug_message)
            restorer.set_progress_callback(self.update_progress)
            
            self.status_text.value = "Restoring from Template..."
            success = await restorer.restore_snapshot(
                self.source_guild["data"], 
                self.dest_guild["id"], 
                token, 
                options
            )
            # Use real stats if available
            final_stats = restorer.get_stats()
            final_stats.update({
                "source": self.source_guild["name"],
                "destination": self.dest_guild["name"],
                "type": "restoration",
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
        else:
            self.cloner.set_progress_callback(self.update_progress)
            async with aiohttp.ClientSession(headers={"Authorization": token}) as session:
                success = await self.cloner.start_clone(self.source_guild, self.dest_guild, session, options)
            
            final_stats = self.cloner.get_stats()
            final_stats.update({
                "source": self.source_guild["name"],
                "destination": self.dest_guild["name"],
                "type": "cloning",
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
        
        if success:
            self.status_text.value = "Mission Accomplished!"
            self.status_text.color = ft.colors.GREEN
            
            # Save stats for analytics
            from src.core.utils.stats_manager import save_stats
            save_stats(final_stats)
        else:
            self.status_text.value = "Engine Failure. See Logs."
            self.status_text.color = ft.colors.RED
            
        self.clone_btn.disabled = False
        self.main_page.update()

    def update_progress(self, progress):
        self.progress_bar.value = progress
        self.main_page.update()

    def on_debug_message(self, message, level="INFO"):
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")
