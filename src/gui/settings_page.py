import customtkinter as ctk
from src.util.config_manager import ConfigManager
from src.util.localizer import _
from tkinter import messagebox

class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.cfg = ConfigManager()

        # --- BAŞLIK ---
        self.title_label = ctk.CTkLabel(self, text=_("CREDENTIALS_MGMT"), font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 30), sticky="w")

        # --- TEDARİKÇİ PORTALI ---
        self.create_section_label(_("SUPPLIER_PORTAL"), 1)
        self.ent_portal_user = self.create_input(_("USERNAME_EMAIL"), 2, "LCW_PORTAL_USER")
        self.ent_portal_pass = self.create_input(_("PASSWORD"), 3, "LCW_PORTAL_PASS", is_password=True)

        # --- SAP ---
        self.create_section_label(_("SAP_SYSTEM"), 4)
        self.ent_sap_user = self.create_input(_("SAP_USERNAME"), 5, "SAP_USERNAME")
        self.ent_sap_pass = self.create_input(_("SAP_PASSWORD"), 6, "SAP_PASS", is_password=True)

        # --- UYGULAMA AYARLARI ---
        self.create_section_label(_("APP_SETTINGS"), 7)
        
        current_lang = self.cfg.get_setting("APP_LANGUAGE") or "TR"
        lang_options = ["Türkçe (TR)", "English (EN)"]
        initial_display = "Türkçe (TR)" if str(current_lang).upper() == "TR" else "English (EN)"
        
        self.combo_lang = self.create_dropdown(_("APP_LANGUAGE_LABEL"), 8, lang_options, initial_display)

        # --- KAYDET BUTONU ---
        self.save_btn = ctk.CTkButton(self, text=_("SAVE_CRED_SECURELY"), 
                                      command=self.save_all_settings,
                                      height=45, corner_radius=10, 
                                      fg_color="#1f538d", hover_color="#14375e",
                                      font=ctk.CTkFont(size=15, weight="bold"))
        self.save_btn.grid(row=9, column=0, padx=20, pady=40, sticky="ew")

    def create_section_label(self, text, row):
        lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=16, weight="bold"), text_color="#3b8ed0")
        lbl.grid(row=row, column=0, padx=20, pady=(20, 10), sticky="w")

    def create_input(self, label_text, row, config_key, is_password=False):
        lbl = ctk.CTkLabel(self, text=label_text, font=ctk.CTkFont(size=13))
        lbl.grid(row=row, column=0, padx=25, pady=2, sticky="w")
        
        entry = ctk.CTkEntry(self, width=350, height=35, placeholder_text=label_text)
        if is_password:
            entry.configure(show="*")
            val = self.cfg.get_password(config_key)
        else:
            val = self.cfg.get_setting(config_key)
            
        entry.insert(0, val or "")
        entry.grid(row=row, column=0, padx=(200, 20), pady=8, sticky="w")
        return entry

    def create_dropdown(self, label_text, row, options, current_val):
        lbl = ctk.CTkLabel(self, text=label_text, font=ctk.CTkFont(size=13))
        lbl.grid(row=row, column=0, padx=25, pady=2, sticky="w")
        
        opt_menu = ctk.CTkOptionMenu(
            self, 
            values=options, 
            width=350, 
            height=35,
            corner_radius=8,
            fg_color="#2b2b2b",
            button_color="#3a3a3a",
            button_hover_color="#4a4a4a",
            dropdown_fg_color="#2b2b2b",
            dropdown_hover_color="#1f538d",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        opt_menu.set(current_val)
        opt_menu.grid(row=row, column=0, padx=(200, 20), pady=8, sticky="w")
        return opt_menu

    def save_all_settings(self):
        try:
            old_lang = self.cfg.get_setting("APP_LANGUAGE") or "TR"
            selected_display = self.combo_lang.get()
            new_lang = "EN" if "EN" in selected_display else "TR"

            # Kullanıcı adlarını ve Dil ayarını JSON'a
            self.cfg.save_setting("LCW_PORTAL_USER", self.ent_portal_user.get())
            self.cfg.save_setting("SAP_USERNAME", self.ent_sap_user.get())
            self.cfg.save_setting("APP_LANGUAGE", new_lang)
            # SAP dilini de güncelle (en/tr olarak, SAP EN/TR olarak bekler)
            self.cfg.save_setting("SAP_LANGUAGE", new_lang)

            # Şifreleri Windows Kasasına
            self.cfg.save_password("LCW_PORTAL_PASS", self.ent_portal_pass.get())
            self.cfg.save_password("SAP_PASS", self.ent_sap_pass.get())

            messagebox.showinfo(_("SAVE_SUCCESS").split(".")[0], _("SAVE_SUCCESS"))
            
            # Dil değiştiyse restart uyarısı ver
            if old_lang != new_lang:
                messagebox.showwarning(_("RESTART_WARNING"), _("RESTART_WARNING_MSG"))
        except Exception as e:
            messagebox.showerror(_("SAVE_ERROR").split(":")[0], _("SAVE_ERROR", error=str(e)))