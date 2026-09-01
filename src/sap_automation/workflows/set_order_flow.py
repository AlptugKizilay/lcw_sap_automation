# src/sap_automation/workflows/set_order_flow.py

import json
import logging
import os
import time
from typing import Dict, Any, List
from src.util.config_manager import ConfigManager

from src.sap_automation.screens.zmm0020_handler import zmm0020_step_1_variants, zmm0020_step_2_routing, zmm0020_step_3_bom, zmm0020_step_4_costing, fetch_main_material_code_from_zmm0020, fetch_material_code_from_zmm0021, handle_set_order_olcu_donusumu, get_material_code_from_zmm0020, get_color_variant_data_from_zmm0020_tab3
from src.sap_automation.workflows.single_order_flow import  zmm0020_single_order_flow, zmm0020_ilk_ekran_giris, zmm0020_model_sekmesi_giris
from src.sap_automation.screens.cs01_handler import handle_cs01_for_set_order
from src.sap_automation.screens.zsd0010_handler import fiori_login, zsd0010_process_plm_items, zsd0010_process_order_integration_gui, zsd0010_process_plm_items_v2, zsd0010_process_order_integration_gui_v2
from src.sap_automation.screens.md01n_handler import run_md01n_mrp
from src.sap_automation.screens.zpp0030_handler import zpp0030_process_production_orders
from src.util.update_json_cache import update_json_cache
from src.util.handle_sap_popups import handle_sap_popups
logger = logging.getLogger(__name__)
cfg = ConfigManager()
MASTER_SET_SEQUENCE = ["ZMM0020", "CS01", "ZSD0010", "MD01N", "ZPP0030"]
def _transform_child_to_single_product_data(child_data: Dict[str, Any], main_order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set siparişindeki bir çocuğu (child) alıp, single sipariş formatına benzer bir
    ürün veri sözlüğüne dönüştürür. Bu sayede mevcut single order handler'ları
    yeniden kullanılabilir.
    """
    transformed_data = {
        "orderType": "single_from_set", # Bu, bir setin parçası olduğunu belirtmek için özel bir tip olabilir
        "styleName": main_order_data.get("styleName", "UNKNOWN_STYLE"), # Ana siparişin styleName'ini kullan
        "po_no": main_order_data.get("po_no"),
        "plm_code": child_data.get("plm_code"), # Çocuğun PLM kodu
        "MAGK": main_order_data.get("MAGK"),
        "season": main_order_data.get("season"),
        "special_code": main_order_data.get("special_code"),
        "fob_price_usd": main_order_data.get("fob_price_usd"),
        "fob_price_egp": child_data.get("price_egp"),
        "fob_price_usd_child": child_data.get("price_usd"),
        "order_color_code": child_data.get("componentColor", []), # Çocuğun renkleri
        "sizes": main_order_data.get("sizes", []), # Ana siparişin bedenleri (tüm çocuklar için aynı)
        "selected_size_sequence_numbers": main_order_data.get("selected_size_sequence_numbers", []),
        "productDefiniton": child_data.get("productDefiniton"), # Çocuğun ürün tanımı
        "sapProductCode": child_data.get("sapProductCode"), # Çocuğun SAP ürün kodu
        "isPrinted": child_data.get("isPrinted", False), # Çocuğun isPrinted durumu
        "size_group": main_order_data.get("size_group"),
        "sale_group": main_order_data.get("sale_group"),
        "exfactoryDate": main_order_data.get("exfactoryDate"),
        "main_plm_id": main_order_data.get("plm_code"),
        "main_material_code": child_data.get("main_material_code"),
        "sap_material_code": child_data.get("sap_material_code"),
        
        
        # Gerekirse diğer ana sipariş verilerini de buraya ekleyebilirsiniz
    }
    #logger.info(f"Çocuk PLM {child_data.get('plm_code')} için single formatına dönüştürülen veri: {transformed_data}")
    return transformed_data


def run_set_order_workflow(session: Any, order_data: Dict[str, Any], cache_file_path):
    """
    Takımlı siparişler için SAP otomasyon iş akışını yönetir.
    Her bir çocuk (child) için ortak adımları tekrarlar.
    """
    logger.info(f"Takımlı Sipariş Workflow'u başlatılıyor: {order_data.get('po_no')}")
    

    # order_data'nın bir liste içinde tek bir dict olduğunu varsayıyoruz (main.py'deki yapıdan dolayı)
    if isinstance(order_data, list) and len(order_data) > 0:
        main_order_data = order_data[0]
    else:
        main_order_data = order_data # Zaten dict ise doğrudan kullan

    childrens = main_order_data.get("childrens", [])

    if not childrens:
        logger.error("Set siparişinde işlenecek çocuk (childrens) bulunamadı.")
        return
    #cache_file_path = f"order_data_cache_{main_order_data['po_no']}.json"    
    #1- Her bir çocuk için ZMM0020 gerçekleştir
    for i, child in enumerate(childrens):
        child_plm = child.get("plm_code")
        logger.info(f"\n--- Çocuk {i+1}/{len(childrens)} (PLM: {child_plm}) için adımlar başlatılıyor ---")
        
        # Çocuğun verisini single order formatına dönüştür
        transformed_child_data = _transform_child_to_single_product_data(child, main_order_data)

        # Ortak adım: ZMM0020 ekranını işle
        try:
            logger.info(f"ZMM0020 ekranı {child_plm} için işleniyor...")
            
            zmm0020_single_order_flow(session, transformed_child_data)
            
            logger.info(f"ZMM0020 ekranı {child_plm} için başarıyla işlendi.")
            
            generated_material_code = get_material_code_from_zmm0020(session)
            if generated_material_code:
                child["sap_material_code"] = generated_material_code
                update_json_cache(cache_file_path, "sap_material_code", generated_material_code)
            else:
                logger.error(f"PLM {child['plm_code']} için malzeme kodu üretilemedi!")
                raise Exception(f"SAP malzeme kodu boş geldi, işleme devam edilemez. PLM: {child['plm_code']}")
            
            logger.info(f"Çocuk (PLM: {child_plm}) material kodu: {child['sap_material_code']}")
        except Exception as e:
            logger.error(f"HATA: ZMM0020 ekranı {child_plm} için işlenirken hata oluştu: {e}", exc_info=True)
            # Hata durumunda diğer çocukları işlemeye devam etmek isteyip istemediğinize karar verin
            # continue veya raise e
            raise Exception(f"ZMM0020 ekranı {child_plm} için işlenirken hata oluştu.") 
        
                   
    # 2- ZMM0020 Main Plm code:***
    try:
               
        # 1. ZMM0020 Ekranına giriş ve temel bilgilerin doldurulması
        if not zmm0020_ilk_ekran_giris(session, main_order_data):
            raise Exception("ZMM0020 ilk ekran giriş adımı başarısız.")

        # 2. ZMM0020 - Model Sekmesi
        if not zmm0020_model_sekmesi_giris(session, main_order_data):
            raise Exception("ZMM0020 model sekmesi giriş adımı başarısız.") 

        # 3. Ölçü Dönüşümü
        if not handle_set_order_olcu_donusumu(session, main_order_data):
            raise Exception("Ölçü Dönüşümü adımı başarısız.")

        # 4. material kodunu al
        main_order_data["main_material_code"] = get_material_code_from_zmm0020(session)
        print(f"Ana sipariş material kodu: {main_order_data['main_material_code']}")
        
        update_json_cache(cache_file_path, "main_material_code", main_order_data["main_material_code"])
        
        
    except Exception as e:
        logger.error(f"HATA: ZMM0020 ekranı {main_order_data.get('main_plm_id')} için işlenirken hata oluştu: {e}", exc_info=True)
        raise
    
    # 3- CS01 Malzeme Ürün Agacı
    
    if not handle_cs01_for_set_order(session, main_order_data):
        raise Exception("CS01 adımı başarısız.")
    
        
    # 4-ZSD0010 Sipariş Entegrasyon 
    
    # --- SET ORDER FLOW ---
    page, browser, p = None, None, None
    main_plm = order_data.get('plm_code')
    main_fob_price = order_data.get('fob_price_usd')
    po_no = order_data.get('po_no')
    childrens = order_data.get('childrens', [])

    # Tüm parçaların verilerini tutacak sözlük
    fiori_results_map = {}

    try:
        page, browser, p = fiori_login(url= cfg.get_setting("FIORI_URL") or os.getenv("FIORI_URL"), username= cfg.get_setting("SAP_USERNAME") or os.getenv("SAP_USERNAME"), password= cfg.get_password("SAP_PASS") or os.getenv("SAP_PASSWORD"))
        if page:
            # 1. Ana PLM İşleniyor (Fiyat Kontrolü AKTİF)
            res_main = zsd0010_process_plm_items_v2(page, str(main_plm), main_fob_price, str(po_no), is_child=False)
            if res_main:
                fiori_results_map[str(main_plm)] = res_main

            # 2. Çocuk PLM'ler İşleniyor (Fiyat Kontrolü PASİF)
            for child in childrens:
                c_plm = child.get('plm_code')
                res_child = zsd0010_process_plm_items_v2(page, str(c_plm), 0, str(po_no), is_child=True)
                if res_child:
                    fiori_results_map[str(c_plm)] = res_child

            # 3. Set Sipariş Entegrasyonu (Daha önce yazdığımız alt gridli GUI fonksiyonu)
            # fiori_results_map burada tüm PLM'lerin verilerini içerir.
            if fiori_results_map:
                print(fiori_results_map)
                update_json_cache(cache_file_path, "fiori_results_map", fiori_results_map)
                if not zsd0010_process_order_integration_gui_v2(session, order_data, fiori_results_map):
                    raise Exception("ZSD0010 Set sipariş entegrasyonu başarısız.")
    finally:
        if browser: browser.close()
        if p: p.stop()
    
    
    # 5- MRP     
    try:
        main_mat = order_data.get('main_material_code')
        children_mats = [child.get('sap_material_code') for child in order_data.get('childrens', [])]

        # 2. Fonksiyonu çağır
        mrp_success = run_md01n_mrp(session, main_mat, children_mats)

        if mrp_success:
            logger.info("MRP başarıyla tetiklendi.")
        else:
            raise Exception("MRP çalıştırma adımı başarısız oldu.")
    except Exception as e:
        logger.error(f"HATA: MRP ekranı {order_data.get('main_plm_id')} için işlenirken hata oluştu: {e}", exc_info=True)
        raise
    
    # 6- ZPP0030 MASTER ORDER
    
    if not zpp0030_process_production_orders(order_data, session, fiori_results_map):
            raise Exception("ZPP0030 masterorder dönüşüm akışı başarısız.")
    




    logger.info("Takımlı Sipariş Workflow'u başarıyla tamamlandı.")


#def step_set_zmm_children(session, data, cache_file_path):
#    """ADIM: Tüm Çocuk PLM'ler için ZMM0020 İşlemleri"""
#    logger.info(">>> [ADIM BAŞLADI] Set Çocukları ZMM0020")
#    childrens = data.get("childrens", [])
#    for i, child in enumerate(childrens):
#        child_plm = child.get("plm_code")
#        transformed_child_data = _transform_child_to_single_product_data(child, data)
#        logger.info(f"Çocuk {i+1}/{len(childrens)} (PLM: {child_plm}) için ZMM0020 işlemi başlıyor...")
#        zmm0020_single_order_flow(session, transformed_child_data)
#        time.sleep(1) # SAP'nin işlemi tamamlaması için kısa bir bekleme
#        generated_code = get_material_code_from_zmm0020(session)
#        if generated_code:
#            child["sap_material_code"] = generated_code
#            # JSON Cache'i her çocuk için güncelle (Garanti olsun)
#            update_json_cache(cache_file_path, "childrens", childrens) 
#        else:
#            return False
#    return True

def step_set_zmm_main(session, data, cache_file_path):
    """ADIM: Ana PLM ZMM0020 ve Ölçü Dönüşümü"""
    logger.info(">>> [ADIM BAŞLADI] Ana PLM ZMM0020")
    if not zmm0020_ilk_ekran_giris(session, data): return False
    if not zmm0020_model_sekmesi_giris(session, data): return False
    if not handle_set_order_olcu_donusumu(session, data): return False
    
    main_mat = get_material_code_from_zmm0020(session)
    if main_mat:
        data["main_material_code"] = main_mat
        update_json_cache(cache_file_path, "main_material_code", main_mat)
        return True
    return False

def step_set_cs01(session, data, cache_file_path):
    """
    ADIM: CS01 Ürün Ağacı Oluşturma.
    Hiyerarşi: RAM -> Cache -> (ZMM0020 for Main / ZMM0021 for Children)
    """
    logger.info(">>> [ADIM BAŞLADI] CS01 BOM (Hibrit Kod Doğrulama Aktif)")

    # --- 1 & 2. SEVİYE: RAM ve CACHE KONTROLÜ ---
    main_mat = data.get('main_material_code')
    childrens = data.get('childrens', [])
    
    # Cache'ten tazeleme (Eğer RAM'de eksik varsa)
    if not main_mat or any(not c.get('sap_material_code') for c in childrens):
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                fresh_data = content[0] if isinstance(content, list) else content
                if not main_mat:
                    main_mat = fresh_data.get('main_material_code')
                    data['main_material_code'] = main_mat
                # Çocukları güncelle
                cache_childrens = fresh_data.get('childrens', [])
                for child in childrens:
                    if not child.get('sap_material_code'):
                        match = next((cc for cc in cache_childrens if cc['plm_code'] == child['plm_code']), None)
                        if match: child['sap_material_code'] = match.get('sap_material_code')

    # --- 3. SEVİYE: ÖZEL SAP SORGULARI (Hala eksik varsa) ---

    # A) ANA MALZEME KURTARMA (ZMM0020 Üzerinden)
    if not main_mat:
        main_plm = data.get("plm_code")
        logger.warning(f"Ana kod eksik! ZMM0020 sorgulanıyor: {main_plm}")
        recovered_main = fetch_main_material_code_from_zmm0020(session, main_plm)
        if recovered_main:
            main_mat = recovered_main
            data['main_material_code'] = main_mat
            update_json_cache(cache_file_path, "main_material_code", recovered_main)

    # B) ÇOCUK MALZEME KURTARMA (ZMM0021 Üzerinden)
    for child in childrens:
        if not child.get('sap_material_code'):
            child_plm = child.get("plm_code")
            logger.warning(f"Çocuk {child_plm} kodu eksik! ZMM0021 sorgulanıyor...")
            recovered_child = fetch_material_code_from_zmm0021(session, child_plm)
            if recovered_child:
                child['sap_material_code'] = recovered_child
                update_json_cache(cache_file_path, "childrens", childrens)

    # --- NİHAİ KONTROL ---
    if not main_mat or any(not c.get('sap_material_code') for c in childrens):
        logger.error("KRİTİK HATA: Gerekli malzeme kodları SAP sorgularına rağmen tamamlanamadı!")
        return False

    logger.info(f"Doğrulama başarılı. CS01'e geçiliyor. (Ana Kod: {main_mat})")
    return handle_cs01_for_set_order(session, data)

def step_set_fiori_zsd(session, data, cache_file_path):
    """ADIM: Fiori Fiyatlandırma ve ZSD0010 Entegrasyonu"""
    logger.info(">>> [ADIM BAŞLADI] Fiori + ZSD0010")
    page, browser, p = None, None, None
    try:
        main_plm = data.get('plm_code')
        main_fob = data.get('fob_price_usd')
        po_no = data.get('po_no')
        childrens = data.get('childrens', [])
        fiori_results_map = {}

        page, browser, p = fiori_login(
            url=cfg.get_setting("FIORI_URL"), 
            username=cfg.get_setting("SAP_USERNAME"), 
            password=cfg.get_password("SAP_PASS")
        )
        
        if page:
            # 1. Ana PLM
            res_main = zsd0010_process_plm_items_v2(page, str(main_plm), main_fob, str(po_no), is_child=False, order_type="set")
            if res_main: fiori_results_map[str(main_plm)] = res_main
            
            # 2. Çocuklar
            for child in childrens:
                c_plm = child.get('plm_code')
                res_child = zsd0010_process_plm_items_v2(page, str(c_plm), 0, str(po_no), is_child=True, order_type="set")
                if res_child: fiori_results_map[str(c_plm)] = res_child
            
            if browser: browser.close()
            print(fiori_results_map)
            if fiori_results_map:
                data["collected_data"] = fiori_results_map
                # 2. Satış Organizasyonu (sale_group) Bulma Mantığı
                sale_org = None
                
                # Önce direkt ana seviyede var mı bak (Single Sipariş durumu için)
                if fiori_results_map.get("sales_organization"):
                    sale_org = fiori_results_map.get("sales_organization")
                else:
                    # SET Durumu: Map içindeki çocukları tara, sales_organization olan ilkini kap
                    for key, val in fiori_results_map.items():
                        if isinstance(val, dict) and val.get("sales_organization"):
                            sale_org = val.get("sales_organization")
                            logger.info(f"Satış grubu bilgisi çocuk PLM'den ({key}) alındı: {sale_org}")
                            break
                
                # 3. Eğer bilgi bulunduysa kaydet
                if sale_org:
                    data["sale_group"] = sale_org
                    # JSON dosyasını ayrı bir element olarak güncelle
                    update_json_cache(cache_file_path, "sale_group", sale_org)
            update_json_cache(cache_file_path, "collected_data", fiori_results_map)
                
        return True
    except Exception as e:
        logger.error(f"Fiori/ZSD Hatası: {e}")
        return False
def step_zsd0010(session, data, cache_file_path):
    """ADIM 3: ZSD0010 Sipariş Entegrasyonu"""
    logger.info(">>> Adım Başlatılıyor: ZSD0010 Entegrasyon")
    
        
    # 1. Önce RAM'deki 'data' içinde var mı diye bak
    collected_data = data.get('collected_data')

    # 2. Eğer RAM'de yoksa, JSON dosyasından (diskten) taze veriyi çek
    if not collected_data:
        logger.info("Veri RAM'de bulunamadı, JSON cache dosyasından okunuyor...")
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                fresh_json = json.load(f)
                # Senin JSON yapına (liste) göre içeri gir
                fresh_data = fresh_json[0] if isinstance(fresh_json, list) else fresh_json
                collected_data = fresh_data.get('collected_data')
                
                # RAM'deki veriyi de güncelle ki bir sonraki adımda (ZPP0030) tekrar okumak zorunda kalmasın
                data['collected_data'] = collected_data

    # 3. Hala yoksa hata ver
    if not collected_data:
        logger.error("HATA: ZSD0010 için gerekli 'collected_data' (Teklif No) ne RAM'de ne de JSON'da bulunamadı!")
        return False

        
    return zsd0010_process_order_integration_gui_v2(session, data, collected_data)
def step_set_md01n(session, data, cache_file_path):
    """ADIM: MD01N MRP Çalıştırma"""
# 1. VERİ TAZELEME: RAM'de malzeme kodları eksikse JSON'dan oku
    main_mat = data.get('main_material_code')
    childrens = data.get('childrens', [])
    production_plant = data.get('sale_group', '2000') # Varsayılan üretim yeri
    
    # Çocuklardan herhangi birinin malzeme kodu eksik mi diye kontrol et
    missing_child_code = any(not child.get('sap_material_code') for child in childrens)

    if not main_mat or missing_child_code:
        logger.info("Malzeme kodları RAM'de eksik, JSON cache dosyasından tazeleniyor...")
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                fresh_json = json.load(f)
                fresh_data = fresh_json[0] if isinstance(fresh_json, list) else fresh_json
                
                # RAM'deki 'data' objesini güncelle
                data['main_material_code'] = fresh_data.get('main_material_code')
                data['childrens'] = fresh_data.get('childrens', [])
                
                # Değişkenleri tekrar ata
                main_mat = data['main_material_code']
                childrens = data['childrens']

    # 2. KONTROL: Hala veri yoksa hata ver
    if not main_mat:
        logger.error("HATA: MD01N için 'main_material_code' bulunamadı!")
        return False
        
    # Çocukların kodlarını listele
    children_mats = [child.get('sap_material_code') for child in childrens if child.get('sap_material_code')]
    
    if len(children_mats) != len(childrens):
        logger.error(f"HATA: Bazı çocukların malzeme kodları eksik! (Beklenen: {len(childrens)}, Bulunan: {len(children_mats)})")
        return False

    # 3. MRP ÇALIŞTIR
    logger.info(f"MRP tetikleniyor. Ana Malzeme: {main_mat}, Çocuklar: {children_mats}")
    return run_md01n_mrp(session, main_mat, children_mats, production_plant)


def step_set_zpp0030(session, data, cache_file_path):
    """ADIM: ZPP0030 Master Order Dönüşümü"""
    logger.info(">>> [ADIM BAŞLADI] ZPP0030 Master Order")
    # RAM'de yoksa diskten oku
    collected_data = data.get('collected_data')
    if not collected_data:
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                fresh_json = json.load(f)
                fresh_data = fresh_json[0] if isinstance(fresh_json, list) else fresh_json
                collected_data = fresh_data.get('collected_data')
                data['collected_data'] = collected_data

    if not collected_data:
        logger.error("HATA: ZPP0030 için gerekli 'collected_data' bulunamadı!")
        return False
    return zpp0030_process_production_orders(data, session, collected_data)

# --- ADIM HARİTASI (MAP) ---
SET_ORDER_STEP_MAP = {
    #"ZMM0020": step_set_zmm_children, # Önce çocuklar
    "ZMM0020_MAIN": step_set_zmm_main, # Sonra ana
    "CS01": step_set_cs01,
    "ZSD0010": step_zsd0010,
    "MD01N": step_set_md01n,
    "ZPP0030": step_set_zpp0030
}

# --- MODÜLER YÜRÜTÜCÜ (RUNNER) ---
def run_modular_set_order_workflow(session, data, cache_file_path, user_selected_steps, bridge):
    """SET Siparişleri için Modüler Yürütücü."""
    steps_to_run = sorted(user_selected_steps, key=get_step_priority)
    total_steps = len(steps_to_run)
    
    for i, step_id in enumerate(steps_to_run):
        bridge.update_step_status(step_id, "running", i / total_steps)
        
        success = False

        # SENARYO 1: ÇOCUK PLM ALT ADIMLARI (S1, S2, S3, S4)
        if step_id.startswith("ZMM_CHILD_"):
            # ID Parçala: ZMM_CHILD_1185317_S1 -> PLM: 1185317, Step: S1
            parts = step_id.split("_")
            target_plm = parts[2]
            sub_step_key = parts[3]
            
            childrens = data.get("childrens", [])
            target_child = next((c for c in childrens if str(c.get("plm_code")) == target_plm), None)
            
            if target_child:
                transformed_data = _transform_child_to_single_product_data(target_child, data)
                step_func = ZMM_STEP_MAP.get(sub_step_key)
                
                if step_func:
                    success = step_func(session, transformed_data, cache_file_path, target_child)
                    # S1 sonrası malzeme kodu takibi
                    if success and sub_step_key == "S1":
                        gen_code = get_material_code_from_zmm0020(session)
                        if gen_code:
                            target_child["sap_material_code"] = gen_code
                            update_json_cache(cache_file_path, "childrens", childrens)
            else:
                logger.warning(f"PLM {target_plm} bulunamadı.")

        # SENARYO 2: ANA SET PLM (S1-S4 adımları yok, tek blok)
        elif step_id.startswith("ZMM_MAIN_"):
            success = step_set_zmm_main(session, data, cache_file_path)

        # SENARYO 3: GLOBAL ADIMLAR (CS01, FIORI, MD01N vb.)
        else:
            step_func = SET_ORDER_STEP_MAP.get(step_id)
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
    """
    Adımları PLM bazlı gruplayarak sıralar.
    Sıralama Mantığı: (Grup Önceliği, PLM Kodu, Adım Sırası)
    """
    # 1. ÇOCUK PLM ADIMLARI (ZMM_CHILD_1204635_S1)
    if step_id.startswith("ZMM_CHILD_"):
        parts = step_id.split("_")
        plm_code = parts[2]  # 1204635
        sub_step = parts[3]  # S1, S2...
        
        step_order = {"S1": 1, "S2": 2, "S3": 3, "S4": 4}.get(sub_step, 9)
        
        # Tuple döndürüyoruz: 
        # 1. eleman: 1 (Çocuk adımları en öncelikli grup)
        # 2. eleman: plm_code (Aynı PLM'ler yan yana gelsin)
        # 3. eleman: step_order (Aynı PLM içinde S1, S2, S3, S4 sırasıyla gitsin)
        return (1, plm_code, step_order)

    # 2. ANA SET PLM ADIMI (ZMM_MAIN_1204633)
    elif step_id.startswith("ZMM_MAIN_"):
        return (2, "0", 0) # Çocuklardan sonra gelsin

    # 3. GLOBAL ADIMLAR (CS01, ZSD0010 vb.)
    else:
        global_order = {
            "CS01": 3,
            "ZSD0010": 4,
            "MD01N": 5,
            "ZPP0030": 6
        }
        return (global_order.get(step_id, 9), "0", 0)