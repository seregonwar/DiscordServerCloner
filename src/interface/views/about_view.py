import flet as ft
from src.core.utils.version import CURRENT_VERSION

class AboutView(ft.Container):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(expand=True, padding=20, **kwargs)
        self.main_page = page
        
        self.content = ft.Column([
            # App Header
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.INFO_ROUNDED, size=80, color=ft.colors.BLUE_400),
                    ft.Text("Discord Server Manager", size=32, weight="bold"),
                    ft.Text(f"Version {CURRENT_VERSION}", color="grey500"),
                ], horizontal_alignment="center"),
                width=float("inf"),
                padding=20,
            ),
            
            ft.Divider(),
            
            ft.Text("Project Contributors", size=24, weight="bold"),
            ft.Text("The amazing people behind this project who made it possible.", color="grey400"),
            
            ft.ResponsiveRow([
                # Aadiwrth Card
                ft.Column([
                    self._create_contributor_card(
                        name="Aadiwrth",
                        role="Developer & UI Designer",
                        github="https://github.com/Aadiwrth",
                        avatar_url="https://github.com/Aadiwrth.png",
                        support_links=[
                            ("Ko-fi", "favorite", "https://ko-fi.com/wokuu", "pink"),
                            ("Patreon", "stars", "https://patreon.com/woku", "orange"),
                            ("PayPal", "payment", "https://paypal.me/deepu468", "blue"),
                            ("GitHub", "code", "https://github.com/Aadiwrth", "grey"),
                        ]
                    )
                ], col={"sm": 12, "md": 6}),
                
                # Seregonwar Card
                ft.Column([
                    self._create_contributor_card(
                        name="Seregonwar",
                        role="Core Developer",
                        github="https://github.com/seregonwar",
                        avatar_url="https://github.com/seregonwar.png",
                        support_links=[
                            ("Ko-fi", "favorite", "https://ko-fi.com/seregon", "pink"),
                            ("PayPal", "payment", "https://www.paypal.com/paypalme/seregonwar", "blue"),
                            ("GitHub", "code", "https://github.com/seregonwar/DiscordServerCloner", "grey"),
                        ]
                    )
                ], col={"sm": 12, "md": 6}),
            ], spacing=20),
            
            ft.Container(height=20),
            
            # Legal/Disclaimer Card
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Disclaimer", weight="bold", color="red400"),
                        ft.Text(
                            "This tool is provided for educational purposes only. The authors are not responsible for any misuse "
                            "of the software. Use of self-bots or automated scripts may violate Discord's Terms of Service.",
                            size=12, color="grey400"
                        )
                    ]),
                    padding=15
                ),
                color="surfaceVariant"
            )
            
        ], scroll="auto", spacing=20)

    def _create_contributor_card(self, name, role, github, avatar_url, support_links):
        buttons = []
        for label, icon, url, color in support_links:
            buttons.append(
                ft.ElevatedButton(
                    label,
                    icon=icon,
                    on_click=lambda _, u=url: self.main_page.launch_url(u),
                    bgcolor=color,
                    color="white",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            )

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Container(
                            content=ft.Image(src=avatar_url, width=40, height=40, fit="cover"),
                            width=40, height=40, border_radius=20, clip_behavior="antiAlias"
                        ),
                        title=ft.Text(name, weight="bold", size=18),
                        subtitle=ft.Text(role, color="grey400"),
                        on_click=lambda _: self.main_page.launch_url(github),
                        tooltip="View GitHub Profile"
                    ),
                    ft.Divider(height=1, thickness=1),
                    ft.Text("Support the contributor:", size=12, weight="bold", color="grey500"),
                    ft.Row(buttons, wrap=True, spacing=10),
                ], spacing=10),
                padding=20
            )
        )
