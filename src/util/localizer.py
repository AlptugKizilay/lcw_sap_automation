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
        "FIORI_INFO_TITLE": "Fiori Bilgilendirme",
        "FIORI_NO_OFFER_MSG_SET": (
            "Fiori'de uygun bir teklif satırı bulunamadı!\n\n"
            "NE YAPMALIYIM?\n"
            "1- Fiori üzerinden teklif plm kodunu ve fiyatlandırmayı kontrol edip düzeltin.\n"
            "Teklif açıklaması PO numarasını içermelidir.\n"
            "2- Excel dosyanızı doldurmaya devam edebilirsiniz.\n"
            "3- İşlemi tamamladığınızda 'SEÇİLİ ADIMLARI BAŞLAT' butonuna basmanız yeterlidir.\n\n"
            "NOT: Otomasyon başladığında sistem Fiori verilerini OTOMATİK olarak tekrar kontrol edecektir."
        ),
        "FIORI_NO_OFFER_MSG_SINGLE": (
            "Fiori'de uygun bir teklif satırı bulunamadı!\n\n"
            "NE YAPMALIYIM?\n"
            "1- Fiori üzerinden teklif plm kodunu ve fiyatlandırmayı kontrol edip düzeltin.\n"
            "2- Excel dosyanızı doldurmaya devam edebilirsiniz.\n"
            "3- İşlemi tamamladığınızda 'SEÇİLİ ADIMLARI BAŞLAT' butonuna basmanız yeterlidir.\n\n"
            "NOT: Otomasyon başladığında sistem Fiori verilerini OTOMATİK olarak tekrar kontrol edecektir."
        ),

        # --- Update Manager Strings ---
        "UPDATE_DIALOG_TITLE": "Yeni Güncelleme Mevcut",
        "UPDATE_NEW_VERSION_AVAIL": "🚀 Yeni Sürüm Mevcut: v{version}",
        "UPDATE_CURRENT_VERSION": "Mevcut Sürümünüz: v{version}",
        "UPDATE_CHANGELOG_HEADER": "Yenilikler:",
        "UPDATE_AUTO_RELAUNCH_NOTICE": "ℹ️ 'Şimdi Güncelle' butonuna tıkladığınızda uygulama otomatik olarak kapanacak, güncellenecek ve tekrar açılacaktır.",
        "UPDATE_NOW_BTN": "Şimdi Güncelle",
        "UPDATE_LATER_BTN": "Daha Sonra",
        "UPDATING_TITLE": "Güncelleniyor",
        "UPDATE_DOWNLOADING_MSG": "Güncelleme paketi indiriliyor, lütfen bekleyin...\n(İndirme tamamlandığında uygulama otomatik kapanıp güncellenecektir)",
        "UPDATE_SCRIPT_NOT_FOUND": "Hata: Güncelleme scripti bulunamadı.",
        "UPDATE_DOWNLOAD_ERR": "İndirme hatası: {error}",
        "FETCHING_DATA": "VERİ ÇEKİLİYOR...",
        "BRIDGE_ERROR": "Köprü Hatası: {error}",
        "MODULAR_BRIDGE_ERROR": "Modüler Köprü Hatası: {error}",
        "TARGET_PO_LOG": "Hedef PO: {po_no}",
        "SAP_LOGIN_ERROR_BRIDGE": "SAP bağlantısı kurulamadı! Lütfen SAP Logon'un açık olduğundan emin olun.",
        "SAP_LANG_MISMATCH": "SAP Dil Uyumsuzluğu: Uygulama dili '{app_lang}' seçili, ancak açık olan SAP oturumunun dili '{sap_lang}'. Lütfen SAP oturumunu kapatıp '{app_lang}' diliyle giriş yapın veya Uygulama Ayarları'ndan dili değiştirin.",
        "LOG_PROCESS_STOPPED": "Otomasyon kullanıcı tarafından anında kesildi.",
        "LOG_NO_ACTIVE_PROCESS": "Şu an durdurulacak aktif bir süreç bulunamadı.",
        "LOG_PO_EMPTY": "PO numarası boş olamaz!",
        "LOG_NO_STEPS_SELECTED": "Çalıştırılacak hiçbir adım seçilmedi!",
        "LOG_MODULAR_START_PREFIX": "[MODÜLER AKIŞ] Başlatılıyor...",
        "LOG_TARGET_PO_PREFIX": "Hedef PO: {po}",
        "LOG_SELECTED_STEPS_PREFIX": "Seçili Adımlar: {steps}",
        "LOG_PLEASE_ENTER_PO": "Lütfen önce bir PO numarası giriniz!",
        "LOG_ACCESSORY_DELETED": "Accessory: Seçili satırlar sheet üzerinden silindi.",
        
        # --- SAP Screen & Flow Log Statements ---
        "LOG_SINGLE_FLOW_START": "--- Tekli Sipariş Otomasyon Akışı Başlatılıyor: {po_no} ---",
        "LOG_SINGLE_FLOW_DONE": "🎉 TEBRİKLER: Tekli Sipariş {po_no} için TÜM süreçler başarıyla tamamlandı! ✅",
        "LOG_SINGLE_FLOW_ERROR": "❌ HATA: Tekli Sipariş {po_no} iş akışında hata oluştu: {error}",
        "LOG_SET_FLOW_START": "--- Set (Takım) Sipariş Otomasyon Akışı Başlatılıyor: {po_no} ---",
        "LOG_SET_FLOW_DONE": "🎉 TEBRİKLER: Set Sipariş {po_no} için TÜM süreçler başarıyla tamamlandı! ✅",
        "LOG_SET_FLOW_ERROR": "❌ HATA: Set Sipariş {po_no} iş akışında hata oluştu: {error}",
        "LOG_STEP_START": ">>> ADIM {step_num}: {step_name} başlatılıyor...",
        "LOG_STEP_SUCCESS": ">>> ADIM {step_num}: {step_name} BAŞARIYLA TAMAMLANDI. ✅",
        
        # --- ZMM0020 Handler Logs ---
        "LOG_ZMM0020_GOTO": "ZMM0020: İşlem koduna gidiliyor: ZMM0020",
        "LOG_ZMM0020_MODEL_VAR_START": "ZMM0020: 1. Adım - Model & Varyant Oluşturma başlatılıyor.",
        "LOG_ZMM0020_MODEL_VAR_DONE": "ZMM0020: 1. Adım - Model & Varyant Oluşturma tamamlandı.",
        "LOG_ZMM0020_WORKPLAN_START": "ZMM0020: 2. Adım - İş Planı Oluşturma başlatılıyor.",
        "LOG_ZMM0020_WORKPLAN_DONE": "ZMM0020: 2. Adım - İş Planı Oluşturma tamamlandı.",
        "LOG_ZMM0020_BOM_START": "ZMM0020: 3. Adım - BOM Yükleme başlatılıyor.",
        "LOG_ZMM0020_BOM_DONE": "ZMM0020: 3. Adım - BOM Yükleme tamamlandı.",
        "LOG_ZMM0020_COSTING_START": "ZMM0020: 4. Adım - Versiyon & Maliyet Hesaplama başlatılıyor.",
        "LOG_ZMM0020_COSTING_DONE": "ZMM0020: 4. Adım - Versiyon & Maliyet Hesaplama tamamlandı.",
        "LOG_ZMM0020_ALV_LOADED": "ALV verileri yüklendi. Satır sayısı: {count}",
        "LOG_ZMM0020_ALV_TIMEOUT": "Zaman aşımı! ALV verileri {timeout} saniye içinde yüklenmedi.",
        
        # --- CS01 Handler Logs ---
        "LOG_CS01_MATRIX_START": "CS01: Varyant matrisi doldurma işlemi başlatılıyor.",
        "LOG_CS01_SET_BOM_START": "CS01: Set siparişi için BOM oluşturma adımı başlatılıyor.",
        "LOG_CS01_MAIN_MAT_NOT_FOUND": "CS01: Ana malzeme kodu bulunamadı. BOM oluşturulamıyor.",
        "LOG_CS01_CHILDREN_NOT_FOUND": "CS01: Çocuk ürünleri bulunamadı. BOM oluşturulamıyor.",
        "LOG_CS01_MAIN_MAT_ENTERED": "CS01: Ana malzeme kodu '{mat_code}' ve diğer BOM bilgileri girildi.",
        "LOG_CS01_CHILD_ROW_ADDING": "CS01: Çocuk PLM {plm} (Malzeme: {mat_code}) için BOM satırı ekleniyor. Miktar: {qty}",
        "LOG_CS01_ALL_ROWS_ENTERED": "CS01: Tüm BOM satırları girildi ve Enter tuşuna basıldı.",
        "LOG_CS01_BOM_SAVED": "CS01: BOM başarıyla kaydedildi.",
        "LOG_CS01_BOM_SET_SUCCESS": "CS01: Set siparişi için BOM oluşturma adımı başarıyla tamamlandı.",
        "LOG_CS01_ERROR": "CS01: Set siparişi için BOM oluşturulurken hata oluştu: {error}",
        
        # --- MD01N Handler Logs ---
        "LOG_MD01N_START": "MD01N: MRP Live çalıştırma işlemi başlatılıyor.",
        "LOG_MD01N_MATERIALS_COUNT": "MD01N: Toplam {count} malzeme listeye giriliyor.",
        "LOG_MD01N_EXECUTING": "MD01N: MRP Live yürütülüyor...",
        "LOG_MD01N_DONE": "MD01N: MRP Live işlemi tamamlandı.",
        "LOG_MD01N_SINGLE_START": "MD01N: MRP Çalıştırılıyor. Malzeme: {mat_code}, Üretim Yeri: {plant}",
        "LOG_MD01N_SINGLE_DONE": "MD01N: {mat_code} için MRP başarıyla tamamlandı.",
        "LOG_MD01N_ERROR": "MD01N Hatası: {error}",
        
        # --- Common Actions & SAP Logs ---
        "LOG_SAP_SAVE_START": "SAP Ekranı: Kaydetme işlemi başlatılıyor (btn[11]).",
        "LOG_SAP_SAVE_SUCCESS": "SAP Ekranı: Kaydetme işlemi başarıyla tamamlandı. Mesaj: {msg}",
        "LOG_SAP_SAVE_FAILED": "SAP Ekranı: Kaydetme işlemi başarısız oldu. Hata Mesajı: {msg}",
        "LOG_SAP_SAVE_TIMEOUT": "SAP Ekranı: Kaydetme işlemi {timeout} saniye içinde tamamlanmadı.",
        "LOG_SAP_STATUS_BAR": "SAP Durum Çubuğu Mesajı: [{msg_type}] {text}",
        "LOG_SAP_MODE": "SAP Ekranı: Mevcut mod '{mode}'.",
        "LOG_SAP_MODE_ALREADY_CHANGE": "SAP Ekranı zaten 'Değiştir' modunda.",
        "LOG_SAP_SWITCHING_CHANGE": "SAP Ekranı 'Görüntüle' modunda. 'Değiştir' moduna geçiliyor.",
        "LOG_SAP_SWITCHED_CHANGE": "SAP Ekranı başarıyla 'Değiştir' moduna geçti.",
        "LOG_SAP_POPUP_OK": "Genel SAP pop-up 'Tamam' butonuna basıldı.",
        
        # --- ZMM0170 & ZPP0030 & ZSD0010 Logs ---
        "LOG_ZMM0170_START": "ZMM0170: Malzeme durum kontrolü başlatılıyor...",
        "LOG_ZMM0170_DONE": "ZMM0170: Malzeme durum kontrolü tamamlandı.",
        "LOG_ZPP0030_START": "ZPP0030: Üretim siparişi kontrolü başlatılıyor...",
        "LOG_ZPP0030_DONE": "ZPP0030: Üretim siparişi kontrolü tamamlandı.",
        "LOG_ZSD0010_START": "ZSD0010: Satış siparişi kontrolü başlatılıyor...",
        "LOG_ZSD0010_DONE": "ZSD0010: Satış siparişi kontrolü tamamlandı.",

        # --- Additional SAP Connection & System Logs ---
        "LOG_SAP_CONN_NOT_FOUND": "HATA: '{system_name}' adlı aktif bir SAP bağlantısı bulunamadı.",
        "LOG_SAP_MANUAL_LOGON": "Lütfen SAP Logon Pad'den sistemi manuel olarak açın.",
        "LOG_SAP_CONNECTED": "'{system_name}' sistemine başarıyla bağlanıldı. İşlem Kodu: '{tx}'",
        "LOG_SAP_LOGIN_DETECTED": "SAP Login ekranı algılandı. Uygulama dili '{app_lang}' uyarınca SAP dili '{target_lang}' ile '{username}' girişi yapılıyor...",
        "LOG_SAP_ACTIVE_LANG": "Aktif SAP Oturum Dili: '{raw_lang}' ({curr_lang}), Uygulama Dili: '{app_lang}'",
        "LOG_SAP_SESSION_READY": "SAP oturumu kullanıma hazır.",
        "LOG_SAP_CONN_ERROR_DETAIL": "SAP bağlantısı / dil kontrolü sırasında hata: {error}",

        # --- ZMM0020 Step & Section Logs ---
        "LOG_S1_START": "--- [S1] Varyant & Model Girişi Başladı ---",
        "LOG_S1_DONE": "--- [S1] Başarıyla Tamamlandı ---",
        "LOG_S2_START": "--- [S2] İş Planı & Rota Başladı ---",
        "LOG_S2_DONE": "--- [S2] Başarıyla Tamamlandı ---",
        "LOG_S3_START": "--- [S3] BOM (Excel) Yükleme Adımı Başladı ---",
        "LOG_S3_DONE": "--- [S3] Başarıyla Tamamlandı ---",
        "LOG_S4_START": "--- [S4] Üretim Versiyonu & Maliyet Adımı Başladı ---",
        "LOG_S4_DONE": "--- [S4] Başarıyla Tamamlandı ---",
        "LOG_ZMM0021_ENTRY": "ZMM0021'e giriş için model kodu: {model_code}, werks: {werks}",
        "LOG_PV_CONTROL_START": "Üretim versiyonları kontrol süreci başlatıldı (Dinamik İlerleme Modu)...",
        "LOG_PV_PROGRESS": "İlerleme tespit edildi: {last} -> {current} boş hücre kaldı. Deneme hakkı harcanmadı.",
        "LOG_PV_NO_PROGRESS": "İlerleme yok! Boş hücre sayısı hala {current}. Deneme: {attempt}/{max_attempt}",
        "LOG_PV_CREATE_BTN": "'Üretim Versiyonu Oluştur' butonuna basılıyor...",
        "LOG_PV_ALL_DONE": "Tüm üretim versiyonları ('X') başarıyla tamamlandı. ✅",
        "LOG_COSTING_TAB_START": "ZMM0020: Maliyetlendirme sekmesi işlemleri başlatılıyor.",
        "LOG_COSTING_DETAIL_BTN": "Maliyetlendirme ALV gridinde 'DETAY' butonuna basılıyor.",
        "LOG_COSTING_ACTION_START": "Maliyetlendirme işlemi başlatılıyor: Buton '{button_id}', Sütun '{check_col}'",
        "LOG_COSTING_COL_SUCCESS": "Tüm satırlarda '{check_col}' sütunu 'X' oldu. İşlem başarılı. ✅",
        "LOG_COSTING_PROGRESS": "İlerleme var: {last} -> {current} satır kaldı. Deneme hakkı korunuyor.",
        "LOG_COSTING_NO_PROGRESS": "İlerleme yok! Hala {current} satır eksik. Deneme: {attempt}/{max_attempt}",
        "LOG_COSTING_ALL_DONE": "Tüm Maliyetlendirme sekmesi işlemleri başarıyla tamamlandı.",
        "LOG_POPUP_CHECKING": "Pop-up kontrolü yapılıyor...",
        "LOG_POPUP_NOT_FOUND": "ZMM0020: Pop-up bulunamadı, normal akışa devam ediliyor.",
        "LOG_SELECTED_STEPS": "Seçili Adımlar (Selected Steps): {steps}",
        "LOG_MODULAR_PROCESS_START": "--- Modüler Süreç Başlatıldı: {po_no} ---",

        # --- ZSD0010 & Fiori Handler Logs ---
        "LOG_FIORI_START_BROWSER": "Playwright tarayıcısı başlatılıyor...",
        "LOG_FIORI_GOTO_LOGIN": "Fiori login sayfasına gidiliyor: {url}",
        "LOG_FIORI_WAIT_FORM": "Login form elementlerinin yüklenmesi bekleniyor...",
        "LOG_FIORI_FORM_FOUND": "Login form elementleri bulundu.",
        "LOG_FIORI_ENTER_CRED": "Kullanıcı adı ve şifre giriliyor.",
        "LOG_FIORI_SELECT_LANG": "Dili '{lang}' olarak seçiliyor.",
        "LOG_FIORI_CLICK_LOGIN": "Giriş butonuna tıklanıyor.",
        "LOG_FIORI_WAIT_LAUNCHPAD": "Fiori Launchpad'in yüklenmesi bekleniyor (#shell-header elementi kontrol ediliyor)...",
        "LOG_FIORI_LOGIN_SUCCESS": "Fiori Launchpad'e başarıyla giriş yapıldı.",
        "LOG_FIORI_LOGIN_FAIL": "Fiori Launchpad'e giriş yapılamadı. #shell-header elementi bulunamadı.",
        "LOG_FIORI_CRITICAL_ERR": "Fiori login sırasında kritik hata oluştu: {error}",
        "LOG_ZSD0010_FILTER_START": "ZSD0010: PLM kodu '{plm_code}' ile filtreleme başlatılıyor.",
        "LOG_ZSD0010_FILTER_APPLIED": "PLM kodu '{plm_code}' girildi ve filtre uygulandı.",
        "LOG_ZSD0010_ROWS_FOUND": "Filtreleme sonrası {count} adet satır bulundu.",
        "LOG_ZSD0010_NO_ITEMS": "PLM kodu '{plm_code}' için hiçbir öğe bulunamadı.",
        "LOG_ZSD0010_ROW_PROCESSING": "Satır {row} işleniyor...",
        "LOG_ZSD0010_EXTRACTED_PRICE": "Satır {row} - Çekilen Fiyat: {price}",
        "LOG_ZSD0010_APPROVAL_STATUS": "Satır {row} - Onay Durumu: {status}",
        "LOG_ZSD0010_PLM_STATUS": "Satır {row} - PLM Durumu: {status}",
        "LOG_ZSD0010_QUERY_PLM": "ZSD0010: PLM '{plm_code}' sorgulanıyor. (Child: {is_child}, PO: {po_no})",
        "LOG_ZSD0010_NO_OFFER_ERR": "HATA: {plm_code} numaralı PLM için Fiori'de uygun bir teklif satırı bulunamadı! Lütfen Fiori üzerinden teklif durumunu ve fiyatlandırmayı kontrol edin.",
        "LOG_ZSD0010_MATCH_FOUND": "Eşleşme Bulundu: {primary_id}. Detaya gidiliyor.",
        "LOG_ZSD0010_JS_SUCCESS": "JS Başarılı! Canlı Veri -> PLM: {plm_check}, Bid: {bid_no}",
        "LOG_ZSD0010_PLM_MISMATCH": "DİKKAT: Ekrandaki PLM ({plm_check}) arananla ({expected}) eşleşmiyor!",
        "LOG_ZSD0010_ORG_FETCHED": "Organizasyonel veriler başarıyla çekildi: {sales_org}",
        "LOG_ZSD0010_POPUP_CLOSE_TRY": "Pop-up kapatma işlemi deneniyor...",
        "LOG_ZSD0010_POPUP_CLOSED_OK": "Pop-up 'Tamam' metni ile kapatıldı.",
        "LOG_ZSD0010_POPUP_CLOSED_ID": "Pop-up ID kalıbı ({id}) ile kapatıldı.",
        "LOG_ZSD0010_POPUP_ESC": "Kapatma butonu bulunamadı, Klavyeden 'ESC' tuşuna basılıyor.",
        "LOG_ZSD0010_POPUP_CLOSE_ERR": "Pop-up kapatılırken kritik hata: {error}",
        "LOG_ZSD0010_ORG_BTN_NOT_FOUND": "Organizasyonel Veriler butonu (#__button13) bu ekranda mevcut değil.",
        "LOG_ZSD0010_ORG_FETCH_FAIL": "Organizasyonel veriler çekilemedi, işleme devam ediliyor: {error}",
        "LOG_ZSD0010_NAV_BACK": "İşlem bitti, ana listeye geri dönülüyor...",
        "LOG_ZSD0010_BACK_CLICKED": "Geri butonuna başarıyla tıklandı.",
        "LOG_ZSD0010_BACK_ERR": "Geri butonu tıklanamadı: {error}. Tarayıcı geri komutu deneniyor.",
        "LOG_ZSD0010_WAIT_NEXT_PLM": "Fiori: Set siparişi için bir sonraki PLM sorgu alanı bekleniyor...",
        "LOG_ZSD0010_NEXT_FIELD_NOT_READY": "Fiori: Sonraki giriş alanı hazır değil ama devam ediliyor: {error}",
        "LOG_ZSD0010_FIORI_ERR": "Fiori İşlem Hatası: {error}",
        "LOG_ZSD0010_BTN_PRESSED": "ZSD0010: '{desc}' ({btn_id}) butonuna başarıyla basıldı.",
        "LOG_ZSD0010_BTN_INACTIVE": "ZSD0010: '{desc}' ({btn_id}) butonu şu an aktif değil veya bulunamadı. Atlanıyor...",
        "LOG_ZSD0010_SUBGRID_ROW": "Alt Grid Satır {row}: Malzeme No: {mat}",
        "LOG_ZSD0010_SUBGRID_DATA": "Alt Grid Satır {row}: PLM {plm} -> Bid: {bid}, Fiyat: {price}",
        "LOG_ZSD0010_SUBGRID_ERR": "Alt Grid Satır {row}: PLM {plm} -> Bid: {bid}, Fiyat: {price} -> HATA: {error}",
        "LOG_ZSD0010_CHECK_ETA": "ZSD0010: Alt grid '&ETA' kontrol ediliyor.",
        "LOG_ZSD0010_CHECK_CHECK": "ZSD0010: Alt grid '&CHECK' kontrol ediliyor.",
        "LOG_ZSD0010_SUBGRID_MSG_ERR": "ZSD0010 Alt Grid Hatası: {msg}",
        "LOG_ZSD0010_SUBGRID_MSG_WARN": "ZSD0010 Alt Grid Uyarısı: {msg}",
        "LOG_ZSD0010_SUBGRID_MSG_SUCCESS": "ZSD0010 Alt Grid Doğrulaması Başarılı: {msg}",
        "LOG_ZSD0010_BTN0_PRESSED": "wnd[2]/tbar[0]/btn[0]: Basıldı",
        "LOG_ZSD0010_SUBGRID_VAL_ERR": "ZSD0010: Alt grid doğrulama sırasında hata: {error}",
        "LOG_ZSD0010_GUI_START": "ZSD0010 GUI: İşlem başlatılıyor. PO: {po}, Tip: {order_type}",
        "LOG_ZSD0010_PO_NOT_FOUND": "ZSD0010: PO {po} için kayıt bulunamadı.",
        "LOG_ZSD0010_SET_BOM_SIZE_START": "ZSD0010: Set siparişi için her satırın BOM_SIZE detayı işleniyor.",
        "LOG_ZSD0010_POPUP_ROW_PROCESSING": "ZSD0010: Pop-up Satır {current}/{total} işleniyor.",
        "LOG_ZSD0010_ROW_SUBGRID_DONE": "ZSD0010: Satır {row} alt grid işlemi tamamlandı.",
        "LOG_ZSD0010_BOM_SIZE_BTN_ERR": "ZSD0010: Satır {row} için BOM_SIZE butonu bulunamadı veya basılamadı: {error}",
        "LOG_ZSD0010_POPUP_MSG": "ZSD0010 Pop-up Mesajı: '{msg}'",
        "LOG_ZSD0010_SAP_INTEG_ERR": "ZSD0010 SAP Entegrasyon Hatası: {msg}",
        "LOG_ZSD0010_POPUP_CONFIRM": "ZSD0010: Pop-up onaylanıyor (Evet/Tamam).",
        "LOG_ZSD0010_FINAL_INFO": "ZSD0010 Final Bilgi: {msg}",
        "LOG_ZSD0010_NO_CONFIRM_POPUP": "ZSD0010: Beklenen onay pop-up'ı (wnd[2]) çıkmadı, status bar kontrol edildi.",
        "LOG_ZSD0010_POPUP_UNEXPECTED_ERR": "ZSD0010: Pop-up işleme sırasında beklenmeyen hata: {error}",
        "LOG_ZSD0010_GUI_ERR": "ZSD0010 GUI Hatası: {error}",
        
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
        "FIORI_DATA_ERROR_MSG": "Could not retrieve offer details (price, plant, etc.) from Fiori!\n\nPlease check the model PLM code and pricing on Fiori.",
        "FIORI_INFO_TITLE": "Fiori Information",
        "FIORI_NO_OFFER_MSG_SET": (
            "No suitable offer line found in Fiori!\n\n"
            "WHAT SHOULD I DO?\n"
            "1- Please check and fix the offer PLM code and pricing on Fiori.\n"
            "The offer description must include the PO number.\n"
            "2- You can continue filling out your Excel file.\n"
            "3- When completed, simply click the 'START SELECTED STEPS' button.\n\n"
            "NOTE: When automation starts, the system will AUTOMATICALLY check Fiori data again."
        ),
        "FIORI_NO_OFFER_MSG_SINGLE": (
            "No suitable offer line found in Fiori!\n\n"
            "WHAT SHOULD I DO?\n"
            "1- Please check and fix the offer PLM code and pricing on Fiori.\n"
            "2- You can continue filling out your Excel file.\n"
            "3- When completed, simply click the 'START SELECTED STEPS' button.\n\n"
            "NOTE: When automation starts, the system will AUTOMATICALLY check Fiori data again."
        ),

        # --- Update Manager Strings ---
        "UPDATE_DIALOG_TITLE": "New Update Available",
        "UPDATE_NEW_VERSION_AVAIL": "🚀 New Version Available: v{version}",
        "UPDATE_CURRENT_VERSION": "Current Version: v{version}",
        "UPDATE_CHANGELOG_HEADER": "What's New:",
        "UPDATE_AUTO_RELAUNCH_NOTICE": "ℹ️ When you click 'Update Now', the application will automatically close, update, and relaunch.",
        "UPDATE_NOW_BTN": "Update Now",
        "UPDATE_LATER_BTN": "Remind Later",
        "UPDATING_TITLE": "Updating",
        "UPDATE_DOWNLOADING_MSG": "Downloading update package, please wait...\n(App will automatically close and relaunch when done)",
        "UPDATE_SCRIPT_NOT_FOUND": "Error: Update script not found.",
        "UPDATE_DOWNLOAD_ERR": "Download error: {error}",
        "FETCHING_DATA": "FETCHING DATA...",
        "BRIDGE_ERROR": "Bridge Error: {error}",
        "MODULAR_BRIDGE_ERROR": "Modular Bridge Error: {error}",
        "TARGET_PO_LOG": "Target PO: {po_no}",
        "SAP_LOGIN_ERROR_BRIDGE": "SAP connection failed! Please make sure SAP Logon is open.",
        "SAP_LANG_MISMATCH": "SAP Language Mismatch: Application language is set to '{app_lang}', but active SAP session language is '{sap_lang}'. Please close the SAP session and log in with '{app_lang}' language, or change the language from Application Settings.",
        "LOG_PROCESS_STOPPED": "Automation stopped immediately by user.",
        "LOG_NO_ACTIVE_PROCESS": "No active process found to stop.",
        "LOG_PO_EMPTY": "PO number cannot be empty!",
        "LOG_NO_STEPS_SELECTED": "No steps selected to run!",
        "LOG_MODULAR_START_PREFIX": "[MODULAR FLOW] Starting...",
        "LOG_TARGET_PO_PREFIX": "Target PO: {po}",
        "LOG_SELECTED_STEPS_PREFIX": "Selected Steps: {steps}",
        "LOG_PLEASE_ENTER_PO": "Please enter a PO number first!",
        "LOG_ACCESSORY_DELETED": "Accessory: Selected rows deleted from sheet.",

        # --- SAP Screen & Flow Log Statements ---
        "LOG_SINGLE_FLOW_START": "--- Starting Single Order Automation Flow: {po_no} ---",
        "LOG_SINGLE_FLOW_DONE": "🎉 CONGRATULATIONS: ALL processes completed successfully for Single Order {po_no}! ✅",
        "LOG_SINGLE_FLOW_ERROR": "❌ ERROR: Error occurred in Single Order {po_no} workflow: {error}",
        "LOG_SET_FLOW_START": "--- Starting Set (Team) Order Automation Flow: {po_no} ---",
        "LOG_SET_FLOW_DONE": "🎉 CONGRATULATIONS: ALL processes completed successfully for Set Order {po_no}! ✅",
        "LOG_SET_FLOW_ERROR": "❌ ERROR: Error occurred in Set Order {po_no} workflow: {error}",
        "LOG_STEP_START": ">>> STEP {step_num}: Starting {step_name}...",
        "LOG_STEP_SUCCESS": ">>> STEP {step_num}: {step_name} COMPLETED SUCCESSFULLY. ✅",
        
        # --- ZMM0020 Handler Logs ---
        "LOG_ZMM0020_GOTO": "ZMM0020: Navigating to transaction code: ZMM0020",
        "LOG_ZMM0020_MODEL_VAR_START": "ZMM0020: Step 1 - Variant & Model Creation starting.",
        "LOG_ZMM0020_MODEL_VAR_DONE": "ZMM0020: Step 1 - Variant & Model Creation completed.",
        "LOG_ZMM0020_WORKPLAN_START": "ZMM0020: Step 2 - Work Plan Creation starting.",
        "LOG_ZMM0020_WORKPLAN_DONE": "ZMM0020: Step 2 - Work Plan Creation completed.",
        "LOG_ZMM0020_BOM_START": "ZMM0020: Step 3 - BOM Loading starting.",
        "LOG_ZMM0020_BOM_DONE": "ZMM0020: Step 3 - BOM Loading completed.",
        "LOG_ZMM0020_COSTING_START": "ZMM0020: Step 4 - Version & Costing Calculation starting.",
        "LOG_ZMM0020_COSTING_DONE": "ZMM0020: Step 4 - Version & Costing Calculation completed.",
        "LOG_ZMM0020_ALV_LOADED": "ALV data loaded. Row count: {count}",
        "LOG_ZMM0020_ALV_TIMEOUT": "Timeout! ALV data could not be loaded within {timeout} seconds.",
        
        # --- CS01 Handler Logs ---
        "LOG_CS01_MATRIX_START": "CS01: Starting variant matrix filling process.",
        "LOG_CS01_SET_BOM_START": "CS01: Starting BOM creation step for set order.",
        "LOG_CS01_MAIN_MAT_NOT_FOUND": "CS01: Main material code not found. Cannot create BOM.",
        "LOG_CS01_CHILDREN_NOT_FOUND": "CS01: Child products not found. Cannot create BOM.",
        "LOG_CS01_MAIN_MAT_ENTERED": "CS01: Main material code '{mat_code}' and other BOM details entered.",
        "LOG_CS01_CHILD_ROW_ADDING": "CS01: Adding BOM row for Child PLM {plm} (Material: {mat_code}). Quantity: {qty}",
        "LOG_CS01_ALL_ROWS_ENTERED": "CS01: All BOM rows entered and Enter key pressed.",
        "LOG_CS01_BOM_SAVED": "CS01: BOM saved successfully.",
        "LOG_CS01_BOM_SET_SUCCESS": "CS01: BOM creation step for set order completed successfully.",
        "LOG_CS01_ERROR": "CS01: Error occurred while creating BOM for set order: {error}",
        
        # --- MD01N Handler Logs ---
        "LOG_MD01N_START": "MD01N: Starting MRP Live execution process.",
        "LOG_MD01N_MATERIALS_COUNT": "MD01N: Entering total {count} materials into list.",
        "LOG_MD01N_EXECUTING": "MD01N: Executing MRP Live...",
        "LOG_MD01N_DONE": "MD01N: MRP Live process completed.",
        "LOG_MD01N_SINGLE_START": "MD01N: Executing MRP. Material: {mat_code}, Plant: {plant}",
        "LOG_MD01N_SINGLE_DONE": "MD01N: MRP completed successfully for {mat_code}.",
        "LOG_MD01N_ERROR": "MD01N Error: {error}",
        
        # --- Common Actions & SAP Logs ---
        "LOG_SAP_SAVE_START": "SAP Screen: Starting save action (btn[11]).",
        "LOG_SAP_SAVE_SUCCESS": "SAP Screen: Save action completed successfully. Message: {msg}",
        "LOG_SAP_SAVE_FAILED": "SAP Screen: Save action failed. Error Message: {msg}",
        "LOG_SAP_SAVE_TIMEOUT": "SAP Screen: Save action did not complete within {timeout} seconds.",
        "LOG_SAP_STATUS_BAR": "SAP Status Bar Message: [{msg_type}] {text}",
        "LOG_SAP_MODE": "SAP Screen: Current mode '{mode}'.",
        "LOG_SAP_MODE_ALREADY_CHANGE": "SAP Screen is already in 'Change' mode.",
        "LOG_SAP_SWITCHING_CHANGE": "SAP Screen is in 'Display' mode. Switching to 'Change' mode.",
        "LOG_SAP_SWITCHED_CHANGE": "SAP Screen successfully switched to 'Change' mode.",
        "LOG_SAP_POPUP_OK": "Generic SAP pop-up 'OK' button pressed.",
        
        # --- ZMM0170 & ZPP0030 & ZSD0010 Logs ---
        "LOG_ZMM0170_START": "ZMM0170: Starting material status check...",
        "LOG_ZMM0170_DONE": "ZMM0170: Material status check completed.",
        "LOG_ZPP0030_START": "ZPP0030: Starting production order check...",
        "LOG_ZPP0030_DONE": "ZPP0030: Production order check completed.",
        "LOG_ZSD0010_START": "ZSD0010: Starting sales order check...",
        "LOG_ZSD0010_DONE": "ZSD0010: Sales order check completed.",

        # --- Additional SAP Connection & System Logs ---
        "LOG_SAP_CONN_NOT_FOUND": "ERROR: Active SAP connection named '{system_name}' not found.",
        "LOG_SAP_MANUAL_LOGON": "Please open the system manually from SAP Logon Pad.",
        "LOG_SAP_CONNECTED": "Successfully connected to '{system_name}' system. Transaction Code: '{tx}'",
        "LOG_SAP_LOGIN_DETECTED": "SAP Login screen detected. Logging in as '{username}' with SAP language '{target_lang}' per app language '{app_lang}'...",
        "LOG_SAP_ACTIVE_LANG": "Active SAP Session Language: '{raw_lang}' ({curr_lang}), Application Language: '{app_lang}'",
        "LOG_SAP_SESSION_READY": "SAP session is ready to use.",
        "LOG_SAP_CONN_ERROR_DETAIL": "Error during SAP connection / language check: {error}",

        # --- ZMM0020 Step & Section Logs ---
        "LOG_S1_START": "--- [S1] Variant & Model Entry Started ---",
        "LOG_S1_DONE": "--- [S1] Completed Successfully ---",
        "LOG_S2_START": "--- [S2] Work Plan & Routing Started ---",
        "LOG_S2_DONE": "--- [S2] Completed Successfully ---",
        "LOG_S3_START": "--- [S3] BOM (Excel) Upload Step Started ---",
        "LOG_S3_DONE": "--- [S3] Completed Successfully ---",
        "LOG_S4_START": "--- [S4] Production Version & Costing Step Started ---",
        "LOG_S4_DONE": "--- [S4] Completed Successfully ---",
        "LOG_ZMM0021_ENTRY": "Entering ZMM0021 for model code: {model_code}, werks: {werks}",
        "LOG_PV_CONTROL_START": "Production versions check process started (Dynamic Progress Mode)...",
        "LOG_PV_PROGRESS": "Progress detected: {last} -> {current} empty cells remaining. Retry count saved.",
        "LOG_PV_NO_PROGRESS": "No progress! Empty cell count is still {current}. Attempt: {attempt}/{max_attempt}",
        "LOG_PV_CREATE_BTN": "Clicking 'Create Production Version' button...",
        "LOG_PV_ALL_DONE": "All production versions ('X') completed successfully. ✅",
        "LOG_COSTING_TAB_START": "ZMM0020: Costing tab operations starting.",
        "LOG_COSTING_DETAIL_BTN": "Clicking 'DETAIL' button in Costing ALV grid.",
        "LOG_COSTING_ACTION_START": "Starting costing operation: Button '{button_id}', Column '{check_col}'",
        "LOG_COSTING_COL_SUCCESS": "Column '{check_col}' set to 'X' in all rows. Operation successful. ✅",
        "LOG_COSTING_PROGRESS": "Progress detected: {last} -> {current} rows remaining. Retry count preserved.",
        "LOG_COSTING_NO_PROGRESS": "No progress! Still {current} rows missing. Attempt: {attempt}/{max_attempt}",
        "LOG_COSTING_ALL_DONE": "All Costing tab operations completed successfully.",
        "LOG_POPUP_CHECKING": "Checking pop-ups...",
        "LOG_POPUP_NOT_FOUND": "ZMM0020: No pop-up found, continuing normal flow.",
        # --- Playwright Auth Manager & Fiori Logs ---
        "LOG_TOKEN_CLEARING": "Önbellekteki token temizleniyor (401 / Yetkisiz erişim veya zorunlu yenileme)...",
        "LOG_TOKEN_USING_CACHED": "Önbellekten geçerli token kullanılıyor (Playwright).",
        "LOG_TOKEN_ACQUIRING": "Playwright ile token alınmaya çalışılıyor...",
        "LOG_TOKEN_CAPTURED_HEADER": "Token Authorization header'ından başarıyla yakalandı! (URL: {url}...)",
        "LOG_TOKEN_CAPTURED_JSON": "Token API yanıtından (JSON) başarıyla yakalandı! (URL: {url}...)",
        "LOG_TOKEN_SAVED": "Token başarıyla alındı ve önbelleğe kaydedildi (Playwright).",

        # --- Core Workflow Manager ---
        "LOG_FETCHING_API_DATA": "API'den veri çekiliyor ve cache'e kaydediliyor...",
        "LOG_DETECTED_COUNTRY": "MDX'ten tespit edilen ülke: '{country}' -> Dinamik PRODUCT_INFO_COUNTRY_ID: {country_id}",
        "LOG_NO_COUNTRY_MDX": "MDX verisinde ülke bilgisi bulunamadı. Kullanılan COUNTRY_ID: {country_id}",
        "LOG_CONVERTING_JSON": "Veri JSON formatına dönüştürülüyor",
        "LOG_DATA_SAVED_JSON": "Veri JSON olarak kaydedildi.",

        # --- Currency Helper ---
        "LOG_EXCHANGE_RATE": "Güncel {curr} Kuru Çekildi: {rate}",

        # --- CLI BOM Template Generator ---
        "LOG_NO_COLOR_CODE": "JSON verisinde renk kodu bulunamadı, Renk dropdown'ı boş olabilir.",
        "LOG_NO_SIZE_CODE": "JSON verisinde beden kodu bulunamadı",
        "LOG_BOM_TEMPLATE_INFO": "BOM Şablonu için PLM ID: {plm_id}, Renkler: {colors}, Bedenler: {sizes}",
        "LOG_BOM_TEMPLATE_CREATED": "BOM şablonu '{path}' başarıyla oluşturuldu. Kullanıcının doldurması bekleniyor.",
        "LOG_FETCHING_VARIANTS": "Varyant değerleri API'den çekiliyor. PO: {po_no}",
        "LOG_CREATING_SET_BOM": "SET BOM Şablonu oluşturuluyor: {style_name} (Çocuk Sayısı: {count})",
        "LOG_CREATING_EXCEL_TEMPLATE_TYPE": "Excel şablonu oluşturuluyor... Tür: {type}",
        "LOG_EXCEL_TEMPLATE_SUCCESS": "Excel şablonu başarıyla oluşturuldu.",

        # --- Variant Value API ---
        "LOG_SENDING_API_REQ": "API isteği gönderiliyor. PO: [{po_no}]",

        # --- Dashboard Page Background & Fiori ---
        "LOG_BACKGROUND_FIORI_START": "--- [ARKA PLAN] Fiori Veri Toplama Başlatıldı (PO: {po_no}) ---",
        "LOG_BACKGROUND_FIORI_SET": "Arka Plan: SET siparişi için Fiori süreci...",
        "LOG_BACKGROUND_FIORI_DONE": "--- [ARKA PLAN] Fiori Başarıyla Tamamlandı ---",
        "LOG_BACKGROUND_FIORI_DONE_PO": "--- [ARKA PLAN] Fiori Veri Toplama Başarıyla Tamamlandı (PO: {po_no}) ---",
        "LOG_STEP_STARTED_FIORI": ">>> [ADIM BAŞLADI] Fiori + ZSD0010",

        # --- ZSD0010 Fiori Handler ---
        "LOG_FIORI_START_BROWSER": "Playwright tarayıcısı başlatılıyor...",
        "LOG_FIORI_GOTO_LOGIN": "Fiori login sayfasına gidiliyor: {url}",
        "LOG_FIORI_WAIT_FORM": "Login form elementlerinin yüklenmesi bekleniyor...",
        "LOG_FIORI_FORM_FOUND": "Login form elementleri bulundu.",
        "LOG_FIORI_ENTER_CRED": "Kullanıcı adı ve şifre giriliyor.",
        "LOG_FIORI_SELECT_LANG": "Dili '{lang}' olarak seçiliyor.",
        "LOG_FIORI_CLICK_LOGIN": "Giriş butonuna tıklanıyor.",
        "LOG_FIORI_WAIT_LAUNCHPAD": "Fiori Launchpad'in yüklenmesi bekleniyor (#shell-header elementi kontrol ediliyor)...",
        "LOG_FIORI_LOGIN_SUCCESS": "Fiori Launchpad'e başarıyla giriş yapıldı.",
        "LOG_ZSD0010_QUERY_PLM": "ZSD0010: PLM '{plm_id}' sorgulanıyor. (Child: {is_child}, PO: {po_no})",
        "LOG_ZSD0010_NO_OFFER_ERR": "HATA: {plm_id} numaralı PLM için Fiori'de uygun bir teklif satırı bulunamadı! Lütfen Fiori üzerinden teklif durumunu ve fiyatlandırmayı kontrol edin.",
        "LOG_ZSD0010_FIORI_ERR": "Fiori İşlem Hatası: {msg}",
        # --- Playwright Auth Manager & Fiori Logs ---
        "LOG_TOKEN_CLEARING": "Clearing cached token (401 / Unauthorized or forced refresh)...",
        "LOG_TOKEN_USING_CACHED": "Using valid token from cache (Playwright).",
        "LOG_TOKEN_ACQUIRING": "Attempting to acquire token with Playwright...",
        "LOG_TOKEN_CAPTURED_HEADER": "Token successfully captured from Authorization header! (URL: {url}...)",
        "LOG_TOKEN_CAPTURED_JSON": "Token successfully captured from API response (JSON)! (URL: {url}...)",
        "LOG_TOKEN_SAVED": "Token successfully acquired and saved to cache (Playwright).",

        # --- Core Workflow Manager ---
        "LOG_FETCHING_API_DATA": "Fetching data from API and saving to cache...",
        "LOG_DETECTED_COUNTRY": "Detected country from MDX: '{country}' -> Dynamic PRODUCT_INFO_COUNTRY_ID: {country_id}",
        "LOG_NO_COUNTRY_MDX": "No country info in MDX data. Using COUNTRY_ID: {country_id}",
        "LOG_CONVERTING_JSON": "Converting data to JSON format",
        "LOG_DATA_SAVED_JSON": "Data saved as JSON.",

        # --- Currency Helper ---
        "LOG_EXCHANGE_RATE": "Current {curr} exchange rate fetched: {rate}",

        # --- CLI BOM Template Generator ---
        "LOG_NO_COLOR_CODE": "No color code found in JSON data, Color dropdown may be empty.",
        "LOG_NO_SIZE_CODE": "No size code found in JSON data",
        "LOG_BOM_TEMPLATE_INFO": "BOM Template PLM ID: {plm_id}, Colors: {colors}, Sizes: {sizes}",
        "LOG_BOM_TEMPLATE_CREATED": "BOM template '{path}' successfully created. Awaiting user input.",
        "LOG_FETCHING_VARIANTS": "Fetching variant values from API. PO: {po_no}",
        "LOG_CREATING_SET_BOM": "Creating SET BOM Template: {style_name} (Child Count: {count})",
        "LOG_CREATING_EXCEL_TEMPLATE_TYPE": "Creating Excel template... Type: {type}",
        "LOG_EXCEL_TEMPLATE_SUCCESS": "Excel template created successfully.",

        # --- Variant Value API ---
        "LOG_SENDING_API_REQ": "Sending API request. PO: [{po_no}]",

        # --- Dashboard Page Background & Fiori ---
        "LOG_BACKGROUND_FIORI_START": "--- [BACKGROUND] Fiori Data Collection Started (PO: {po_no}) ---",
        "LOG_BACKGROUND_FIORI_SET": "Background: Fiori process for SET order...",
        "LOG_BACKGROUND_FIORI_DONE": "--- [BACKGROUND] Fiori Successfully Completed ---",
        "LOG_BACKGROUND_FIORI_DONE_PO": "--- [BACKGROUND] Fiori Data Collection Successfully Completed (PO: {po_no}) ---",
        "LOG_STEP_STARTED_FIORI": ">>> [STEP STARTED] Fiori + ZSD0010",

        # --- ZSD0010 Fiori Handler ---
        "LOG_FIORI_START_BROWSER": "Starting Playwright browser...",
        "LOG_FIORI_GOTO_LOGIN": "Navigating to Fiori login page: {url}",
        "LOG_FIORI_WAIT_FORM": "Waiting for login form elements to load...",
        "LOG_FIORI_FORM_FOUND": "Login form elements found.",
        "LOG_FIORI_ENTER_CRED": "Entering username and password.",
        "LOG_FIORI_SELECT_LANG": "Selecting language as '{lang}'.",
        "LOG_FIORI_CLICK_LOGIN": "Clicking login button.",
        "LOG_FIORI_WAIT_LAUNCHPAD": "Waiting for Fiori Launchpad to load (checking #shell-header element)...",
        "LOG_FIORI_LOGIN_SUCCESS": "Successfully logged in to Fiori Launchpad.",
        "LOG_FIORI_LOGIN_FAIL": "Could not log in to Fiori Launchpad. #shell-header element not found.",
        "LOG_FIORI_CRITICAL_ERR": "Critical error during Fiori login: {error}",
        "LOG_ZSD0010_FILTER_START": "ZSD0010: Starting filter with PLM code '{plm_code}'.",
        "LOG_ZSD0010_FILTER_APPLIED": "PLM code '{plm_code}' entered and filter applied.",
        "LOG_ZSD0010_ROWS_FOUND": "Found {count} rows after filtering.",
        "LOG_ZSD0010_NO_ITEMS": "No items found for PLM code '{plm_code}'.",
        "LOG_ZSD0010_ROW_PROCESSING": "Processing row {row}...",
        "LOG_ZSD0010_EXTRACTED_PRICE": "Row {row} - Extracted Price: {price}",
        "LOG_ZSD0010_APPROVAL_STATUS": "Row {row} - Approval Status: {status}",
        "LOG_ZSD0010_PLM_STATUS": "Row {row} - PLM Status: {status}",
        "LOG_ZSD0010_QUERY_PLM": "ZSD0010: Querying PLM '{plm_code}'. (Child: {is_child}, PO: {po_no})",
        "LOG_ZSD0010_NO_OFFER_ERR": "ERROR: Suitable offer line not found in Fiori for PLM {plm_code}! Please check offer status and pricing on Fiori.",
        "LOG_ZSD0010_MATCH_FOUND": "Match Found: {primary_id}. Navigating to detail.",
        "LOG_ZSD0010_JS_SUCCESS": "JS Success! Live Data -> PLM: {plm_check}, Bid: {bid_no}",
        "LOG_ZSD0010_PLM_MISMATCH": "WARNING: Screen PLM ({plm_check}) does not match expected ({expected})!",
        "LOG_ZSD0010_ORG_FETCHED": "Organizational data fetched successfully: {sales_org}",
        "LOG_ZSD0010_POPUP_CLOSE_TRY": "Attempting to close pop-up...",
        "LOG_ZSD0010_POPUP_CLOSED_OK": "Pop-up closed with 'Tamam' text.",
        "LOG_ZSD0010_POPUP_CLOSED_ID": "Pop-up closed with ID pattern ({id}).",
        "LOG_ZSD0010_POPUP_ESC": "Close button not found, pressing 'ESC' key.",
        "LOG_ZSD0010_POPUP_CLOSE_ERR": "Critical error while closing pop-up: {error}",
        "LOG_ZSD0010_ORG_BTN_NOT_FOUND": "Organizational Data button (#__button13) not present on this screen.",
        "LOG_ZSD0010_ORG_FETCH_FAIL": "Could not fetch organizational data, continuing process: {error}",
        "LOG_ZSD0010_NAV_BACK": "Process finished, returning to main list...",
        "LOG_ZSD0010_BACK_CLICKED": "Back button clicked successfully.",
        "LOG_ZSD0010_BACK_ERR": "Back button could not be clicked: {error}. Trying browser back command.",
        "LOG_ZSD0010_WAIT_NEXT_PLM": "Fiori: Waiting for next PLM query field for set order...",
        "LOG_ZSD0010_NEXT_FIELD_NOT_READY": "Fiori: Next input field not ready, but continuing: {error}",
        "LOG_ZSD0010_FIORI_ERR": "Fiori Operation Error: {error}",
        "LOG_ZSD0010_BTN_PRESSED": "ZSD0010: '{desc}' ({btn_id}) button pressed successfully.",
        "LOG_ZSD0010_BTN_INACTIVE": "ZSD0010: '{desc}' ({btn_id}) button is currently inactive or not found. Skipping...",
        "LOG_ZSD0010_SUBGRID_ROW": "Sub Grid Row {row}: Material No: {mat}",
        "LOG_ZSD0010_SUBGRID_DATA": "Sub Grid Row {row}: PLM {plm} -> Bid: {bid}, Price: {price}",
        "LOG_ZSD0010_SUBGRID_ERR": "Sub Grid Row {row}: PLM {plm} -> Bid: {bid}, Price: {price} -> ERROR: {error}",
        "LOG_ZSD0010_CHECK_ETA": "ZSD0010: Checking sub grid '&ETA'.",
        "LOG_ZSD0010_CHECK_CHECK": "ZSD0010: Checking sub grid '&CHECK'.",
        "LOG_ZSD0010_SUBGRID_MSG_ERR": "ZSD0010 Sub Grid Error: {msg}",
        "LOG_ZSD0010_SUBGRID_MSG_WARN": "ZSD0010 Sub Grid Warning: {msg}",
        "LOG_ZSD0010_SUBGRID_MSG_SUCCESS": "ZSD0010 Sub Grid Verification Successful: {msg}",
        "LOG_ZSD0010_BTN0_PRESSED": "wnd[2]/tbar[0]/btn[0]: Pressed",
        "LOG_ZSD0010_SUBGRID_VAL_ERR": "ZSD0010: Error during sub grid verification: {error}",
        "LOG_ZSD0010_GUI_START": "ZSD0010 GUI: Process starting. PO: {po}, Type: {order_type}",
        "LOG_ZSD0010_PO_NOT_FOUND": "ZSD0010: No records found for PO {po}.",
        "LOG_ZSD0010_SET_BOM_SIZE_START": "ZSD0010: Processing BOM_SIZE details for each row in set order.",
        "LOG_ZSD0010_POPUP_ROW_PROCESSING": "ZSD0010: Processing Pop-up Row {current}/{total}.",
        "LOG_ZSD0010_ROW_SUBGRID_DONE": "ZSD0010: Row {row} sub grid process completed.",
        "LOG_ZSD0010_BOM_SIZE_BTN_ERR": "ZSD0010: BOM_SIZE button for row {row} not found or could not be pressed: {error}",
        "LOG_ZSD0010_POPUP_MSG": "ZSD0010 Pop-up Message: '{msg}'",
        "LOG_ZSD0010_SAP_INTEG_ERR": "ZSD0010 SAP Integration Error: {msg}",
        "LOG_ZSD0010_POPUP_CONFIRM": "ZSD0010: Confirming pop-up (Yes/OK).",
        "LOG_ZSD0010_FINAL_INFO": "ZSD0010 Final Info: {msg}",
        "LOG_ZSD0010_NO_CONFIRM_POPUP": "ZSD0010: Expected confirmation pop-up (wnd[2]) did not appear, checked status bar.",
        "LOG_ZSD0010_POPUP_UNEXPECTED_ERR": "ZSD0010: Unexpected error during pop-up processing: {error}",
        "LOG_ZSD0010_GUI_ERR": "ZSD0010 GUI Error: {error}",
        "LOG_SELECTED_STEPS": "Selected Steps: {steps}",
        "LOG_MODULAR_PROCESS_START": "--- Modular Process Started: {po_no} ---",

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
