import flet as ft
from src.core.utils.language_manager import LanguageManager
from src.core.utils.settings_manager import SettingsManager
from src.core.utils.version import CURRENT_VERSION

class SettingsView(ft.Container):
    def __init__(self, page: ft.Page, refresh_callback=None, **kwargs):
        super().__init__(expand=True, padding=20, **kwargs)
        self.main_page = page
        self.lang = LanguageManager()
        self.settings = SettingsManager()
        self.refresh_callback = refresh_callback
        
        # Stored components for refreshing
        self.title_text = ft.Text(self.lang.get_text("settings.title"), size=30, weight="bold")
        self.theme_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("dark", "Dark"),
                ft.dropdown.Option("light", "Light"),
                ft.dropdown.Option("system", "System"),
            ],
            value=self.settings.get_setting("appearance", "theme"),
            on_change=self.change_theme,
        )
        self.lang_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(code, name) for code, name in self.lang.get_available_languages().items()],
            value=self.lang.current_language,
            on_change=self.change_language,
        )
        self.adv_switch = ft.Switch(
            label="Advanced Explorer",
            value=self.settings.get_setting("features", "advanced_explorer"),
            on_change=self.toggle_advanced,
        )

        self.content = ft.Column([
            self.title_text,
            ft.Divider(),
            
            # Appearance Section
            self._create_section("Appearance", ft.icons.PALETTE, ft.Column([ft.Text("Theme Mode"), self.theme_dropdown])),
            
            # Language Section
            self._create_section("Language", ft.icons.LANGUAGE, ft.Column([ft.Text("Select Language"), self.lang_dropdown])),
            
            # Features Section
            self._create_section("Features", ft.icons.EXTENSION, ft.Column([self.adv_switch])),
            
        ], scroll=ft.ScrollMode.AUTO)

    def update_ui(self):
        """Refresh texts for the current language"""
        self.title_text.value = self.lang.get_text("settings.title")
        self.main_page.update()

    def _create_section(self, title, icon, content):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon), ft.Text(title, size=20, weight="bold")]),
                ft.Container(content=content, padding=ft.Padding(30, 10, 0, 10)),
            ]),
            padding=10,
            border_radius=10,
            bgcolor="surfaceVariant",
        )

    def change_theme(self, e):
        theme = e.control.value
        self.main_page.theme_mode = theme
        self.settings.set_setting("appearance", "theme", theme)
        self.main_page.update()

    def change_language(self, e):
        code = e.control.value
        if self.lang.set_language(code):
            self.settings.set_setting("language", "current", code)
            if self.refresh_callback:
                self.refresh_callback()
            self.main_page.update()

    def toggle_advanced(self, e):
        self.settings.set_setting("features", "advanced_explorer", e.control.value)
        self.main_page.update()
