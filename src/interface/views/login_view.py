import flet as ft
import aiohttp
from src.core.utils.language_manager import LanguageManager

class LoginView(ft.Container):
    def __init__(self, page: ft.Page, on_login_success, **kwargs):
        super().__init__(expand=True, **kwargs)
        self.main_page = page
        self.on_login_success = on_login_success
        self.lang = LanguageManager()
        
        self.token_input = ft.TextField(
            label="Discord Token",
            hint_text="Paste your user token here...",
            password=True,
            can_reveal_password=True,
            width=400,
            on_submit=self.verify_token
        )
        
        self.error_text = ft.Text("", color="red")
        self.loading_indicator = ft.ProgressBar(width=400, visible=False)
        
        self.content = ft.Column([
            ft.Container(height=50),
            ft.Icon(ft.icons.SECURITY_ROUNDED, size=100, color=ft.colors.BLUE_400),
            ft.Text("Discord Server Manager", size=32, weight="bold"),
            ft.Text("Please verify your token to continue", color="grey500"),
            ft.Container(height=20),
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        self.token_input,
                        self.loading_indicator,
                        self.error_text,
                        ft.ElevatedButton(
                            "Verify & Login",
                            icon=ft.icons.LOGIN,
                            width=400,
                            height=50,
                            on_click=self.verify_token
                        ),
                    ], horizontal_alignment="center", spacing=20),
                    padding=30
                )
            ),
            ft.TextButton("Where do I find my token?", on_click=lambda _: self.main_page.launch_url("https://github.com/Aadiwrth/Discord-Server-Manger/wiki/How-to-get-token")),
        ], horizontal_alignment="center", alignment="center")

    async def verify_token(self, e):
        token = self.token_input.value.strip()
        if not token:
            self.error_text.value = "Token cannot be empty"
            self.main_page.update()
            return
            
        self.loading_indicator.visible = True
        self.error_text.value = ""
        self.main_page.update()
        
        async with aiohttp.ClientSession(headers={"Authorization": token}) as session:
            try:
                async with session.get("https://discord.com/api/v10/users/@me") as resp:
                    if resp.status == 200:
                        user_data = await resp.json()
                        self.main_page.session.set("discord_token", token)
                        self.main_page.session.set("user_data", user_data)
                        if self.on_login_success:
                            await self.on_login_success(user_data)
                    else:
                        self.error_text.value = f"Invalid Token (HTTP {resp.status})"
            except Exception as ex:
                self.error_text.value = f"Connection error: {str(ex)}"
        
        self.loading_indicator.visible = False
        self.main_page.update()
