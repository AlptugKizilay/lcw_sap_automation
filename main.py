import json
import logging
import os
import time # Gerekirse bekleme süreleri için eklendi

# İş akışını yönetecek ana fonksiyonu src/core/workflow_manager.py'den import ediyoruz
from src.util.update_json_cache import update_json_cache
from src.core.workflow_manager import run_full_sap_automation
from src.sap_automation.sap_connection import get_sap_session
# Workflow'ları import ediyoruz
from src.sap_automation.workflows.single_order_flow import run_single_order_workflow, run_modular_single_order_workflow
from src.sap_automation.workflows.set_order_flow import run_modular_set_order_workflow, run_set_order_workflow, step_set_fiori_zsd
from src.cli.generate_bom_template import generate_bom_template_cli
from src.util.config_manager import ConfigManager
MASTER_SET_SEQUENCE = ["ZMM0020", "CS01", "FIORI", "ZSD0010", "MD01N", "ZPP0030"]
MASTER_SINGLE_SEQUENCE = ["ZMM0020", "FIORI", "ZSD0010", "ZPP0030"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- API'ler için gerekli parametreler ---
PRODUCT_INFO_PUBLISHED_LABEL_ID = 61
# PRODUCT_INFO_COUNTRY_ID varsayılan olarak None bırakılırsa MDX'teki 'Siparişin Geçildiği Ülke'ye göre otomatik seçilir:
# {id: 56, name: "EGYPT"}, {id: 57, name: "MOROCCO"}, {id: 48, name: "TURKEY"}
PRODUCT_INFO_COUNTRY_ID = None 
PRODUCT_INFO_PRODUCT_SEARCH_TYPE = 0
# ---------------------------------------------------

# --- CACHE AYARLARI ---
JSON_CACHE_DIR = "cache" # Cache dosyalarının saklanacağı dizin
# JSON_CACHE_FILE yolu, hedef_siparis_kodu'na göre dinamik olarak belirlenecek.
# ----------------------

# --- GELİŞTİRME MODU AYARLARI (MEVCUT KALSIN) ---
USE_STATIC_JSON = False # True JSON'u dosyadan okur. False API'den çeker.
STATIC_JSON_PATH = "src\data\dev_single_order_data.json" # Statik JSON dosyasının yolu
# -------------------------------------------------

if __name__ == "__main__":
    #for development
    hedef_siparis_kodu = 1208703
    create_template = False # !!! İlk çalıştırma için False yapın (cache'lemek ve Excel oluşturmak için)
                            # !!! Daha sonra True yapın (cache'ten okuyup otomasyonu başlatmak için)
    
    final_json_output = None # final_json_output'ı başlangýtça None olarak ayarlayın

    # Sipariş koduna özel cache dosya yolunu belirle
    json_cache_file_path = os.path.join(JSON_CACHE_DIR, f"order_data_cache_{hedef_siparis_kodu}.json")

    # Cache dizinini kontrol et ve yoksa oluştur
    if not os.path.exists(JSON_CACHE_DIR):
        os.makedirs(JSON_CACHE_DIR)
        logger.info(f"Cache dizini oluşturuldu: {JSON_CACHE_DIR}")

    print("--- SAP Otomasyonu Başlatılıyor ---")
    try:
        # 1. JSON Verisini Yönetme (API'den çekme, Cache'ten okuma veya Statik JSON kullanma)
        if USE_STATIC_JSON: # Geliştirme modu: API'yi hiç çağırma, doğrudan statik dosyadan oku
            if os.path.exists(STATIC_JSON_PATH):
                with open(STATIC_JSON_PATH, 'r', encoding='utf-8') as f:
                    final_json_output = json.load(f)
                logger.info(f"Geliştirme modu aktif: Veri '{STATIC_JSON_PATH}' dosyasından yüklendi.")
            else:
                logger.error(f"HATA: Statik JSON dosyası bulunamadı: '{STATIC_JSON_PATH}'. Lütfen dosyayı oluşturun veya USE_STATIC_JSON'ı False yapın.")
                exit()
        elif create_template: # create_template = True ise cache'ten oku (API'yi çağırma)
            if os.path.exists(json_cache_file_path):
                with open(json_cache_file_path, 'r', encoding='utf-8') as f:
                    final_json_output = json.load(f)
                logger.info(f"Veri '{json_cache_file_path}' cache dosyasından yüklendi. API çağrısı yapılmadı.")
            else:
                logger.error(f"HATA: '{json_cache_file_path}' cache dosyası bulunamadı. "
                             f"Lütfen ilk olarak 'create_template = False' ile Excel şablonunu oluşturup veriyi cache'leyin.")
                exit()
        else: # create_template = False ise API'den çek ve cache'e kaydet
            logger.info("API'den veri çekiliyor ve cache'e kaydediliyor...")
            final_json_output = run_full_sap_automation(
                hedef_siparis_kodu,
                PRODUCT_INFO_PUBLISHED_LABEL_ID,
                PRODUCT_INFO_COUNTRY_ID, # None geçildiğinde MDX'teki 'Siparişin Geçildiği Ülke'ye göre dinamik seçilir
                PRODUCT_INFO_PRODUCT_SEARCH_TYPE
            )        
            if final_json_output:
                with open(json_cache_file_path, 'w', encoding='utf-8') as f:
                    json.dump(final_json_output, f, indent=4, ensure_ascii=False)
                logger.info(f"API'den çekilen veri '{json_cache_file_path}' dosyasına kaydedildi.")
            else:
                logger.error("API'den veri çekilemedi. Otomasyon durduruluyor.")
                exit()

        # JSON verisinin nihai çıktısını göster (sadece bilgi amaçlı)
        if final_json_output:
            print("\n--- Nihai JSON Çıktısı ---")
            print(json.dumps(final_json_output, indent=4, ensure_ascii=False))
        else:
            logger.error("JSON verisi boş veya geçersiz. Otomasyon durduruluyor.")
            exit()


        # 2. Sipariş Tipi Belirleme ve İş Akışını Başlatma
        order_data = None
        if isinstance(final_json_output, list) and len(final_json_output) > 0:
            order_data = final_json_output[0] # Listenin ilk elemanını al
        elif isinstance(final_json_output, dict):
            order_data = final_json_output # Zaten dict ise doğrudan kullan
        
        if not order_data:
            logger.error("Sipariş verisi JSON çıktısından alınamadı. Otomasyon durduruluyor.")
            exit()

        order_type = order_data.get("orderType")
        if not order_type:
            logger.error("Sipariş tipi JSON verisinde bulunamadı. Otomasyon durduruluyor.")
            exit()
            
        print(f"\nSipariş Tipi Belirlendi: {order_type.upper()}")
        
        # create_template durumuna göre farklı aksiyonlar
        if not create_template: 
            logger.info("BOM Şablonu oluşturma modu aktif. Excel şablonu oluşturuluyor...")
            # Sipariş tipine göre farklı CLI fonksiyonlarını çağırıyoruz
            if order_type == "single":
                from src.cli.generate_bom_template import generate_bom_template_cli
                generate_bom_template_cli(order_data)
            elif order_type == "set":
                from src.cli.generate_bom_template import generate_set_bom_template_cli
                generate_set_bom_template_cli(order_data)
            
            logger.info("BOM Şablonu başarıyla oluşturuldu. SAP otomasyonu başlatılmadı.")
            exit() 
        else: # create_template True ise, SAP otomasyonunu başlat
            logger.info("create_template = True. SAP otomasyonu başlatılıyor...")
            
            # SAP Session'ı başlat (Daha önce hazırladığınız sağlam yapı)
            session = get_sap_session()
            if session:
                if order_type == "single":
                    print("Tekli Sipariş Workflow'u başlatılıyor...")
                    run_single_order_workflow(session, order_data)
                elif order_type == "set":
                    print("Takımlı Sipariş Workflow'u başlatılıyor...")
                    run_set_order_workflow(session, order_data)
                else:
                    print(f"HATA: Tanımlanamayan sipariş tipi: {order_type}")
            else:
                print("HATA: SAP bağlantısı kurulamadığı için otomasyon adımlarına geçilemiyor.")

    except Exception as e:
        print(f"\n--- Otomasyonda Beklenmedik Bir Hata Oluştu ---")
        print(f"Hata: {e}")
        logger.error(f"Uygulama hatası: {e}", exc_info=True)


def start_automation_process1(hedef_siparis_kodu, create_template):

    json_dir = ConfigManager.JSON_DIR
    final_json_output = None # final_json_output'ı başlangıçta None olarak ayarlayın

    # Sipariş koduna özel cache dosya yolunu belirle
    json_cache_file_path = os.path.join(json_dir, f"order_data_cache_{hedef_siparis_kodu}.json")

    # Cache dizinini kontrol et ve yoksa oluştur
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
        logger.info(f"Cache dizini oluşturuldu: {json_dir}")

    print("--- SAP Otomasyonu Başlatılıyor ---")
    try:
        # 1. JSON Verisini Yönetme (API'den çekme, Cache'ten okuma veya Statik JSON kullanma)
        if USE_STATIC_JSON: # Geliştirme modu: API'yi hiç çağırma, doğrudan statik dosyadan oku
            if os.path.exists(STATIC_JSON_PATH):
                with open(STATIC_JSON_PATH, 'r', encoding='utf-8') as f:
                    final_json_output = json.load(f)
                logger.info(f"Geliştirme modu aktif: Veri '{STATIC_JSON_PATH}' dosyasından yüklendi.")
            else:
                logger.error(f"HATA: Statik JSON dosyası bulunamadı: '{STATIC_JSON_PATH}'. Lütfen dosyayı oluşturun veya USE_STATIC_JSON'ı False yapın.")
                exit()
        elif create_template: # create_template = True ise cache'ten oku (API'yi çağırma)
            if os.path.exists(json_cache_file_path):
                with open(json_cache_file_path, 'r', encoding='utf-8') as f:
                    final_json_output = json.load(f)
                logger.info(f"Veri '{json_cache_file_path}' cache dosyasından yüklendi. API çağrısı yapılmadı.")
            else:
                logger.error(f"HATA: '{json_cache_file_path}' cache dosyası bulunamadı. "
                             f"Lütfen ilk olarak 'create_template = False' ile Excel şablonunu oluşturup veriyi cache'leyin.")
                exit()
        else: # create_template = False ise API'den çek ve cache'e kaydet
            logger.info("API'den veri çekiliyor ve cache'e kaydediliyor...")
            final_json_output = run_full_sap_automation(
                hedef_siparis_kodu,
                PRODUCT_INFO_PUBLISHED_LABEL_ID,
                PRODUCT_INFO_COUNTRY_ID,
                PRODUCT_INFO_PRODUCT_SEARCH_TYPE
            )        
            if final_json_output:
                with open(json_cache_file_path, 'w', encoding='utf-8') as f:
                    json.dump(final_json_output, f, indent=4, ensure_ascii=False)
                logger.info(f"API'den çekilen veri '{json_cache_file_path}' dosyasına kaydedildi.")
            else:
                logger.error("API'den veri çekilemedi. Otomasyon durduruluyor.")
                exit()

        # JSON verisinin nihai çıktısını göster (sadece bilgi amaçlı)
        if final_json_output:
            print("\n--- Nihai JSON Çıktısı ---")
            print(json.dumps(final_json_output, indent=4, ensure_ascii=False))
        else:
            logger.error("JSON verisi boş veya geçersiz. Otomasyon durduruluyor.")
            exit()


        # 2. Sipariş Tipi Belirleme ve İş Akışını Başlatma
        order_data = None
        if isinstance(final_json_output, list) and len(final_json_output) > 0:
            order_data = final_json_output[0] # Listenin ilk elemanını al
        elif isinstance(final_json_output, dict):
            order_data = final_json_output # Zaten dict ise doğrudan kullan
        
        if not order_data:
            logger.error("Sipariş verisi JSON çıktısından alınamadı. Otomasyon durduruluyor.")
            exit()

        order_type = order_data.get("orderType")
        if not order_type:
            logger.error("Sipariş tipi JSON verisinde bulunamadı. Otomasyon durduruluyor.")
            exit()
            
        print(f"\nSipariş Tipi Belirlendi: {order_type.upper()}")
        
        # create_template durumuna göre farklı aksiyonlar
        if not create_template: 
            logger.info("BOM Şablonu oluşturma modu aktif. Excel şablonu oluşturuluyor...")
            # Sipariş tipine göre farklı CLI fonksiyonlarını çağırıyoruz
            if order_type == "single":
                from src.cli.generate_bom_template import generate_bom_template_cli
                generate_bom_template_cli(order_data)
            elif order_type == "set":
                from src.cli.generate_bom_template import generate_set_bom_template_cli
                generate_set_bom_template_cli(order_data)
            
            logger.info("BOM Şablonu başarıyla oluşturuldu. Şablon doldurulduktan sonra 'START AUTOMATION' butonuna tıklayın.")
            exit() 
        else: # create_template True ise, SAP otomasyonunu başlat
            logger.info("create_template = True. SAP otomasyonu başlatılıyor...")
            
            # SAP Session'ı başlat (Daha önce hazırladığınız sağlam yapı)
            session = get_sap_session()
            if session:
                if order_type == "single":
                    print("Tekli Sipariş Workflow'u başlatılıyor...")
                    run_single_order_workflow(session, order_data, json_cache_file_path)
                elif order_type == "set":
                    print("Takımlı Sipariş Workflow'u başlatılıyor...")
                    run_set_order_workflow(session, order_data, json_cache_file_path)
                else:
                    print(f"HATA: Tanımlanamayan sipariş tipi: {order_type}")
            else:
                print("HATA: SAP bağlantısı kurulamadığı için otomasyon adımlarına geçilemiyor.")

    except Exception as e:
        print(f"\n--- Otomasyonda Beklenmedik Bir Hata Oluştu ---")
        print(f"Hata: {e}")
        logger.error(f"Uygulama hatası: {e}", exc_info=True)
        
        





def start_automation_process(hedef_siparis_kodu, create_template):
    """
    KLASİK AKIŞ:
    - create_template=False: API'den veri çeker, JSON kaydeder ve Excel oluşturur.
    - create_template=True:  JSON'dan veriyi okur ve TÜM SAP adımlarını sırayla yapar.
    """
    json_dir = ConfigManager.JSON_DIR
    json_cache_file_path = os.path.join(json_dir, f"order_data_cache_{hedef_siparis_kodu}.json")

    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    print(f"\n--- SAP Otomasyonu (Klasik Mod) Başlatıldı: {hedef_siparis_kodu} ---")
    
    try:
        final_json_output = None

        # 1. VERİ YÖNETİMİ
        if create_template: # SAP OTOMASYON MODU: Cache'ten oku
            if os.path.exists(json_cache_file_path):
                with open(json_cache_file_path, 'r', encoding='utf-8') as f:
                    final_json_output = json.load(f)
                logger.info(f"Veri cache dosyasından yüklendi.")
            else:
                logger.error(f"HATA: {json_cache_file_path} bulunamadı. Önce Excel şablonu oluşturmalısınız.")
                return False
        else: # EXCEL/API MODU: API'den çek ve kaydet
            logger.info("API'den veri çekiliyor ve cache'e kaydediliyor...")
            
            # SENİN FONKSİYONUNU ÇAĞIRIYORUZ
            # Eğer bu fonksiyon main.py içinde değilse, yukarıda import edilmiş olmalı.
            final_json_output = run_full_sap_automation(
                hedef_siparis_kodu,
                PRODUCT_INFO_PUBLISHED_LABEL_ID,
                PRODUCT_INFO_COUNTRY_ID,
                PRODUCT_INFO_PRODUCT_SEARCH_TYPE
            )        
            
            if final_json_output:
                with open(json_cache_file_path, 'w', encoding='utf-8') as f:
                    json.dump(final_json_output, f, indent=4, ensure_ascii=False)
                logger.info(f"Veri JSON olarak kaydedildi.")
            else:
                logger.error("API'den veri çekilemedi.")
                return False

        # 2. VERİ ANALİZİ
        if not final_json_output: return False
        order_data = final_json_output[0] if isinstance(final_json_output, list) else final_json_output
        order_type = str(order_data.get("orderType", "")).lower()

        # 3. AKSİYON BELİRLEME
        if not create_template: # EXCEL OLUŞTURMA MODU
            logger.info(f"Excel şablonu oluşturuluyor... Tür: {order_type}")
            if order_type == "single":
                from src.cli.generate_bom_template import generate_bom_template_cli
                generate_bom_template_cli(order_data)
            elif order_type == "set":
                from src.cli.generate_bom_template import generate_set_bom_template_cli
                generate_set_bom_template_cli(order_data)
            
            logger.info("Excel şablonu başarıyla oluşturuldu.")
            
            # --- B. FIORI ARKA PLAN THREAD'İ (Hemen ardından ateşlenir) ---
            # Kullanıcı Excel'i açarken robot Fiori'ye login olmaya başlar.
            fiori_thread = threading.Thread(
                target=run_background_fiori_task,
                args=(hedef_siparis_kodu, json_cache_file_path),
                daemon=True # Program kapanırsa thread de kapansın
            )
            fiori_thread.start()
            
            return True # Fonksiyon biter, UI rahatlar, Excel klasörü açılır.
            

        else: # SAP OTOMASYON MODU (TÜM ADIMLAR)
            if order_type == "single":
                target_steps = MASTER_SINGLE_SEQUENCE
            elif order_type == "set":
                target_steps = MASTER_SET_SEQUENCE
            else:
                logger.error(f"Tanımlanamayan sipariş tipi: {order_type}")
                return False

            logger.info(f"Klasik 'Start Automation' tetiklendi. Modüler motor '{order_type}' için tüm adımları ( {target_steps} ) sırayla yapacak.")
            
            # Tüm işi artık tek bir noktaya (Modular Process) devrediyoruz
            return start_modular_process(hedef_siparis_kodu, target_steps)

    except Exception as e:
        logger.error(f"start_automation_process hatası: {e}", exc_info=True)
        return False


def start_modular_process(po_no, selected_steps, bridge):
    """
    MODÜLER AKIŞ (FAZ-2):
    Sadece kullanıcının seçtiği adımları çalıştırır.
    """
    try:
        logger.info(f"--- Modüler Süreç Başlatıldı: {po_no} ---")
        
        # 1. Veriyi Cache'ten yükle
        json_path = os.path.join(ConfigManager.JSON_DIR, f"order_data_cache_{po_no}.json")
        if not os.path.exists(json_path):
            logger.error(f"HATA: {po_no} için JSON cache bulunamadı.")
            return False
            
        with open(json_path, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
            order_data = full_data[0] if isinstance(full_data, list) else full_data
            
        # --- [ZORUNLU FIORI KONTROLÜ] ---
        # Üretim yeri vb. kritik bilgiler için collected_data şart!
        
        fiori_status = order_data.get('fiori_status')
        collected_data = order_data.get('collected_data')
        if not collected_data or fiori_status == "FAILED":
            logger.info("Kritik Fiori verileri eksik, sistem otomatik tamamlıyor...")
            bridge.update_step_status(selected_steps[0], "running", 0.01)
            
            order_type = str(order_data.get("orderType", "")).lower()
            fiori_success = False
            
            if order_type == "set":
                from src.sap_automation.workflows.set_order_flow import step_set_fiori_zsd
                fiori_success = step_set_fiori_zsd(None, order_data, json_path)
            else:
                from src.sap_automation.workflows.single_order_flow import step_fiori
                fiori_success = step_fiori(None, order_data, json_path)

            # --- HATA KONTROLÜ VE DURDURMA ---
            if not fiori_success:
                error_title = "Fiori Veri Hatası"
                error_msg = "Fiori'den teklif bilgileri (fiyat, üretim yeri vb.) alınamadı!\n\nLütfen Fiori üzerinden modelin plm kodunu ve fiyatını kontrol edin."
                
                logger.error(f"Otomasyon Durduruldu: {error_msg}")

                # 1. UI'daki adımı kırmızı (error) yap
                bridge.update_step_status(selected_steps[0], "error")

                # 2. Pop-up mesajı göster
                from tkinter import messagebox
                messagebox.showerror(error_title, error_msg)

                # 3. OTOMASYONU DURDUR (False dönerek akışı kesiyoruz)
                return False 
            else:
                update_json_cache(json_path, "fiori_status", "SUCCESS")
                logger.info("Fiori verileri başarıyla tamamlandı, SAP adımlarına geçiliyor.")
            
            # Veriyi tazeleyelim
            with open(json_path, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
                order_data = full_data[0] if isinstance(full_data, list) else full_data

        # 2. SAP Session Al
        session = get_sap_session()
        if not session: return False

        # 3. Türüne göre modüler runner'a yönlendir
        order_type = str(order_data.get("orderType", "")).lower()
        
        if order_type == "single":
            return run_modular_single_order_workflow(session, order_data, json_path, selected_steps, bridge)
        elif order_type == "set":
            return run_modular_set_order_workflow(session, order_data, json_path, selected_steps, bridge)
            
        return False

    except Exception as e:
        logger.error(f"start_modular_process hatası: {e}", exc_info=True)
        return False

import threading

def run_background_fiori_task(po_no, cache_file_path):
    """
    Kullanıcı Excel doldururken arka planda Fiori verilerini toplayan işçi.
    """
    try:
        logger.info(f"--- [ARKA PLAN] Fiori Veri Toplama Başlatıldı (PO: {po_no}) ---")
        
        # 1. Cache dosyasından güncel veriyi oku
        if not os.path.exists(cache_file_path):
            logger.error("Arka Plan: Cache dosyası bulunamadı, Fiori işlemi iptal.")
            return
            
        with open(cache_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # JSON liste ise ilk elemanı al
            if isinstance(data, list): data = data[0]

        order_type = str(data.get("orderType", "")).lower()
        fiori_success = False
        # 2. Sipariş Tipine Göre İlgili Fiori Mantığını Çalıştır
        # Not: Session parametresini None gönderiyoruz çünkü Fiori için SAP GUI session gerekmiyor.
        if order_type == "set":
            logger.info("Arka Plan: SET siparişi için Fiori süreci...")
            from src.sap_automation.workflows.set_order_flow import step_set_fiori_zsd 
            fiori_success = step_set_fiori_zsd(None, data, cache_file_path)
            
        else: # single veya single_from_set
            logger.info("Arka Plan: SINGLE siparişi için Fiori süreci...")
            from src.sap_automation.workflows.single_order_flow import step_fiori 
            fiori_success = step_fiori(None, data, cache_file_path)
        if not fiori_success:
            # Hata durumunu JSON'a işaretle (Otomasyon başladığında pop-up tetiklemek için)
            update_json_cache(cache_file_path, "fiori_status", "FAILED")
            # 2. POP-UP GÖSTER (Thread içinden güvenli çağrı)
            if order_type == "set":
                error_msg = (
                    "Fiori'de uygun bir teklif satırı bulunamadı!\n\n"
                    "NE YAPMALIYIM?\n"
                    "1- Fiori üzerinden teklif plm kodunu ve fiyatlandırmayı kontrol edip düzeltin.\n"
                    "Teklif açıklaması PO numasını içermelidir.\n"
                    "2- Excel dosyanızı doldurmaya devam edebilirsiniz.\n"
                    "3- İşlemi tamamladığınızda 'SEÇİLİ ADIMLARI BAŞLAT' butonuna basmanız yeterlidir.\n\n"
                    "NOT: Otomasyon başladığında sistem Fiori verilerini OTOMATİK olarak tekrar kontrol edecektir."
                )
            else:
                error_msg = (
                    "Fiori'de uygun bir teklif satırı bulunamadı!\n\n"
                    "NE YAPMALIYIM?\n"
                    "1- Fiori üzerinden teklif plm kodunu ve fiyatlandırmayı kontrol edip düzeltin.\n"
                    "2- Excel dosyanızı doldurmaya devam edebilirsiniz.\n"
                    "3- İşlemi tamamladığınızda 'SEÇİLİ ADIMLARI BAŞLAT' butonuna basmanız yeterlidir.\n\n"
                    "NOT: Otomasyon başladığında sistem Fiori verilerini OTOMATİK olarak tekrar kontrol edecektir."
                )
            from tkinter import messagebox
            messagebox.showwarning("Fiori Bilgilendirme", error_msg)
            return
        else:
            update_json_cache(cache_file_path, "fiori_status", "SUCCESS")
            logger.info(f"--- [ARKA PLAN] Fiori Başarıyla Tamamlandı ---")

        logger.info(f"--- [ARKA PLAN] Fiori Veri Toplama Başarıyla Tamamlandı (PO: {po_no}) ---")

    except Exception as e:
        logger.error(f"Arka Plan Fiori Hatası: {e}")
        update_json_cache(cache_file_path, "fiori_status", "FAILED")