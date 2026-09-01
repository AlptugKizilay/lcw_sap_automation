# src/sap_automation/workflows/single_order_flow.py

import time
import logging
import json
import os
from src.util.config_manager import ConfigManager
from src.sap_automation.screens.zmm0020_handler import zmm0020_step_1_variants, zmm0020_step_2_routing, zmm0020_step_3_bom, zmm0020_step_4_costing, ensure_target_sizes_selected, press_add_variant_button, ensure_target_colors_selected, manage_color_selections, zmm0020_handle_costing_tab, zmm0020_ensure_production_versions_created, _get_afs_column_metadata_from_prod_versions_tab, zmm0020_set_bom_afs_data, zmm0020_select_bom_operation_and_add_components, zmm0020_bom_sekmesi_matris_ekle, zmm0020_press_create_routing_button, zmm0020_press_create_material_button, zmm0020_is_plani_adimlari, zmm0020_is_plani_sekmesi_giris, get_material_code_from_zmm0020, zmm0020_renk_secimi, zmm0020_ilk_ekran_giris, zmm0020_model_sekmesi_giris, zmm0020_beden_secimi
from src.sap_automation.screens.common_actions import save_sap_screen
from src.cli.generate_bom_template import generate_bom_template_cli
from src.sap_automation.screens.zsd0010_handler import fiori_login ,zsd0010_process_order_integration_gui_v2, zsd0010_process_plm_items_v2,zsd0010_process_plm_items, zsd0010_process_order_integration_gui
from src.sap_automation.screens.zpp0030_handler import zpp0030_process_production_orders
from src.util.config_manager import ConfigManager
from src.util.update_json_cache import update_json_cache
from src.util.handle_sap_popups import handle_sap_popups
from src.sap_automation.screens.md01n_handler import step_md01n_single_mrp
logger = logging.getLogger(__name__)
cfg = ConfigManager()

MASTER_SINGLE_SEQUENCE = ["ZMM0020", "ZSD0010", "ZPP0030"]
def zmm0020_single_order_flow(session, data):
    """
    ZMM0020 ekranı için genel iş akışını yönetir.
    Tekli siparişler ve set siparişler için ortak adımlar burada yer alır.
    """
    try:
        print("--- ZMM0020 Genel Akışı Başladı ---")
       
        # 1. ZMM0020 Ekranına giriş ve temel bilgilerin doldurulması
        if not zmm0020_ilk_ekran_giris(session, data):
            raise Exception("ZMM0020 ilk ekran giriş adımı başarısız.")
        # 2. ZMM0020 - Model Sekmesi
        if not zmm0020_model_sekmesi_giris(session, data):
            raise Exception("ZMM0020 model sekmesi giriş adımı başarısız.")
   #    
        # 3. Beden Seçimi ve Varyant Oluşturma adımları
        if not zmm0020_beden_secimi(session, data):
            raise Exception("Beden seçimi adımı başarısız.")
        #ensure size selected
        if not ensure_target_sizes_selected(session, data):
            raise Exception("Beden seçimi ensure adımı basarısız.")
   #    
        # manage_color_selections
        if not manage_color_selections(session, data):
            raise Exception("Varyant kontrol adımı basarısız.")
        # 4. Renk Seçimi adımları
        if not zmm0020_renk_secimi(session, data):
            raise Exception("Renk seçimi adımı başarısız.")     
   #    #ensure color selected
        if not ensure_target_colors_selected(session, data):
            raise Exception("Varyant ensure adımı basarısız.")
        #add variant
        if not press_add_variant_button(session):
            raise Exception("Varyant ekleme adımı basarısız.")
        
        # 5. Ekranı kaydet
        if not save_sap_screen(session):
            raise Exception("SAP ekranı kaydetme adımı başarısız.")   

    
      # 7. Is planı sekmesine gecis
        if not zmm0020_is_plani_sekmesi_giris(session):
            raise Exception("ZMM0020 Is planı sekmesi giriş adımı başarısız.")
   #    
        # 8. Is planı adımları
        if not zmm0020_is_plani_adimlari(session, data):
            raise Exception("ZMM0020 Is planı adımları doldurma adımı başarısız.")
       
        # 9. ZMM0020'e 'Create Material' butonuna tıkla
        if not zmm0020_press_create_material_button(session):
            raise Exception("ZMM0020 'Create Material' butonuna basma adımı başarısız.")
        
        # 10. ZMM0020'e 'Create Routing' butonuna tıkla
        if not zmm0020_press_create_routing_button(session):
            raise Exception("ZMM0020 'Create Routing' butonuna basma adımı başarısız.")
        
       # 11. ZMM0020 'BOM Sekmesine Geçiş, matris ekleme
        if not zmm0020_bom_sekmesi_matris_ekle(session):
             raise Exception("ZMM0020 'BOM Sekmesine Matris Ekle' adımı başarısız.")
        
        # 12. BOM Şablonunun yüklenmesi ve SAP'ye aktarılması
        
        try: 
            order_type = data['orderType']
            if order_type == "single_from_set":
                plm_id = data.get('main_plm_id')
                child_plm_id = data.get('plm_code')
            else:
                plm_id = data.get('plm_code') 
                child_plm_id = plm_id
            style_name = data.get('styleName')
            if not plm_id:
                raise Exception("JSON verisinde 'plm_code' bulunamadı, ")
            file_name = f"{style_name}_BOM_Template_{plm_id}.xlsx"
            output_directory= ConfigManager.OUTPUT_EXCEL_DIR
            input_path = os.path.join(output_directory, file_name)
            if not os.path.exists(input_path):
                raise Exception(f"BOM şablon dosyası bulunamadı: {input_path}. Lütfen dosyanın mevcut olduğundan emin olun.")            
            available_colors = list(data['order_color_code']) if 'order_color_code' in data else []
            if not available_colors:
                logger.warning("JSON verisinde renk kodu bulunamadı, Renk dropdown'ı boş olabilir.")
            available_sizes = [str(s) for s in data['sizes']] if 'sizes' in data else []
            if not available_sizes:
                logger.warning("JSON verisinde beden kodu bulunamadı")
            
             # --- Önce Üretim Versiyonları sekmesinden AFS sütun metadata'sını al ---
            afs_column_metadata_from_prod_versions = _get_afs_column_metadata_from_prod_versions_tab(session)
            #logger.info(f"Üretim Versiyonları sekmesinden AFS sütun metadata'sı alındı: {afs_column_metadata_from_prod_versions}")
            if not afs_column_metadata_from_prod_versions:
                logger.error("Üretim Versiyonları sekmesinden AFS sütun metadata'sı alınamadı. Akış durduruluyor.")
                return False
            
            
            processed_bom_data = zmm0020_select_bom_operation_and_add_components(session, input_path, available_colors, available_sizes, afs_column_metadata_from_prod_versions, child_plm_id)
            if processed_bom_data is None:
                raise Exception("Excel BOM verileri SAP'ye eklenirken hata oluştu veya veri boş.")  
            data['processed_bom_data'] = processed_bom_data
            logger.info(f"{len(processed_bom_data)} adet BOM kalemi Excel'den okundu ve SAP'ye ekleme süreci başlatıldı.")
            
            if not zmm0020_set_bom_afs_data(session, processed_bom_data, available_colors, available_sizes, afs_column_metadata_from_prod_versions):
                raise Exception("BOM AFS verilerinin SAP'ye aktarılması adımı başarısız.")
            # 5. Ekranı kaydet
            if not save_sap_screen(session):
                raise Exception("SAP ekranı kaydetme adımı başarısız.")
           
        except Exception as e:
            raise Exception("JSON verisinde 'plm_code' bulunamadı, BOM şablonu oluşturulamadı.")
        
        
    
        # 13. Üretim Versiyonlarının Oluşturulması
       
        if not zmm0020_ensure_production_versions_created(session):
            raise Exception("Üretim versiyonlarının oluşturulması adımı başarısız.")
        
        # 14. Maliyetlendirme Sekmesi İşlemleri
        if not zmm0020_handle_costing_tab(session):
            raise Exception("Maliyetlendirme sekmesi işlemleri adımı başarısız.")
        
        print("--- ZMM0020 Genel Akışı Tamamlandı ---")
        return True
        
    except Exception as e:
        logger.error(f"ZMM0020 Genel Akış Hatası: {e}")
        return False

def run_single_order_workflow(session, data, cache_file_path):
    """
    Tekli siparişler için SAP dosya açma adımlarını yönetir.
    """
    try:
        print("--- Tekli Sipariş Akışı Başladı ---")
        
        
        # 1. ZMM0020 Akışını Başlat
        if not zmm0020_single_order_flow(session, data):
            raise Exception("ZMM0020 tekli sipariş akışı başarısız.")       
        
       # 2. ZSD0010 Akışını Başlat
        page, browser, p = None, None, None
        
        plm_id = data.get('plm_code') # JSON'dan PLM ID'yi al
        po_no = data.get('po_no')
        if not plm_id:
            raise Exception("JSON verisinde 'plm_code' bulunamadı, ")
        fob_price_usd = data.get('fob_price_usd') # JSON'dan FOB Fiyatı'yi al
        if not fob_price_usd:
            raise Exception("JSON verisinde 'fob_price_usd' bulunamadı, ")

        try:
            page, browser, p = fiori_login(url= cfg.get_setting("FIORI_URL") or os.getenv("FIORI_URL"), username= cfg.get_setting("SAP_USERNAME") or os.getenv("SAP_USERNAME"), password= cfg.get_password("SAP_PASS") or os.getenv("SAP_PASSWORD"))
            if page:
                logging.info("Giriş başarılı. ZSD0010 PLM öğeleri işleniyor.")

                collected_data = zsd0010_process_plm_items_v2(page, str(plm_id), fob_price_usd, str(po_no), is_child=False)

                if collected_data and 'standard_bid_number' in collected_data:
                    update_json_cache(cache_file_path, "collected_data", collected_data)
                    logging.info(f"İşlem başarıyla tamamlandı. Elde edilen Standart Teklif Numarası: {collected_data['standard_bid_number']}")
                else:
                    logging.error("ZSD0010 PLM öğeleri işlenirken bir sorun oluştu veya Standart Teklif Numarası bulunamadı.")

            else:
                logging.error("Fiori giriş işlemi başarısız oldu.")

        except Exception as e:
            logging.exception(f"Ana scriptte beklenmeyen bir hata oluştu: {e}")
        
        # 3- ZSD0010 ekranına girş ve sipariş entegrasyonunu yap
        if not zsd0010_process_order_integration_gui_v2(session, data, collected_data):
            raise Exception("ZSD0010 sipariş entegrasyon akışı başarısız.")
        

        # 4- ZPP0030 ekranı MasterOrder Dönüşümü
        if not zpp0030_process_production_orders(data, session, collected_data):
            raise Exception("ZPP0030 masterorder dönüşüm akışı başarısız.")
        
        
       
        print("--- Tekli Sipariş Akışı Başarıyla Tamamlandı ---")
        return True
        

    except Exception as e:
        logger.error(f"Single Order Workflow hatası: {e}")
        return False
    
    
def step_zmm0020(session, data, cache_file_path):
    """ADIM 1: ZMM0020 Varyant, Malzeme ve BOM İşlemleri"""
    logger.info(">>> Adım Başlatılıyor: ZMM0020")
    
    # TAZELEME: Eğer ZMM verileri RAM'de yoksa (direkt bu adımdan başlanırsa)
    if not data.get('plm_code'):
        logger.info("ZMM verileri RAM'de yok, JSON'dan tazeleniyor...")
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                fresh_data = content[0] if isinstance(content, list) else content
                data.update(fresh_data) # RAM'deki boş data'yı doldur

    success = zmm0020_single_order_flow(session, data)
    if success:
        logger.info(">>> Adım Tamamlandı: ZMM0020")
    return success

def step_fiori(session, data, cache_file_path):
    """ADIM 2: Fiori Fiyatlandırma ve Teklif No Alma"""
    logger.info(">>> Adım Başlatılıyor: FIORI Fiyatlandırma")
    
    # TAZELEME
    if not data.get('plm_code'):
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                data.update(content[0] if isinstance(content, list) else content)

    page, browser, p = None, None, None
    try:
        plm_id = data.get('plm_code')
        po_no = data.get('po_no')
        fob_price_usd = data.get('fob_price_usd')

        page, browser, p = fiori_login(
            url=cfg.get_setting("FIORI_URL"), 
            username=cfg.get_setting("SAP_USERNAME"), 
            password=cfg.get_password("SAP_PASS")
        )
        
        if page:
            collected_data = zsd0010_process_plm_items_v2(page, str(plm_id), fob_price_usd, str(po_no), is_child=False, order_type="single")
            
            if collected_data: # Veri geldiyse işlem yap
                # 1. collected_data'yı RAM'e ve JSON'a kaydet
                data['collected_data'] = collected_data 
                update_json_cache(cache_file_path, "collected_data", collected_data)
                
                # 2. sales_organization bilgisini çek ve sale_group olarak kaydet
                sale_org = collected_data.get("sales_organization")
                if sale_org:
                    data['sale_group'] = sale_org
                    update_json_cache(cache_file_path, "sale_group", sale_org)
                    logger.info(f"Single Sipariş: sale_group = {sale_org} olarak güncellendi.")
                else:
                    logger.warning("Single Sipariş: Fiori'den sales_organization bilgisi alınamadı.")

                # 3. Teklif Numarası kontrolü ve dönme
                if 'standard_bid_number' in collected_data:
                    logger.info(f"Teklif No Alındı: {collected_data['standard_bid_number']}")
                    return True # Başarılı dönüş
                else:
                    logger.error("Single Sipariş: Fiori'den teklif numarası alınamadı.")
            else:
                logger.error("Single Sipariş: Fiori'den hiçbir veri toplanamadı.")
                
        return False
    except Exception as e:
        logger.error(f"Fiori Adımı Hatası: {e}")
        return False
    finally:
        if browser: browser.close()

def step_zsd0010(session, data, cache_file_path):
    """ADIM 3: ZSD0010 Sipariş Entegrasyonu"""
    logger.info(">>> Adım Başlatılıyor: ZSD0010 Entegrasyon")
    
    # TAZELEME: RAM'de collected_data yoksa JSON'dan oku
    collected_data = data.get('collected_data')
    if not collected_data:
        logger.info("Teklif verisi RAM'de yok, JSON cache'den okunuyor...")
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                fresh_data = content[0] if isinstance(content, list) else content
                collected_data = fresh_data.get('collected_data')
                data['collected_data'] = collected_data # RAM'i de güncelle

    if not collected_data:
        logger.error("HATA: ZSD0010 için gerekli 'collected_data' bulunamadı!")
        return False
        
    return zsd0010_process_order_integration_gui_v2(session, data, collected_data)

def step_zpp0030(session, data, cache_file_path):
    """ADIM 4: ZPP0030 Master Order Dönüşümü"""
    logger.info(">>> Adım Başlatılıyor: ZPP0030 Master Order")
    
    # TAZELEME
    collected_data = data.get('collected_data')
    if not collected_data:
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                fresh_data = content[0] if isinstance(content, list) else content
                collected_data = fresh_data.get('collected_data')
                data['collected_data'] = collected_data

    if not collected_data:
        logger.error("HATA: ZPP0030 için gerekli 'collected_data' bulunamadı!")
        return False
        
    return zpp0030_process_production_orders(data, session, collected_data)

# Adım ID'lerini fonksiyonlarla eşleştiriyoruz
SINGLE_ORDER_STEP_MAP = {
    "ZMM0020": step_zmm0020,
    "ZSD0010": step_zsd0010,
    "ZPP0030": step_zpp0030,
    "MD01N": step_md01n_single_mrp
}

def run_modular_single_order_workflow(session, data, cache_file_path, user_selected_steps, bridge):
    """SINGLE Siparişler için Modüler Yürütücü."""
    # Adımları önceliğe göre sırala (S1, S2, S3, S4, FIORI...)
    steps_to_run = sorted(user_selected_steps, key=get_step_priority)
    total_steps = len(steps_to_run)
    
    for i, step_id in enumerate(steps_to_run):
        bridge.update_step_status(step_id, "running", i / total_steps)
        success = False

        # ZMM Alt Adımları (S1-S4)
        if "_MAIN_" in step_id and "_S" in step_id:
            sub_step_key = step_id[-2:] # S1, S2..
            step_func = ZMM_STEP_MAP.get(sub_step_key)
            if step_func:
                success = step_func(session, data, cache_file_path)
                # Eğer S1 bittiyse malzeme kodunu cache'e yaz
                if success and sub_step_key == "S1":
                    gen_code = get_material_code_from_zmm0020(session)
                    if gen_code:
                        data["sap_material_code"] = gen_code
                        data["main_material_code"] = gen_code
                        update_json_cache(cache_file_path, "sap_material_code", gen_code)

        # Diğer Global Adımlar (FIORI, ZSD0010 vb.)
        else:
            step_func = SINGLE_ORDER_STEP_MAP.get(step_id)
            if step_func:
                success = step_func(session, data, cache_file_path)

        if success:
            bridge.update_step_status(step_id, "success", (i + 1) / total_steps)
        else:
            bridge.update_step_status(step_id, "error")
            return False
            
    return True

ZMM_STEP_MAP = {
    "S1": zmm0020_step_1_variants,
    "S2": zmm0020_step_2_routing,
    "S3": zmm0020_step_3_bom,
    "S4": zmm0020_step_4_costing
}

def get_step_priority(step_id):
    """Adımların çalışma sırasını belirler (S1 > S2 > S3 > S4)."""
    if "_CHILD_" in step_id:
        suffix = step_id[-2:] # S1, S2..
        prio = {"S1": 1.1, "S2": 1.2, "S3": 1.3, "S4": 1.4}
        return prio.get(suffix, 1.9)
    if "_MAIN_" in step_id:
        if "_S" in step_id: # Single sipariş alt adımları
            suffix = step_id[-2:]
            prio = {"S1": 2.1, "S2": 2.2, "S3": 2.3, "S4": 2.4}
            return prio.get(suffix, 2.9)
        return 2.0 # Set ana ZMM adımı
    
    # Global Adımlar
    global_prio = {"ZSD0010": 3,"MD01N": 4, "ZPP0030": 5}
    return global_prio.get(step_id, 99)