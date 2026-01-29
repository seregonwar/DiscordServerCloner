import customtkinter as ctk
import discord
import asyncio
import time
import sys
import os
import aiohttp
import webbrowser
import tkinter as tk
import threading
from tkinter import simpledialog, messagebox
import re
from PIL import Image, ImageTk

# Import Colors directly
from src.interface.styles.colors import Colors
from src.operation_file.serverclone import Clone
from src.interface.utils.language_manager import LanguageManager
from src.interface.utils.settings_manager import SettingsManager


# Define a custom exception for request errors
class RequestsError(Exception):
    """Custom exception for Discord API request errors"""
    pass

class GuildInput(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Get language manager
        self.lang = LanguageManager()
        self.settings = SettingsManager()
        
        # Initialize advanced explorer setting cache
        adv_flag = self.settings.get_setting("features", "advanced_explorer")
        self._advanced_explorer_enabled = True if adv_flag is None else bool(adv_flag)
        
                # Main frame
        self.main_frame = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent",
            height=430
        )
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=(1, 0))  

        # Source Guild Frame
        self.source_label = ctk.CTkLabel(
            self.main_frame,
            text=self.lang.get_text("input.guild.source.title"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.source_label.pack(anchor="w", pady=(10, 5))
        
        # Source dropdown e input frame
        self.source_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.source_frame.pack(fill="x", pady=(0, 10))
        
        # Selettore sorgente: pulsante che apre la ricerca
        self.source_select_btn = ctk.CTkButton(
            self.source_frame,
            text=self.lang.get_text("input.guild.dropdown_placeholder"),
            height=40,
            command=lambda: self.open_guild_selector(is_source=True),
            fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.TEXT, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.SETTINGS_BG, ctk.get_appearance_mode().lower())
        )
        self.source_select_btn.pack(side="left", fill="x", expand=True)
        
        # Entry per inserimento manuale ID source, inizialmente nascosto
        self.source_entry = ctk.CTkEntry(
            self.source_frame,
            placeholder_text=self.lang.get_text("input.guild.source.placeholder"),
            height=40,
            text_color=Colors.get_color(Colors.TEXT),
            fg_color=Colors.get_color(Colors.INPUT_BG)
        )
        # Non pacchettizziamo ancora, sarà mostrato quando necessario
        
        # Pulsante per passare da dropdown a input manuale
        self.source_toggle = ctk.CTkButton(
            self.source_frame,
            text="⌨️",
            width=40,
            command=self.toggle_source_input,
            fg_color=Colors.get_color(Colors.TEXT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.BACKGROUND, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.TEXT_MUTED, ctk.get_appearance_mode().lower())
        )
        self.source_toggle.pack(side="left", padx=(10, 0))
        
        # Destination Guild Frame
        self.dest_label = ctk.CTkLabel(
            self.main_frame,
            text=self.lang.get_text("input.guild.destination.title"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.dest_label.pack(anchor="w", pady=(10, 5))
        
        # Destination dropdown e input frame
        self.dest_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.dest_frame.pack(fill="x", pady=(0, 20))
        
        # Selettore destinazione: pulsante che apre la ricerca
        self.dest_select_btn = ctk.CTkButton(
            self.dest_frame,
            text=self.lang.get_text("input.guild.dropdown_placeholder"),
            height=40,
            command=lambda: self.open_guild_selector(is_source=False),
            fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.TEXT, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.SETTINGS_BG, ctk.get_appearance_mode().lower())
        )
        self.dest_select_btn.pack(side="left", fill="x", expand=True)
        
        # Entry per inserimento manuale ID destination, inizialmente nascosto
        self.dest_entry = ctk.CTkEntry(
            self.dest_frame,
            placeholder_text=self.lang.get_text("input.guild.destination.placeholder"),
            height=40,
            text_color=Colors.get_color(Colors.TEXT),
            fg_color=Colors.get_color(Colors.INPUT_BG)
        )
        # Non pacchettizziamo ancora, sarà mostrato quando necessario
        
        # Pulsante per creare un nuovo server
        self.create_server_button = ctk.CTkButton(
            self.dest_frame,
            text="➕",
            width=40,
            command=self.create_new_server,
            fg_color=Colors.get_color(Colors.SUCCESS, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.BACKGROUND, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.SUCCESS_DARK, ctk.get_appearance_mode().lower())
        )
        self.create_server_button.pack(side="left", padx=(10, 0))
        
        # Pulsante per passare da dropdown a input manuale
        self.dest_toggle = ctk.CTkButton(
            self.dest_frame,
            text="⌨️",
            width=40,
            command=self.toggle_dest_input,
            fg_color=Colors.get_color(Colors.TEXT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.BACKGROUND, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.TEXT_MUTED, ctk.get_appearance_mode().lower())
        )
        self.dest_toggle.pack(side="left", padx=(10, 0))
        
        # Selezioni correnti e flag input
        self.selected_source_display = None
        self.selected_dest_display = None
        # Flag per tenere traccia dell'input attivo
        self.source_manual_input = False
        self.dest_manual_input = False
        
        # Memorizziamo i server recuperati
        self.guilds_dict = {}  # Dizionario id -> details
        self.guild_display_names = []  # Lista dei nomi visualizzati (name (id))
        
        # Controlli avanzati
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", pady=(0, 10))
        
        # Pulsante per resettare i campi
        self.reset_button = ctk.CTkButton(
            self.controls_frame,
            text=self.lang.get_text("input.guild.reset_button"),
            command=self.reset_fields,
            height=30,
            width=100,
            fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.TEXT_MUTED, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.BACKGROUND, ctk.get_appearance_mode().lower()),
            border_width=1,
            border_color=Colors.get_color(Colors.TEXT_MUTED)
        )
        self.reset_button.pack(side="left", padx=(0, 10))
        
        # Spazio vuoto espandibile
        spacer = ctk.CTkFrame(self.controls_frame, fg_color="transparent", height=30)
        spacer.pack(side="left", fill="x", expand=True)
        
        # Sezione delle opzioni di clonazione
        self.options_frame = ctk.CTkFrame(self.main_frame)
        self.options_frame.pack(fill="x", pady=10)
        
        # Titolo opzioni
        self.options_title = ctk.CTkLabel(
            self.options_frame,
            text=self.lang.get_text("input.guild.options_title"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.options_title.pack(anchor="w", pady=(10, 5), padx=10)
        
        # Contenitore per le checkbox
        self.checkboxes_frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.checkboxes_frame.pack(fill="x", padx=20, pady=5)
        self.checkboxes_frame.grid_columnconfigure(0, weight=1)
        self.checkboxes_frame.grid_columnconfigure(1, weight=1)

        # Opzione Clone Name e Icon
        self.clone_name_icon_var = ctk.BooleanVar(value=True)
        self.clone_name_icon_checkbox = ctk.CTkCheckBox(
            self.checkboxes_frame,
            text=self.lang.get_text("input.guild.option_michelleneous"),  # add this key in your language files
            variable=self.clone_name_icon_var,
            onvalue=True,
            offvalue=False
        )
        self.clone_name_icon_checkbox.grid(row=3, column=0, sticky="w", pady=5)

        # Opzione ruoli
        self.clone_roles_var = ctk.BooleanVar(value=True)
        self.clone_roles_checkbox = ctk.CTkCheckBox(
            self.checkboxes_frame,
            text=self.lang.get_text("input.guild.option_roles"),
            variable=self.clone_roles_var,
            onvalue=True,
            offvalue=False
        )
        self.clone_roles_checkbox.grid(row=0, column=0, sticky="w", pady=5)
        
        # Opzione categorie
        self.clone_categories_var = ctk.BooleanVar(value=True)
        self.clone_categories_checkbox = ctk.CTkCheckBox(
            self.checkboxes_frame,
            text=self.lang.get_text("input.guild.option_categories"),
            variable=self.clone_categories_var,
            onvalue=True,
            offvalue=False
        )
        self.clone_categories_checkbox.grid(row=0, column=1, sticky="w", pady=5)
        
        # Opzione canali testuali
        self.clone_text_channels_var = ctk.BooleanVar(value=True)
        self.clone_text_channels_checkbox = ctk.CTkCheckBox(
            self.checkboxes_frame,
            text=self.lang.get_text("input.guild.option_text_channels"),
            variable=self.clone_text_channels_var,
            onvalue=True,
            offvalue=False
        )
        self.clone_text_channels_checkbox.grid(row=1, column=0, sticky="w", pady=5)
        
        # Opzione canali vocali
        self.clone_voice_channels_var = ctk.BooleanVar(value=True)
        self.clone_voice_channels_checkbox = ctk.CTkCheckBox(
            self.checkboxes_frame,
            text=self.lang.get_text("input.guild.option_voice_channels"),
            variable=self.clone_voice_channels_var,
            onvalue=True,
            offvalue=False
        )
        self.clone_voice_channels_checkbox.grid(row=1, column=1, sticky="w", pady=5)
        
        # Opzione messaggi
        self.clone_messages_var = ctk.BooleanVar(value=True)
        self.clone_messages_checkbox = ctk.CTkCheckBox(
            self.checkboxes_frame,
            text=self.lang.get_text("input.guild.option_messages"),
            variable=self.clone_messages_var,
            onvalue=True,
            offvalue=False,
            command=self.toggle_messages_options
        )
        self.clone_messages_checkbox.grid(row=2, column=0, sticky="w", pady=5)
        
        # Opzione numero massimo di messaggi
        self.messages_limit_frame = ctk.CTkFrame(self.checkboxes_frame, fg_color="transparent")
        self.messages_limit_frame.grid(row=2, column=1, sticky="w", pady=5)
        
        self.messages_limit_label = ctk.CTkLabel(
            self.messages_limit_frame,
            text=self.lang.get_text("input.guild.option_messages_limit")
        )
        self.messages_limit_label.pack(side="left", padx=(0, 5))
        
        self.messages_limit_var = ctk.StringVar(value="100")
        self.messages_limit_entry = ctk.CTkEntry(
            self.messages_limit_frame,
            width=60,
            textvariable=self.messages_limit_var
        )
        self.messages_limit_entry.pack(side="left")
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self.main_frame)
        self.progress.set(0)
        
        # Info panel (inizialmente nascosto)
        self.info_panel = ctk.CTkFrame(self.main_frame)
        self.info_panel.configure(fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT))
        
        # Creiamo le etichette per le statistiche
        self.stats_title = ctk.CTkLabel(
            self.info_panel,
            text=self.lang.get_text("input.guild.stats_title"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.stats_title.pack(anchor="w", pady=(10, 5))
        
        # Contenitore per le statistiche
        self.stats_container = ctk.CTkFrame(self.info_panel, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=10, pady=5)
        self.stats_container.grid_columnconfigure(1, weight=1)
        
        # Statistiche: ruoli
        self.roles_label = ctk.CTkLabel(
            self.stats_container, 
            text=self.lang.get_text("input.guild.stats_roles")
        )
        self.roles_label.grid(row=0, column=0, sticky="w", pady=2)
        
        self.roles_value = ctk.CTkLabel(
            self.stats_container,
            text="0/0"
        )
        self.roles_value.grid(row=0, column=1, sticky="e", pady=2)
        
        # Statistiche: canali
        self.channels_label = ctk.CTkLabel(
            self.stats_container, 
            text=self.lang.get_text("input.guild.stats_channels")
        )
        self.channels_label.grid(row=1, column=0, sticky="w", pady=2)
        
        self.channels_value = ctk.CTkLabel(
            self.stats_container,
            text="0/0"
        )
        self.channels_value.grid(row=1, column=1, sticky="e", pady=2)
        
        # Statistiche: messaggi
        self.messages_label = ctk.CTkLabel(
            self.stats_container, 
            text=self.lang.get_text("input.guild.stats_messages")
        )
        self.messages_label.grid(row=2, column=0, sticky="w", pady=2)
        
        self.messages_value = ctk.CTkLabel(
            self.stats_container,
            text="0"
        )
        self.messages_value.grid(row=2, column=1, sticky="e", pady=2)
        
        # Statistiche: errori
        self.errors_label = ctk.CTkLabel(
            self.stats_container, 
            text=self.lang.get_text("input.guild.stats_errors"),
            text_color="red"
        )
        self.errors_label.grid(row=3, column=0, sticky="w", pady=2)
        
        self.errors_value = ctk.CTkLabel(
            self.stats_container,
            text="0",
            text_color="red"
        )
        self.errors_value.grid(row=3, column=1, sticky="e", pady=2)
        
        # Statistiche: tempo
        self.time_label = ctk.CTkLabel(
            self.stats_container, 
            text=self.lang.get_text("input.guild.stats_time")
        )
        self.time_label.grid(row=4, column=0, sticky="w", pady=2)
        
        self.time_value = ctk.CTkLabel(
            self.stats_container,
            text="00:00"
        )
        self.time_value.grid(row=4, column=1, sticky="e", pady=2)
        
        # Clone Button
        self.clone_button = ctk.CTkButton(
            self.main_frame,
            text=self.lang.get_text("input.guild.clone_button"),
            command=self.start_clone,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=Colors.get_color(Colors.TEXT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.BACKGROUND, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.TEXT_MUTED, ctk.get_appearance_mode().lower())
        )
        self.clone_button.pack(pady=10)

        # Cancel Button (initially hidden)
        self.cancel_button = ctk.CTkButton(
            self.main_frame,
            text="Cancel",
            command=self.cancel_clone,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=Colors.get_color(Colors.DANGER if hasattr(Colors, 'DANGER') else Colors.TEXT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.BACKGROUND, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.TEXT_MUTED, ctk.get_appearance_mode().lower())
        )
        # Do not pack yet; shown when cloning starts

        # Discord client
        self.client = None

        # Clone task threading state
        self._clone_thread = None
        self._clone_loop = None
        self._clone_task = None
        self._cancel_requested = False
        
        # Update colors when theme changes
        self._update_colors()
        self.bind('<Configure>', lambda e: self._update_colors())
        
        # Add observer for language changes
        self.lang.add_observer(self.update_texts)
        
    def _update_colors(self):
        mode = ctk.get_appearance_mode().lower()
        
        # Update button colors
        self.clone_button.configure(
            fg_color=Colors.get_color(Colors.TEXT, mode),
            text_color=Colors.get_color(Colors.BACKGROUND, mode),
            hover_color=Colors.get_color(Colors.TEXT_MUTED, mode)
        )
        
        # Update input colors
        for entry in [self.source_entry, self.dest_entry]:
            entry.configure(
                text_color=Colors.get_color(Colors.TEXT, mode),
                fg_color=Colors.get_color(Colors.INPUT_BG, mode)
            )

    def update_progress(self, value, show=True):
        """Update progress bar value and visibility (thread-safe)."""
        def _apply():
            if show and not self.progress.winfo_ismapped():
                self.progress.pack(fill="x", pady=(0, 10))
            elif not show and self.progress.winfo_ismapped():
                self.progress.pack_forget()
            self.progress.set(value)
        try:
            # Marshal to main thread
            self.after(0, _apply)
        except Exception:
            _apply()
    
    def update_advanced_explorer_visibility(self, enabled):
        """Update the visibility of advanced explorer buttons based on settings"""
        # Store the current setting for future modal creations
        self._advanced_explorer_enabled = enabled
        
        # If there are any open guild selector modals, we would need to update them
        # For now, the setting will take effect the next time a modal is opened
        # This is acceptable since the modal is typically short-lived
        
    def toggle_source_input(self):
        """Passa dall'input da dropdown all'input manuale e viceversa"""
        self.source_manual_input = not self.source_manual_input
        
        if self.source_manual_input:
            # Nascondiamo il selettore e mostriamo l'input manuale
            self.source_select_btn.pack_forget()
            self.source_entry.pack(side="left", fill="x", expand=True)
            self.source_toggle.configure(text="📋")
        else:
            # Nascondiamo l'input manuale e mostriamo il selettore
            self.source_entry.pack_forget()
            self.source_select_btn.pack(side="left", fill="x", expand=True)
            self.source_toggle.configure(text="⌨️")
            
    def toggle_dest_input(self):
        """Passa dall'input da dropdown all'input manuale e viceversa"""
        self.dest_manual_input = not self.dest_manual_input
        
        if self.dest_manual_input:
            # Nascondiamo il selettore e mostriamo l'input manuale
            self.dest_select_btn.pack_forget()
            self.dest_entry.pack(side="left", fill="x", expand=True)
            self.dest_toggle.configure(text="📋")
        else:
            # Nascondiamo l'input manuale e mostriamo il selettore
            self.dest_entry.pack_forget()
            self.dest_select_btn.pack(side="left", fill="x", expand=True)
            self.dest_toggle.configure(text="⌨️")

    def source_selected(self, option):
        """Callback quando un server sorgente viene selezionato"""
        # Se è stato selezionato un vero server (non il placeholder)
        if option in self.guilds_dict:
            self.selected_source_display = option
            self.source_select_btn.configure(text=option)
            # Aggiorniamo lo stato
            main_window = self.winfo_toplevel()
            main_window.status_bar.update_status(
                self.lang.get_text("status.source_selected").format(name=option), 
                "black"
            )
    
    def dest_selected(self, option):
        """Callback quando un server destinazione viene selezionato"""
        # Se è stato selezionato un vero server (non il placeholder)
        if option in self.guilds_dict:
            self.selected_dest_display = option
            self.dest_select_btn.configure(text=option)
            # Aggiorniamo lo stato
            main_window = self.winfo_toplevel()
            main_window.status_bar.update_status(
                self.lang.get_text("status.destination_selected").format(name=option), 
                "black"
            )
    
    def update_guilds_dropdowns(self, guilds_list):
        """Aggiorna i dropdown con l'elenco dei server disponibili"""
        if not guilds_list:
            return
            
        # Resettiamo i dizionari e le liste
        self.guilds_dict = {}
        server_names = [self.lang.get_text("input.guild.dropdown_placeholder")]
        self.guild_display_names = []
        
        # Popoliamo il dizionario e la lista dei nomi
        for guild in guilds_list:
            guild_id = str(guild['id'])
            guild_name = guild['name']
            display_name = f"{guild_name} ({guild_id})"
            
            self.guilds_dict[display_name] = guild
            server_names.append(display_name)
            self.guild_display_names.append(display_name)
        
        # Reset testo dei selettori se non è già stata fatta una scelta
        placeholder = server_names[0]
        if not self.selected_source_display:
            self.source_select_btn.configure(text=placeholder)
        if not self.selected_dest_display:
            self.dest_select_btn.configure(text=placeholder)
            
        # Aggiorniamo lo stato
        main_window = self.winfo_toplevel()
        main_window.status_bar.update_status(
            self.lang.get_text("status.guilds_loaded").format(count=len(guilds_list)), 
            "green"
        )

    def open_guild_selector(self, is_source: bool):
        """Apre una finestra con barra di ricerca per selezionare un server."""
        # Costruzione finestra modale
        top = ctk.CTkToplevel(self)
        top.title(self.lang.get_text("input.guild.search_title") if hasattr(self.lang, 'get_text') else "Seleziona Server")
        top.geometry("560x560")
        top.after(10, top.grab_set)   # wait a few ms until window is mapped

        
        mode = ctk.get_appearance_mode().lower()
        top.configure(fg_color=Colors.get_color(Colors.SETTINGS_BG, mode))
        
        # Header con titolo e pulsante chiudi
        header = ctk.CTkFrame(top, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 8))
        title_lbl = ctk.CTkLabel(
            header,
            text=self.lang.get_text("input.guild.search_title") if hasattr(self.lang, 'get_text') else "Seleziona Server",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_lbl.pack(side="left")
        close_btn = ctk.CTkButton(
            header,
            text="✖",
            width=36,
            height=32,
            command=top.destroy,
            fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, mode),
            text_color=Colors.get_color(Colors.TEXT, mode),
            hover_color=Colors.get_color(Colors.SETTINGS_ITEM_BG, mode)
        )
        close_btn.pack(side="right")

        # Barra ricerca con pulsante clear
        search_row = ctk.CTkFrame(top, fg_color="transparent")
        search_row.pack(fill="x", padx=12, pady=(0, 8))
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_row,
            textvariable=search_var,
            height=38,
            placeholder_text=self.lang.get_text("input.guild.search_placeholder") if hasattr(self.lang, 'get_text') else "Cerca server...",
        )
        search_entry.pack(side="left", fill="x", expand=True)
        clear_btn = ctk.CTkButton(
            search_row,
            text="🧹",
            width=44,
            height=36,
            command=lambda: (search_var.set(""), on_key_release()),
            fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, mode),
            text_color=Colors.get_color(Colors.TEXT, mode),
            hover_color=Colors.get_color(Colors.SETTINGS_ITEM_BG, mode)
        )
        clear_btn.pack(side="left", padx=(8, 0))
        
        # Contenitore scrollabile per l'elenco
        list_frame = ctk.CTkScrollableFrame(top, fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, mode))
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Footer con conteggio risultati e tasto Explorer avanzato (se abilitato)
        footer = ctk.CTkFrame(top, fg_color="transparent")
        footer.pack(fill="x", padx=12, pady=(0, 12))
        count_lbl = ctk.CTkLabel(footer, text="")
        count_lbl.pack(side="left")
        # Check if we have a cached setting from update_advanced_explorer_visibility
        if hasattr(self, '_advanced_explorer_enabled'):
            adv_enabled = self._advanced_explorer_enabled
        else:
            # Fallback to reading from settings
            adv_flag = self.settings.get_setting("features", "advanced_explorer")
            adv_enabled = True if adv_flag is None else bool(adv_flag)
        if adv_enabled:
            explorer_btn = ctk.CTkButton(
                footer,
                text=self.lang.get_text("input.guild.advanced_explorer_button") if hasattr(self.lang, 'get_text') else "Explorer avanzato",
                width=180,
                command=lambda: open_advanced_for_current(),
                fg_color=Colors.get_color(Colors.BUTTON_BG, mode),
                text_color=Colors.get_color(Colors.TEXT, mode),
                hover_color=Colors.get_color(Colors.BUTTON_HOVER, mode)
            )
            explorer_btn.pack(side="right")
        
        # Stato per debounce
        self._search_after_id = None
        selected_index = tk.IntVar(value=0)
        current_items = []
        item_buttons = []

        def highlight_selection():
            for idx, btn in enumerate(item_buttons):
                if idx == selected_index.get():
                    btn.configure(fg_color=Colors.get_color(Colors.TEXT, mode), text_color=Colors.get_color(Colors.BACKGROUND, mode))
                else:
                    btn.configure(fg_color=Colors.get_color(Colors.SETTINGS_ITEM_BG, mode), text_color=Colors.get_color(Colors.TEXT, mode))
        
        def populate(items):
            # Pulisci
            for w in list_frame.winfo_children():
                w.destroy()
            item_buttons.clear()
            current_items.clear()
            # Aggiungi voci
            for name in items:
                btn = ctk.CTkButton(
                    list_frame,
                    text=name,
                    anchor="w",
                    height=36,
                    fg_color=Colors.get_color(Colors.SETTINGS_ITEM_BG, mode),
                    text_color=Colors.get_color(Colors.TEXT, mode),
                    hover_color=Colors.get_color(Colors.SETTINGS_BG, mode),
                    command=lambda n=name: select_and_close(n)
                )
                btn.pack(fill="x", padx=6, pady=4)
                item_buttons.append(btn)
                current_items.append(name)
            # Aggiorna conteggio e selezione
            count_lbl.configure(text=f"{len(items)}")
            if items:
                selected_index.set(0)
                highlight_selection()
        
        def select_and_close(name):
            # Imposta il valore sul selettore corretto e invoca callback
            if name in self.guilds_dict:
                if is_source:
                    self.source_selected(name)
                else:
                    self.dest_selected(name)
            top.destroy()

        def open_advanced_for_current():
            # Apre l'explorer per l'elemento correntemente selezionato
            if not current_items:
                return
            display = current_items[selected_index.get()]
            if display in self.guilds_dict:
                guild_obj = self.guilds_dict[display]
                # Chiudi il selettore prima di aprire l'explorer per evitare doppi modali
                try:
                    top.destroy()
                except Exception:
                    pass
                def on_select(display_name: str):
                    if is_source:
                        self.source_selected(display_name)
                    else:
                        self.dest_selected(display_name)
                # Use embedded explorer within the main window
                main_window = self.winfo_toplevel()
                if hasattr(main_window, 'show_advanced_explorer'):
                    try:
                        main_window.show_advanced_explorer(guild_obj, is_source, on_select)
                    except Exception as e:
                        try:
                            messagebox.showerror("Advanced Explorer", str(e))
                        except Exception:
                            pass
        
        def on_key_release(_event=None):
            # Debounce
            if self._search_after_id is not None:
                try:
                    search_entry.after_cancel(self._search_after_id)
                except Exception:
                    pass
            def do_filter():
                q = search_var.get().strip().lower()
                if not q:
                    items = self.guild_display_names
                else:
                    items = [n for n in self.guild_display_names if q in n.lower()]
                populate(items)
            self._search_after_id = search_entry.after(150, do_filter)
        
        def on_key_nav(event):
            if not current_items:
                return
            key = event.keysym
            idx = selected_index.get()
            if key in ("Down", "KP_Down"):
                idx = (idx + 1) % len(current_items)
                selected_index.set(idx)
                highlight_selection()
            elif key in ("Up", "KP_Up"):
                idx = (idx - 1) % len(current_items)
                selected_index.set(idx)
                highlight_selection()
            elif key in ("Return", "KP_Enter"):
                select_and_close(current_items[selected_index.get()])
            elif key == "Escape":
                top.destroy()

        search_entry.bind("<KeyRelease>", on_key_release)
        top.bind("<Key>", on_key_nav)
        
        # Popola inizialmente
        populate(self.guild_display_names)
        search_entry.focus_set()


    def reset_fields(self):
        """Cancella i campi di input"""
        # Resettiamo i selettori
        placeholder = self.lang.get_text("input.guild.dropdown_placeholder")
        self.selected_source_display = None
        self.selected_dest_display = None
        self.source_select_btn.configure(text=placeholder)
        self.dest_select_btn.configure(text=placeholder)
        
        # Cancelliamo gli input manuali
        self.source_entry.delete(0, 'end')
        self.dest_entry.delete(0, 'end')
        
        # Resettiamo le opzioni
        self.clone_roles_var.set(True)
        self.clone_categories_var.set(True)
        self.clone_text_channels_var.set(True)
        self.clone_voice_channels_var.set(True)
        self.clone_messages_var.set(True)
        self.messages_limit_var.set("100")
        self.toggle_messages_options()
        
        # Nascondiamo eventuali elementi visibili
        self.update_progress(0, show=False)
        self.hide_stats()
        
        # Reset dello stato
        main_window = self.winfo_toplevel()
        main_window.status_bar.update_status(self.lang.get_text("status.ready"), "black")
        
    def get_source_guild_id(self):
        """Ottiene l'ID del server sorgente selezionato"""
        if self.source_manual_input:
            return self.source_entry.get()
        else:
            selected = self.selected_source_display
            if selected and selected in self.guilds_dict:
                return str(self.guilds_dict[selected]['id'])
            return ""
    
    def get_dest_guild_id(self):
        """Ottiene l'ID del server destinazione selezionato"""
        if self.dest_manual_input:
            return self.dest_entry.get()
        else:
            selected = self.selected_dest_display
            if selected and selected in self.guilds_dict:
                return str(self.guilds_dict[selected]['id'])
            return ""

    def start_clone(self):
        """Start the cloning process"""
        # Get token from token input
        main_window = self.winfo_toplevel()
        token = main_window.verified_token if hasattr(main_window, 'verified_token') else main_window.token_input.entry.get()
        source_id = self.get_source_guild_id()
        dest_id = self.get_dest_guild_id()
        
        # Validazione migliorata
        error_message = None
        
        if not token:
            error_message = self.lang.get_text("input.token.error_empty")
        elif not source_id:
            error_message = self.lang.get_text("input.guild.source.error_empty")
        elif not dest_id:
            error_message = self.lang.get_text("input.guild.destination.error_empty")
        elif source_id == dest_id:
            error_message = self.lang.get_text("input.guild.error_same_ids")
        
        # Validazione formato IDs
        if not error_message:
            try:
                int(source_id)
                int(dest_id)
            except ValueError:
                error_message = self.lang.get_text("input.guild.error_invalid_id")
        
        # Validazione del limite messaggi
        if not error_message and self.clone_messages_var.get():
            try:
                messages_limit = int(self.messages_limit_var.get())
                if messages_limit <= 0:
                    error_message = self.lang.get_text("input.guild.error_invalid_limit")
            except ValueError:
                error_message = self.lang.get_text("input.guild.error_invalid_limit")
        
        # Mostra errore se presente
        if error_message:
            main_window.status_bar.update_status(error_message, "red")
            return
            
        # Disable clone button during process
        self.clone_button.configure(state="disabled")
        main_window.status_bar.update_status(
            self.lang.get_text("status.cloning"), 
            "blue"
        )
        
        # Mostra la progress bar
        self.update_progress(0, True)
        
        # Prepare cancellation and show cancel button
        self._cancel_requested = False
        if not self.cancel_button.winfo_ismapped():
            self.cancel_button.pack(pady=(0, 10))
            self.cancel_button.configure(state="normal")
        
        # Run cloning in background thread with its own event loop
        def worker():
            try:
                loop = asyncio.new_event_loop()
                self._clone_loop = loop
                asyncio.set_event_loop(loop)
                self._clone_task = loop.create_task(self._clone_guild(token, source_id, dest_id))
                try:
                    loop.run_until_complete(self._clone_task)
                except asyncio.CancelledError:
                    # Task was cancelled
                    pass
            finally:
                try:
                    loop.close()
                except Exception:
                    pass
                self._clone_loop = None
                self._clone_task = None
                self._clone_thread = None
        
        self._clone_thread = threading.Thread(target=worker, daemon=True)
        self._clone_thread.start()

    def cancel_clone(self):
        """Request cancellation of the running clone task."""
        if self._clone_loop and self._clone_task:
            self._cancel_requested = True
            def _cancel():
                if not self._clone_task.done():
                    self._clone_task.cancel()
            try:
                self._clone_loop.call_soon_threadsafe(_cancel)
            except Exception:
                pass
            # Update UI indication
            self._debug_log(self.lang.get_text("status.cancelling") if hasattr(self.lang, 'get_text') else "Cancelling...", "INFO")
            try:
                self.cancel_button.configure(state="disabled")
            except Exception:
                pass
    
    async def _clone_guild(self, token, source_id, dest_id):
        """Execute server cloning process using REST API"""
        main_window = self.winfo_toplevel()
        connector = None
        try:
            # Creiamo un connector sicuro per evitare memory leak
            import ssl
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context, force_close=True)
            
            # Prepariamo l'header per le richieste API - assicuriamoci che il token sia nel formato corretto
            if not token.startswith("Bot ") and not token.startswith("Bearer "):
                # Se non è specificato il tipo di token, assumiamo che sia un user token
                auth_token = token
            else:
                auth_token = token
                
            headers = {
                "Authorization": auth_token,
                "Content-Type": "application/json"
            }
            
            # Mostra la barra di progresso e impostiamo a 0
            self.update_progress(0, show=True)
            
            # Nascondiamo le statistiche all'inizio
            self.hide_stats()
            
            # Creiamo il cloner
            cloner = Clone(self._debug_log)
            
            # Timer per aggiornare le statistiche
            stats_timer = None
            
            # Configuriamo una funzione per aggiornare la barra di progresso
            def progress_callback(progress_percentage):
                # Convertiamo il progresso in un valore tra 0.1 e 0.9
                progress_value = 0.1 + (progress_percentage * 0.8)
                self.update_progress(progress_value)
            
            # Passiamo la callback al cloner
            cloner.set_progress_callback(progress_callback)
            
            # Verifichiamo l'accesso ai server source e destination
            async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
                # Verifichiamo il server source
                self._debug_log(f"Verifico accesso al server source (ID: {source_id})")
                source_url = f"https://discord.com/api/v10/guilds/{source_id}"
                async with session.get(source_url) as source_response:
                    if source_response.status != 200:
                        self._debug_log(f"Errore nell'accesso al server source: {source_response.status}", "ERROR")
                        self.update_progress(0, show=False)  # Nascondiamo la barra di progresso
                        return
                    
                    source_data = await source_response.json()
                    source_name = source_data.get("name", "Unknown")
                    self._debug_log(f"Accesso al server source verificato: {source_name}")
                
                # Verifichiamo il server destination
                self._debug_log(f"Verifico accesso al server destination (ID: {dest_id})")
                dest_url = f"https://discord.com/api/v10/guilds/{dest_id}"
                async with session.get(dest_url) as dest_response:
                    if dest_response.status != 200:
                        self._debug_log(f"Errore nell'accesso al server destination: {dest_response.status}", "ERROR")
                        self.update_progress(0, show=False)  # Nascondiamo la barra di progresso
                        return
                    
                    dest_data = await dest_response.json()
                    dest_name = dest_data.get("name", "Unknown")
                    self._debug_log(f"Accesso al server destination verificato: {dest_name}")
                
                # Aggiorniamo la barra di progresso al 10%
                self.update_progress(0.1)
                
                # Configuriamo un timer per aggiornare le statistiche ogni secondo
                async def update_stats_timer():
                    try:
                        while True:
                            self.update_stats(cloner.get_stats())
                            await asyncio.sleep(1)
                    except asyncio.CancelledError:
                        # Gestiamo la cancellazione pulita del task
                        pass
                
                # Avviamo il timer in un task separato
                stats_timer = asyncio.create_task(update_stats_timer())
                
                # Avviamo la clonazione con le opzioni
                try:
                    self._debug_log(f"Avvio clonazione da {source_name} a {dest_name}")
                    success = await cloner.start_clone(
                        guild_from=source_data,
                        guild_to=dest_data,
                        session=session,
                        options={
                            "clone_roles": self.clone_roles_var.get(),
                            "clone_categories": self.clone_categories_var.get(),
                            "clone_text_channels": self.clone_text_channels_var.get(),
                            "clone_voice_channels": self.clone_voice_channels_var.get(),
                            "clone_messages": self.clone_messages_var.get(),
                            "clone_name_icon": self.clone_name_icon_var.get(),
                            "messages_limit": int(self.messages_limit_var.get()) if self.clone_messages_var.get()
                            else 0
                        }
                    )
                    
                    if self._cancel_requested:
                        self._debug_log(self.lang.get_text("status.cancelled") if hasattr(self.lang, 'get_text') else "Cloning cancelled", "INFO")
                        self.update_progress(0, show=False)
                        return
                    if success:
                        # Impostiamo la barra al 100% al completamento
                        self.update_progress(1.0)
                        self._debug_log(self.lang.get_text("logs.clone.completed"), "SUCCESS")
                        # Aggiorniamo un'ultima volta le statistiche
                        self.update_stats(cloner.get_stats())
                    else:
                        self.update_progress(0, show=False)  # Nascondiamo la barra in caso di errore
                except Exception as clone_error:
                    self._debug_log(
                        self.lang.get_text("logs.clone.error").format(error=str(clone_error)), 
                        "ERROR"
                    )
                    self.update_progress(0, show=False)  # Nascondiamo la barra in caso di errore
        except Exception as e:
            self._debug_log(
                self.lang.get_text("logs.clone.connection_error").format(error=str(e)), 
                "ERROR"
            )
            self.update_progress(0, show=False)  # Nascondiamo la barra in caso di errore
        finally:
            # Cancelliamo il timer se esistente
            if 'stats_timer' in locals() and stats_timer and not stats_timer.done():
                stats_timer.cancel()
                await asyncio.sleep(0.1)  # Piccola pausa per assicurarsi che il task venga cancellato
            
            # Ripristiniamo il pulsante
            def _restore_ui():
                self.clone_button.configure(state="normal")
                if self.cancel_button.winfo_ismapped():
                    self.cancel_button.pack_forget()
            try:
                self.after(0, _restore_ui)
            except Exception:
                _restore_ui()
            
            # Chiudiamo il connector anche in caso di errore
            if connector:
                try:
                    await connector.close()
                except Exception as connector_error:
                    print(f"Error closing connector: {connector_error}")
    

    def _debug_log(self, message, level="INFO"):
        """Send log to debug window if active (thread-safe)"""
        def _apply():
            main_window = self.winfo_toplevel()
            if hasattr(main_window, 'debug_mode') and main_window.debug_mode:
                if hasattr(main_window, 'debug_window'):
                    try:
                        # Verifichiamo che la finestra di debug esista ancora e sia valida
                        if main_window.debug_window.winfo_exists():
                            main_window.debug_window.log(message, level)
                    except Exception as e:
                        print(f"Debug window error: {e}")
            # Always update status bar
            color = "red" if level == "ERROR" else "blue" if level == "INFO" else "green"
            main_window.status_bar.update_status(message, color)
        try:
            self.after(0, _apply)
        except Exception:
            _apply()
    

    def update_texts(self):
        """Update texts when language changes"""
        self.source_label.configure(text=self.lang.get_text("input.guild.source.title"))
        self.source_entry.configure(placeholder_text=self.lang.get_text("input.guild.source.placeholder"))
        self.dest_label.configure(text=self.lang.get_text("input.guild.destination.title"))
        self.dest_entry.configure(placeholder_text=self.lang.get_text("input.guild.destination.placeholder"))
        self.clone_button.configure(text=self.lang.get_text("input.guild.clone_button"))
        self.reset_button.configure(text=self.lang.get_text("input.guild.reset_button"))
        
        # Aggiorniamo i dropdown
        placeholder = self.lang.get_text("input.guild.dropdown_placeholder")
        if self.source_dropdown.get() == "":
            self.source_dropdown.set(placeholder)
        if self.dest_dropdown.get() == "":
            self.dest_dropdown.set(placeholder)
        
        # Aggiorniamo i testi delle opzioni
        self.options_title.configure(text=self.lang.get_text("input.guild.options_title"))
        self.clone_roles_checkbox.configure(text=self.lang.get_text("input.guild.option_roles"))
        self.clone_categories_checkbox.configure(text=self.lang.get_text("input.guild.option_categories"))
        self.clone_text_channels_checkbox.configure(text=self.lang.get_text("input.guild.option_text_channels"))
        self.clone_voice_channels_checkbox.configure(text=self.lang.get_text("input.guild.option_voice_channels"))
        self.clone_messages_checkbox.configure(text=self.lang.get_text("input.guild.option_messages"))
        self.messages_limit_label.configure(text=self.lang.get_text("input.guild.option_messages_limit"))
        
        # Aggiorniamo anche i testi del pannello statistiche
        self.stats_title.configure(text=self.lang.get_text("input.guild.stats_title"))
        self.roles_label.configure(text=self.lang.get_text("input.guild.stats_roles"))
        self.channels_label.configure(text=self.lang.get_text("input.guild.stats_channels"))
        self.messages_label.configure(text=self.lang.get_text("input.guild.stats_messages"))
        self.errors_label.configure(text=self.lang.get_text("input.guild.stats_errors"))
        self.time_label.configure(text=self.lang.get_text("input.guild.stats_time"))

    def update_stats(self, stats: dict):
        """Aggiorna il pannello delle statistiche con i dati forniti (thread-safe)"""
        def _apply():
            # Assicuriamoci che il pannello sia visibile
            if not self.info_panel.winfo_ismapped():
                self.info_panel.pack(fill="x", pady=10, before=self.clone_button)
            # Aggiorniamo i valori
            self.roles_value.configure(text=f"{stats.get('roles_created', 0)}/{stats.get('total_roles', 0)}")
            self.channels_value.configure(text=f"{stats.get('channels_created', 0)}/{stats.get('total_channels', 0)}")
            self.messages_value.configure(text=str(stats.get('messages_copied', 0)))
            # Errori in rosso se presenti
            errors = stats.get('errors', 0)
            self.errors_value.configure(text=str(errors))
            # Formattiamo il tempo in minuti:secondi
            elapsed_time = stats.get('elapsed_time', 0)
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            self.time_value.configure(text=f"{minutes:02d}:{seconds:02d}")
        try:
            self.after(0, _apply)
        except Exception:
            _apply()
        
    def hide_stats(self):
        """Nasconde il pannello delle statistiche (thread-safe)"""
        def _apply():
            if self.info_panel.winfo_ismapped():
                self.info_panel.pack_forget()
        try:
            self.after(0, _apply)
        except Exception:
            _apply()
    

    def toggle_messages_options(self):
        """Abilita/disabilita le opzioni relative ai messaggi"""
        if self.clone_messages_var.get():
            self.messages_limit_entry.configure(state="normal")
            self.messages_limit_label.configure(text_color=Colors.get_color(Colors.TEXT))
        else:
            self.messages_limit_entry.configure(state="disabled")
            self.messages_limit_label.configure(text_color=Colors.get_color(Colors.TEXT_MUTED))

    def _setup_context_menu(self, widget, is_source=True):
        """Configura il menu contestuale (tasto destro) per i dropdown dei server"""
        context_menu = tk.Menu(widget, tearoff=0)
        
        if is_source:
            # Menu per il server sorgente
            context_menu.add_command(
                label=self.lang.get_text("input.guild.open_in_browser"), 
                command=lambda: self.open_server_in_browser(self.get_source_guild_id())
            )
        else:
            # Menu per il server destinazione
            context_menu.add_command(
                label=self.lang.get_text("input.guild.open_in_browser"), 
                command=lambda: self.open_server_in_browser(self.get_dest_guild_id())
            )
            
        # Bind per il tasto destro 
        widget.bind("<Button-3>", lambda event: self._show_context_menu(event, context_menu))
        
        # Salva un riferimento al menu
        if is_source:
            self.source_context_menu = context_menu
        else:
            self.dest_context_menu = context_menu
    
    def _show_context_menu(self, event, menu):
        """Mostra il menu contestuale alla posizione del mouse"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def open_server_in_browser(self, guild_id):
        """Apre il server Discord nel browser"""
        if not guild_id:
            return
            
        # URL del server Discord
        discord_url = f"https://discord.com/channels/{guild_id}"
        
        try:
            # Apri il browser con l'URL
            webbrowser.open(discord_url)
            
            # Log dell'azione
            self._debug_log(f"Apertura server {guild_id} nel browser", "INFO")
        except Exception as e:
            self._debug_log(f"Errore nell'apertura del browser: {str(e)}", "ERROR")
    
    async def create_guild_request(self, token, guild_name):
        """Crea un nuovo server Discord tramite API REST"""
        self._debug_log(f"Creazione nuovo server: {guild_name}", "INFO")
        
        try:
            import ssl
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context, force_close=True)
            

            api_url = "https://discord.com/api/v9/guilds"
            
            if not token.startswith("Bot ") and not token.startswith("Bearer "):
                auth_token = token
            else:
                auth_token = token
            
            if auth_token.startswith("Bot "):
                return {"success": False, "error": "Guild creation via API requires a user token. A Bot token cannot create servers (403 Forbidden)."}
                
            headers = {
                "Authorization": auth_token,
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            }
            
            guild_data = {
                "name": guild_name
            }
            
            max_retries = 3
            attempt = 0
            async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
                while attempt <= max_retries:
                    if attempt > 0:
                        self._debug_log(f"Retry creazione server, tentativo {attempt}/{max_retries}", "WARN")
                    async with session.post(api_url, json=guild_data) as response:
                        if response.status == 201:
                            result = await response.json()
                            guild_id = result.get("id")
                            guild_name = result.get("name")
                            self._debug_log(f"Server creato: {guild_name} (ID: {guild_id})", "SUCCESS")
                            return {"success": True, "id": guild_id, "name": guild_name}
                        
                        if response.status == 429:
                            retry_after = None
                            header_val = response.headers.get("Retry-After")
                            if header_val:
                                try:
                                    retry_after = float(header_val)
                                except Exception:
                                    retry_after = None
                            if retry_after is None:
                                try:
                                    err = await response.json()
                                    retry_after = float(err.get("retry_after", 1))
                                except Exception:
                                    retry_after = 1.0
                            retry_after = max(0.5, min(retry_after, 15.0))
                            self._debug_log(f"Rate limited (429). Attendo {retry_after}s prima del retry.", "WARN")
                            attempt += 1
                            if attempt > max_retries:
                                return {"success": False, "error": f"Errore API (429): Le tue azioni sono limitate. Riprova tra {retry_after:.0f}s."}
                            await asyncio.sleep(retry_after)
                            continue

                        try:
                            error_json = await response.json()
                            msg = error_json.get("message") or str(error_json)
                            code = error_json.get("code")
                            details = f"{msg} (code={code})" if code is not None else msg
                        except Exception:
                            details = await response.text()
                        self._debug_log(f"Errore nella creazione del server: {response.status} - {details}", "ERROR")
                        return {"success": False, "error": f"Errore API ({response.status}): {details}"}
        except Exception as e:
            self._debug_log(f"Errore imprevisto: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def create_new_server(self):
        """Mostra un dialogo per creare un nuovo server Discord"""
        main_window = self.winfo_toplevel()
        
        token = main_window.verified_token if hasattr(main_window, 'verified_token') else main_window.token_input.entry.get()
        
        if not token:
            main_window.status_bar.update_status(
                self.lang.get_text("input.token.error_empty"), 
                "red"
            )
            return
        
        server_name = simpledialog.askstring(
            self.lang.get_text("input.guild.create_server_title"), 
            self.lang.get_text("input.guild.create_server_prompt"),
            parent=self
        )
        
        if not server_name:
            return
            
        self.create_server_button.configure(state="disabled")
        
        main_window.status_bar.update_status(
            self.lang.get_text("status.creating_server").format(name=server_name), 
            "blue"
        )
        
        # Esegui la richiesta in un thread separato
        threading.Thread(target=self._create_server_thread, args=(token, server_name), daemon=True).start()
    
    def _create_server_thread(self, token, server_name):
        """Thread per la creazione di un nuovo server"""
        main_window = self.winfo_toplevel()
        
        try:
            # Creiamo un loop asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Eseguiamo la richiesta API
            result = loop.run_until_complete(self.create_guild_request(token, server_name))
            
            # Gestiamo il risultato nel thread principale
            if result["success"]:
                self.after(0, lambda: self._handle_server_creation_success(result))
            else:
                self.after(0, lambda: self._handle_server_creation_error(result["error"]))
            
        except Exception as e:
            # Gestiamo eventuali errori
            self.after(0, lambda: self._handle_server_creation_error(str(e)))
        finally:
            # Chiudiamo l'event loop
            loop.close()
    
    def _handle_server_creation_success(self, result):
        """Gestisce la creazione riuscita di un server"""
        main_window = self.winfo_toplevel()
        
        # Ripristina il pulsante
        self.create_server_button.configure(state="normal")
        
        # Aggiorna la barra di stato
        main_window.status_bar.update_status(
            self.lang.get_text("status.server_created").format(name=result['name']), 
            "green"
        )
        
        # Aggiorna l'elenco server facendo riutilizzare il token esistente
        main_window.token_input.verify_token()
        
        # Mostra un messaggio di conferma
        messagebox.showinfo(
            self.lang.get_text("input.guild.create_server_success"), 
            f"{self.lang.get_text('input.guild.create_server_success')}:\n\n{result['name']}\nID: {result['id']}"
        )
    
    def _handle_server_creation_error(self, error_message):
        """Gestisce gli errori durante la creazione del server"""
        main_window = self.winfo_toplevel()
        
        # Ripristina il pulsante
        self.create_server_button.configure(state="normal")
        
        # Aggiorna la barra di stato
        main_window.status_bar.update_status(
            f"{self.lang.get_text('input.guild.create_server_error')}: {error_message}", 
            "red"
        )
        
        # Mostra un errore
        messagebox.showerror(
            self.lang.get_text("input.guild.create_server_error"), 
            f"{self.lang.get_text('input.guild.create_server_error')}:\n\n{error_message}"
        )