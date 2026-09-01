# src/util/localizer.py

import logging
from src.util.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# KTSCH Codes to localized names mapping
KTSCH_TR = {
    "1000001": "Harici Dikim", "1000002": "Harici Dış Kesim", "1000003": "Harici Ütü Paket",
    "1000005": "Harici Baskı", "1000006": "Harici Biye Kesim", "1000007": "Harici Yıkama",
    "1000008": "Harici Nakış", "1000009": "Harici Çıtçıt", "1000010": "Harici İlik Düğme",
    "1000011": "Harici El İşçiliği", "1000012": "Harici Special Dikiş",
    "1000016": "APLIKE KESİM", "1000017": "POPLİN KESİM", "1000018": "ANA BEDEN KESİM",
    "1000019": "KOL UCU KESİM", "1000020": "YAKA KESİM", "1000021": "suprem kesim",
    "1000024": "oxford kesim", "1000027": "ribana kesim", "1000049": "ön beden kesim",
    "1000055": "pike kesim", "1000067": "pat kesim", "1000073": "alt pat kesim",
    "1000090": "kaskorse kesim", "1000104": "ic yaka kesim", "1000132": "kesim",
    "1000135": "dantel kesim", "1000183": "kemer kesim", "1000185": "astar kesim",
    "1000193": "garni kesim", "1000197": "ceplik kesim", "1000237": "YIKAMA",
    "1000241": "ilik düğme", "1000267": "aplike nakış", "1000271": "ÖN BASKI",
    "1000509": "tela kesim", "1000517": "tül kesim", "1000790": "cep kesim",
    "1001055": "pano kesim", "1001105": "pano baskı", "1001110": "Ara dikim",
    "1001381": "Dahili Kesim", "1001382": "JUT TEMİZLEME", "1001383": "Dahili Biye Kesim",
    "1001385": "Dahili Dikim", "1001386": "dahili yikama", "1001387": "Dahili UKP",
    "1001388": "Örgü", "1001389": "Rosso", "1001390": "Formahane", "1001391": "Jardon",
    "1001392": "Overlok", "1001393": "parça boya", "1001394": "elyaf dolum",
    "ZQM001": "Aksesuar Depo Kalite isyeri", "ZQM002": "Aksesuar Satınalma Kalite İş",
    "ZQM003": "Dokuma Depo Kontrolleri", "ZQM004": "Dokuma Tedarik Kontrolleri",
    "ZQM005": "Örme Depo Kontrolleri", "ZQM006": "Örme Tedarik Kontrolleri",
    "ZQM007": "Tübaş Kalite Kontrol"
}

KTSCH_EN = {
    "1000001": "External Sewing", "1000002": "External Cutting", "1000003": "External Packaging",
    "1000005": "External Printing", "1000006": "External Bia Cutting", "1000007": "External Washing",
    "1000008": "External Embroidery", "1000009": "External Snap Fastening", "1000010": "External Buttonhole",
    "1000011": "External Handcrafted", "1000012": "External Special Stitch",
    "1000016": "Applique Cutting", "1000017": "Poplin Cutting", "1000018": "Main Size Cutting",
    "1000019": "Arm Tip Cutting", "1000020": "Collar Cutting", "1000021": "Jumpsuit Cutting",
    "1000024": "Oxford Cutting", "1000027": "Rib Cutting", "1000049": "Front Size Cutting",
    "1000055": "Pike Cutting", "1000067": "Pat Cutting", "1000073": "Bottom Pat Cutting",
    "1000090": "Camisole Cutting", "1000104": "Inner Collar Cutting", "1000132": "Cutting",
    "1000135": "Lace Cutting", "1000183": "Belt Cutting", "1000185": "Undercoat Cutting",
    "1000193": "Garni Cutting", "1000197": "Pocket Cutting", "1000237": "Washing",
    "1000241": "Buttonhole", "1000267": "Applique Embroidery", "1000271": "Pre-Printing",
    "1000509": "Interfacing Cutting", "1000517": "Tulle Cutting", "1000790": "Pocket Cutting",
    "1001055": "Pano Cutting", "1001105": "Pano Printing", "1001110": "Secondary Sewing",
    "1001381": "Internal Cutting", "1001382": "Jut Cleaning", "1001383": "Internal Bia Cutting",
    "1001385": "Internal Sewing", "1001386": "Internal Washing", "1001387": "Internal Packaging",
    "1001388": "Knitting (Socks)", "1001389": "Rosso (Socks)", "1001390": "Packaging (Socks)",
    "1001391": "Jardon (Socks)", "1001392": "Overlock (Socks)", "1001393": "Piece Dyeing",
    "1001394": "Fiber Filling",
    "ZQM001": "Accessory Warehouse Quality Workplace", "ZQM002": "Accessory Purchasing Quality Work",
    "ZQM003": "Weaving Warehouse Controls", "ZQM004": "Weaving Supply Controls",
    "ZQM005": "Knitting Warehouse Controls", "ZQM006": "Knitting Supply Controls",
    "ZQM007": "Tubas Quality Control"
}

TRANSLATIONS = {
    "TR": {
        # --- UI Labels & Buttons ---
        "SYSTEM_READY": "● SYSTEM READY",
        "STOPPED_BY_USER": "● STOPPED BY USER",
        "ACTIVE_PO": "● ACTIVE: {po} - {style_name}",
        "SAP_AUTOMATION_SYSTEM": "SAP AUTOMATION SYSTEM",
        "WORKFLOW": "İŞ AKIŞI",
        "WORKFLOW_WITH_DETAILS": "İŞ AKIŞI: {order_type} ({po_no} - {order_name})",
        "OPERATION_STEPS": "OPERASYON ADIMLARI",
        "START_SELECTED_STEPS": "SEÇİLİ ADIMLARI BAŞLAT",
        "TARGET_PO": "HEDEF PO",
        "PO_ENTRY_PLACEHOLDER": "PO (örn. 1305306)",
        "CREATE_EXCEL_TEMPLATE": "EXCEL ŞABLONU OLUŞTUR",
        "LOAD_DATA": "BİLGİLERİ YÜKLE",
        "STOP_ROBOT": "STOP ROBOT",
        "SYSTEM_LOGS": "SYSTEM LOGS",
        "OPEN_EXCEL_FOLDER": "📂 EXCEL KLASÖRÜNÜ AÇ",
        
        # --- Settings Page ---
        "CREDENTIALS_MGMT": "Kimlik Bilgileri Yönetimi",
        "SUPPLIER_PORTAL": "Tedarikçi Portalı (LCW)",
        "USERNAME_EMAIL": "Kullanıcı Adı (Email):",
        "PASSWORD": "Şifre:",
        "SAP_SYSTEM": "SAP Sistemi",
        "SAP_USERNAME": "SAP Kullanıcı Adı:",
        "SAP_PASSWORD": "SAP Şifre:",
        "SAVE_CRED_SECURELY": "Bilgileri Güvenli Kaydet",
        "SAVE_SUCCESS": "Kimlik bilgileri Windows Güvenlik Kasasına kaydedildi.",
        "SAVE_ERROR": "Kaydedilemedi: {error}",
        "APP_LANGUAGE_LABEL": "Uygulama Dili:",
        "APP_SETTINGS": "Uygulama Ayarları",
        "RESTART_WARNING": "Dil Değişikliği",
        "RESTART_WARNING_MSG": "Dil değişikliğinin geçerli olması için lütfen uygulamayı yeniden başlatın.",

        # --- Accessory Page ---
        "GENERAL_INFO": "Genel Bilgiler",
        "MODEL_NAME": "Model Adı:",
        "FETCH_MODEL": "Model Getir",
        "MATERIAL_SPECS": "Malzeme Spesifikasyonları",
        "MATERIAL_TYPE": "Malzeme Türü:",
        "PLANT": "Üretim Yeri:",
        "UNIT_PRICE": "Birim Fiyat:",
        "MATERIALS_PREVIEW": "Eklenecek Malzemeler (Önizleme)",
        "DELETE_SELECTED_ROWS": "Seçili Satırları Sil",
        "EXPORT_TO_EXCEL": "Excel Olarak İndir",
        "MEMORY_HISTORY": "Hafıza Geçmişi",
        "RESET": "Sıfırla",
        "CREATE_IN_SAP": "SAP'de Oluştur",
        "PREFIX": "Ön Ek",
        "VARIABLES": "Değişkenler",
        "SUFFIX": "Son Ek",
        "ADD_TO_LIST": "Listeye Ekle",
        "MATERIAL_FULL_DESC": "Malzeme Tam Tanımı",
        
        # --- Accessory Page Messages ---
        "EMPTY_RECORD_ERROR": "Accessory: Boş kayıt eklenemez!",
        "CHAR_LIMIT_EXCEEDED": "Karakter Sınırı Aşıldı!",
        "CHAR_LIMIT_EXCEEDED_MSG": "SAP kuralları gereği Malzeme Tanımı maksimum 40 karakter olmalıdır! Aşan Kayıtlar:\n{details}\nLütfen tabloya eklemeden önce kelimeleri kısaltarak tekrar deneyin.",
        "DUPLICATE_CHECK_INFO": "Bilgi",
        "DUPLICATE_CHECK_MSG": "{added} satır eklendi. {skipped} adet tabloda zaten olduğu için atlandı. 🔥 {cached} adet malzeme Cache'ten anında getirildi!",
        "DELETE_ROW_WARNING": "Lütfen silmek için en soldaki satır numaralarından satır seçin.",
        "NO_DATA_TO_EXPORT": "Dışa aktarılacak veri bulunamadı!",
        "SAVE_CSV_TITLE": "Malzeme Listesini Kaydet",
        "SAVE_CSV_SUCCESS": "Veriler Excel olarak kaydedildi!\n{path}",
        "SAVE_CSV_ERROR": "Dosya kaydedilirken hata oluştu: {error}",
        "SAP_CONFIRM_TITLE": "SAP Robotu Onayı",
        "SAP_CONFIRM_MSG": "Tablodaki {count} adet yeni malzeme şimdi SAP'de otomatik yaratılacaktır. Başlatılsın mı?",
        "SAP_REPORT_TITLE": "SAP Otomasyon Raporu",
        "SAP_REPORT_MSG": "İşlem Tamamlandı! Başarılı: {success} Hatalı: {failed}\n",
        "MEMORY_HISTORY_TITLE": "Hafıza Geçmişi",
        "MEMORY_HISTORY_SUMMARY": "Sistem Hafızasındaki Kayıtlar (Toplam: {total} Adet)",
        "CANLIVE_SEARCH": "Canlı Ara:",
        "SEARCH_PLACEHOLDER": "Tür, Kod, Tanım veya Model girin...",
        "CLEAR": "Temizle",
        "SEARCH_RESULTS": "Arama Sonuçları (Bulunan: {count} Adet)",
        "NO_MEMORY_RECORDS": "Hafızada (Cache) henüz kaydedilmiş hiçbir malzeme yok.",
        "FETCH_PO_WARNING": "Accessory: Lütfen model bilgisini getirmek için PO numarası giriniz.",
        "FETCH_CACHE_ERROR": "Accessory: {po} için yerel JSON bulunamadı! Lütfen manuel giriniz.",
        "PO_AUTO_LOAD": "Accessory: Dashboard'dan gelen aktif PO otomatik yükleniyor...",

        # --- Dashboard Workflow Labels ---
        "ZMM0020_PROCESSES": "ZMM0020 SÜREÇLERİ",
        "ZMM0020_PROCESS": "ZMM0020 SÜRECİ",
        "OTHER_OPERATIONS": "DİĞER OPERASYONLAR",
        "PART": "Parça",
        "PRODUCT": "Ürün",
        "MAIN_SET": "Ana Set",
        "ZMM0020_STEP1": "1. Varyant & Model",
        "ZMM0020_STEP2": "2. İş Planı",
        "ZMM0020_STEP3": "3. BOM Yükleme",
        "ZMM0020_STEP4": "4. Versiyon & Maliyet",

        # --- Logs and Process Statements ---
        "STARTING_AUTOMATION": "Otomasyon başlatıldı: {po_no}",
        "JSON_WATCHER_WAIT": "Watcher: JSON bekleniyor... {path}",
        "JSON_WATCHER_FOUND": "Watcher: JSON yakalandı! Tür: {order_type}. GUI güncelleniyor.",
        "JSON_WATCHER_TIMEOUT": "Watcher: {po_no} için JSON zaman aşımına uğradı.",
        "JSON_NOT_FOUND_DEFAULT": "JSON dosyası bulunamadı, varsayılan olarak SINGLE atanıyor: {path}",
        "PO_SET_DETECTED": "PO {po_no} için SET (Takım) siparişi tespit edildi.",
        "PO_CHILD_COMPONENTS_FOUND": "PO {po_no} için çocuk bileşenler bulundu, SET olarak atanıyor.",
        "PO_DETECT_ERROR": "Sipariş türü tespit edilirken hata: {error}",
        "MODULAR_FLOW_START": "--- Modüler Akış Başlatılıyor ---",
        "MODULAR_FLOW_SUCCESS": "TEBRİKLER: PO {po_no} için seçili adımlar başarıyla tamamlandı. ✅",
        "MODULAR_FLOW_FAILED": "HATA: PO {po_no} için modüler akış bir noktada kesildi. ❌",
        "CACHE_FOUND_LOADING": "[CACHE] {po} için yerel veri bulundu. Adımlar yükleniyor...",
        "CACHE_NOT_FOUND": "[CACHE] {po} için yerel veri bulunamadı! Lütfen önce 'Create Excel Template' yapınız.",
        "SAP_CONN_ERROR": "SAP bağlantısı kurulamadı! Lütfen SAP Logon'un açık olduğundan emin olun.",
        "FIORI_DATA_ERROR_TITLE": "Fiori Veri Hatası",
        "FIORI_DATA_ERROR_MSG": "Fiori'den teklif bilgileri (fiyat, üretim yeri vb.) alınamadı!\n\nLütfen Fiori üzerinden modelin plm kodunu ve fiyatını kontrol edin.",
        "FETCHING_DATA": "VERİ ÇEKİLİYOR...",
        "BRIDGE_ERROR": "Köprü Hatası: {error}",
        "MODULAR_BRIDGE_ERROR": "Modüler Köprü Hatası: {error}",
        "TARGET_PO_LOG": "Hedef PO: {po_no}",
        "SAP_LOGIN_ERROR_BRIDGE": "SAP bağlantısı kurulamadı! Lütfen SAP Logon'un açık olduğundan emin olun.",
        "SAP_LANG_MISMATCH": "SAP Dil Uyumsuzluğu: Uygulama dili '{app_lang}' seçili, ancak açık olan SAP oturumunun dili '{sap_lang}'. Lütfen SAP oturumunu kapatıp '{app_lang}' diliyle giriş yapın veya Uygulama Ayarları'ndan dili değiştirin.",
        
        # --- Excel Generator Instruction text ---
        "EXCEL_INSTRUCTIONS": (
            "Ürün Ağacı (BOM) Şablonu Talimatları:\n\n"
            "1. Her ürün parçası (child) için ayrı İş Planı ve BOM sayfaları oluşturulmuştur.\n"
            "2. İlgili parçanın 'İş Planı' sayfasında operasyonları seçin.\n"
            "3. İlgili parçanın 'BOM' sayfasında malzemeleri girin (Operasyonlar iş planından otomatik gelir).\n"
            "4. GENEL_RENK / GENEL_BEDEN için 'TÜMÜ' seçebilir veya ilgili sütunlara 'X' koyabilirsiniz.\n\n"
            "NOT: Set siparişlerde her sayfa kendi PLM koduyla eşleşir.\n"
            "5. Eğer malzeme kodunuz renk varyantlı ise kodu varyantlı olarak girebilirsiniz.\n"
            "Malzemenin rengi ana malzeme kodunun renginden farklı ise MALZEME RENGİ FARKLI MI? sütununa X koymalısınız."
        ),
        
        # --- Excel Column Names ---
        "EXCEL_COL_OPERATION": "OPERASYON",
        "EXCEL_COL_IS_VAR_COLOR": "MALZEME RENGİ FARKLI MI?",
        "EXCEL_COL_MAT_CODE": "MALZEME KODU",
        "EXCEL_COL_ITEM_TYPE": "KALEM TIPI",
        "EXCEL_COL_QTY": "MİKTAR",
        "EXCEL_COL_COMP_SCRAP": "BİLEŞEN ISKARTASI",
        "EXCEL_COL_GEN_COLOR": "GENEL_RENK_SEÇİMİ",
        "EXCEL_COL_GEN_SIZE": "GENEL_BEDEN_SEÇİMİ",
        "EXCEL_TOTAL_COMP_COUNT": "TOPLAM PARÇA SAYISI (ZMM0020):",
        "EXCEL_VARIANT_DESC_COL": "Bileşen Tanımı (Ürün-PLM-Renk)",
        "EXCEL_ANARENK_PREFIX": "ANARENK- "
    },
    "EN": {
        # --- UI Labels & Buttons ---
        "SYSTEM_READY": "● SYSTEM READY",
        "STOPPED_BY_USER": "● STOPPED BY USER",
        "ACTIVE_PO": "● ACTIVE: {po} - {style_name}",
        "SAP_AUTOMATION_SYSTEM": "SAP AUTOMATION SYSTEM",
        "WORKFLOW": "WORKFLOW",
        "WORKFLOW_WITH_DETAILS": "WORKFLOW: {order_type} ({po_no} - {order_name})",
        "OPERATION_STEPS": "OPERATION STEPS",
        "START_SELECTED_STEPS": "START SELECTED STEPS",
        "TARGET_PO": "TARGET PO",
        "PO_ENTRY_PLACEHOLDER": "PO (e.g. 1305306)",
        "CREATE_EXCEL_TEMPLATE": "CREATE EXCEL TEMPLATE",
        "LOAD_DATA": "LOAD DATA",
        "STOP_ROBOT": "STOP ROBOT",
        "SYSTEM_LOGS": "SYSTEM LOGS",
        "OPEN_EXCEL_FOLDER": "📂 OPEN EXCEL FOLDER",
        
        # --- Settings Page ---
        "CREDENTIALS_MGMT": "Credentials Management",
        "SUPPLIER_PORTAL": "Supplier Portal (LCW)",
        "USERNAME_EMAIL": "Username (Email):",
        "PASSWORD": "Password:",
        "SAP_SYSTEM": "SAP System",
        "SAP_USERNAME": "SAP Username:",
        "SAP_PASSWORD": "SAP Password:",
        "SAVE_CRED_SECURELY": "Save Credentials Securely",
        "SAVE_SUCCESS": "Credentials have been saved to Windows Credential Locker.",
        "SAVE_ERROR": "Save failed: {error}",
        "APP_SETTINGS": "Application Settings",
        "APP_LANGUAGE_LABEL": "Application Language:",
        "RESTART_WARNING": "Language Change",
        "RESTART_WARNING_MSG": "Please restart the application for the language changes to take effect.",

        # --- Accessory Page ---
        "GENERAL_INFO": "General Information",
        "MODEL_NAME": "Model Name:",
        "FETCH_MODEL": "Fetch Model",
        "MATERIAL_SPECS": "Material Specifications",
        "MATERIAL_TYPE": "Material Type:",
        "PLANT": "Plant:",
        "UNIT_PRICE": "Unit Price:",
        "MATERIALS_PREVIEW": "Materials to Add (Preview)",
        "DELETE_SELECTED_ROWS": "Delete Selected Rows",
        "EXPORT_TO_EXCEL": "Export to Excel",
        "MEMORY_HISTORY": "Memory History",
        "RESET": "Reset",
        "CREATE_IN_SAP": "Create in SAP",
        "PREFIX": "Prefix",
        "VARIABLES": "Variables",
        "SUFFIX": "Suffix",
        "ADD_TO_LIST": "Add to List",
        "MATERIAL_FULL_DESC": "Material Full Description",
        
        # --- Accessory Page Messages ---
        "EMPTY_RECORD_ERROR": "Accessory: Cannot add empty record!",
        "CHAR_LIMIT_EXCEEDED": "Character Limit Exceeded!",
        "CHAR_LIMIT_EXCEEDED_MSG": "Per SAP rules, Material Description must be maximum 40 characters! Exceeded records:\n{details}\nPlease shorten the words before adding them to the table.",
        "DUPLICATE_CHECK_INFO": "Information",
        "DUPLICATE_CHECK_MSG": "{added} rows added. {skipped} duplicates skipped. 🔥 {cached} materials retrieved instantly from Cache!",
        "DELETE_ROW_WARNING": "Please select a row by clicking on row numbers on the far left to delete.",
        "NO_DATA_TO_EXPORT": "No data found to export!",
        "SAVE_CSV_TITLE": "Save Material List",
        "SAVE_CSV_SUCCESS": "Data saved as Excel CSV!\n{path}",
        "SAVE_CSV_ERROR": "Error occurred while saving file: {error}",
        "SAP_CONFIRM_TITLE": "SAP Robot Confirmation",
        "SAP_CONFIRM_MSG": "{count} new materials in the table will be created in SAP automatically. Start now?",
        "SAP_REPORT_TITLE": "SAP Automation Report",
        "SAP_REPORT_MSG": "Process Completed! Success: {success} Failed: {failed}\n",
        "MEMORY_HISTORY_TITLE": "Memory History",
        "MEMORY_HISTORY_SUMMARY": "Records in System Memory (Total: {total} Pcs)",
        "CANLIVE_SEARCH": "Live Search:",
        "SEARCH_PLACEHOLDER": "Enter Type, Code, Description or Model...",
        "CLEAR": "Clear",
        "SEARCH_RESULTS": "Search Results (Found: {count} Pcs)",
        "NO_MEMORY_RECORDS": "No materials saved in memory (Cache) yet.",
        "FETCH_PO_WARNING": "Accessory: Please enter a PO number to fetch model information.",
        "FETCH_CACHE_ERROR": "Accessory: Local JSON not found for {po}! Please enter manually.",
        "PO_AUTO_LOAD": "Accessory: Active PO from Dashboard is loading automatically...",

        # --- Dashboard Workflow Labels ---
        "ZMM0020_PROCESSES": "ZMM0020 PROCESSES",
        "ZMM0020_PROCESS": "ZMM0020 PROCESS",
        "OTHER_OPERATIONS": "OTHER OPERATIONS",
        "PART": "Part",
        "PRODUCT": "Product",
        "MAIN_SET": "Main Set",
        "ZMM0020_STEP1": "1. Variant & Model",
        "ZMM0020_STEP2": "2. Work Plan",
        "ZMM0020_STEP3": "3. Load BOM",
        "ZMM0020_STEP4": "4. Version & Costing",

        # --- Logs and Process Statements ---
        "STARTING_AUTOMATION": "Automation started: {po_no}",
        "JSON_WATCHER_WAIT": "Watcher: Waiting for JSON... {path}",
        "JSON_WATCHER_FOUND": "Watcher: JSON captured! Type: {order_type}. GUI updating.",
        "JSON_WATCHER_TIMEOUT": "Watcher: JSON timed out for {po_no}.",
        "JSON_NOT_FOUND_DEFAULT": "JSON file not found, defaulting to SINGLE: {path}",
        "PO_SET_DETECTED": "SET (Team) order detected for PO {po_no}.",
        "PO_CHILD_COMPONENTS_FOUND": "Child components found for PO {po_no}, assigning as SET.",
        "PO_DETECT_ERROR": "Error detecting order type: {error}",
        "MODULAR_FLOW_START": "--- Modular Flow Starting ---",
        "MODULAR_FLOW_SUCCESS": "CONGRATULATIONS: Selected steps completed successfully for PO {po_no}. ✅",
        "MODULAR_FLOW_FAILED": "ERROR: Modular flow was interrupted for PO {po_no}. ❌",
        "CACHE_FOUND_LOADING": "[CACHE] Local data found for {po}. Loading steps...",
        "CACHE_NOT_FOUND": "[CACHE] Local data not found for {po}! Please run 'Create Excel Template' first.",
        "SAP_CONN_ERROR": "SAP connection failed! Please make sure SAP Logon is open.",
        "FIORI_DATA_ERROR_TITLE": "Fiori Data Error",
        "FIORI_DATA_ERROR_MSG": "Could not retrieve bid information (price, plant, etc.) from Fiori!\n\nPlease check the plm code and pricing of the model on Fiori.",
        "FETCHING_DATA": "FETCHING DATA...",
        "BRIDGE_ERROR": "Bridge Error: {error}",
        "MODULAR_BRIDGE_ERROR": "Modular Bridge Error: {error}",
        "TARGET_PO_LOG": "Target PO: {po_no}",
        "SAP_LOGIN_ERROR_BRIDGE": "SAP connection failed! Please make sure SAP Logon is open.",
        "SAP_LANG_MISMATCH": "SAP Language Mismatch: Application language is set to '{app_lang}', but active SAP session language is '{sap_lang}'. Please close the SAP session and log in with '{app_lang}' language, or change the language from Application Settings.",

        # --- Excel Generator Instruction text ---
        "EXCEL_INSTRUCTIONS": (
            "Bill of Materials (BOM) Template Instructions:\n\n"
            "1. Separate Work Plan and BOM sheets have been created for each child component.\n"
            "2. Select operations on the 'Work Plan' sheet of the relevant component.\n"
            "3. Enter materials on the 'BOM' sheet of the relevant component (Operations populate automatically).\n"
            "4. For GENERAL_COLOR / GENERAL_SIZE, you can select 'ALL' or put 'X' in the relevant columns.\n\n"
            "NOTE: For set orders, each page matches its own PLM code.\n"
            "5. If your material code is color-variant, you can enter it as a variant code.\n"
            "If the color of the material differs from the main material color, place 'X' in the IS MATERIAL COLOR DIFFERENT? column."
        ),
        
        # --- Excel Column Names ---
        "EXCEL_COL_OPERATION": "OPERATION",
        "EXCEL_COL_IS_VAR_COLOR": "IS MATERIAL COLOR DIFFERENT?",
        "EXCEL_COL_MAT_CODE": "MATERIAL CODE",
        "EXCEL_COL_ITEM_TYPE": "ITEM TYPE",
        "EXCEL_COL_QTY": "QUANTITY",
        "EXCEL_COL_COMP_SCRAP": "COMPONENT SCRAP",
        "EXCEL_COL_GEN_COLOR": "GENERAL_COLOR_SELECTION",
        "EXCEL_COL_GEN_SIZE": "GENERAL_SIZE_SELECTION",
        "EXCEL_TOTAL_COMP_COUNT": "TOTAL COMPONENT COUNT (ZMM0020):",
        "EXCEL_VARIANT_DESC_COL": "Component Description (Product-PLM-Color)",
        "EXCEL_ANARENK_PREFIX": "MAINCOLOR- "
    }
}

def get_language():
    """Fetches the current application language from settings."""
    try:
        lang = ConfigManager.get_setting("APP_LANGUAGE")
        if lang in ["TR", "EN"]:
            return lang
    except Exception as e:
        logger.debug(f"Could not read APP_LANGUAGE, defaulting to TR. Error: {e}")
    return "TR"

def _(key, **kwargs):
    """Translates the given key based on current language settings."""
    lang = get_language()
    val = TRANSLATIONS[lang].get(key, TRANSLATIONS["TR"].get(key, key))
    if kwargs:
        try:
            return val.format(**kwargs)
        except Exception as e:
            logger.error(f"Error formatting translation string for '{key}': {e}")
    return val

def get_ktsch_map():
    """Returns the KTSCH map for the current language."""
    lang = get_language()
    if lang == "EN":
        return {name: code for code, name in KTSCH_EN.items()}
    else:
        return {name: code for code, name in KTSCH_TR.items()}

def get_ktsch_code_to_name():
    """Returns the KTSCH code to name map for the current language."""
    lang = get_language()
    if lang == "EN":
        return KTSCH_EN
    else:
        return KTSCH_TR

def get_operation_name(code):
    """Returns the operation name for a given code in current language."""
    lang = get_language()
    if lang == "EN":
        return KTSCH_EN.get(code, KTSCH_TR.get(code, code))
    else:
        return KTSCH_TR.get(code, code)

def get_unit_symbol():
    """
    Uygulama dili ingilizce (EN) seçili ise 'PC' (Piece),
    Türkçe (TR) seçili ise 'ADT' (Adet) değerini döner.
    """
    return "PC" if get_language() == "EN" else "ADT"
