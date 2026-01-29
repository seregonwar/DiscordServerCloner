import customtkinter as ctk
from PIL import Image
import os
import threading
import asyncio
import aiohttp
from src.interface.utils.language_manager import LanguageManager
from src.interface.styles.colors import Colors
from src.interface.utils.validators import is_token_valid

class TokenInput(ctk.CTkFrame):
    def __init__(self, master):
        mode = ctk.get_appearance_mode().lower()
        super().__init__(master, fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, mode))
        
        # Get the language manager
        self.lang = LanguageManager()
        
        # Main frame (use solid color to avoid transparency cost)
        self.main_frame = ctk.CTkFrame(self, fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, mode))
        self.main_frame.pack(fill="x", padx=20)

        # Label
        self.label = ctk.CTkLabel(
            self.main_frame,
            text=self.lang.get_text("input.token.title"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label.pack(anchor="w", pady=(10, 5))
        
        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, mode))
        self.input_frame.pack(fill="x")
        
        # Entry
        self.entry = ctk.CTkEntry(
            self.input_frame,
            show="•",
            placeholder_text=self.lang.get_text("input.token.placeholder"),
            height=40
        )
        self.entry.pack(side="left", fill="x", expand=True)
        
        # Show/Hide button
        self.show_button = ctk.CTkButton(
            self.input_frame,
            text="👁",
            width=40,
            command=self.toggle_show_hide,
            fg_color=Colors.get_color(Colors.TEXT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.BACKGROUND, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.TEXT_MUTED, ctk.get_appearance_mode().lower())
        )
        self.show_button.pack(side="left", padx=(10, 0))
        # Delete button (clear token)
        self.delete_token_button = ctk.CTkButton(
            self.input_frame,
            text="❌",
            width=30,
            command=self.clear_token,
            fg_color=Colors.get_color(Colors.TEXT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.BACKGROUND, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.TEXT_MUTED, ctk.get_appearance_mode().lower())
        )
        self.delete_token_button.pack(side="right", padx=(10, 0))


        # Verify button per testare il token e recuperare i server
        self.verify_button = ctk.CTkButton(
            self.input_frame,
            text=self.lang.get_text("input.token.verify_button"),
            width=100,
            command=self.verify_token,
            fg_color=Colors.get_color(Colors.TEXT, ctk.get_appearance_mode().lower()),
            text_color=Colors.get_color(Colors.BACKGROUND, ctk.get_appearance_mode().lower()),
            hover_color=Colors.get_color(Colors.TEXT_MUTED, ctk.get_appearance_mode().lower())
        )
        self.verify_button.pack(side="left", padx=(10, 0))
        
        # Help text with tooltip
        self.help_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.help_frame.pack(fill="x", pady=(5, 10))
        
        self.help_label = ctk.CTkLabel(
            self.help_frame,
            text=self.lang.get_text("input.token.help"),
            text_color=Colors.get_color(Colors.LINK),
            cursor="hand2"
        )
        self.help_label.pack(anchor="w")
        
        # Aggiungiamo l'attributo help_button che manca 
        self.help_button = self.help_label  # Questo punta all'etichetta esistente come fallback
        
        # Discord client per verificare il token
        self.client = None
        self.guilds_list = []
        
        # Tooltip frame (initially hidden)
        self.tooltip = None
        self.tooltip_timer = None
        
        # Bind mouse events
        self.help_label.bind("<Enter>", self.schedule_tooltip)
        self.help_label.bind("<Leave>", self.hide_tooltip)
        
        # Add observer for language changes
        self.lang.add_observer(self.update_texts)
        
    def update_texts(self):
        """Update texts when the language changes"""
        self.label.configure(text=self.lang.get_text("input.token.title"))
        self.entry.configure(placeholder_text=self.lang.get_text("input.token.placeholder"))
        self.help_label.configure(text=self.lang.get_text("input.token.help"))
        self.verify_button.configure(text=self.lang.get_text("input.token.verify_button"))
   # Force placeholder refresh if entry is empty
        if self.entry.get() == "":
            self.entry.focus()                  
            self.entry.master.focus_set()       

        # If the tooltip is visible, update it
        if self.tooltip:
            for child in self.tooltip.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.configure(text=self.lang.get_text("input.token.help_text"))      
    def schedule_tooltip(self, event):
        """Schedule the appearance of the tooltip after a delay"""
        if self.tooltip_timer:
            self.help_frame.after_cancel(self.tooltip_timer)
        self.tooltip_timer = self.help_frame.after(500, self.show_tooltip)  # 500ms delay
        
    def show_tooltip(self):
        """Show the tooltip"""
        if self.tooltip:
            return
            
        # Create the tooltip as a toplevel window
        self.tooltip = ctk.CTkToplevel()
        self.tooltip.overrideredirect(True)  # Remove window decoration
        
        # Configure the tooltip style
        self.tooltip.configure(fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT))
        
        # Create the tooltip content
        help_text = ctk.CTkLabel(
            self.tooltip,
            text=self.lang.get_text("input.token.help_text"),
            justify="left",
            wraplength=400,
            padx=20,
            pady=20,
            text_color=Colors.get_color(Colors.TEXT)
        )
        help_text.pack()
        
        # Calculate the tooltip position
        x = self.help_label.winfo_rootx()
        y = self.help_label.winfo_rooty() + self.help_label.winfo_height() + 5
        
        # Update the tooltip geometry
        self.tooltip.geometry(f"+{x}+{y}")
        
        # Keep the tooltip above the main window
        self.tooltip.lift()
        self.tooltip.attributes('-topmost', True)
    
    def hide_tooltip(self, event=None):
        """Hide the tooltip"""
        if self.tooltip_timer:
            self.help_frame.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None
            
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    def clear_token(self):
        self.entry.delete(0, "end")        
    def toggle_show_hide(self):
        if self.entry.cget("show") == "•":
            self.entry.configure(show="")
            self.show_button.configure(text="🔒")
        else:
            self.entry.configure(show="•")
            self.show_button.configure(text="👁")
            
    def _update_colors(self):
        mode = ctk.get_appearance_mode().lower()
        self.show_button.configure(
            fg_color=Colors.get_color(Colors.TEXT, mode),
            text_color=Colors.get_color(Colors.BACKGROUND, mode),
            hover_color=Colors.get_color(Colors.TEXT_MUTED, mode)
        )
        
        if self.tooltip:
            self.tooltip.configure(fg_color=Colors.get_color(Colors.BACKGROUND_LIGHT, mode))
            for child in self.tooltip.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.configure(text_color=Colors.get_color(Colors.TEXT, mode))

    def verify_token(self):
        """Verifica il token e recupera l'elenco dei server disponibili"""
        token = self.entry.get()
        main_window = self.winfo_toplevel()
        
        if not token:
            main_window.status_bar.update_status(
                self.lang.get_text("input.token.error_empty"), 
                "red"
            )
            return
        
        # Non validiamo più il formato del token, accettiamo qualsiasi input
        # Questo permette di accettare qualsiasi formato di token
        
        # Disattiva il pulsante durante la verifica
        self.verify_button.configure(state="disabled", text=self.lang.get_text("input.token.verifying"))
        
        # Aggiorna la barra di stato
        main_window.status_bar.update_status(
            self.lang.get_text("status.connecting"), 
            "blue"
        )
        
        # Esegui la verifica in un thread separato
        threading.Thread(target=self._verify_token_thread, args=(token,), daemon=True).start()
    
    def _verify_token_thread(self, token):
        """Thread per verificare il token e recuperare i server"""
        try:
            # Creiamo un evento asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Eseguiamo la verifica
            result = loop.run_until_complete(self._verify_token_async(token))
            
            # Aggiorniamo l'UI nel thread principale
            self.after(0, lambda: self._handle_verification_result(result, token))
            
        except Exception as e:
            # Gestiamo eventuali errori
            self.after(0, lambda: self._handle_verification_error(str(e)))
        finally:
            # Chiudiamo l'event loop
            loop.close()

    async def _verify_token_async(self, token):
        """Verifica il token in modo asincrono usando solo HTTP"""
        try:
            import ssl
            import certifi
            
            # Create SSL context using certifi's CA bundle
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            
            # Creiamo un connector sicuro per evitare memory leak e usando il bundle CA corretto
            connector = aiohttp.TCPConnector(ssl=ssl_context, force_close=True)
            
            # URL delle API Discord per ottenere i server dell'utente
            api_url = "https://discord.com/api/v10/users/@me/guilds"
            user_url = "https://discord.com/api/v10/users/@me"
            
            headers = {
                "Authorization": token,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
                # Prima verifichiamo le informazioni utente
                async with session.get(user_url) as user_response:
                    if user_response.status == 401:
                        # Token non valido
                        return {"success": False, "error": "Token Discord non valido o scaduto"}
                    elif user_response.status != 200:
                        # Altri errori
                        error_data = await user_response.text()
                        return {"success": False, "error": f"Errore API ({user_response.status}): {error_data}"}
                    
                    # Otteniamo i dati utente
                    user_data = await user_response.json()
                    username = user_data.get("username", "Utente")
                    
                    # Ora recuperiamo i server
                    async with session.get(api_url) as guilds_response:
                        if guilds_response.status != 200:
                            error_data = await guilds_response.text()
                            return {"success": False, "error": f"Errore API ({guilds_response.status}): {error_data}"}
                        
                        guilds_data = await guilds_response.json()
                        
                        # Convertiamo i dati nel formato atteso
                        guilds = []
                        for guild in guilds_data:
                            guilds.append({
                                'id': guild.get('id'),
                                'name': guild.get('name'),
                                'icon': guild.get('icon')
                            })
                        
                        return {
                            "success": True, 
                            "guilds": guilds, 
                            "username": username
                        }
                
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Errore di connessione: {str(e)}"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout durante la connessione alle API Discord"}
        except Exception as e:
            return {"success": False, "error": f"Errore imprevisto: {str(e)}"}
    
    def _handle_verification_result(self, result, token):
        """Gestisce il risultato della verifica nel thread principale"""
        main_window = self.winfo_toplevel()
        
        if result["success"]:
            # Salviamo l'elenco dei server
            self.guilds_list = result["guilds"]
            
            # Aggiorniamo l'interfaccia
            guild_input = main_window.guild_input
            guild_input.update_guilds_dropdowns(self.guilds_list)
            
            # Aggiorniamo lo stato
            main_window.status_bar.update_status(
                self.lang.get_text("status.connected").format(user=result["username"]), 
                "green"
            )
            
            # Salviamo il token
            main_window.verified_token = token
            
        else:
            # Mostriamo l'errore
            main_window.status_bar.update_status(
                self.lang.get_text("status.connection_error").format(error=result["error"]), 
                "red"
            )
        
        # Ripristiniamo il pulsante
        self.verify_button.configure(
            state="normal", 
            text=self.lang.get_text("input.token.verify_button")
        )
    
    def _handle_verification_error(self, error_message):
        """Gestisce gli errori durante la verifica"""
        main_window = self.winfo_toplevel()
        
        # Mostriamo l'errore
        main_window.status_bar.update_status(
            self.lang.get_text("status.connection_error").format(error=error_message), 
            "red"
        )
        
        # Ripristiniamo il pulsante
        self.verify_button.configure(
            state="normal", 
            text=self.lang.get_text("input.token.verify_button")
        )