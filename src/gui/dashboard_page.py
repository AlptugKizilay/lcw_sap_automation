import sys

import customtkinter as ctk
import os
import subprocess
import threading
import logging
from src.util.logger_gui import setup_gui_logging
from src.logic_bridge import AutomationBridge
from src.util.automation_state import AutomationState
from src.util.localizer import _, get_language
from PIL import Image

# --- TEMA ZORLAMASI (Windows Ayarlarını Devre Dışı Bırakır) ---
ctk.set_appearance_mode("dark")  # Her zaman karanlık mod
ctk.set_default_color_theme("blue") # Standart mavi tema
WORKFLOW_STEPS = {
    "SINGLE": [
        ("ZMM0020", "ZMM0020 - Varyant Girişi"),
        ("ZSD0010", "ZSD0010 - Satış Siparişi"),
        ("ZPP0030", "ZPP0030 - Üretim Takip")
    ],
    "SET": [
        ("ZMM0020", "ZMM0020 - Varyant (Ana/Çocuk)"),
        ("CS01", "CS01 - Ürün Ağacı (BOM)"),
        ("ZSD0010", "ZSD0010 - Satış Siparişi"),
        ("MD01N", "MD01N - MRP Çalıştırma"),
        ("ZPP0030", "ZPP0030 - Üretim Takip")
    ]
}

logger = logging.getLogger(__name__)
def resource_path(relative_path):
    """ PyInstaller için dinamik dosya yolu oluşturur """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.pop("fg_color", None) 
        super().__init__(master, fg_color="#0f0f10", **kwargs)
        self.step_indicators = {}
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.bridge = AutomationBridge(self)

        self.setup_ui()
        setup_gui_logging(self.log_textbox)


    def setup_ui(self):
        """Premium Dark RPA Dashboard UI - Modüler İş Akışı Destekli"""
        logo_path = resource_path("assets/lcw_logo.png") 
        # 1. ANA GRID YAPILANDIRMASI
        self.grid_columnconfigure(0, weight=3) # Sol taraf geniş
        self.grid_columnconfigure(1, weight=1) # Sağ taraf (İş Akışı) dar
        self.grid_rowconfigure(1, weight=0)    # Kontrol Paneli boyutu kadar
        self.grid_rowconfigure(2, weight=1)    # Terminal alanı esnek

        # --- 1. HEADER (Satır 0, Sütun 0-1) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="#1a1a1b", height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header_frame.grid_propagate(False)

        self.header_left_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.header_left_container.place(relx=0.02, rely=0.5, anchor="w")

        # 1. Logo (PNG)
        if os.path.exists(logo_path):
            self.header_logo_img = ctk.CTkImage(
                Image.open(logo_path), 
                size=(180, 60) # Başlığa uygun küçük boyut
            )
            self.header_logo_label = ctk.CTkLabel(
                self.header_left_container, 
                image=self.header_logo_img, 
                text=""
            )
            self.header_logo_label.pack(side="left", padx=(0, 10))
        else:
            # Debug için logo bulunamazsa terminale yazdır
            print(f"UYARI: Logo bulunamadı! Yol: {logo_path}")

        # 2. Başlık Metni
        self.title_label = ctk.CTkLabel(
            self.header_left_container, 
            text=_("SAP_AUTOMATION_SYSTEM"), 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#3b8ed0"
        )
        self.title_label.pack(side="left")

        self.status_indicator = ctk.CTkLabel(
            self.header_frame, 
            text=_("SYSTEM_READY"), 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#14a44d"
        )
        self.status_indicator.place(relx=0.97, rely=0.5, anchor="e")

        # --- 2. WORKFLOW SELECTOR (SAĞ PANEL - Satır 1 ve 2'yi kaplar) ---
        # Önce bu kartı oluşturuyoruz ki AttributeError almayalım
        self.wf_card = ctk.CTkFrame(self, fg_color="#111111", corner_radius=15)
        self.wf_card.grid(row=1, column=1, rowspan=2, padx=20, pady=25, sticky="nsew")
        
        self.wf_card.grid_columnconfigure(0, weight=1)
        self.wf_card.grid_rowconfigure(1, weight=1)

        self.wf_title = ctk.CTkLabel(self.wf_card, text=_("WORKFLOW"), font=ctk.CTkFont(size=15, weight="bold"), text_color="#3b8ed0")
        self.wf_title.grid(row=0, column=0, pady=(15, 10), padx=20, sticky="w")

        self.steps_container = ctk.CTkScrollableFrame(
            self.wf_card, 
            fg_color="transparent",
            label_text=_("OPERATION_STEPS"),
            label_font=ctk.CTkFont(size=12, weight="bold"),
            label_text_color="#555555"
        )
        self.steps_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.btn_run_selected = ctk.CTkButton(
            self.wf_card, 
            text=_("START_SELECTED_STEPS"),
            fg_color="#14a44d", 
            hover_color="#118a41",
            height=45,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.run_selected_steps_action,
            state="disabled"
        )
        self.btn_run_selected.grid(row=2, column=0, padx=20, pady=20, sticky="ew")

        # --- 3. CONTROL CENTER (Sol Orta - Satır 1) ---
        self.card_frame = ctk.CTkFrame(self, fg_color="#161617", corner_radius=15, border_width=1, border_color="#2a2a2b")
        self.card_frame.grid(row=1, column=0, padx=(30, 15), pady=25, sticky="ew")
        
        self.po_label = ctk.CTkLabel(self.card_frame, text=_("TARGET_PO"), font=ctk.CTkFont(size=11, weight="bold"), text_color="#777777")
        self.po_label.grid(row=0, column=0, padx=(25, 10), pady=(20, 0), sticky="w")

        self.po_entry = ctk.CTkEntry(
            self.card_frame, 
            placeholder_text=_("PO_ENTRY_PLACEHOLDER"), 
            width=320, height=45, 
            font=ctk.CTkFont(size=15),
            fg_color="#0a0a0b", border_color="#333333", corner_radius=8
        )
        self.po_entry.grid(row=1, column=0, padx=(25, 10), pady=(5, 25), sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(self.card_frame, mode="determinate", height=10, progress_color="#3b8ed0")
        self.progress_bar.grid(row=2, column=0, columnspan=2, padx=25, pady=(0, 20), sticky="ew")
        self.progress_bar.set(0)

        self.button_group = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.button_group.grid(row=1, column=1, padx=(0, 25), pady=(5, 25), sticky="e")

        self.btn_template = ctk.CTkButton(self.button_group, text=_("CREATE_EXCEL_TEMPLATE"), fg_color="#1e1e1f", hover_color="#2a2a2b", border_width=1, border_color="#333333", width=180, height=45, font=ctk.CTkFont(size=12, weight="bold"), command=self.create_template_action)
        self.btn_template.pack(side="left", padx=5)

        self.btn_load_cache = ctk.CTkButton(self.button_group, text=_("LOAD_DATA"), fg_color="#1e1e1f", hover_color="#2a2a2b", border_width=1, border_color="#333333", width=150, height=45, font=ctk.CTkFont(size=11, weight="bold"), command=self.load_cache_action)
        self.btn_load_cache.pack(side="left", padx=5)
        
        self.btn_stop = ctk.CTkButton(self.button_group, text=_("STOP_ROBOT"), fg_color="#c42b1c", hover_color="#a22417", width=130, height=45, font=ctk.CTkFont(size=11, weight="bold"), command=self.stop_automation_action)
        self.btn_stop.pack(side="left", padx=5)

        # --- 4. TERMINAL AREA (Sol Alt - Satır 2) ---
        self.terminal_frame = ctk.CTkFrame(self, fg_color="#0a0a0b", corner_radius=15, border_width=1, border_color="#1a1a1b")
        self.terminal_frame.grid(row=2, column=0, padx=(30, 15), pady=(0, 30), sticky="nsew")
        self.terminal_frame.grid_columnconfigure(0, weight=1)
        self.terminal_frame.grid_rowconfigure(1, weight=1)

        self.term_header = ctk.CTkFrame(self.terminal_frame, fg_color="#161617", height=35, corner_radius=0)
        self.term_header.grid(row=0, column=0, sticky="ew")
        
        self.term_title = ctk.CTkLabel(self.term_header, text=_("SYSTEM_LOGS"), font=ctk.CTkFont(size=10, weight="bold"), text_color="#555555")
        self.term_title.pack(side="left", padx=15)

        self.btn_open_folder = ctk.CTkButton(self.term_header, text=_("OPEN_EXCEL_FOLDER"), fg_color="transparent", hover_color="#2a2a2b", width=130, height=25, font=ctk.CTkFont(size=10, weight="bold"), command=self.open_excel_folder)
        self.btn_open_folder.pack(side="right", padx=10)

        self.log_textbox = ctk.CTkTextbox(self.terminal_frame, corner_radius=0, font=ctk.CTkFont(family="Consolas", size=12), fg_color="transparent", text_color="#00ff41", border_width=0)
        self.log_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.log_textbox.configure(state="disabled")
  
        # --- ACTIONS ---

    def run_in_thread(self, target_func, *args):
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()
        AutomationState.current_thread_id = thread.ident 
        return thread

    def create_template_action(self):
        po = self.po_entry.get().strip()
        if po:
            logger.info(f"[ACTION] Triggering Excel Template creation for PO: {po}")
            self.run_in_thread(self.bridge.execute_workflow, po, False)
            
    def stop_automation_action(self):
        if AutomationState.force_stop():
            logger.info("Otomasyon kullanıcı tarafından anında kesildi.")
            
            # GUI Elemanlarını Sıfırla
            self.btn_run_selected.configure(state="normal", text=_("START_SELECTED_STEPS"))
            self.btn_template.configure(state="normal")
            self.status_indicator.configure(text=_("STOPPED_BY_USER"), text_color="#c42b1c")
            
            # Progress Bar'ı sıfırla (Opsiyonel)
            if hasattr(self, 'progress_bar'):
                self.progress_bar.set(0)
        else:
            logger.info("Şu an durdurulacak aktif bir süreç bulunamadı.")      

    def run_automation_action(self):
        po = self.po_entry.get().strip()
        if po:
            logger.info(f"[ACTION] Starting Full SAP Automation for PO: {po}")
            self.run_in_thread(self.bridge.execute_workflow, po, True)

    def open_excel_folder(self):
        # ConfigManager'daki çıktı yolunu al
        from src.util.config_manager import ConfigManager
        path = ConfigManager.OUTPUT_EXCEL_DIR
        
        # Klasör yoksa oluştur (Kullanıcı henüz hiç işlem yapmamış olabilir)
        if not os.path.exists(path): 
            os.makedirs(path)
            
        # Windows Explorer ile klasörü aç
        subprocess.Popen(f'explorer "{path}"')

    def update_header(self, po, style_name):
        """Bu metod logic_bridge'den çağrılır, başlığı günceller."""
        self.status_indicator.configure(text=_("ACTIVE_PO", po=po, style_name=style_name), text_color="#3b8ed0")
    
    def draw_workflow_steps(self, order_type, po_no, order_name):
        for widget in self.steps_container.winfo_children():
            widget.destroy()
        
        self.step_vars = {}
        self.step_indicators = {}
        self.collapsible_frames = {} 

        self.wf_title.configure(text=_("WORKFLOW_WITH_DETAILS", order_type=order_type, po_no=po_no, order_name=order_name.upper()))
        order_data = self.bridge.get_full_order_data(po_no)

        if order_type == "SET":
            childrens = order_data.get("childrens", []) if order_data else []
            self._create_section_label(_("ZMM0020_PROCESSES"))
            
            # ÇOCUKLAR: Adımlı (Açılır-Kapanır)
            for child in childrens:
                plm = child.get("plm_code")
                self._create_plm_group(_("PART") + f": {plm}", plm, is_main=False)
            
            # ANA SET: Basit (Tek Checkbox) - İsteğin üzerine sadeleşti
            main_plm = order_data.get("plm_code")
            self._create_step_cb(f"ZMM_MAIN_{main_plm}", _("MAIN_SET") + f": {main_plm} (ZMM0020)")

        else: # SINGLE
            self._create_section_label(_("ZMM0020_PROCESS"))
            plm = order_data.get("plm_code")
            # SINGLE'da ana ürünün adımları lazım olduğu için is_main=True
            self._create_plm_group(_("PRODUCT") + f": {plm}", plm, is_main=True)

        # ORTAK DİĞER ADIMLAR
        self._create_section_label(_("OTHER_OPERATIONS"))
        steps = [
            ("ZSD0010", "ZSD0010 - " + ("Sipariş Entegrasyonu" if get_language() == "TR" else "Order Integration")),
            ("MD01N", "MD01N - " + ("MRP Çalıştırma" if get_language() == "TR" else "MRP Run")),
            ("ZPP0030", "ZPP0030 - " + ("Üretim Takip" if get_language() == "TR" else "Production Tracking"))
        ]
        # SET ise CS01 ve MD01N ekle
        if order_type == "SET":
            steps.insert(0, ("CS01", "CS01 - " + ("Ürün Ağacı (BOM)" if get_language() == "TR" else "Bill of Materials (BOM)")))

        for sid, sname in steps:
            self._create_step_cb(sid, sname)

        self.btn_run_selected.configure(state="normal")        
    def _create_plm_group(self, label_text, plm_code, is_main=False):
        """is_main parametresi ID prefix'i için geri eklendi."""
        prefix = "ZMM_MAIN" if is_main else "ZMM_CHILD"
        group_id = f"{prefix}_{plm_code}"
        
        # ANA KONTEYNER (Kaymayı önleyen yapı)
        group_container = ctk.CTkFrame(self.steps_container, fg_color="transparent")
        group_container.pack(fill="x", pady=2)

        header_frame = ctk.CTkFrame(group_container, fg_color="transparent")
        header_frame.pack(fill="x")

        toggle_btn = ctk.CTkButton(header_frame, text="▼", width=20, height=20, 
                                   fg_color="transparent", text_color="#3b8ed0", font=("Arial", 12, "bold"))
        toggle_btn.pack(side="left", padx=(0, 5))
        toggle_btn.configure(command=lambda b=toggle_btn, gid=group_id: self._toggle_group(gid, b))

        master_var = ctk.BooleanVar(value=True)
        master_cb = ctk.CTkCheckBox(header_frame, text=label_text, variable=master_var, 
                                    font=ctk.CTkFont(size=12, weight="bold"),
                                    command=lambda: self._toggle_sub_steps(group_id, master_var.get()))
        master_cb.pack(side="left")

        sub_frame = ctk.CTkFrame(group_container, fg_color="transparent")
        sub_frame.pack(fill="x", padx=(45, 0))
        self.collapsible_frames[group_id] = sub_frame

        sub_steps = [
            _("ZMM0020_STEP1"),
            _("ZMM0020_STEP2"),
            _("ZMM0020_STEP3"),
            _("ZMM0020_STEP4")
        ]
        for i, name in enumerate(sub_steps, 1):
            self._create_step_cb(f"{group_id}_S{i}", f"{i}. {name}", container=sub_frame)

    def _toggle_group(self, group_id, btn):
        frame = self.collapsible_frames[group_id]
        if frame.winfo_viewable():
            frame.pack_forget()
            btn.configure(text="▶")
        else:
            frame.pack(fill="x", padx=(45, 0))
            btn.configure(text="▼")            
    def _toggle_sub_steps(self, group_id, value):
        for sid, var in self.step_vars.items():
            if sid.startswith(group_id):
                var.set(value)

    def _create_section_label(self, text):
        """Mavi başlık ekler"""
        lbl = ctk.CTkLabel(self.steps_container, text=text, font=ctk.CTkFont(size=11, weight="bold"), text_color="#3b8ed0")
        lbl.pack(pady=(12, 4), padx=10, anchor="w")

    def _create_step_cb(self, step_id, text, container=None):
        """Standart checkbox ve indikatör yapısı. Opsiyonel container desteği ekledik."""
        # Eğer bir container (sub_frame) verilmişse onu kullan, yoksa ana container'ı kullan
        parent = container if container else self.steps_container
        
        step_frame = ctk.CTkFrame(parent, fg_color="transparent")
        step_frame.pack(pady=2, padx=10, anchor="w")

        status_label = ctk.CTkLabel(step_frame, text="●", font=("Arial", 14), text_color="#555555")
        status_label.pack(side="left", padx=(0, 5))

        var = ctk.BooleanVar(value=True)
        cb = ctk.CTkCheckBox(step_frame, text=text, variable=var, font=ctk.CTkFont(size=11))
        cb.pack(side="left")

        self.step_vars[step_id] = var
        self.step_indicators[step_id] = status_label
    def run_selected_steps_action(self):
        """
        Seçili adımları checkbox'lardan toplar ve LogicBridge üzerinden 
        modüler robot akışını başlatır.
        """
        # 1. PO Numarasını Al ve Kontrol Et
        po = self.po_entry.get().strip()
        if not po:
            logger.warning("PO numarası boş olamaz!")
            # İstersen burada bir uyarı penceresi de açabilirsin:
            # messagebox.showwarning("Hata", "Lütfen bir PO numarası giriniz.")
            return

        # 2. Seçili Checkbox'ları Topla
        # self.step_vars sözlüğündeki BooleanVar'ları kontrol ediyoruz
        selected_steps = [sid for sid, var in self.step_vars.items() if var.get()]
        
        if not selected_steps:
            logger.warning("Çalıştırılacak hiçbir adım seçilmedi!")
            return

        # 3. Kullanıcıya Bilgi Ver
        logger.info(f"[MODÜLER AKIŞ] Başlatılıyor...")
        logger.info(f"Hedef PO: {po}")
        logger.info(f"Seçili Adımlar: {selected_steps}")

        # 4. Butonları Geçici Olarak Devre Dışı Bırak (Çakışmayı önlemek için)
        #self.btn_run_selected.configure(state="disabled", text="ROBOT ÇALIŞIYOR...")
        #self.btn_template.configure(state="disabled")

        # 5. Arka Planda (Thread) Modüler Akışı Başlat
        # LogicBridge içindeki execute_modular_workflow metodunu çağırıyoruz
        self.run_in_thread(
            self.bridge.execute_modular_workflow, 
            po, 
            selected_steps
        )
    def load_cache_action(self):
        po = self.po_entry.get().strip()
        if not po:
            logger.warning("Lütfen önce bir PO numarası giriniz!")
            return

        # Bridge üzerinden cache kontrolü yap
        order_type = self.bridge.check_cache_and_get_type(po)
        order_name = self.bridge.check_cache_and_get_orderName(po)

        if order_type:
            logger.info(f"[CACHE] {po} için yerel veri bulundu. Adımlar yükleniyor...")
            self.draw_workflow_steps(order_type, po, order_name)
        else:
            logger.error(f"[CACHE] {po} için yerel veri bulunamadı! Lütfen önce 'Create Excel Template' yapınız.")
            
    # DURUM GÜNCELLEME METODU (Bridge tarafından çağrılacak)
    def update_ui_status(self, step_id, status, progress_val=None):
        """
        status: 'pending', 'running', 'success', 'error'
        progress_val: 0.0 ile 1.0 arası
        """
        colors = {
            "pending": "#555555", # Gri
            "running": "#3b8ed0", # Mavi
            "success": "#14a44d", # Yeşil
            "error": "#c42b1c"    # Kırmızı
        }

        if step_id in self.step_indicators:
            self.step_indicators[step_id].configure(text_color=colors.get(status, "#555555"))

        if progress_val is not None:
            self.progress_bar.set(progress_val)