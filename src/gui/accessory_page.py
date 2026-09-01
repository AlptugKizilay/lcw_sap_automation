import customtkinter as ctk
import logging
from tkinter import ttk, messagebox
import tkinter as tk
from tksheet import Sheet

from src.logic_bridge import AutomationBridge
from src.util.material_cache import MaterialCache
from src.util.localizer import _, get_language

logger = logging.getLogger(__name__)

class AccessoryPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.bridge = AutomationBridge()
        self.cache = MaterialCache()
        self.variable_entries = []

        # ==========================================
        # MODERN UI/UX TASARIM SİSTEMİ (KOMPAKT VERSİYON)
        # ==========================================
        self.theme = {
            "bg_color": "transparent",
            "card_color": "#27272a",
            "text_main": "#f4f4f5",
            "text_muted": "#a1a1aa",
            "primary": "#2563eb",
            "primary_hover": "#1d4ed8",
            "secondary": "#3f3f46",
            "secondary_hover": "#52525b",
            "danger": "#7f1d1d",
            "danger_hover": "#991b1b",
            "border": "#3f3f46",
            "input_height": 28,        # Eskiden 36'ydı, daraltıldı
            "action_height": 32        # Alt butonlar için biraz daha büyük yükseklik
        }

        # Fontlar Küçültüldü
        self.font_title = ctk.CTkFont(size=13, weight="bold")
        self.font_label = ctk.CTkFont(size=12, weight="bold")
        self.font_normal = ctk.CTkFont(size=12)

        self.configure(fg_color=self.theme["bg_color"])

        # ==========================================
        # BLOCK 1: GENEL BİLGİLER
        # ==========================================
        self.block1_frame = ctk.CTkFrame(self, fg_color=self.theme["card_color"], corner_radius=6)
        self.block1_frame.pack(fill="x", padx=15, pady=(15, 5)) # padding daraltıldı
        
        ctk.CTkLabel(self.block1_frame, text=_("GENERAL_INFO"), font=self.font_title, text_color=self.theme["text_main"]).pack(anchor="w", padx=15, pady=(8,0))
        
        self.info_frame = ctk.CTkFrame(self.block1_frame, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkLabel(self.info_frame, text="PO No:", font=self.font_label, text_color=self.theme["text_muted"]).grid(row=0, column=0, padx=(0,5), pady=2, sticky="w")
        self.entry_po = ctk.CTkEntry(self.info_frame, width=120, height=self.theme["input_height"], border_color=self.theme["border"])
        self.entry_po.grid(row=0, column=1, padx=(0,10), pady=2)
        
        self.btn_fetch = ctk.CTkButton(self.info_frame, text=_("FETCH_MODEL"), width=90, height=self.theme["input_height"], 
                                       fg_color=self.theme["secondary"], hover_color=self.theme["secondary_hover"], font=self.font_normal,
                                       command=self.fetch_model_info)
        self.btn_fetch.grid(row=0, column=2, padx=(0,20), pady=2)

        ctk.CTkLabel(self.info_frame, text=_("MODEL_NAME"), font=self.font_label, text_color=self.theme["text_muted"]).grid(row=0, column=3, padx=(0,5), pady=2, sticky="w")
        self.entry_model = ctk.CTkEntry(self.info_frame, width=280, height=self.theme["input_height"], border_color=self.theme["border"])
        self.entry_model.grid(row=0, column=4, padx=(0,10), pady=2)

        # ==========================================
        # BLOCK 2: MALZEME SPESİFİKASYONLARI
        # ==========================================
        self.block2_frame = ctk.CTkFrame(self, fg_color=self.theme["card_color"], corner_radius=6)
        self.block2_frame.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(self.block2_frame, text=_("MATERIAL_SPECS"), font=self.font_title, text_color=self.theme["text_main"]).pack(anchor="w", padx=15, pady=(8,0))

        self.type_frame = ctk.CTkFrame(self.block2_frame, fg_color="transparent")
        self.type_frame.pack(fill="x", padx=15, pady=(5, 2))
        
        ctk.CTkLabel(self.type_frame, text=_("MATERIAL_TYPE"), font=self.font_label, text_color=self.theme["text_muted"]).grid(row=0, column=0, padx=(0,5), sticky="w")
        combo_vals = ["Select", "Zipper", "Cord", "Button", "Care Label"] if get_language() == "EN" else ["Seçiniz", "Fermuar", "Kordon", "Düğme", "Yıkama Talimatı"]
        self.combo_type = ctk.CTkComboBox(self.type_frame, values=combo_vals, 
                                          width=130, height=self.theme["input_height"], border_color=self.theme["border"],
                                          command=self.on_type_select)
        self.combo_type.grid(row=0, column=1, padx=(0,20))
        self.combo_type.set(combo_vals[0])

        ctk.CTkLabel(self.type_frame, text=_("PLANT"), font=self.font_label, text_color=self.theme["text_muted"]).grid(row=0, column=2, padx=(0,5), sticky="w")
        self.entry_plant = ctk.CTkEntry(self.type_frame, width=80, height=self.theme["input_height"], border_color=self.theme["border"])
        self.entry_plant.grid(row=0, column=3, padx=(0,20))
        self.entry_plant.insert(0, "2000")

        ctk.CTkLabel(self.type_frame, text=_("UNIT_PRICE"), font=self.font_label, text_color=self.theme["text_muted"]).grid(row=0, column=4, padx=(0,5), sticky="w")
        self.entry_price = ctk.CTkEntry(self.type_frame, width=80, height=self.theme["input_height"], border_color=self.theme["border"])
        self.entry_price.grid(row=0, column=5)
        self.entry_price.insert(0, "0.50")

        self.dynamic_form_container = ctk.CTkFrame(self.block2_frame, fg_color="transparent", height=0)
        self.dynamic_form_container.pack(fill="x", padx=15, pady=(5, 10))        

        # ==========================================
        # BLOCK 3: TABLO VE AKSİYONLAR
        # ==========================================
        self.table_frame = ctk.CTkFrame(self, fg_color=self.theme["card_color"], corner_radius=6)
        self.table_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        ctk.CTkLabel(self.table_frame, text=_("MATERIALS_PREVIEW"), font=self.font_title, text_color=self.theme["text_main"]).pack(anchor="w", padx=15, pady=(8, 2))

        self.sheet = Sheet(self.table_frame, theme="dark")
        self.sheet.pack(fill="both", expand=True, padx=15, pady=(0,10))
        sheet_headers = ["Type", "SAP Code", "Material Description", "Model Name", "Price", "Plant"] if get_language() == "EN" else ["Tür", "SAP Kodu", "Malzeme Tanımı", "Model Adı", "Fiyat", "Üretim Yeri"]
        self.sheet.headers(sheet_headers)
        self.sheet.set_column_widths([100, 130, 400, 180, 80, 100]) # Sütunlar da biraz daraltıldı
        self.sheet.enable_bindings(("single_select", "drag_select", "column_select", "row_select", "column_width_resize", "row_height_resize", "copy", "cut", "paste", "delete", "undo", "edit_cell", "right_click_popup_menu", "rc_select", "ctrl_click_select"))

        # --- ALT BUTONLAR (BİRAZ DAHA YÜKSEK, ACTION_HEIGHT) ---
        self.table_action_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        self.table_action_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.left_action_frame = ctk.CTkFrame(self.table_action_frame, fg_color="transparent")
        self.left_action_frame.pack(side="left")

        self.btn_delete_row = ctk.CTkButton(self.left_action_frame, text=_("DELETE_SELECTED_ROWS"), fg_color=self.theme["danger"], hover_color=self.theme["danger_hover"], height=self.theme["action_height"], command=self.delete_selected_row)
        self.btn_delete_row.pack(side="left", padx=(0, 10))

        self.btn_export_excel = ctk.CTkButton(self.left_action_frame, text=_("EXPORT_TO_EXCEL"), fg_color=self.theme["secondary"], hover_color=self.theme["secondary_hover"], height=self.theme["action_height"], command=self.export_to_excel)
        self.btn_export_excel.pack(side="left", padx=(0, 10))        

        self.btn_show_cache = ctk.CTkButton(self.left_action_frame, text=_("MEMORY_HISTORY"), fg_color=self.theme["secondary"], hover_color=self.theme["secondary_hover"], height=self.theme["action_height"], command=self.show_cache_window)
        self.btn_show_cache.pack(side="left")

        self.right_action_frame = ctk.CTkFrame(self.table_action_frame, fg_color="transparent")
        self.right_action_frame.pack(side="right")

        self.btn_reset = ctk.CTkButton(self.right_action_frame, text=_("RESET"), fg_color=self.theme["secondary"], hover_color=self.theme["secondary_hover"], height=self.theme["action_height"], command=self.reset_page)
        self.btn_reset.pack(side="left", padx=(0, 10))

        self.btn_run_sap = ctk.CTkButton(self.right_action_frame, text=_("CREATE_IN_SAP"), fg_color=self.theme["primary"], hover_color=self.theme["primary_hover"], font=self.font_title, height=self.theme["action_height"], command=self.run_sap_creation)
        self.btn_run_sap.pack(side="left")        
        
    # --- DİNAMİK FORM FONKSİYONLARI ---

    def on_type_select(self, selected_type):
        for widget in self.dynamic_form_container.winfo_children():
            widget.destroy()
        self.variable_entries.clear()
        self.variable_frames = []

        mapped_type = selected_type
        if selected_type in ["Fermuar", "Zipper"]:
            mapped_type = "Fermuar"
        elif selected_type in ["Kordon", "Cord"]:
            mapped_type = "Kordon"
        elif selected_type in ["Düğme", "Button"]:
            mapped_type = "Düğme"
        elif selected_type in ["Yıkama Talimatı", "Care Label"]:
            mapped_type = "Yıkama Talimatı"

        if mapped_type in ["Fermuar", "Kordon"]:
            self.draw_smart_form(mapped_type)
        elif mapped_type == "Düğme":
            self.draw_button_form()
        elif mapped_type == "Yıkama Talimatı":
            self.draw_care_label_form()

    def add_variable_row(self, is_first=False, entry_width=100, default_text=""):
        # parent olarak artık vars_container kullanıyoruz
        row_frame = ctk.CTkFrame(self.vars_container, fg_color="transparent")
        
        entry = ctk.CTkEntry(row_frame, width=entry_width, height=self.theme["input_height"], border_color=self.theme["border"])
        entry.pack(side="left", padx=(0, 5))
        if default_text: 
            entry.insert(0, default_text)
            
        self.variable_entries.append(entry)
        self.variable_frames.append(row_frame) # Satırın kendisini de hafızaya alıyoruz

        if is_first:
            btn = ctk.CTkButton(row_frame, text="+", width=self.theme["input_height"], height=self.theme["input_height"], 
                                fg_color=self.theme["secondary"], hover_color=self.theme["secondary_hover"], font=self.font_title, 
                                command=lambda: self.add_variable_row(is_first=False, entry_width=entry_width))
        else:
            btn = ctk.CTkButton(row_frame, text="-", width=self.theme["input_height"], height=self.theme["input_height"], 
                                fg_color=self.theme["danger"], hover_color=self.theme["danger_hover"], font=self.font_title, 
                                command=lambda f=row_frame, e=entry: self.remove_variable_row(f, e))
        btn.pack(side="left")        
        
        # Elementi ekledikten sonra gridi yeniden hesapla
        self.refresh_variable_grid()

    def remove_variable_row(self, row_frame, entry):
        row_frame.destroy()
        if entry in self.variable_entries: 
            self.variable_entries.remove(entry)
        if row_frame in self.variable_frames:
            self.variable_frames.remove(row_frame)
            
        # Element silindikten sonra gridi yeniden hesapla ki boşluk kapansın
        self.refresh_variable_grid()
            
    def draw_smart_form(self, type_name):
        ctk.CTkLabel(self.dynamic_form_container, text=_("PREFIX"), text_color=self.theme["text_muted"], font=self.font_label).grid(row=0, column=0, sticky="w", padx=(0,10), pady=(0, 2))
        ctk.CTkLabel(self.dynamic_form_container, text=_("VARIABLES"), text_color=self.theme["text_muted"], font=self.font_label).grid(row=0, column=1, sticky="w", padx=(0,10), pady=(0, 2))
        ctk.CTkLabel(self.dynamic_form_container, text=_("SUFFIX"), text_color=self.theme["text_muted"], font=self.font_label).grid(row=0, column=2, sticky="w", padx=(0,10), pady=(0, 2))

        self.entry_prefix = ctk.CTkEntry(self.dynamic_form_container, width=250, height=self.theme["input_height"], border_color=self.theme["border"])
        self.entry_prefix.grid(row=1, column=0, sticky="nw", padx=(0,10))

        # --- YENİ EKLENDİ: Artık Scrollable değil, düz şeffaf Frame ---
        self.vars_container = ctk.CTkFrame(self.dynamic_form_container, fg_color="transparent")
        self.vars_container.grid(row=1, column=1, sticky="nw", padx=(0,10))
        self.add_variable_row(is_first=True, entry_width=100)

        self.entry_suffix = ctk.CTkEntry(self.dynamic_form_container, width=210, height=self.theme["input_height"], border_color=self.theme["border"], placeholder_text="Örn: CM ZIPPER" if get_language() == "TR" else "e.g. CM ZIPPER")
        self.entry_suffix.grid(row=1, column=2, sticky="nw", padx=(0,10))

        self.btn_generate = ctk.CTkButton(self.dynamic_form_container, text=_("ADD_TO_LIST"), fg_color=self.theme["secondary"], hover_color=self.theme["secondary_hover"], font=self.font_normal, width=90, height=self.theme["input_height"], command=lambda: self.test_generate(mode="smart"))
        self.btn_generate.grid(row=1, column=3, sticky="nw")

    def draw_button_form(self):
        ctk.CTkLabel(self.dynamic_form_container, text=_("MATERIAL_FULL_DESC"), text_color=self.theme["text_muted"], font=self.font_label).grid(row=0, column=0, sticky="w", padx=(0,10), pady=(0, 2))

        self.vars_container = ctk.CTkFrame(self.dynamic_form_container, fg_color="transparent")
        self.vars_container.grid(row=1, column=0, sticky="nw", padx=(0,10))
        self.add_variable_row(is_first=True, entry_width=250, default_text="")

        self.btn_generate = ctk.CTkButton(self.dynamic_form_container, text=_("ADD_TO_LIST"), fg_color=self.theme["secondary"], hover_color=self.theme["secondary_hover"], font=self.font_normal, width=90, height=self.theme["input_height"], command=lambda: self.test_generate(mode="direct"))
        self.btn_generate.grid(row=1, column=1, sticky="nw")

    def draw_care_label_form(self):
        ctk.CTkLabel(self.dynamic_form_container, text=_("MATERIAL_FULL_DESC"), text_color=self.theme["text_muted"], font=self.font_label).grid(row=0, column=0, sticky="w", padx=(0,10), pady=(0, 2))

        self.vars_container = ctk.CTkFrame(self.dynamic_form_container, fg_color="transparent")
        self.vars_container.grid(row=1, column=0, sticky="nw", padx=(0,10))
        
        model_name = self.entry_model.get().strip()
        default_val = f"{model_name} CARE LABEL" if model_name else "CARE LABEL"
        self.add_variable_row(is_first=True, entry_width=250, default_text=default_val)

        self.btn_generate = ctk.CTkButton(self.dynamic_form_container, text=_("ADD_TO_LIST"), fg_color=self.theme["secondary"], hover_color=self.theme["secondary_hover"], font=self.font_normal, width=90, height=self.theme["input_height"], command=lambda: self.test_generate(mode="direct"))
        self.btn_generate.grid(row=1, column=1, sticky="nw")
                
    def refresh_variable_grid(self):
        """Değişkenleri sayar ve max_rows limitine göre sütunlara yayar (Flex-wrap mantığı)."""
        max_rows = 3  # Her sütunda maksimum kaç satır olacağını buradan belirleyebilirsin.
        
        for index, frame in enumerate(self.variable_frames):
            col_index = index // max_rows
            row_index = index % max_rows
            # .grid() mevcut elementi yok etmeden yeni koordinatlarına taşır
            frame.grid(row=row_index, column=col_index, sticky="nw", padx=(0, 15), pady=(0, 5))
        
             
    def fetch_model_info(self):
        po = self.entry_po.get().strip()
        if not po:
            logger.warning(_("FETCH_PO_WARNING"))
            return
        
        # Bridge üzerinden tüm JSON verisini çekiyoruz (Tek okumada her şeyi alır)
        order_data = self.bridge.get_full_order_data(po)
        
        # İçlerini temizle
        self.entry_model.delete(0, "end")
        self.entry_plant.delete(0, "end")
        
        if order_data:
            # 1. MODEL ADI (styleName)
            order_name = order_data.get("styleName", "")
            if order_name:
                self.entry_model.insert(0, order_name.upper())
                
            # 2. ÜRETİM YERİ (sale_group)
            sale_group = order_data.get("sale_group", "")
            if sale_group:
                self.entry_plant.insert(0, str(sale_group))
            else:
                self.entry_plant.insert(0, "2000") # Bulamazsa varsayılan 2000 kalsın
            
            # PO değiştiği için eski tablo verilerini tamamen temizle!
            self.sheet.set_sheet_data([])
            sheet_headers = ["Type", "SAP Code", "Material Description", "Model Name", "Price", "Plant"] if get_language() == "EN" else ["Tür", "SAP Kodu", "Malzeme Tanımı", "Model Adı", "Fiyat", "Üretim Yeri"]
            self.sheet.headers(sheet_headers)
            self.sheet.set_column_widths([120, 150, 450, 200, 100, 120]) # Genişlikler de korunsun
            
            # YENİ: Combobox'ı ve dinamik alanları sıfırla
            default_val = "Select" if get_language() == "EN" else "Seçiniz"
            self.combo_type.set(default_val)
            self.on_type_select(default_val) 

            logger.info(f"Accessory: model name and plant loaded for {po}.")
        else:
            # Json yoksa manuel girilmesi için varsayılan yeri doldur
            self.entry_plant.insert(0, "2000")
            logger.error(_("FETCH_CACHE_ERROR", po=po))

    def auto_load_po(self, po_no):
        """Dashboard'dan gelen aktif PO'yu otomatik yazar ve modeli yükler."""
        current_po = self.entry_po.get().strip()
        
        # Eğer sayfa zaten bu PO'yu yüklemişse boşuna tekrar JSON okumasına gerek yok
        if current_po != po_no:
            # Kutuyu temizle ve yeni PO'yu yaz
            self.entry_po.delete(0, "end")
            self.entry_po.insert(0, po_no)
            
            # Sanki kullanıcı "Model Getir" butonuna basmış gibi otomatik tetikle
            logger.info(_("PO_AUTO_LOAD"))
            self.fetch_model_info() 
                           
    def test_generate(self, mode="smart"):
        """Varyantları Üretir, Karakter Sınırını ve Mükerrer Kontrolü Yapar, Sheet'e Ekler"""
        variables = [e.get().strip() for e in self.variable_entries if e.get().strip() != ""]
        model = self.entry_model.get().strip().upper()
        fiyat = self.entry_price.get().strip()
        uretim_yeri = self.entry_plant.get().strip()
        tur = self.combo_type.get()
        
        if not variables:
            logger.warning(_("EMPTY_RECORD_ERROR"))
            return
            
        # --- 1. GENİŞLİKLERİ HAFIZAYA AL ---
        current_widths = self.sheet.get_column_widths()
        if not current_widths:
            current_widths = [120, 150, 450, 200, 100, 120]

        # --- 2. TANIMLARI OLUŞTUR VE 40 KARAKTER KONTROLÜ YAP ---
        yeni_tanimlar = []
        hatali_tanimlar = [] # 40 karakteri aşanları burada toplayacağız

        if mode == "smart":
            prefix = self.entry_prefix.get().strip()
            suffix = self.entry_suffix.get().strip()
            for var in variables:
                tanim = f"{prefix} {var} {suffix}".strip().upper()
                tanim = " ".join(tanim.split()) # Aradaki fazladan boşlukları teke düşür
                
                if len(tanim) > 40:
                    hatali_tanimlar.append(tanim)
                else:
                    yeni_tanimlar.append(tanim)
                    
        elif mode == "direct":
            for var in variables:
                tanim = var.strip().upper()
                tanim = " ".join(tanim.split())
                
                if len(tanim) > 40:
                    hatali_tanimlar.append(tanim)
                else:
                    yeni_tanimlar.append(tanim)

        # EĞER 40 KARAKTERİ AŞAN VARSA İŞLEMİ DURDUR VE KULLANICIYI UYAR!
        if hatali_tanimlar:
            details = "\n".join([f"❌ {t} ({len(t)} chars)" for t in hatali_tanimlar])
            hata_mesaji = _("CHAR_LIMIT_EXCEEDED_MSG", details=details)
            messagebox.showerror(_("CHAR_LIMIT_EXCEEDED"), hata_mesaji)
            return # İşlemi burada kes, tabloya ekleme yapma!

        # --- 3. MÜKERRER KONTROLÜ VE CACHE KONTROLÜ ---
        current_data = self.sheet.get_sheet_data()
        existing_items = [str(row[2]).upper() for row in current_data if len(row) > 2]
            
        eklenen_sayi = 0
        atlanilan_sayi = 0
        hazir_sayisi = 0

        for tanim in yeni_tanimlar:
            if tanim in existing_items:
                atlanilan_sayi += 1
                continue
            
            # CACHE (HAFIZA) KONTROLÜ
            cached_data = self.cache.get_material(tanim)
            
            if cached_data:
                # Hafızada varsa koduyla birlikte ekle!
                matnr = cached_data["matnr"]
                current_data.append([tur, matnr, tanim, model, fiyat, uretim_yeri])
                hazir_sayisi += 1
            else:
                # Hafızada yoksa yeni açılacak olarak (-) ekle
                current_data.append([tur, "-", tanim, model, fiyat, uretim_yeri])
            
            existing_items.append(tanim)
            eklenen_sayi += 1

        # --- 4. TABLOYU GÜNCELLE VE FORMATI YENİDEN KUR ---
        self.sheet.set_sheet_data(current_data)
        sheet_headers = ["Type", "Material Code", "Material Description", "Model Name", "Price", "Plant"] if get_language() == "EN" else ["Tür", "Malzeme Kodu", "Malzeme Tanımı", "Model Adı", "Fiyat", "Üretim Yeri"]
        self.sheet.headers(sheet_headers)
        self.sheet.set_column_widths(current_widths)
                
        # Bilgi Mesajını Güncelledik
        mesaj = _("DUPLICATE_CHECK_MSG", added=eklenen_sayi, skipped=atlanilan_sayi, cached=hazir_sayisi)
        messagebox.showinfo(_("DUPLICATE_CHECK_INFO"), mesaj)            
            
    def delete_selected_row(self):
        """Kullanıcının seçtiği satırları sheet'ten siler"""
        selected_rows = list(self.sheet.get_selected_rows())
        if not selected_rows:
            messagebox.showwarning(_("DUPLICATE_CHECK_INFO"), _("DELETE_ROW_WARNING"))
            return
            
        # İndex kaymasını önlemek için tersten siliyoruz
        selected_rows.sort(reverse=True)
        for row_idx in selected_rows:
            self.sheet.delete_row(row_idx)
            
        logger.info("Accessory: Seçili satırlar sheet üzerinden silindi.")

    def export_to_excel(self):
        """Sheet üzerindeki verileri CSV olarak kaydeder"""
        import csv
        from tkinter import filedialog

        current_data = self.sheet.get_sheet_data()
        if not current_data:
            messagebox.showwarning("Boş Tablo" if get_language() != "EN" else "Empty Table", _("NO_DATA_TO_EXPORT"))
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Excel CSV File" if get_language() == "EN" else "Excel CSV Dosyası", "*.csv")],
            title=_("SAVE_CSV_TITLE"),
            initialfile=f"Materials_{self.entry_po.get().strip() or 'List'}.csv" if get_language() == "EN" else f"Malzemeler_{self.entry_po.get().strip() or 'Liste'}.csv"
        )

        if not file_path:
            return

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(["Type", "Material Code", "Material Description", "Model Name", "Price", "Plant"] if get_language() == "EN" else ["Tur", "Malzeme Kodu", "Malzeme Tanimi", "Model Adi", "Fiyat", "Uretim Yeri"])
                for row in current_data:
                    writer.writerow(row)
            messagebox.showinfo(_("SAVE_CSV_SUCCESS").split("\n")[0], _("SAVE_CSV_SUCCESS", path=file_path))
        except Exception as e:
            messagebox.showerror(_("SAVE_CSV_ERROR").split(":")[0], _("SAVE_CSV_ERROR", error=str(e)))


    def run_sap_creation(self):
        """Tablodaki boş olan satırları alır ve tek tek SAP'de yaratır"""
        current_data = self.sheet.get_sheet_data()
        if not current_data:
            messagebox.showwarning("Boş Tablo" if get_language() != "EN" else "Empty Table", _("NO_DATA_TO_EXPORT"))
            return
            
        # Sadece Malzeme Kodu "-" olanları (Henüz yaratılmamış olanları) bul
        to_process = [i for i, row in enumerate(current_data) if str(row[1]).strip() == "-"]
        
        if not to_process:
            messagebox.showinfo(_("DUPLICATE_CHECK_INFO"), "SAP'ye gönderilecek yeni malzeme bulunamadı. Tümü zaten oluşturulmuş." if get_language() != "EN" else "No new materials to send to SAP. All are already created.")
            return
            
        if not messagebox.askyesno(_("SAP_CONFIRM_TITLE"), _("SAP_CONFIRM_MSG", count=len(to_process))):
            return
            
        basarili_sayisi = 0
        hatali_sayisi = 0
        
        # Seçilen satırları tek tek döndür
        for row_idx in to_process:
            row = current_data[row_idx]
            
            # Veriyi Dictionary (Sözlük) formatına çevir ki bridge ve handler anlayabilsin
            data_dict = {
                "tur": row[0],
                "tanim": row[2],
                "model": row[3],
                "fiyat": row[4],
                "uretim_yeri": row[5]
            }
            
            # "İşleniyor..." yazısı gösterelim ki kullanıcı anlasın
            self.sheet.set_cell_data(row_idx, 1, "Processing..." if get_language() == "EN" else "İşleniyor...")
            self.update() # Arayüzü donmadan anlık yenile
            
            # SAP Botunu Köprü Üzerinden Çağır!
            result = self.bridge.create_accessory_in_sap(data_dict)
            
            if result.get("status") == "success":
                matnr = result.get("matnr")
                # Başarılı olursa SAP'den dönen gerçek kodu yaz!
                self.sheet.set_cell_data(row_idx, 1, matnr)
                self.cache.add_material(
                    tanim=row[2], 
                    matnr=matnr, 
                    tur=row[0], 
                    model=row[3]
                )
                
                basarili_sayisi += 1
            else:
                hata = result.get('message', 'Bilinmeyen Hata')
                # Hata olursa "HATA!" yaz
                self.sheet.set_cell_data(row_idx, 1, "ERROR!" if get_language() == "EN" else "HATA!")
                logger.error(f"Accessory: SAP Hatası ({row[2]}): {hata}")
                hatali_sayisi += 1
                
            # Tabloyu her satır işleminde tazele
            self.update()
            
        # Tüm döngü bitince rapor ver
        mesaj = _("SAP_REPORT_MSG", success=basarili_sayisi, failed=hatali_sayisi)
        if hatali_sayisi > 0:
            mesaj += "\n" + ("Hatalı kayıtların detayları için loglara bakınız." if get_language() != "EN" else "Please check logs for error details.")
        messagebox.showinfo(_("SAP_REPORT_TITLE"), mesaj)


    def show_cache_window(self):
        """Cache dosyasındaki kayıtları okur, arama/filtreleme özellikli bir pop-up ekranda gösterir"""
        cache_data = self.cache.cache # Dict objesini al
        
        if not cache_data:
            messagebox.showinfo(_("DUPLICATE_CHECK_INFO"), _("NO_MEMORY_RECORDS"))
            return

        # 1. Pop-up Pencereyi Oluştur
        top = ctk.CTkToplevel(self)
        top.title(_("MEMORY_HISTORY_TITLE")) # Emoji kaldırıldı, sadeleştirildi
        top.geometry("1000x600") 
        top.transient(self) 
        top.grab_set() 
        
        # --- TEMA UYGULAMASI (Arka planı ana pencereyle aynı zifiri/koyu gri yapıyoruz) ---
        top.configure(fg_color="#09090b") 

        # --- BAŞLIK ---
        lbl_title = ctk.CTkLabel(top, text=_("MEMORY_HISTORY_SUMMARY", total=len(cache_data)), 
                                 font=ctk.CTkFont(size=15, weight="bold"), text_color="#f4f4f5")
        lbl_title.pack(anchor="w", padx=20, pady=(20, 10))

        # --- ARAMA (FİLTRELEME) ÇUBUĞU ---
        search_frame = ctk.CTkFrame(top, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 15))

        lbl_search = ctk.CTkLabel(search_frame, text=_("CANLIVE_SEARCH"), font=ctk.CTkFont(size=13, weight="bold"), text_color="#a1a1aa")
        lbl_search.pack(side="left", padx=(0, 10))

        search_var = ctk.StringVar()
        
        # Arama kutusu modernleştirildi (Ana sayfadaki input_height gibi 32px yapıldı)
        entry_search = ctk.CTkEntry(search_frame, textvariable=search_var, width=400, height=32, 
                                    placeholder_text=_("SEARCH_PLACEHOLDER"),
                                    border_color="#3f3f46", fg_color="#18181b", text_color="#f4f4f5")
        entry_search.pack(side="left")

        # Buton modernleştirildi
        btn_clear = ctk.CTkButton(search_frame, text=_("CLEAR"), width=90, height=32, 
                                  fg_color="#3f3f46", hover_color="#52525b", font=ctk.CTkFont(size=12),
                                  command=lambda: search_var.set(""))
        btn_clear.pack(side="left", padx=10)

        # 2. BÜTÜN VERİYİ TABLO FORMATINA ÇEVİR
        full_table_rows = []
        for tanim, detay in cache_data.items():
            full_table_rows.append([
                detay.get("tur", "-"),
                detay.get("matnr", "-"),
                tanim,
                detay.get("model", "-"),
                detay.get("created_at", "-")
            ])
            
        full_table_rows.reverse() 

        # 3. TABLOYU ÇİZ
        from tksheet import Sheet 
        
        # Tablonun etrafına şık bir kart (card) çerçevesi çiziyoruz
        sheet_frame = ctk.CTkFrame(top, fg_color="#27272a", corner_radius=8)
        sheet_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # --- TKSHEET KARANLIK TEMA (BEYAZLIĞI ÇÖZEN KISIM: theme="dark") ---
        cache_sheet = Sheet(sheet_frame, data=full_table_rows, theme="dark")
        
        cache_sheet.enable_bindings(
            "single_select", "drag_select", "row_select", "column_width_resize",
            "arrowkeys", "right_click_popup_menu", "rc_select", "copy", "ctrl_click_select"
        )
        
        # Çerçevenin kenar yuvarlaklıkları belli olsun diye tablonun etrafında 2px boşluk bırakıyoruz
        cache_sheet.pack(fill="both", expand=True, padx=2, pady=2)

        cache_sheet.headers(["Type", "SAP Code", "Material Description", "Model Name", "Record Date"] if get_language() == "EN" else ["Tür", "SAP Kodu", "Malzeme Tanımı", "Model Adı", "Kayıt Tarihi"])
        
        # Sütun Genişliklerini Sabit Bir Değişkene Alıyoruz
        standart_genislikler = [120, 150, 350, 150, 150]
        cache_sheet.set_column_widths(standart_genislikler)
        cache_sheet.readonly_columns(columns=[0, 1, 2, 3, 4])

        # =======================================================
        # 4. CANLI ARAMA / FİLTRELEME MANTIĞI
        # =======================================================
        def on_search_change(*args):
            query = search_var.get().strip().lower()
            
            if not query:
                # Kutu boşsa tüm veriyi geri yükle ama SÜTUNLARA DOKUNMA!
                cache_sheet.set_sheet_data(
                    full_table_rows, 
                    reset_col_positions=False, 
                    reset_row_positions=False
                )
                lbl_title.configure(text=_("MEMORY_HISTORY_SUMMARY", total=len(full_table_rows)))
                return
            
            filtered_rows = []
            for row in full_table_rows:
                if any(query in str(cell).lower() for cell in row):
                    filtered_rows.append(row)
            
            # Filtreli veriyi yükle ama SÜTUNLARA DOKUNMA!
            cache_sheet.set_sheet_data(
                filtered_rows, 
                reset_col_positions=False, 
                reset_row_positions=False
            )
            lbl_title.configure(text=_("SEARCH_RESULTS", count=len(filtered_rows)))

        search_var.trace_add("write", on_search_change)
        
    def reset_page(self):
        """Tüm girişleri ve tabloyu temizler, ekranı ilk haline döndürür"""
        # 1. PO ve Model bilgisini temizle
        self.entry_po.delete(0, 'end')
        self.entry_model.configure(state="normal")
        self.entry_model.delete(0, 'end')
        self.entry_model.configure(state="normal")
        
        # 2. Combobox'ı sıfırla ve alt özellikleri temizle
        default_val = "Select" if get_language() == "EN" else "Seçiniz"
        self.combo_type.set(default_val)
        self.on_type_select(default_val)
        
        # 3. Tabloyu Sıfırla VE GENİŞLİKLERİ KİLİTLE!
        self.sheet.set_sheet_data([])
        sheet_headers = ["Type", "SAP Code", "Material Description", "Model Name", "Price", "Plant"] if get_language() == "EN" else ["Tür", "SAP Kodu", "Malzeme Tanımı", "Model Adı", "Fiyat", "Üretim Yeri"]
        self.sheet.headers(sheet_headers)
        
        # Kendi varsayılan genişliklerine geri set ediyoruz
        self.sheet.set_column_widths([120, 150, 450, 200, 100, 120])
        
