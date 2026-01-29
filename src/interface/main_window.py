import customtkinter as ctk
from PIL import Image
import os
import threading
import webbrowser
import requests
import io

from src.interface.components.header import Header
from src.interface.components.token_input import TokenInput
from src.interface.components.guild_input import GuildInput
from src.interface.components.status_bar import StatusBar
from src.interface.components.advanced_explorer import create_advanced_explorer_frame
from src.interface.components.settings_panel import SettingsPanel
from src.interface.utils.language_manager import LanguageManager
from src.interface.utils.settings_manager import SettingsManager
from src.interface.styles.colors import Colors
from src.interface.utils.version import CURRENT_VERSION, get_latest_version_sync, is_newer

from src.utils.assets import get_asset_path

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize the settings manager
        self.settings = SettingsManager()
        
        # Token verificato e server trovati
        self.verified_token = None
        self.debug_mode = False
        
        # Load and apply the saved theme
        saved_theme = self.settings.get_setting("appearance", "theme")
        if saved_theme:
            ctk.set_appearance_mode(saved_theme)
        else:
            ctk.set_appearance_mode("dark")  # default theme
            self.settings.set_setting("appearance", "theme", "dark")
        
        # Initialize the language manager
        self.lang = LanguageManager()
        
        # Load and apply the saved language
        saved_language = self.settings.get_setting("language", "current")
        if saved_language:
            self.lang.set_language(saved_language)
        else:
            self.lang.set_language("en-US")  # default language
            self.settings.set_setting("language", "current", "en-US")
        
        # Register the main window as an observer for language changes
        self.lang.add_observer(self.update_texts)
        
        # Theme configuration
        ctk.set_default_color_theme("blue")

        # Performance/animation flag (default: disabled for faster startup)
        anim_flag = self.settings.get_setting("features", "ui_animations")
        self.enable_animations = bool(anim_flag) if anim_flag is not None else False
        
        # Configurazione finestra con design moderno
        self.title(self.lang.get_text("app.title"))
      
        self.geometry("1200x1000")
        self.minsize(1200, 1000)
        
        # Configurazione stile moderno
        self.configure(relief="flat", bd=0)
        
        # Variabili per animazioni e transizioni
        self.animation_speed = 200
        self.hover_color = Colors.PRIMARY_HOVER
        self.accent_color = Colors.ACCENT
        
        # Icona dell'applicazione
        icon_path = get_asset_path("src/interface/assets/discord_logo.png")
        if os.path.exists(icon_path):
       
            pass
        
        # Colori personalizzati
        self.bg_color = Colors.get_color(Colors.BACKGROUND)
        self.accent_color = Colors.PRIMARY
        self.configure(fg_color=self.bg_color)
        
        # Main grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar con design moderno
        self.sidebar = ctk.CTkFrame(
            self, 
            fg_color=Colors.get_color(Colors.SURFACE), 
            width=280, 
            corner_radius=0,
            border_width=1,
            border_color=Colors.get_color(Colors.BORDER)
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)  # Mantiene la larghezza fissa
        
        # Aggiungi ombra alla sidebar
        shadow_frame = ctk.CTkFrame(
            self.sidebar,
            width=2,
            fg_color=Colors.get_color(Colors.BORDER)
        )
        shadow_frame.pack(side="right", fill="y")
        
        # Header profilo utente (nome + avatar) in alto nella sidebar
        self.profile_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            corner_radius=0
        )
        self.profile_frame.pack(fill="x", padx=10, pady=(10, 6), side="top")
        self.profile_frame.grid_propagate(False)

        self.profile_avatar_label = ctk.CTkLabel(self.profile_frame, text="", width=40, height=40)
        self.profile_avatar_label.pack(side="left")

        self.profile_texts = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        self.profile_texts.pack(side="left", padx=10)
        self.profile_name_label = ctk.CTkLabel(self.profile_texts, text="Not signed in", font=ctk.CTkFont(size=13, weight="bold"))
        self.profile_name_label.pack(anchor="w")
        self.profile_sub_label = ctk.CTkLabel(self.profile_texts, text="", font=ctk.CTkFont(size=11), text_color=Colors.get_color(Colors.TEXT_MUTED))
        self.profile_sub_label.pack(anchor="w")

        self._profile_image_ref = None  # keep CTkImage ref
        self._profile_loaded = False
        
        # Rimozione completa del contenitore dell'icona per massimizzare lo spazio
            
        # Main container con design moderno
        self.main_container = ctk.CTkFrame(self, fg_color=Colors.get_color(Colors.BACKGROUND))
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)
        
        # Frame per contenuto con padding moderno
        self.content_wrapper = ctk.CTkFrame(
            self.main_container,
            corner_radius=0,
            fg_color="transparent"
        )
        self.content_wrapper.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.content_wrapper.grid_columnconfigure(0, weight=1)
        self.content_wrapper.grid_rowconfigure(1, weight=1)
        
        # Header moderno
        self.header = Header(self.content_wrapper)
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 25))
        
        # Migliora lo stile dell'header
        if hasattr(self.header, 'configure'):
            self.header.configure(
                corner_radius=16,
                border_width=1,
                border_color=Colors.get_color(Colors.BORDER)
            )
        
        # Central frame moderno con effetti visivi migliorati
        self.main_frame = ctk.CTkFrame(
            self.content_wrapper,
            fg_color=Colors.get_color(Colors.SURFACE),
            corner_radius=20,
            border_width=1,
            border_color=Colors.get_color(Colors.BORDER)
        )
        self.main_frame.grid(row=1, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Frame interno per contenuto con padding
        self.inner_content_frame = ctk.CTkFrame(
            self.main_frame,
            corner_radius=16,
            fg_color="transparent"
        )
        self.inner_content_frame.pack(fill="both", expand=True, padx=25, pady=25)
        self.inner_content_frame.columnconfigure(0, weight=1)
        self.inner_content_frame.rowconfigure(1, weight=1)
        
        # Optional shadow background (disabled by default)
        if self.enable_animations:
            self.shadow_frame = ctk.CTkFrame(
                self.main_container,
                fg_color=Colors.get_color(Colors.BACKGROUND),
                corner_radius=15
            )
            self.shadow_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
            self.shadow_frame.lower()
        
        # Sezione configurazione ottimizzata
        config_section = ctk.CTkFrame(
            self.inner_content_frame,
            corner_radius=10,
            fg_color=Colors.get_color(Colors.SURFACE_ELEVATED),
            border_width=1,
            border_color=Colors.get_color(Colors.BORDER_LIGHT)
        )
        config_section.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        
        # Header compatto
        header_frame = ctk.CTkFrame(config_section, fg_color="transparent", height=35)
        header_frame.pack(fill="x", padx=10, pady=(10, 6))
        header_frame.pack_propagate(False)
        
        section_title = ctk.CTkLabel(
            header_frame,
            text="🔧 Configurazione",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Colors.get_color(Colors.TEXT)
        )
        section_title.pack(side="left", pady=6)
        
        # Container per input
        input_container = ctk.CTkFrame(config_section, fg_color="transparent")
        input_container.pack(fill="x", padx=10, pady=(0, 10))
        input_container.grid_columnconfigure(0, weight=1)
        
        # Input components compatti
        self.token_input = TokenInput(input_container)
        self.token_input.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        
        self.guild_input = GuildInput(input_container)
        self.guild_input.grid(row=1, column=0, sticky="ew", pady=(0, 0))
        
        # Settings Panel (initially hidden)
        self.settings_panel = SettingsPanel(
            self,
            width=350,
            height=self.winfo_height() - 40,
            on_feature_toggle=self.on_feature_toggle
        )
        self.settings_visible = False
        
        # Settings Button with emoji icon for better visibility
        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text="⚙️ " + self.lang.get_text("settings.title"),
            height=45,
            command=self.toggle_settings,
            fg_color="transparent",
            text_color=Colors.get_color(Colors.TEXT),
            hover_color=Colors.get_color(Colors.PRIMARY),
            anchor="w",
            corner_radius=8,
            border_width=1,
            border_color=Colors.get_color(Colors.BORDER),
            font=ctk.CTkFont(size=14, weight="normal")
        )
        self.settings_button.pack(fill="x", padx=10, pady=(10, 5), side="bottom")
        
        # Add hover effects
        self.add_button_hover_effects(self.settings_button)
        
        # About button in sidebar
        self.about_button = ctk.CTkButton(
            self.sidebar,
            text=self.lang.get_text("settings.info.title"),
            height=45,
            command=self.show_about,
            fg_color="transparent",
            text_color=Colors.get_color(Colors.TEXT),
            hover_color=Colors.get_color(Colors.PRIMARY),
            anchor="w",
            corner_radius=8,
            border_width=1,
            border_color=Colors.get_color(Colors.BORDER)
        )
        self.about_button.pack(fill="x", padx=10, pady=5, side="bottom")
        
        # Add hover effects
        self.add_button_hover_effects(self.about_button)
        
        # Status bar with enhanced styling
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # Add a subtle separator line above status bar
        self.status_separator = ctk.CTkFrame(
            self,
            height=1,
            fg_color=Colors.get_color(Colors.BORDER)
        )
        self.status_separator.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 34))
        
        # Show current version on status
        try:
            ver_text = f"v{CURRENT_VERSION} • " + self.lang.get_text("status.ready")
        except Exception:
            ver_text = f"v{CURRENT_VERSION} • Ready"
        self.status_bar.update_status(ver_text, "green")
        
        # Applica stili moderni
        self.apply_modern_styling()
        
        # Binding for window resizing
        self.bind("<Configure>", self._on_resize)
        
        # Apply transitions and startup animation only if enabled
        if self.enable_animations:
            self.after(50, self.add_smooth_transitions)
            self.after(100, self.startup_animation)
        else:
            # Ensure window is fully opaque and responsive immediately
            try:
                self.attributes('-alpha', 1.0)
            except Exception:
                pass
        # Background update check
        self.after(300, self._check_updates_start)
        
        # Auto-open advanced explorer if enabled
        # self.after(500, self._auto_open_advanced_explorer)
        
        # Placeholder for embedded advanced explorer frame
        self.embedded_explorer = None

        # Avvia controllo periodico per caricare il profilo quando il token è disponibile
        self.after(600, self._maybe_load_profile)
        
    def show_about(self):
        """Mostra la finestra di about"""
        about_window = ctk.CTkToplevel(self)
        about_window.title(self.lang.get_text("settings.info.title"))
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        # about_window.grab_set()  # Modal dialog
        about_window.after(10, about_window.grab_set)   # wait a few ms until window is mapped

        
        # Try to set icon
        try:
            icon_path = os.path.join("src", "interface", "assets", "discord_logo.png")
            # Non possiamo usare iconbitmap con immagini PNG, quindi non impostiamo l'icona
            pass
        except:
            pass
        
        # Center the window
        about_window.update_idletasks()
        width = about_window.winfo_width()
        height = about_window.winfo_height()
        x = (about_window.winfo_screenwidth() // 2) - (width // 2)
        y = (about_window.winfo_screenheight() // 2) - (height // 2)
        about_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Content frame
        about_frame = ctk.CTkFrame(about_window, fg_color="transparent")
        about_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # App logo/name
        about_logo_label = ctk.CTkLabel(
            about_frame, 
            text=self.lang.get_text("app.title"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        about_logo_label.pack(pady=(0, 5))
        
        # Version
        version = CURRENT_VERSION
        version_label = ctk.CTkLabel(
            about_frame, 
            text=self.lang.get_text("settings.info.version").format(version=version),
            font=ctk.CTkFont(size=12),
            text_color=Colors.get_color(Colors.TEXT_MUTED)
        )
        version_label.pack(pady=(0, 20))
        
        # Description
        description = ctk.CTkLabel(
            about_frame,
            text=self.lang.get_text("app.about_description"),
            font=ctk.CTkFont(size=12),
            justify="center",
            wraplength=350
        )
        description.pack(pady=10)
        
        # Credits
        credits = ctk.CTkLabel(
            about_frame,
            text=" 2025",
            font=ctk.CTkFont(size=12),
            text_color=Colors.get_color(Colors.TEXT_MUTED)
        )
        credits.pack(pady=(20, 0))
        
        # Close button
        close_button = ctk.CTkButton(
            about_frame,
            text="OK",
            command=about_window.destroy,
            width=100
        )
        close_button.pack(pady=20)
    
    def _check_updates_start(self):
        def worker():
            latest = get_latest_version_sync()
            if latest and is_newer(latest, CURRENT_VERSION):
                def notify():
                    try:
                        msg = None
                        try:
                            msg = self.lang.get_text("status.update_available").format(version=latest)
                        except Exception:
                            msg = f"Update available: v{latest}"
                        self.status_bar.update_status(msg + "  (Open Releases)", "orange")
                        # Make status clickable to open releases page
                        def open_releases(_event=None):
                            webbrowser.open_new("https://github.com/seregonwar/DiscordServerCloner/releases")
                        # Bind click on the status bar label if available
                        if hasattr(self.status_bar, 'status_label'):
                            self.status_bar.status_label.bind('<Button-1>', open_releases)
                            self.status_bar.status_label.configure(cursor="hand2")
                    except Exception:
                        pass
                self.after(0, notify)
        threading.Thread(target=worker, daemon=True).start()
    
    def update_texts(self):
        """Update all interface texts when the language changes"""
        # Update the window title
        self.title(self.lang.get_text("app.title"))
        
        # Update sidebar
        if hasattr(self, 'logo_label') and not isinstance(self.logo_label, ctk.CTkImage):
            self.logo_label.configure(text=self.lang.get_text("app.title"))
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.configure(text=self.lang.get_text("app.subtitle"))
        
        # Update buttons
        if hasattr(self, 'settings_button'):
            if hasattr(self.settings_button, 'cget'):
                current_text = self.settings_button.cget("text")
                if current_text:  # Only if it has text (not just icon)
                    self.settings_button.configure(text=self.lang.get_text("settings.title"))
        
        if hasattr(self, 'about_button'):
            self.about_button.configure(text=self.lang.get_text("settings.info.title"))
            
        # Update the header
        self.header.title.configure(text=self.lang.get_text("app.title"))
        self.header.subtitle.configure(text=self.lang.get_text("app.subtitle"))
        
        # Update the token input
        self.token_input.label.configure(text=self.lang.get_text("input.token.title"))
        self.token_input.entry.configure(placeholder_text=self.lang.get_text("input.token.placeholder"))
        self.token_input.help_label.configure(text=self.lang.get_text("input.token.help"))
        self.token_input.verify_button.configure(text=self.lang.get_text("input.token.verify_button"))
        
        # Update the guild input (modificato per i dropdown)
        self.guild_input.source_label.configure(text=self.lang.get_text("input.guild.source.title"))
        
        # Aggiorniamo in base al tipo di input attivo
        if hasattr(self.guild_input, 'source_manual_input') and self.guild_input.source_manual_input:
            self.guild_input.source_entry.configure(placeholder_text=self.lang.get_text("input.guild.source.placeholder"))
        else:
            placeholder = self.lang.get_text("input.guild.dropdown_placeholder")
            if self.guild_input.source_dropdown.get() == "":
                self.guild_input.source_dropdown.set(placeholder)
        
        self.guild_input.dest_label.configure(text=self.lang.get_text("input.guild.destination.title"))
        
        # Aggiorniamo in base al tipo di input attivo
        if hasattr(self.guild_input, 'dest_manual_input') and self.guild_input.dest_manual_input:
            self.guild_input.dest_entry.configure(placeholder_text=self.lang.get_text("input.guild.destination.placeholder"))
        else:
            placeholder = self.lang.get_text("input.guild.dropdown_placeholder")
            if self.guild_input.dest_dropdown.get() == "":
                self.guild_input.dest_dropdown.set(placeholder)
        
        self.guild_input.clone_button.configure(text=self.lang.get_text("input.guild.clone_button"))
        
        # Update the status bar
        self.status_bar.status_label.configure(text=self.lang.get_text("status.ready"))
        
        # Update the settings panel if it exists
        if hasattr(self, 'settings_panel') and self.settings_panel:
            self.settings_panel.update_texts()
    
    def _on_resize(self, event):
        """Handle window resize"""
        if hasattr(self, 'settings_panel'):
            new_height = self.winfo_height() - 40
            if self.enable_animations:
                self.animate_height_change(self.settings_panel, new_height)
            else:
                try:
                    self.settings_panel.configure(height=new_height)
                except Exception:
                    pass
            if self.settings_visible:
                self.settings_panel.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(0, 20), pady=20)
                
    def animate_height_change(self, widget, target_height):
        """Smoothly animate height changes"""
        try:
            current_height = widget.winfo_height()
            if abs(current_height - target_height) > 5:
                step = (target_height - current_height) / 5
                new_height = current_height + step
                widget.configure(height=int(new_height))
                self.after(10, lambda: self.animate_height_change(widget, target_height))
            else:
                widget.configure(height=target_height)
        except:
            widget.configure(height=target_height)
    
    def startup_animation(self):
        """Smooth startup animation with fade-in effect"""
        self.attributes('-alpha', 0.0)
        self.animate_fade_in(0.0, 1.0, 20)
        
    def animate_fade_in(self, current_alpha, target_alpha, steps):
        """Animate fade-in effect"""
        if current_alpha < target_alpha:
            current_alpha += (target_alpha / steps)
            if current_alpha > target_alpha:
                current_alpha = target_alpha
            self.attributes('-alpha', current_alpha)
            self.after(20, lambda: self.animate_fade_in(current_alpha, target_alpha, steps))
    
    def toggle_settings(self):
        """Toggle settings panel (animations optional)"""
        if self.settings_visible:
            if self.enable_animations:
                # Animate panel hiding
                self.animate_panel_slide(self.settings_panel, 350, 0, 15, hide_after=True)
            else:
                self.settings_panel.grid_remove()
            self.settings_visible = False
            # Restore the main column weight
            self.grid_columnconfigure(1, weight=1)
            self.grid_columnconfigure(2, weight=0)
        else:
            # Show panel
            self.settings_panel.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(0, 20), pady=20)
            self.settings_visible = True
            # Adjust the column weights
            self.grid_columnconfigure(1, weight=1)
            self.grid_columnconfigure(2, weight=0)
            if self.enable_animations:
                self.animate_panel_slide(self.settings_panel, 0, 350, 15)
            
        # Force color update
        mode = ctk.get_appearance_mode().lower()
        self.settings_panel._update_colors(mode)
        
    def animate_panel_slide(self, panel, start_width, end_width, steps, hide_after=False):
        """Animate panel sliding with smooth width transition"""
        if steps <= 0:
            panel.configure(width=end_width)
            if hide_after:
                panel.grid_remove()
            return
            
        current_width = start_width + (end_width - start_width) * (15 - steps) / 15
        panel.configure(width=int(current_width))
        self.after(20, lambda: self.animate_panel_slide(panel, start_width, end_width, steps - 1, hide_after))
        
    def add_button_hover_effects(self, button):
        """Aggiunge effetti hover migliorati ai bottoni"""
        try:
            # Ottieni colori originali
            original_fg = button.cget("fg_color")
            original_text = button.cget("text_color")
            original_border_color = button.cget("border_color")
            
            # Definisci colori hover moderni
            hover_fg = Colors.get_color(Colors.PRIMARY_HOVER)
            hover_text = Colors.get_color(Colors.TEXT_ON_PRIMARY)
            
            def on_enter(event):
                button.configure(
                    fg_color=hover_fg,
                    text_color=hover_text,
                    border_color=Colors.get_color(Colors.PRIMARY)
                )
            
            def on_leave(event):
                button.configure(
                    fg_color=original_fg,
                    text_color=original_text,
                    border_color=original_border_color
                )
            
            # Bind eventi
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
            
        except Exception as e:
            print(f"Errore nell'aggiunta degli effetti hover: {e}")
        
    def animate_status_change(self, new_text, color=None):
        """Animate status bar text changes with fade effect"""
        if hasattr(self, 'status_bar'):
            # Fade out current text
            self.fade_status_text(0.0, new_text, color, fade_out=True)
            
    def fade_status_text(self, alpha, new_text, color, fade_out=True, steps=10):
        """Create fade effect for status text"""
        if not hasattr(self, 'status_bar'):
            return
            
        if fade_out:
            if steps > 0:
                # Fade out current text
                alpha = steps / 10.0
                self.after(20, lambda: self.fade_status_text(alpha, new_text, color, True, steps - 1))
            else:
                # Switch to new text and fade in
                if hasattr(self.status_bar, 'configure'):
                    self.status_bar.configure(text=new_text)
                    if color:
                        self.status_bar.configure(text_color=color)
                self.fade_status_text(0.0, new_text, color, False, 0)
        else:
            if steps < 10:
                # Fade in new text
                alpha = steps / 10.0
                self.after(20, lambda: self.fade_status_text(alpha, new_text, color, False, steps + 1))
                
    def apply_modern_styling(self):
        """Applica stili moderni all'interfaccia"""
        try:
            # Configura stili globali
            current_mode = ctk.get_appearance_mode().lower()
            
            # Applica effetti hover moderni
            self.add_modern_hover_effects()
            
            # Configura animazioni se abilitate
            if self.enable_animations:
                self.add_smooth_transitions()
                
        except Exception as e:
            print(f"Errore nell'applicazione degli stili moderni: {e}")
    
    def add_modern_hover_effects(self):
        """Aggiunge effetti hover moderni agli elementi"""
        def apply_hover_recursive(widget):
            try:
                if hasattr(widget, 'configure'):
                    # Effetti hover per frame
                    if isinstance(widget, ctk.CTkFrame) and widget.cget("border_width") > 0:
                        original_border = widget.cget("border_color")
                        hover_border = Colors.get_color(Colors.PRIMARY)
                        
                        def on_enter(event):
                            widget.configure(border_color=hover_border)
                        
                        def on_leave(event):
                            widget.configure(border_color=original_border)
                        
                        widget.bind("<Enter>", on_enter)
                        widget.bind("<Leave>", on_leave)
                    
                    # Effetti hover per bottoni
                    elif isinstance(widget, ctk.CTkButton):
                        self.add_button_hover_effects(widget)
                
                # Applica ricorsivamente
                for child in widget.winfo_children():
                    apply_hover_recursive(child)
                    
            except Exception as e:
                print(f"Errore negli effetti hover: {e}")
        
        apply_hover_recursive(self)
    
    def add_smooth_transitions(self):
        """Aggiunge transizioni fluide a tutti gli elementi interattivi"""
        def apply_transitions_recursive(widget):
            try:
                # Applica transizioni ai widget CTk
                if hasattr(widget, 'configure'):
                    # Configura transizioni per i frame
                    if isinstance(widget, ctk.CTkFrame):
                        # Migliora l'aspetto dei frame con angoli arrotondati
                        current_radius = widget.cget("corner_radius")
                        if current_radius < 12:
                            widget.configure(corner_radius=12)
                    
                    # Transizioni per bottoni
                    elif isinstance(widget, ctk.CTkButton):
                        widget.configure(
                            corner_radius=8,
                            border_width=1,
                            border_color=Colors.get_color(Colors.BORDER)
                        )
                    
                    # Transizioni per entry/input
                    elif isinstance(widget, ctk.CTkEntry):
                        widget.configure(
                            corner_radius=8,
                            border_width=1,
                            border_color=Colors.get_color(Colors.BORDER)
                        )
                
                # Applica ricorsivamente ai widget figli
                for child in widget.winfo_children():
                    apply_transitions_recursive(child)
                    
            except Exception as e:
                print(f"Errore nell'applicazione delle transizioni: {e}")
        
        apply_transitions_recursive(self)

    def _maybe_load_profile(self):
        """Se il token è stato verificato e il profilo non è ancora caricato, avvia il fetch."""
        try:
            if self.verified_token and not self._profile_loaded:
                threading.Thread(target=self._load_user_profile_thread, daemon=True).start()
        finally:
            # ricontrolla periodicamente, così se l'utente verifica il token dopo
            self.after(1000, self._maybe_load_profile)

    def _load_user_profile_thread(self):
        """Carica i dati utente Discord e aggiorna la UI (thread secondario)."""
        token = self.verified_token
        if not token:
            return
        headers = {"Authorization": token, "Content-Type": "application/json"}
        user_api = "https://discord.com/api/v10/users/@me"
        user = None
        try:
            resp = requests.get(user_api, headers=headers, timeout=8)
            if resp.status_code == 200:
                user = resp.json()
            else:
                user = None
        except Exception:
            user = None

        def finish():
            if not user:
                return
            # Ricava nome visualizzato e avatar URL
            username = user.get("global_name") or user.get("username") or "User"
            user_id = user.get("id")
            avatar = user.get("avatar")
            avatar_url = None
            if user_id and avatar:
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png?size=64"

            photo = None
            if avatar_url:
                try:
                    img_resp = requests.get(avatar_url, timeout=6)
                    if img_resp.status_code == 200:
                        img = Image.open(io.BytesIO(img_resp.content)).convert("RGBA")
                        # Usa CTkImage per HiDPI
                        photo = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
                except Exception:
                    photo = None

            # Aggiorna UI
            try:
                self.profile_name_label.configure(text=username)
                # sotto-etichetta opzionale: @username
                tag = user.get("username")
                if tag:
                    self.profile_sub_label.configure(text=f"@{tag}")
                if photo:
                    self._profile_image_ref = photo
                    self.profile_avatar_label.configure(image=photo, text="")
                else:
                    self.profile_avatar_label.configure(text="🙂", image=None)
                self._profile_loaded = True
            except Exception:
                pass

        self.after(0, finish)
    
    def on_feature_toggle(self, feature_name, enabled):
        """Handle feature toggle changes from settings panel"""
        if feature_name == "advanced_explorer":
            # Update the guild input component to show/hide advanced explorer button
            if hasattr(self, 'guild_input'):
                self.guild_input.update_advanced_explorer_visibility(enabled)
            
            # Update status to inform user using proper translation key format
            status_key = "status.advanced_mode_enabled" if enabled else "status.advanced_mode_disabled"
            status_text = self.lang.get_text(status_key)
            if hasattr(self, 'status_bar'):
                self.status_bar.update_status(status_text, "green" if enabled else "orange")
    
    def show_advanced_explorer(self, guild_obj, is_source: bool, on_select):
        """Replace main content with the embedded Advanced Explorer."""
        try:
            # Ensure container exists
            if not hasattr(self, 'main_container'):
                raise RuntimeError("Main container not initialized")

            # Hide main content
            if hasattr(self, 'header') and self.header.winfo_ismapped():
                self.header.grid_remove()
            if hasattr(self, 'main_frame') and self.main_frame.winfo_ismapped():
                self.main_frame.grid_remove()

            # Clean up previous explorer
            if hasattr(self, 'embedded_explorer') and self.embedded_explorer is not None:
                try:
                    self.embedded_explorer.destroy()
                except Exception:
                    pass
                self.embedded_explorer = None

            def on_close():
                self.restore_main_view()

            def wrapped_select(display_name: str):
                try:
                    on_select(display_name)
                finally:
                    self.restore_main_view()

            # Create embedded explorer
            self.embedded_explorer = create_advanced_explorer_frame(
                self.main_container,
                self.lang,
                guild_obj,
                is_source,
                wrapped_select,
                on_close
            )
            # Place it in the same grid row as main content was
            self.embedded_explorer.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

            # Status
            if hasattr(self, 'status_bar'):
                try:
                    self.status_bar.update_status(self.lang.get_text("status.advanced_mode_enabled"), "blue")
                except Exception:
                    self.status_bar.update_status("Advanced Explorer", "blue")
        except Exception as e:
            if hasattr(self, 'status_bar'):
                self.status_bar.update_status(str(e), "red")

    def restore_main_view(self):
        """Restore the default main UI and remove the embedded explorer if present."""
        try:
            if hasattr(self, 'embedded_explorer') and self.embedded_explorer is not None:
                try:
                    self.embedded_explorer.destroy()
                except Exception:
                    pass
                self.embedded_explorer = None

            if hasattr(self, 'header') and not self.header.winfo_ismapped():
                self.header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
            if hasattr(self, 'main_frame') and not self.main_frame.winfo_ismapped():
                self.main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

            if hasattr(self, 'status_bar'):
                try:
                    self.status_bar.update_status(self.lang.get_text("status.ready"), "green")
                except Exception:
                    self.status_bar.update_status("Ready", "green")
        except Exception:
            pass

    def _auto_open_advanced_explorer(self):
        """Auto-open advanced explorer if enabled in settings."""
        try:
            adv_enabled = self.settings.get_setting("features", "advanced_explorer")
            if adv_enabled and hasattr(self, 'guild_input'):
                # Open the guild selector for source; embedded explorer can be launched from there
                self.guild_input.open_guild_selector(is_source=True)
                if hasattr(self, 'status_bar'):
                    try:
                        self.status_bar.update_status(self.lang.get_text("status.advanced_mode_auto_opened"), "blue")
                    except Exception:
                        self.status_bar.update_status("Advanced Explorer auto-opened", "blue")
        except Exception as e:
            print(f"Error auto-opening advanced explorer: {e}")
