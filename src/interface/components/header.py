import customtkinter as ctk
from PIL import Image
import os
from src.interface.utils.language_manager import LanguageManager
from src.utils.assets import get_asset_path

class Header(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Get the language manager
        self.lang = LanguageManager()
        
        # Discord Logo
        try:
            image_path = get_asset_path("src/interface/assets/discord_logo.png")
            self.logo = ctk.CTkImage(
                light_image=Image.open(image_path),
                dark_image=Image.open(image_path),
                size=(50, 50)
            )
            
            self.logo_label = ctk.CTkLabel(
                self,
                image=self.logo,
                text=""
            )
            self.logo_label.pack(pady=10)
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        self.title = ctk.CTkLabel(
            self,
            text=self.lang.get_text("app.title"),
            font=ctk.CTkFont(size=32, weight="bold"),
        )
        self.title.pack()
        
        self.subtitle = ctk.CTkLabel(
            self,
            text=self.lang.get_text("app.subtitle"),
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        self.subtitle.pack(pady=5)