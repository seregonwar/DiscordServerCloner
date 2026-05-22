import flet as ft
import asyncio
import aiohttp
import os
from src.core.utils.language_manager import LanguageManager
from src.core.utils.settings_manager import SettingsManager
from src.interface.views.cloning_view import CloningView
from src.interface.views.settings_view import SettingsView
from src.interface.views.debug_view import DebugView
from src.interface.views.explorer_view import ExplorerView
from src.interface.views.about_view import AboutView
from src.interface.views.dashboard_view import DashboardView
from src.interface.views.snapshot_view import SnapshotView
from src.interface.views.templates_view import TemplatesView
from src.interface.views.analytics_view import AnalyticsView
from src.interface.views.login_view import LoginView

async def main(page: ft.Page):
    page.title = "Discord Server Manager"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1300
    page.window_height = 950
    page.window_min_width = 1100
    page.window_min_height = 800
    
    lang = LanguageManager()
    settings = SettingsManager()
    
    # Theme configuration
    page.theme = ft.Theme(
        color_scheme_seed="#5865F2",
    )

    # Global State
    is_logged_in = False
    
    # Profile UI Components
    profile_avatar_img = ft.Image(
        src=None,
        width=40,
        height=40,
        fit=ft.ImageFit.COVER,
        visible=False
    )
    profile_avatar_icon = ft.Icon(ft.icons.PERSON, size=24, visible=True)
    
    profile_avatar = ft.Container(
        content=ft.Stack([
            profile_avatar_icon,
            profile_avatar_img
        ], alignment=ft.alignment.center),
        width=40,
        height=40,
        border_radius=20,
        bgcolor=ft.colors.GREY_800,
        clip_behavior=ft.ClipBehavior.HARD_EDGE
    )
    
    profile_name = ft.Text("Not signed in", weight="bold")
    profile_tag = ft.Text("", size=11, color="grey400")

    def update_profile_ui(user_data):
        try:
            username = user_data.get("username", "Unknown User")
            global_name = user_data.get("global_name")
            
            profile_name.value = global_name or username
            profile_tag.value = f"@{username}"
            
            avatar_hash = user_data.get("avatar")
            user_id = user_data.get("id")
            
            if avatar_hash and user_id:
                # Use .gif for animated (a_ prefix) and .webp for static for best quality
                is_animated = avatar_hash.startswith("a_")
                ext = "gif" if is_animated else "webp"
                url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ext}?size=128"
                
                profile_avatar_img.src = url
                profile_avatar_img.visible = True
                profile_avatar_icon.visible = False
                debug_view.log(f"Loading {'animated ' if is_animated else ''}avatar: {url}", "DEBUG")
            else:
                profile_avatar_img.visible = False
                profile_avatar_icon.visible = True
                
            page.update()
        except Exception as e:
            print(f"Error updating profile UI: {e}")
            if debug_view:
                debug_view.log(f"Profile UI Error: {str(e)}", "ERROR")

    async def check_for_updates():
        from src.core.utils.version import fetch_latest_version, CURRENT_VERSION, is_newer
        try:
            debug_view.log("Checking for updates...", "INFO")
            latest_version = await fetch_latest_version()
            if latest_version and is_newer(latest_version, CURRENT_VERSION):
                debug_view.log(f"New version available: {latest_version}", "SUCCESS")
                
                def close_banner(e):
                    page.banner.open = False
                    page.update()

                page.banner = ft.Banner(
                    bgcolor=ft.colors.AMBER_100,
                    leading=ft.Icon(ft.icons.UPDATE_ROUNDED, color=ft.colors.AMBER_700, size=40),
                    content=ft.Text(
                        f"A new version of Discord Server Manager is available ({latest_version})! Current version is {CURRENT_VERSION}.",
                        color=ft.colors.BLACK,
                    ),
                    actions=[
                        ft.TextButton("Update Now", on_click=lambda _: page.launch_url("https://github.com/seregonwar/DiscordServerManager/releases")),
                        ft.TextButton("Ignore", on_click=close_banner),
                    ],
                )
                page.banner.open = True
                page.update()
            else:
                debug_view.log("App is up to date", "SUCCESS")
        except Exception as e:
            debug_view.log(f"Update check failed: {str(e)}", "WARNING")

    async def on_login_success(user_data):
        nonlocal is_logged_in
        try:
            is_logged_in = True
            debug_view.log(f"Login successful for {user_data.get('username')}", "SUCCESS")
            
            # 1. Show Main UI
            login_screen.visible = False
            main_layout.visible = True
            page.update()
            
            # 2. Update Profile Header
            update_profile_ui(user_data)
            
            # 3. Initialize Views sequentially for stability
            debug_view.log("Initializing Dashboard...", "INFO")
            await dashboard_view.refresh_data()
            
            debug_view.log("Initializing Cloning Engine...", "INFO")
            await cloning_view.initialize_data()
            
            debug_view.log("Initializing Snapshot Manager...", "INFO")
            await snapshot_view.initialize_data()
            
            debug_view.log("Initializing Templates Marketplace...", "INFO")
            await templates_view.initialize_data()

            debug_view.log("Initializing Analytics Dashboard...", "INFO")
            await analytics_view.initialize_data()
            
            # 4. Share server list across views
            if hasattr(cloning_view, 'all_guilds') and cloning_view.all_guilds:
                page.session.set("all_guilds", cloning_view.all_guilds)
                debug_view.log(f"Session synchronized with {len(cloning_view.all_guilds)} servers", "SUCCESS")
            
            # 5. Check for updates
            page.run_task(check_for_updates)
            
            page.update()
            debug_view.log("Workspace Ready", "SUCCESS")
            
        except Exception as e:
            error_msg = f"Initialization failure: {str(e)}"
            print(error_msg)
            if debug_view:
                debug_view.log(error_msg, "ERROR")
                import traceback
                debug_view.log(traceback.format_exc(), "DEBUG")

    def refresh_all_views():
        cloning_view.update_ui()
        settings_view.update_ui()
        page.update()

    def on_nav_change(e):
        index = int(e.control.selected_index) if hasattr(e, "control") else int(e)
        rail.selected_index = index
        for i, view in enumerate(views_list):
            view.visible = (i == index)
        page.update()

    async def switch_page(index):
        on_nav_change(index)

    # Sidebar Destinations
    destinations = [
        ft.NavigationRailDestination(icon="dashboard_outlined", selected_icon="dashboard", label="Dashboard"),
        ft.NavigationRailDestination(icon="rocket_launch_outlined", selected_icon="rocket_launch", label="Cloning"),
        ft.NavigationRailDestination(icon="search_outlined", selected_icon="search", label="Explorer"),
        ft.NavigationRailDestination(icon="camera_alt_outlined", selected_icon="camera_alt", label="Snapshots"),
        ft.NavigationRailDestination(icon="dashboard_customize_outlined", selected_icon="dashboard_customize", label="Templates"),
        ft.NavigationRailDestination(icon="analytics_outlined", selected_icon="analytics", label="Analytics"),
        ft.NavigationRailDestination(icon="settings_outlined", selected_icon="settings", label="Settings"),
        ft.NavigationRailDestination(icon="bug_report_outlined", selected_icon="bug_report", label="Debug"),
        ft.NavigationRailDestination(icon="info_outline", selected_icon="info", label="About"),
    ]

    # Sidebar
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        leading=ft.Column([
            ft.Container(profile_avatar, padding=ft.padding.only(top=20)),
            profile_name,
            profile_tag,
        ], horizontal_alignment="center", spacing=0),
        destinations=destinations,
        on_change=on_nav_change,
    )

    # Views Initialization
    debug_view = DebugView(page, visible=False)
    explorer_view = ExplorerView(page, visible=False)
    dashboard_view = DashboardView(page, visible=True)
    snapshot_view = SnapshotView(page, log_callback=debug_view.log, visible=False)
    templates_view = TemplatesView(page, nav_callback=switch_page, log_callback=debug_view.log, visible=False)
    analytics_view = AnalyticsView(page, visible=False)
    about_view = AboutView(page, visible=False)
    
    async def show_explorer(guild):
        await switch_page(2)
        await explorer_view.load_guild(guild)

    cloning_view = CloningView(page, log_callback=debug_view.log, explorer_callback=show_explorer, visible=False)
    settings_view = SettingsView(page, refresh_callback=refresh_all_views, visible=False)

    views_list = [
        dashboard_view,
        cloning_view,
        explorer_view,
        snapshot_view,
        templates_view,
        analytics_view,
        settings_view,
        debug_view,
        about_view
    ]

    # Main Layout
    main_layout = ft.Row([
        rail,
        ft.VerticalDivider(width=1),
        ft.Column(views_list, expand=True),
    ], expand=True, visible=False)

    # Login Screen
    login_screen = LoginView(page, on_login_success=on_login_success)

    page.add(
        login_screen,
        main_layout
    )

if __name__ == "__main__":
    ft.app(target=main)
