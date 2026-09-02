import customtkinter as ctk
from src.gui.dashboard_page import DashboardPage
from src.gui.settings_page import SettingsPage
from src.gui.accessory_page import AccessoryPage
import ctypes
import os
import sys
import shutil
import subprocess
from PIL import Image, ImageDraw # ImageDraw eklendi!

from src.util.config_manager import APP_VERSION
from src.util.update_manager import UpdateManager

# Görev çubuğunda doğru ikonu göstermek için AppUserModelID ayarı
myappid = 'lcw.sap.automation.v2' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- YENİ EKLENEN GÖRSEL YUMUŞATMA FONKSİYONU ---
def make_image_rounded(image_path, radius):
    """Bir resmi okur, saydamlık kanalı ekler ve köşelerini maskeleyerek ovalleştirir."""
    img = Image.open(image_path).convert("RGBA")
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    img.putalpha(mask)
    return img

class LCWAutomationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- 1. ULTRA İNCE SIDEBAR AYARLARI ---
        self.sidebar_width = 72 # Çift sayı olması hizalama için her zaman daha iyidir
        
        self.title("LCW SAP Automation Hub v2026")
        self.after(0, lambda: self.state('zoomed')) 
        
        icon_path = resource_path("app_icon.ico")
        if os.path.exists(icon_path): 
            self.iconbitmap(icon_path)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Arka planı koyu, modern bir griye sabitleyelim
        self.configure(fg_color="#09090b") 

        # --- TASARIM JETONLARI (Renk Uyumu İçin) ---
        self.theme = {
            "sidebar_bg": "#18181b",      # Ana ekrandan biraz daha açık bir siyah/gri
            "btn_hover": "#27272a",       # Üzerine gelince zarif bir aydınlanma
            "btn_active": "#2563eb",      # Ana eylem rengimiz (Modern Mavi)
            "content_bg": "#09090b"       # İçerik arka planı
        }

        # İkonları Yükle (Ovalleştirme burada yapılıyor)
        self.load_assets()

        # --- 2. SIDEBAR ÇERÇEVESİ ---
        self.sidebar_frame = ctk.CTkFrame(self, width=self.sidebar_width, corner_radius=0, fg_color=self.theme["sidebar_bg"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_frame.grid_propagate(False)

        # --- 3. MENÜ BUTONLARI ---
        self.spacer = ctk.CTkLabel(self.sidebar_frame, text="", height=20)
        self.spacer.grid(row=0, column=0)

        # Buton genişlikleri sidebar ile tam uyumlu hale getirildi, köşe yumuşatmaları (corner_radius) ayarlandı.
        self.dashboard_btn = ctk.CTkButton(
            self.sidebar_frame, text="", image=self.home_icon, 
            width=50, height=50, corner_radius=12,
            fg_color=self.theme["btn_active"], hover_color=self.theme["btn_hover"],
            command=self.show_dashboard
        )
        self.dashboard_btn.grid(row=1, column=0, padx=11, pady=10)

        self.accessory_btn = ctk.CTkButton(
            self.sidebar_frame, text="", image=self.accessory_icon, 
            width=50, height=50, corner_radius=12,
            fg_color="transparent", hover_color=self.theme["btn_hover"],
            command=self.show_accessory
        )
        self.accessory_btn.grid(row=2, column=0, padx=11, pady=10)

        self.settings_btn = ctk.CTkButton(
            self.sidebar_frame, text="", image=self.settings_icon, 
            width=50, height=50, corner_radius=12,
            fg_color="transparent", hover_color=self.theme["btn_hover"],
            command=self.show_settings
        )
        self.settings_btn.grid(row=3, column=0, padx=11, pady=10)
                
        # --- 4. FOOTER ---
        self.version_label = ctk.CTkLabel(
            self.sidebar_frame, text=f"v{APP_VERSION}", 
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#52525b"
        )
        self.version_label.grid(row=4, column=0, sticky="s", pady=20)

        # --- 5. ANA İÇERİK ALANI ---
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=self.theme["content_bg"])
        self.content_frame.grid(row=0, column=1, sticky="nsew") # Dış boşluklar kaldırıldı, sayfalar tam otursun
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        self.pages = {
            "dashboard": DashboardPage(self.content_frame, fg_color="transparent"),
            "accessory": AccessoryPage(self.content_frame, fg_color="transparent"),
            "settings": SettingsPage(self.content_frame, fg_color="transparent")            
        }
        self.show_dashboard()

        # Otomatik güncelleme kontrolünü başlat (1.5 saniye sonra)
        self.after(1500, lambda: UpdateManager.check_for_updates_async(self))

    def load_assets(self):
        home_path = resource_path(os.path.join("assets", "home.png"))
        settings_path = resource_path(os.path.join("assets", "settings.png"))
        accessory_path = resource_path(os.path.join("assets", "accessory.png"))

        # GÖRSELLERİ OVALLEŞTİRME (256x256 piksellik bir simge için radius=60 o "Apple/iOS" tarzı squircle görünümünü verir)
        radius_val = 60 
        
        # Try-except bloğu eklendi ki dosya bulunamazsa uygulama çökmesin, terminale uyarı versin.
        try:
            r_home = make_image_rounded(home_path, radius_val)
            r_settings = make_image_rounded(settings_path, radius_val)
            r_accessory = make_image_rounded(accessory_path, radius_val)

            self.home_icon = ctk.CTkImage(light_image=r_home, dark_image=r_home, size=(28, 28))
            self.settings_icon = ctk.CTkImage(light_image=r_settings, dark_image=r_settings, size=(28, 28))
            self.accessory_icon = ctk.CTkImage(light_image=r_accessory, dark_image=r_accessory, size=(28, 28))
        except Exception as e:
            print(f"Ikonlar yuklenirken hata: {e}. Lutfen 'assets' klasorundeki dosyalarin adlarini kontrol et.")
            # Hata durumunda boş görsel oluşturur ki kod çalışmaya devam etsin
            empty_img = Image.new('RGBA', (100, 100), (0,0,0,0))
            self.home_icon = ctk.CTkImage(light_image=empty_img, size=(28, 28))
            self.settings_icon = self.home_icon
            self.accessory_icon = self.home_icon

    def show_dashboard(self):
        self.pages["settings"].grid_forget()
        self.pages["accessory"].grid_forget()
        self.pages["dashboard"].grid(row=0, column=0, sticky="nsew")
        
        self.dashboard_btn.configure(fg_color=self.theme["btn_active"])
        self.settings_btn.configure(fg_color="transparent")
        self.accessory_btn.configure(fg_color="transparent")

    def show_settings(self):
        self.pages["dashboard"].grid_forget()
        self.pages["accessory"].grid_forget()
        self.pages["settings"].grid(row=0, column=0, sticky="nsew")
        
        self.settings_btn.configure(fg_color=self.theme["btn_active"])
        self.dashboard_btn.configure(fg_color="transparent")
        self.accessory_btn.configure(fg_color="transparent")

    def show_accessory(self):
        self.pages["dashboard"].grid_forget()
        self.pages["settings"].grid_forget()
        self.pages["accessory"].grid(row=0, column=0, sticky="nsew")
        
        self.accessory_btn.configure(fg_color=self.theme["btn_active"])
        self.dashboard_btn.configure(fg_color="transparent")
        self.settings_btn.configure(fg_color="transparent")

        active_po = self.pages["dashboard"].po_entry.get().strip()
        
        if active_po:
            self.pages["accessory"].auto_load_po(active_po)

if __name__ == "__main__":
    app = LCWAutomationApp()
    app.mainloop()