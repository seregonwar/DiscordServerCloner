import flet as ft
import aiohttp
import asyncio
from src.core.utils.language_manager import LanguageManager

class ExplorerView(ft.Container):
    def __init__(self, main_page: ft.Page, **kwargs):
        super().__init__(expand=True, padding=10, **kwargs)
        self.main_page = main_page
        self.lang = LanguageManager()
        
        # State
        self.current_guild = None
        self.channels = []
        
        # UI Components
        self.sidebar = ft.Column(scroll="auto", spacing=5)
        self.main_content = ft.Container(
            content=ft.Column([
                ft.Icon("explore", size=100, color="grey700"),
                ft.Text("Select a channel to view details", size=16, color="grey500")
            ], horizontal_alignment="center", alignment="center"),
            expand=True,
            bgcolor="black26",
            border_radius=10,
            padding=20
        )
        
        self.status_lbl = ft.Text("No server loaded", color="grey400")

        self.content = ft.Column([
            ft.Row([
                ft.Text("Server Explorer", size=24, weight="bold"),
                self.status_lbl
            ], alignment="spaceBetween"),
            ft.Divider(),
            ft.Row([
                ft.Container(content=self.sidebar, width=280),
                ft.VerticalDivider(width=1),
                self.main_content
            ], expand=True)
        ])

    async def load_guild(self, guild):
        self.current_guild = guild
        self.status_lbl.value = f"Exploring: {guild['name']}"
        self.sidebar.controls.clear()
        self.sidebar.controls.append(ft.ProgressBar(visible=True))
        self.main_page.update()
        
        token = self.main_page.session.get("discord_token")
        async with aiohttp.ClientSession(headers={"Authorization": token}) as session:
            try:
                async with session.get(f"https://discord.com/api/v10/guilds/{guild['id']}/channels") as resp:
                    if resp.status == 200:
                        self.channels = await resp.json()
                        self._render_tree()
                    else:
                        self.status_lbl.value = f"Error: {resp.status}"
            except Exception as e:
                self.status_lbl.value = f"Error: {str(e)}"
        
        self.main_page.update()

    def _render_tree(self):
        self.sidebar.controls.clear()
        
        # Build maps
        categories = {c['id']: c for c in self.channels if c.get('type') == 4}
        by_category = {cid: [] for cid in categories.keys()}
        uncategorized = []
        
        for ch in self.channels:
            if ch.get('type') == 4: continue
            parent_id = ch.get('parent_id')
            if parent_id in by_category:
                by_category[parent_id].append(ch)
            else:
                uncategorized.append(ch)
                
        # Sort
        for lst in by_category.values():
            lst.sort(key=lambda x: (x.get('position', 0), x.get('id')))
        uncategorized.sort(key=lambda x: (x.get('position', 0), x.get('id')))

        # Render categories
        for cat_id, cat in sorted(categories.items(), key=lambda kv: kv[1].get('position', 0)):
            expansion = ft.ExpansionTile(
                title=ft.Text(cat.get('name', 'UNKNOWN').upper(), size=12, weight="bold", color="grey400"),
                initially_expanded=True,
                controls=[]
            )
            for ch in by_category[cat_id]:
                expansion.controls.append(self._channel_item(ch))
            self.sidebar.controls.append(expansion)
            
        # Uncategorized
        if uncategorized:
            for ch in uncategorized:
                self.sidebar.controls.append(self._channel_item(ch))

    def _channel_item(self, ch):
        ch_type = ch.get('type')
        icon_map = {0: "tag", 2: "volume_up", 4: "folder", 5: "announcement", 13: "mic_external_on", 15: "forum"}
        icon = icon_map.get(ch_type, "tag")
        
        return ft.ListTile(
            leading=ft.Icon(icon, size=18, color="grey400"),
            title=ft.Text(ch.get('name', 'unknown'), size=14),
            dense=True,
            on_click=lambda _: self._show_channel_details(ch)
        )

    def _show_channel_details(self, ch):
        type_names = {0: 'Text Channel', 2: 'Voice Channel', 4: 'Category', 5: 'News Channel', 13: 'Stage Channel', 15: 'Forum'}
        
        details = ft.Column([
            ft.Row([ft.Icon("info_outline"), ft.Text(f"#{ch['name']}", size=20, weight="bold")]),
            ft.Divider(),
            ft.Text(f"ID: {ch['id']}"),
            ft.Text(f"Type: {type_names.get(ch['type'], f'Type {ch['type']}')}"),
            ft.Text(f"Topic: {ch.get('topic') or 'No topic set'}", italic=True),
            ft.Text(f"NSFW: {'Yes' if ch.get('nsfw') else 'No'}"),
            ft.Text(f"Slowmode: {ch.get('rate_limit_per_user', 0)}s"),
        ], spacing=10)
        
        self.main_content.content = details
        self.main_page.update()
