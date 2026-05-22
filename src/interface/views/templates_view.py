import flet as ft
import json
import os
import shutil
import asyncio
import aiohttp
from datetime import datetime
from src.operation_file.restore_manager import RestoreManager

class TemplatesView(ft.Container):
    def __init__(self, page: ft.Page, nav_callback=None, log_callback=None, **kwargs):
        super().__init__(expand=True, padding=20, **kwargs)
        self.main_page = page
        self.nav_callback = nav_callback
        self.log_callback = log_callback
        self.restorer = RestoreManager(debug_callback=log_callback)
        
        # File Picker for JSON Import
        self.file_picker = ft.FilePicker(on_result=self._on_file_result)
        self.main_page.overlay.append(self.file_picker)
        
        # UI Components
        self.progress_bar = ft.ProgressBar(value=0, visible=False, color=ft.colors.BLUE_400, bgcolor=ft.colors.BLACK26)
        self.status_text = ft.Text("", size=12, italic=True, color="grey500")

        self.template_list = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=450,
            child_aspect_ratio=1.3,
            spacing=20,
            run_spacing=20,
        )
        
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Local Templates", icon=ft.icons.STORAGE),
                ft.Tab(text="Community Explorer", icon=ft.icons.PUBLIC),
            ],
            on_change=self._on_tab_change,
            expand=False
        )
        
        self.search_bar = ft.TextField(
            hint_text="Search templates...",
            prefix_icon=ft.icons.SEARCH,
            border_radius=10,
            width=300,
            on_change=self._on_search_change
        )

        self.content = ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Templates Marketplace", size=32, weight="bold"),
                    ft.Text("Download community layouts or import custom JSON structures.", color="grey500"),
                ], expand=True),
                ft.Row([
                    ft.ElevatedButton(
                        "Submit Template",
                        icon=ft.icons.PUBLISH,
                        on_click=lambda _: self.main_page.launch_url("https://github.com/DiscordServerCloner/tree/main/community_templates"),
                        style=ft.ButtonStyle(color=ft.colors.AMBER_400)
                    ),
                    ft.ElevatedButton(
                        "Import JSON", 
                        icon=ft.icons.UPLOAD_FILE, 
                        on_click=lambda _: self.file_picker.pick_files(allowed_extensions=["json"]),
                        style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color="white")
                    ),
                ], spacing=10),
            ], alignment="spaceBetween"),
            ft.Row([
                ft.Text("Quickly apply pre-made server structures.", color="grey600", size=14),
                ft.Column([self.status_text, self.progress_bar], spacing=2, width=350, horizontal_alignment="end")
            ], alignment="spaceBetween"),
            ft.Divider(height=30),
            ft.Row([self.tabs, self.search_bar], alignment="spaceBetween"),
            ft.Container(height=10),
            self.template_list
        ], expand=True)

    def _on_search_change(self, e):
        if self.tabs.selected_index == 0:
            self.main_page.run_task(self._load_local_templates, e.control.value)
        else:
            self.main_page.run_task(self._load_community_templates, e.control.value)

    def update_progress(self, value):
        self.progress_bar.value = value
        if value >= 1.0:
            self.status_text.value = "Template Applied Successfully!"
            self.progress_bar.color = ft.colors.GREEN_400
        elif value > 0:
            self.progress_bar.visible = True
            self.progress_bar.color = ft.colors.BLUE_400
            self.status_text.value = f"Applying Template... {int(value*100)}%"
        self.main_page.update()

    async def initialize_data(self):
        await self._load_local_templates()

    async def initialize_guilds(self):
        """Fetch guild list if missing from session"""
        token = self.main_page.session.get("discord_token")
        if not token: return []
        
        async with aiohttp.ClientSession(headers={"Authorization": token}) as session:
            try:
                async with session.get("https://discord.com/api/v10/users/@me/guilds") as resp:
                    if resp.status == 200:
                        guilds = await resp.json()
                        self.main_page.session.set("all_guilds", guilds)
                        return guilds
            except:
                pass
        return []

    def _on_tab_change(self, e):
        if self.tabs.selected_index == 0:
            self.main_page.run_task(self._load_local_templates)
        else:
            self.main_page.run_task(self._load_community_templates)

    async def _load_local_templates(self, search=""):
        self.template_list.controls.clear()
        templates = await self._scan_directory("snapshots", search)

        if not templates:
            self.template_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.SEARCH_OFF, size=50, color="grey700"),
                        ft.Text("No matching templates found.", color="grey500")
                    ], horizontal_alignment="center"),
                    padding=50,
                    col=12
                )
            )
        else:
            for t in templates:
                self.template_list.controls.append(self._create_template_card(t, is_community=False))
        
        self.main_page.update()

    async def _scan_directory(self, directory, search=""):
        if not os.path.exists(directory):
            os.makedirs(directory)
            return []
            
        templates = []
        search = search.lower()
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(directory, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        metadata = data.get("metadata", {})
                        name = metadata.get("guild_name", filename)
                        
                        if search not in name.lower():
                            continue
                            
                        guild_data = data.get("data", {})
                        roles = guild_data.get("roles", [])
                        channels = guild_data.get("channels", [])
                        
                        categories = [c for c in channels if c.get("type") == 4]
                        text_channels = [c for c in channels if c.get("type") in [0, 5]]
                        voice_channels = [c for c in channels if c.get("type") in [2, 13]]

                        templates.append({
                            "name": name,
                            "description": metadata.get("description", "No description provided"),
                            "filename": filename,
                            "roles": len(roles),
                            "channels": len(channels),
                            "cat_count": len(categories),
                            "txt_count": len(text_channels),
                            "vc_count": len(voice_channels),
                            "top_roles": roles[:12],  # First 12 roles for preview
                            "top_cats": [c["name"] for c in categories[:3]], # Top 3 categories
                            "author": metadata.get("author", "Local User"),
                            "date": metadata.get("captured_at", "")[:10]
                        })
                except:
                    continue
        return templates

    async def _load_community_templates(self, search=""):
        self.template_list.controls.clear()
        
        # Info Banner
        if not search:
            self.template_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.PUBLIC, color="blue400"),
                            ft.Text("Community Explorer (Online)", size=18, weight="bold"),
                        ]),
                        ft.Text("Fetching the latest verified templates directly from GitHub. An active internet connection is required.", color="grey400", size=13),
                        ft.Divider(height=10, thickness=0.5, color="white10"),
                    ], spacing=10),
                    padding=20,
                    bgcolor="white10",
                    border_radius=15,
                    col=12
                )
            )
        
        loading_bar = ft.ProgressBar(width=400, color="blue")
        self.template_list.controls.append(loading_bar)
        self.main_page.update()
        
        GITHUB_API = "https://api.github.com/repos/seregonwar/DiscordServerManager/contents/community_templates"
        headers = {
            "User-Agent": "Discord-Management-Suite-V3",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(GITHUB_API, timeout=15) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"GitHub API error {resp.status}: {error_text[:100]}")
                    
                    files = await resp.json()
                    if not isinstance(files, list):
                        raise Exception("Invalid response from GitHub API.")
                        
                    json_files = [f for f in files if f.get("name", "").endswith(".json")]
                    
                    if not json_files:
                        self.template_list.controls.remove(loading_bar)
                        self.template_list.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.icons.INFO_OUTLINE, size=50, color="amber400"),
                                    ft.Text("No JSON templates found in the repository.", color="grey500"),
                                ], horizontal_alignment="center"),
                                padding=50, col=12
                            )
                        )
                        self.main_page.update()
                        return

                    # Parallel fetch of actual JSON contents to get metadata
                    async def fetch_one(f_info):
                        try:
                            async with session.get(f_info["download_url"], timeout=10) as r:
                                if r.status == 200:
                                    # GitHub Raw often serves JSON as text/plain, so we bypass strict mimetype check
                                    data = await r.json(content_type=None)
                                    metadata = data.get("metadata", {})
                                    guild_data = data.get("data", {})
                                    roles = guild_data.get("roles", [])
                                    channels = guild_data.get("channels", [])
                                    
                                    cats = [c for c in channels if c.get("type") == 4]
                                    txt = [c for c in channels if c.get("type") in [0, 5]]
                                    vc = [c for c in channels if c.get("type") in [2, 13]]
                                    
                                    return {
                                        "name": metadata.get("guild_name", f_info["name"]),
                                        "description": metadata.get("description", "No description provided"),
                                        "filename": f_info["name"],
                                        "roles": len(roles),
                                        "channels": len(channels),
                                        "cat_count": len(cats),
                                        "txt_count": len(txt),
                                        "vc_count": len(vc),
                                        "top_roles": roles[:12],
                                        "top_cats": [c["name"] for c in cats[:3]],
                                        "author": metadata.get("author", "Community"),
                                        "date": metadata.get("captured_at", "Recent")[:10],
                                        "raw_data": data
                                    }
                                else:
                                    print(f"Failed to download {f_info['name']}: {r.status}")
                        except Exception as e:
                            print(f"Error fetching {f_info['name']}: {e}")
                        return None

                    tasks = [fetch_one(f) for f in json_files]
                    results = await asyncio.gather(*tasks)
                    community_data = [r for r in results if r is not None]

                    if loading_bar in self.template_list.controls:
                        self.template_list.controls.remove(loading_bar)

                    # Filter by search
                    if search:
                        community_data = [t for t in community_data if search.lower() in t["name"].lower()]
                    
                    for t in community_data:
                        self.template_list.controls.append(self._create_template_card(t, is_community=True))
                    
                    if not community_data and not search:
                        raise Exception("All template fetches failed or returned invalid data.")
                    elif not community_data:
                        self.template_list.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Icon(ft.icons.SEARCH_OFF, size=50, color="grey700"),
                                    ft.Text("No community templates found matching your search.", color="grey500"),
                                ], horizontal_alignment="center"),
                                padding=50, col=12
                            )
                        )
        except Exception as e:
            if loading_bar in self.template_list.controls:
                self.template_list.controls.remove(loading_bar)
            
            self.template_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.WIFI_OFF_ROUNDED, size=50, color="red400"),
                        ft.Text("Marketplace Error", size=20, weight="bold"),
                        ft.Text(f"Connection Issue: {str(e)}", color="grey500", text_align="center"),
                        ft.ElevatedButton("Try Again", icon=ft.icons.REFRESH, on_click=lambda _: self.main_page.run_task(self._load_community_templates))
                    ], horizontal_alignment="center"),
                    padding=50, col=12
                )
            )
        
        self.main_page.update()

    def _create_template_card(self, t, is_community):
        # Preview Section
        preview_content = ft.Container(
            content=ft.Column([
                ft.Divider(height=1, thickness=0.5, color="white10"),
                ft.Text("STRUCTURE BREAKDOWN", size=9, weight="bold", color="grey600", style=ft.TextStyle(letter_spacing=1.1)),
                ft.Row([
                    ft.Column([
                        ft.Row([ft.Icon(ft.icons.CATEGORY_OUTLINED, size=12, color="blue400"), ft.Text(f"{t['cat_count']} Categories", size=10, color="grey400")]),
                        ft.Row([ft.Icon(ft.icons.CHAT_BUBBLE_OUTLINE, size=12, color="blue400"), ft.Text(f"{t['txt_count']} Text", size=10, color="grey400")]),
                        ft.Row([ft.Icon(ft.icons.MIC_NONE, size=12, color="blue400"), ft.Text(f"{t['vc_count']} Voice", size=10, color="grey400")]),
                    ], spacing=2, expand=True),
                    ft.VerticalDivider(width=1, color="white10"),
                    ft.Column([
                        ft.Text("INCLUDES:", size=9, color="grey600", weight="bold"),
                        *[ft.Text(f"• {cat}", size=10, color="grey500", overflow=ft.TextOverflow.ELLIPSIS, max_lines=1) for cat in t['top_cats']]
                    ], spacing=2, expand=True) if t['top_cats'] else ft.Container()
                ], spacing=10),
                ft.Text("TOP ROLES", size=9, weight="bold", color="grey600", style=ft.TextStyle(letter_spacing=1.1)),
                ft.Row([
                    ft.Container(
                        content=ft.CircleAvatar(bgcolor=self._int_to_hex(r.get('color', 0)), radius=4),
                        tooltip=r['name']
                    ) for r in t['top_roles'] if r['name'] != "@everyone"
                ], spacing=4, wrap=True)
            ], spacing=8),
            padding=ft.padding.only(left=15, right=15, bottom=10),
            expand=True
        )

        return ft.Container(
            content=ft.Column([
                ft.ListTile(
                    leading=ft.Icon(ft.icons.DASHBOARD_CUSTOMIZE if not is_community else ft.icons.PUBLIC, color="blue400" if not is_community else "green400", size=30),
                    title=ft.Text(t["name"], weight="bold", no_wrap=True, size=15),
                    subtitle=ft.Text(t['description'], size=11, color="grey400", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ),
                ft.Container(
                    content=ft.Row([
                        self._badge(f"{t['roles']} Roles", ft.colors.AMBER_800),
                        self._badge(f"{t['channels']} Channels", ft.colors.BLUE_800),
                    ], spacing=10),
                    padding=ft.padding.only(left=15, right=15)
                ),
                preview_content,
                ft.Divider(height=1, thickness=0.5, color="white10"),
                ft.Container(
                    content=ft.Row([
                        ft.TextButton(
                            "Explore", 
                            icon=ft.icons.EXPLORE,
                            on_click=lambda _: self.main_page.run_task(self._explore_template, t)
                        ),
                        ft.TextButton(
                            "Use Template", 
                            icon=ft.icons.REPLAY if not is_community else ft.icons.ROCKET_LAUNCH,
                            on_click=lambda _: self.main_page.run_task(self._use_template, t, is_community)
                        )
                    ], alignment="spaceBetween"),
                    padding=ft.padding.only(left=10, right=10)
                )
            ], spacing=5),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=15,
            border=ft.border.all(1, "white10"),
            ink=True,
            on_hover=lambda e: self._on_hover(e)
        )

    def _int_to_hex(self, color_int):
        if not color_int: return "grey700"
        return f"#{color_int:06x}"

    async def _explore_template(self, t):
        try:
            if "raw_data" in t:
                data = t["raw_data"]
            else:
                filepath = os.path.join("snapshots", t['filename'])
                if not os.path.exists(filepath):
                    filepath = os.path.join("community_templates", t['filename'])
                
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            
            from src.interface.views.explorer_view import ExplorerView
            
            # Create a localized explorer for the template
            temp_explorer = ExplorerView(self.main_page)
            temp_explorer.status_lbl.value = f"Previewing Template: {t['name']}"
            temp_explorer.channels = data["data"]["channels"]
            temp_explorer._render_tree()
            
            dlg = ft.AlertDialog(
                title=ft.Text(f"Structure Preview: {t['name']}"),
                content=ft.Container(content=temp_explorer, width=1000, height=600),
                actions=[ft.TextButton("Close", on_click=lambda _: self.main_page.close(dlg))],
                actions_alignment="end"
            )
            self.main_page.open(dlg)
        except Exception as e:
            self.main_page.open(ft.SnackBar(content=ft.Text(f"Failed to explore template: {str(e)}")))

    def _badge(self, text, color):
        return ft.Container(
            content=ft.Text(text, size=10, weight="bold"),
            bgcolor=color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=5
        )

    def _on_hover(self, e):
        e.control.border = ft.border.all(1, "blue400") if e.data == "true" else ft.border.all(1, "white10")
        e.control.update()

    async def _on_file_result(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return
            
        file = e.files[0]
        try:
            with open(file.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "metadata" not in data or "data" not in data:
                raise ValueError("Invalid snapshot format")
            
            dest = os.path.join("snapshots", file.name)
            shutil.copy(file.path, dest)
            
            self.main_page.open(ft.SnackBar(content=ft.Text(f"Imported {file.name} successfully!"), bgcolor="green700"))
            await self._load_local_templates()
        except Exception as ex:
            self.main_page.open(ft.SnackBar(content=ft.Text(f"Import failed: {str(ex)}"), bgcolor="red700"))

    async def _use_template(self, t, is_community=False):
        # 1. Ensure we have the target guilds
        all_guilds = self.main_page.session.get("all_guilds")
        if not all_guilds:
            self.main_page.open(ft.SnackBar(content=ft.Text("Refreshing server list...")))
            all_guilds = await self.initialize_guilds()
        
        if not all_guilds:
            self.main_page.open(ft.SnackBar(content=ft.Text("No destination servers found."), bgcolor="red700"))
            return

        # 2. Setup Options Controls
        opt_roles = ft.Switch(label="Apply Roles", value=True)
        opt_categories = ft.Switch(label="Apply Categories", value=True)
        opt_text = ft.Switch(label="Apply Text Channels", value=True)
        opt_voice = ft.Switch(label="Apply Voice Channels", value=True)
        opt_clear = ft.Switch(label="Wipe Destination First", value=True)
        
        list_container = ft.Column(scroll="auto", height=250, spacing=5)
        
        async def run_apply(dest_guild):
            self.main_page.close(dlg)
            
            try:
                if "raw_data" in t:
                    template_data = t["raw_data"]
                else:
                    filepath = os.path.join("snapshots", t['filename'])
                    if not os.path.exists(filepath):
                        filepath = os.path.join("community_templates", t['filename'])
                    
                    with open(filepath, "r", encoding="utf-8") as f:
                        template_data = json.load(f)
                
                options = {
                    "clone_roles": opt_roles.value,
                    "clone_categories": opt_categories.value,
                    "clone_text_channels": opt_text.value,
                    "clone_voice_channels": opt_voice.value,
                    "clear_roles": opt_clear.value,
                    "clear_categories": opt_clear.value,
                    "clear_channels": opt_clear.value
                }

                self.status_text.value = f"Preparing to apply {t['name']}..."
                self.progress_bar.value = 0
                self.progress_bar.visible = True
                self.main_page.update()

                token = self.main_page.session.get("discord_token")
                self.restorer.set_progress_callback(self.update_progress)

                success = await self.restorer.restore_snapshot(template_data, dest_guild['id'], token, options)
                if success:
                    self.main_page.open(ft.SnackBar(content=ft.Text("Template Applied!"), bgcolor="green700"))
                else:
                    self.main_page.open(ft.SnackBar(content=ft.Text("Application failed. Check debug logs."), bgcolor="red700"))
                    
            except Exception as ex:
                self.main_page.open(ft.SnackBar(content=ft.Text(f"Error: {str(ex)}"), bgcolor="red700"))
            finally:
                await asyncio.sleep(3)
                self.progress_bar.visible = False
                self.status_text.value = ""
                self.main_page.update()

        # 3. Build the server list
        for g in all_guilds:
            list_container.controls.append(
                ft.ListTile(
                    title=ft.Text(g['name']),
                    subtitle=ft.Text(f"ID: {g['id']}"),
                    on_click=lambda _, guild=g: self.main_page.run_task(run_apply, guild)
                )
            )

        # 4. Open the Dialog
        dlg = ft.AlertDialog(
            title=ft.Text(f"Apply Template: {t['name']}"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Select Components to Apply", weight="bold"),
                    ft.Row([opt_roles, opt_categories], wrap=True),
                    ft.Row([opt_text, opt_voice], wrap=True),
                    opt_clear,
                    ft.Divider(),
                    ft.Text("Select Destination Server", weight="bold"),
                    list_container
                ], tight=True, spacing=10),
                width=450
            ),
            actions=[ft.TextButton("Cancel", on_click=lambda _: self.main_page.close(dlg))]
        )
        self.main_page.open(dlg)
