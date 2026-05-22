import flet as ft
import asyncio
import os
import json
import shutil
from src.operation_file.snapshot_manager import SnapshotManager
from src.operation_file.restore_manager import RestoreManager
from datetime import datetime
import aiohttp

class SnapshotView(ft.Container):
    def __init__(self, page: ft.Page, log_callback=None, **kwargs):
        super().__init__(expand=True, padding=20, **kwargs)
        self.main_page = page
        self.manager = SnapshotManager()
        self.restorer = RestoreManager(debug_callback=log_callback)
        self.log_callback = log_callback
        
        # State
        self.snapshots = []
        
        # UI Components
        self.progress_bar = ft.ProgressBar(value=0, visible=False, color=ft.colors.AMBER_400, bgcolor=ft.colors.BLACK26)
        self.status_text = ft.Text("", size=12, italic=True, color="grey500")
        
        self.snapshot_list = ft.Column(spacing=15, scroll="auto")
        self.empty_state = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.CAMERA_ALT_OUTLINED, size=100, color="grey700"),
                ft.Text("No Snapshots Found", size=24, weight="bold", color="grey500"),
                ft.Text("Capture your first server backup to see it here.", color="grey600"),
                ft.Container(height=10),
                ft.ElevatedButton("Create Your First Snapshot", icon=ft.icons.ADD_A_PHOTO, on_click=self._open_create_dlg)
            ], horizontal_alignment="center", alignment="center"),
            visible=True,
            expand=True
        )

        self.content = ft.Column([
            ft.Row([
                ft.Row([
                    ft.Icon(ft.icons.CAMERA_ALT, size=35, color=ft.colors.AMBER_400),
                    ft.Text("Snapshot Manager", size=32, weight="bold"),
                ]),
                ft.Row([
                    ft.TextButton("Open Folder", icon=ft.icons.FOLDER_OPEN, on_click=self._open_folder),
                    ft.ElevatedButton(
                        "Create Snapshot", 
                        icon=ft.icons.ADD_A_PHOTO, 
                        on_click=self._open_create_dlg,
                        style=ft.ButtonStyle(bgcolor=ft.colors.AMBER_700, color="white")
                    ),
                ], spacing=15),
            ], alignment="spaceBetween"),
            ft.Row([
                ft.Text("Full backups of server structures stored locally.", color="grey500", size=14),
                ft.Column([self.status_text, self.progress_bar], spacing=2, width=350, horizontal_alignment="end")
            ], alignment="spaceBetween"),
            ft.Divider(height=30, thickness=1),
            
            # List Area
            ft.Stack([
                self.snapshot_list,
                self.empty_state
            ], expand=True)
        ], expand=True)

    def update_progress(self, value):
        self.progress_bar.value = value
        if value >= 1.0:
            self.status_text.value = "Restoration Complete"
            self.progress_bar.color = ft.colors.GREEN_400
        elif value > 0:
            self.progress_bar.visible = True
            self.progress_bar.color = ft.colors.AMBER_400
            self.status_text.value = f"Restoring... {int(value*100)}%"
        self.main_page.update()

    async def initialize_data(self):
        self.snapshots = self.manager.list_snapshots()
        self._render_list()

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

    def _render_list(self):
        self.snapshot_list.controls.clear()
        self.empty_state.visible = (len(self.snapshots) == 0)
        
        for s in self.snapshots:
            dt = datetime.fromisoformat(s['captured_at']).strftime("%b %d, %Y - %H:%M")
            self.snapshot_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Container(
                                content=ft.Icon(ft.icons.INSERT_DRIVE_FILE_OUTLINED, color="white", size=30),
                                bgcolor=ft.colors.AMBER_800,
                                border_radius=10,
                                width=50, height=50,
                                alignment=ft.alignment.center
                            ),
                            title=ft.Text(s['guild_name'], weight="bold", size=18),
                            subtitle=ft.Text(s.get('description') or f"Captured: {dt}", color="grey400", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            trailing=ft.Container(
                                content=ft.Text(f"{s['roles_count']} Roles • {s['channels_count']} Channels", weight="bold", size=12),
                                padding=ft.padding.all(8),
                                bgcolor="black26",
                                border_radius=8
                            ),
                        ),
                        ft.Divider(height=1, thickness=0.5, color="white10"),
                        ft.Row([
                            ft.TextButton("Restore", icon=ft.icons.REPLAY, on_click=lambda _, x=s: self._restore_snapshot(x)),
                            ft.TextButton("Edit Info", icon=ft.icons.EDIT_NOTE, on_click=lambda _, x=s: self._edit_description(x)),
                            ft.TextButton("View Details", icon=ft.icons.VISIBILITY, on_click=lambda _, x=s: self._view_details(x)),
                            ft.TextButton("Export Template", icon=ft.icons.FILE_DOWNLOAD_OUTLINED, on_click=lambda _, x=s: self._export_to_template(x)),
                            ft.VerticalDivider(width=1, thickness=1, color="white10"),
                            ft.IconButton(ft.icons.DELETE_OUTLINE, icon_color="red400", tooltip="Delete Snapshot", on_click=lambda _, x=s: self._delete_snapshot(x)),
                        ], alignment="end")
                    ]),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    padding=10,
                    border_radius=15,
                    border=ft.border.all(1, "white10"),
                    on_hover=lambda e: self._on_card_hover(e)
                )
            )
        self.main_page.update()

    def _on_card_hover(self, e):
        e.control.bgcolor = "white10" if e.data == "true" else ft.colors.SURFACE_VARIANT
        e.control.update()

    def _edit_description(self, s):
        desc_input = ft.TextField(
            label="Edit Description", 
            value=s.get('description', ''),
            multiline=True,
            max_lines=3,
            border_radius=10
        )

        async def save_edit(e):
            new_desc = desc_input.value.strip()
            if self.manager.update_description(s['filename'], new_desc):
                self.main_page.close(dlg)
                await self.initialize_data()
                self.main_page.open(ft.SnackBar(content=ft.Text("Description updated!"), bgcolor="green700"))
            else:
                self.main_page.open(ft.SnackBar(content=ft.Text("Failed to update description."), bgcolor="red700"))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Edit Info: {s['guild_name']}"),
            content=ft.Container(content=desc_input, width=400),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.main_page.close(dlg)),
                ft.ElevatedButton("Save Changes", on_click=save_edit, bgcolor="blue700", color="white")
            ]
        )
        self.main_page.open(dlg)


    def _open_folder(self, e):
        import subprocess
        import platform
        path = os.path.abspath("snapshots")
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _view_details(self, snapshot):
        filepath = os.path.join("snapshots", snapshot['filename'])
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            roles = data["data"]["roles"]
            channels = data["data"]["channels"]
            role_names = ", ".join([r['name'] for r in roles[:15]]) + ("..." if len(roles) > 15 else "")
            channel_names = ", ".join([c['name'] for c in channels[:15]]) + ("..." if len(channels) > 15 else "")

            dlg = ft.AlertDialog(
                title=ft.Text(f"Details: {snapshot['guild_name']}"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Snapshot Metadata", size=16, weight="bold"),
                        ft.Text(f"File: {snapshot['filename']}", size=12, color="grey400"),
                        ft.Text(f"Captured: {snapshot['captured_at']}", size=12, color="grey400"),
                        ft.Divider(),
                        ft.Text(f"Roles ({len(roles)})", size=14, weight="bold", color="amber"),
                        ft.Text(role_names, size=13),
                        ft.Container(height=10),
                        ft.Text(f"Channels ({len(channels)})", size=14, weight="bold", color="blue400"),
                        ft.Text(channel_names, size=13),
                    ], scroll="auto", tight=True, spacing=10),
                    width=500
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda _: self.main_page.close(dlg))
                ]
            )
            self.main_page.open(dlg)
        except Exception as ex:
            self.main_page.open(ft.SnackBar(content=ft.Text(f"Error loading details: {str(ex)}")))

    def _open_create_dlg(self, e):
        async def prepare_and_open():
            all_guilds = self.main_page.session.get("all_guilds")
            if not all_guilds:
                self.main_page.open(ft.SnackBar(content=ft.Text("Refreshing server list...")))
                all_guilds = await self.initialize_guilds()
            
            if not all_guilds:
                self.main_page.open(ft.SnackBar(content=ft.Text("Failed to load servers. Check your connection."), bgcolor="red700"))
                return

            list_container = ft.Column(scroll="auto", height=300, spacing=5)
            desc_field = ft.TextField(label="Snapshot Description", hint_text="e.g. Clean structure for community server", border_radius=10, multiline=True, max_lines=2)

            def capture(guild):
                description = desc_field.value.strip()
                self.main_page.close(dlg)
                self.main_page.run_task(self._do_capture, guild, description)

            def update_list(search_term=""):
                list_container.controls.clear()
                term = search_term.lower()
                for g in all_guilds:
                    if term in g['name'].lower() or term in g['id']:
                        icon_url = f"https://cdn.discordapp.com/icons/{g['id']}/{g['icon']}.png" if g['icon'] else ""
                        list_container.controls.append(
                            ft.ListTile(
                                leading=ft.Image(src=icon_url, width=32, height=32, border_radius=16) if icon_url else ft.Icon(ft.icons.GROUP),
                                title=ft.Text(g['name']),
                                subtitle=ft.Text(f"ID: {g['id']}"),
                                on_click=lambda _, guild=g: capture(guild)
                            )
                        )
                self.main_page.update()

            search_field = ft.TextField(hint_text="Search servers...", prefix_icon=ft.icons.SEARCH, border_radius=10, on_change=lambda e: update_list(e.control.value))
            update_list() 
            dlg = ft.AlertDialog(
                title=ft.Text("Capture Server Snapshot"),
                content=ft.Container(content=ft.Column([search_field, list_container, ft.Divider(), desc_field], tight=True), width=450),
                actions=[ft.TextButton("Cancel", on_click=lambda _: self.main_page.close(dlg))]
            )
            self.main_page.open(dlg)

        self.main_page.run_task(prepare_and_open)

    async def _do_capture(self, guild, description=""):
        token = self.main_page.session.get("discord_token")
        self.main_page.open(ft.SnackBar(content=ft.Text(f"Capturing {guild['name']}...")))
        try:
            snapshot_data = await self.manager.capture_server(guild['id'], token, description=description)
            self.manager.save_snapshot(snapshot_data)
            await self.initialize_data()
            self.main_page.open(ft.SnackBar(content=ft.Text(f"Snapshot saved successfully!"), bgcolor="green700"))
        except Exception as e:
            self.main_page.open(ft.SnackBar(content=ft.Text(f"Capture failed: {str(e)}"), bgcolor="red700"))

    def _restore_snapshot(self, snapshot_info):
        print(f"Opening restore dialog for {snapshot_info['filename']}...")
        async def prepare_and_open():
            all_guilds = self.main_page.session.get("all_guilds")
            if not all_guilds:
                self.main_page.open(ft.SnackBar(content=ft.Text("Refreshing server list...")))
                all_guilds = await self.initialize_guilds()
            
            if not all_guilds:
                self.main_page.open(ft.SnackBar(content=ft.Text("No destination servers found."), bgcolor="red700"))
                return

            opt_roles = ft.Switch(label="Restore Roles", value=True)
            opt_categories = ft.Switch(label="Restore Categories", value=True)
            opt_text = ft.Switch(label="Restore Text Channels", value=True)
            opt_voice = ft.Switch(label="Restore Voice Channels", value=True)
            opt_clear_all = ft.Switch(label="Wipe Destination First", value=True)
            
            list_container = ft.Column(scroll="auto", height=300, spacing=5)

            async def run_restore(dest_guild):
                print(f"Starting restoration to {dest_guild['name']}...")
                self.main_page.close(dlg)
                
                filepath = os.path.join("snapshots", snapshot_info['filename'])
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        snapshot_data = json.load(f)
                    
                    options = {
                        "clone_roles": opt_roles.value,
                        "clone_categories": opt_categories.value,
                        "clone_text_channels": opt_text.value,
                        "clone_voice_channels": opt_voice.value,
                        "clear_roles": opt_clear_all.value,
                        "clear_categories": opt_clear_all.value,
                        "clear_channels": opt_clear_all.value
                    }
                    
                    self.status_text.value = f"Restoring to {dest_guild['name']}..."
                    self.progress_bar.value = 0
                    self.progress_bar.visible = True
                    self.main_page.update()
                    
                    token = self.main_page.session.get("discord_token")
                    self.restorer.set_progress_callback(self.update_progress)
                    
                    success = await self.restorer.restore_snapshot(snapshot_data, dest_guild['id'], token, options)
                    if success:
                        self.main_page.open(ft.SnackBar(content=ft.Text("Restoration Successful!"), bgcolor="green700"))
                    else:
                        self.main_page.open(ft.SnackBar(content=ft.Text("Restoration Failed. Check Debug logs."), bgcolor="red700"))
                except Exception as e:
                    print(f"Restore error: {e}")
                    self.main_page.open(ft.SnackBar(content=ft.Text(f"Error: {str(e)}"), bgcolor="red700"))
                finally:
                    # Keep completion status for a moment then hide
                    await asyncio.sleep(3)
                    self.progress_bar.visible = False
                    self.status_text.value = ""
                    self.main_page.update()

            for g in all_guilds:
                list_container.controls.append(
                    ft.ListTile(
                        title=ft.Text(g['name']),
                        subtitle=ft.Text(f"ID: {g['id']}"),
                        on_click=lambda _, guild=g: self.main_page.run_task(run_restore, guild)
                    )
                )

            dlg = ft.AlertDialog(
                title=ft.Text(f"Restore Snapshot to Server"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Options", weight="bold"),
                        ft.Row([opt_roles, opt_categories], wrap=True),
                        ft.Row([opt_text, opt_voice], wrap=True),
                        opt_clear_all,
                        ft.Divider(),
                        ft.Text("Select Destination Server", weight="bold"),
                        list_container
                    ], tight=True),
                    width=500
                ),
                actions=[ft.TextButton("Cancel", on_click=lambda _: self.main_page.close(dlg))]
            )
            self.main_page.open(dlg)

        self.main_page.run_task(prepare_and_open)

    def _export_to_template(self, snapshot):
        # Create a specific export file picker
        save_picker = ft.FilePicker(on_result=lambda e: self._handle_save_result(e, snapshot))
        self.main_page.overlay.append(save_picker)
        self.main_page.update()
        
        suggested_name = f"TEMPLATE_{snapshot['filename']}"
        save_picker.save_file(
            file_name=suggested_name,
            allowed_extensions=["json"]
        )

    def _handle_save_result(self, e: ft.FilePickerResultEvent, snapshot):
        if not e.path:
            return
            
        try:
            src_path = os.path.join("snapshots", snapshot['filename'])
            shutil.copy(src_path, e.path)
            self.main_page.open(ft.SnackBar(content=ft.Text(f"Template exported to: {e.path}"), bgcolor="green700"))
        except Exception as ex:
            self.main_page.open(ft.SnackBar(content=ft.Text(f"Export failed: {str(ex)}"), bgcolor="red700"))

    def _delete_snapshot(self, snapshot):
        filepath = os.path.join("snapshots", snapshot['filename'])
        
        async def confirm_delete(e):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                self.main_page.close(delete_dlg)
                await self.initialize_data()
                self.main_page.open(ft.SnackBar(content=ft.Text("Snapshot deleted.")))
            except Exception as ex:
                self.main_page.open(ft.SnackBar(content=ft.Text(f"Delete failed: {str(ex)}"), bgcolor="red700"))

        delete_dlg = ft.AlertDialog(
            title=ft.Text("Delete Snapshot?"),
            content=ft.Text(f"Are you sure you want to delete the snapshot for '{snapshot['guild_name']}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.main_page.close(delete_dlg)),
                ft.TextButton("Delete", on_click=lambda e: self.main_page.run_task(confirm_delete, e), style=ft.ButtonStyle(color="red")),
            ]
        )
        self.main_page.open(delete_dlg)
