# src/sap_automation/screens/zmm0020_handler.py

import json
import os
import time
import re
import logging

import win32com
from src.file_management.excel_reader import read_bom_from_excel, read_work_plan_from_excel, read_variant_values_from_excel
from src.sap_automation.screens.common_actions import ensure_change_mode, read_sap_status_bar, save_sap_screen
from src.util.config_manager import ConfigManager
from src.util.localizer import get_unit_symbol
from src.util.handle_sap_popups import handle_sap_popups
from src.util.update_json_cache import update_json_cache

logger = logging.getLogger(__name__)

# Operasyon metin anahtarları haritası (Turkish and English keys)
KTSCH_MAP = {
    # Turkish keys
    "Harici Dikim": "1000001", "Harici Dış Kesim": "1000002", "Harici Ütü Paket": "1000003",
    "Harici Baskı": "1000005", "Harici Biye Kesim": "1000006", "Harici Yıkama": "1000007",
    "Harici Nakış": "1000008", "Harici Çıtçıt": "1000009", "Harici İlik Düğme": "1000010",
    "Harici El İşçiliği": "1000011", "Harici Special Dikiş": "1000012",
    "APLIKE KESİM": "1000016", "POPLİN KESİM": "1000017", "ANA BEDEN KESİM": "1000018",
    "KOL UCU KESİM": "1000019", "YAKA KESİM": "1000020", "suprem kesim": "1000021",
    "oxford kesim": "1000024", "ribana kesim": "1000027", "ön beden kesim": "1000049",
    "pike kesim": "1000055", "pat kesim": "1000067", "alt pat kesim": "1000073",
    "kaskorse kesim": "1000090", "ic yaka kesim": "1000104", "kesim": "1000132",
    "dantel kesim": "1000135", "kemer kesim": "1000183", "astar kesim": "1000185",
    "garni kesim": "1000193", "ceplik kesim": "1000197", "YIKAMA": "1000237",
    "ilik düğme": "1000241", "aplike nakış": "1000267", "ÖN BASKI": "1000271",
    "Dahili Kesim": "1001381", "Dahili Dikim": "1001385", "Dahili UKP": "1001387",
    "Örgü": "1001388",
    # English keys
    "External Sewing": "1000001", "External Cutting": "1000002", "External Packaging": "1000003",
    "External Printing": "1000005", "External Bia Cutting": "1000006", "External Washing": "1000007",
    "External Embroidery": "1000008", "External Snap Fastening": "1000009", "External Buttonhole": "1000010",
    "External Handcrafted": "1000011", "External Special Stitch": "1000012",
    "Applique Cutting": "1000016", "Poplin Cutting": "1000017", "Main Size Cutting": "1000018",
    "Arm Tip Cutting": "1000019", "Collar Cutting": "1000020", "Jumpsuit Cutting": "1000021",
    "Oxford Cutting": "1000024", "Rib Cutting": "1000027", "Front Size Cutting": "1000049",
    "Pike Cutting": "1000055", "Pat Cutting": "1000067", "Bottom Pat Cutting": "1000073",
    "Camisole Cutting": "1000090", "Inner Collar Cutting": "1000104", "Cutting": "1000132",
    "Lace Cutting": "1000135", "Belt Cutting": "1000183", "Undercoat Cutting": "1000185",
    "Garni Cutting": "1000193", "Pocket Cutting": "1000197", "Washing": "1000237",
    "Buttonhole": "1000241", "Applique Embroidery": "1000267", "Pre-Printing": "1000271",
    "Internal Cutting": "1001381", "Internal Sewing": "1001385", "Internal Packaging": "1001387",
    "Knitting (Socks)": "1001388"
}

OPERATION_PREFIX_MAP = {
    # Turkish keys
    "Harici Dış Kesim": "2010",
    "Harici Baskı": "2012",
    "Harici Dikim": "2014",
    "Harici Ütü Paket": "3010",
    "Örgü": "2007",
    "Harici Yıkama": "2019",
    # English keys
    "External Cutting": "2010",
    "External Printing": "2012",
    "External Sewing": "2014",
    "External Packaging": "3010",
    "Knitting (Socks)": "2007",
    "External Washing": "2019"
}

# --- Yardımcı Fonksiyon: ALV Verilerinin Yüklenmesini Bekle ---
def wait_for_alv_data_load(alv_object, timeout_seconds=20, min_rows=1):
    """
    Belirtilen ALV (GuiShell veya GuiTree) objesinin verilerinin yüklenmesini bekler.
    RowCount'a erişilebildiğini ve en az min_rows kadar satır içerdiğini kontrol eder.
    """
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            # RowCount'a erişebiliyor muyuz ve beklenen minimum satır sayısı var mı?
            if alv_object.RowCount >= min_rows:
                logger.info(f"ALV verileri yüklendi. Satır sayısı: {alv_object.RowCount}")
                return True
        except Exception as e:
            # RowCount'a erişilemezse hata verebilir, bu normaldir, beklemeye devam et
            logger.info(f"ALV RowCount'a erişilemedi, bekliyor... Hata: {e}")
        
        time.sleep(0.5) # Her yarım saniyede bir dene
    
    logger.error(f"Zaman aşımı! ALV verileri {timeout_seconds} saniye içinde yüklenmedi veya RowCount'a erişilemedi.")
    return False
def zmm0020_ilk_ekran_giris(session, data):
    """
    ZMM0020 işlem koduna gider, başlangıç bilgilerini (PLMKODU, WERKS) doldurur
    ve olası pop-up uyarılarını yönetir.
    """
    try:
        plm_code = data['plm_code']
        werks = data['sale_group'] if 'sale_group' in data else "2000" # Varsayılan değer
        

        logger.info(f"ZMM0020: İşlem koduna gidiliyor: ZMM0020")
        session.startTransaction("ZMM0020")
        time.sleep(1) # İşlemin yüklenmesini bekle

        logger.info(f"ZMM0020: PLM Kodu '{plm_code}' ve Fabrika '{werks}' giriliyor.")
        session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-PLMKODU").text = plm_code
        session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-WERKS").text = werks
        
        # WERKS alanına odaklan ve caretPosition'ı ayarla
        session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-WERKS").setFocus()
        session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-WERKS").caretPosition = len(werks)
        session.findById("wnd[0]").sendVKey(0) # Enter'a bas
        time.sleep(1) # Enter sonrası ekranın değişmesini/pop-up'ın gelmesini bekle

        # Pop-up uyarısını kontrol et ve kapat
        # wnd[1] penceresinin varlığını kontrol ediyoruz
        try:
            # session.Children.Count > 1 demek, ana pencere (wnd[0]) dışında bir pencere (wnd[1]) var demektir.
            if session.Children.Count > 1:
                popup_window = session.findById("wnd[1]")
                # Pop-up'ın başlığını veya ID'sini kontrol ederek spesifik bir pop-up olduğunu doğrulayabiliriz
                # Örneğin: if "Uyarı" in popup_window.Text:
                
                logger.warning(f"ZMM0020: Pop-up uyarısı algılandı: '{popup_window.Text}'. Kapatılıyor.")
                popup_window.findById("tbar[0]/btn[0]").press() # İlk butona bas (Genellikle "Devam" veya "OK")
                time.sleep(0.5)
                
                # İkinci bir pop-up gelme ihtimaline karşı tekrar kontrol
                if session.Children.Count > 1:
                    popup_window_2 = session.findById("wnd[1]")
                    logger.warning(f"ZMM0020: İkinci pop-up uyarısı algılandı: '{popup_window_2.Text}'. Kapatılıyor.")
                    popup_window_2.findById("tbar[0]/btn[0]").press() # İkinci butona bas
                    time.sleep(1)

        except Exception as e_popup:
            logger.debug(f"ZMM0020: Pop-up kontrolü sırasında hata oluştu veya pop-up gelmedi (normal olabilir): {e_popup}")
            pass # Pop-up yoksa veya beklenenden farklıysa hata vermeden devam et

        logger.info("ZMM0020: İlk giriş ve pop-up yönetimi tamamlandı.")
        return True

    except Exception as e:
        logger.error(f"ZMM0020 ilk ekran giriş adımı sırasında kritik hata: {e}")
        # Hata durumunda session'ı kapatmak isteyebiliriz veya bir sonraki adıma geçmeden durabiliriz.
        return False
def zmm0020_model_sekmesi_giris(session, data):
    """
    ZMM0020 ekranındaki "Model" sekmesine (TAB2) gerekli bilgileri doldurur.
    """
    try:
        # JSON'dan gerekli verileri al
        # Bu yolların JSON yapına göre doğru olduğunu varsayıyoruz.
        order_type = data['orderType']
        if order_type == "single_from_set":
            sap_product_code = data['sapProductCode']
            # 1. Önce çocuk fiyatına bak, yoksa ana fiyata bak, o da yoksa "0" kabul et.
            raw_price = data.get('fob_price_usd_child') or data.get('fob_price_usd') or "1"

            # 2. String'e çevir ve noktayı virgüle dönüştür (SAP formatı)
            fob_price_usd = str(raw_price).replace('.', ',')

            logger.info(f"Kullanılacak FOB Fiyatı: {fob_price_usd}")
        else:
            sap_product_code = data.get('sapProductCode') or data.get('sap_product_code_main')
            fob_price_usd = str(data['fob_price_usd']).replace('.', ',')
        fob_price_egp = str(data['fob_price_egp']).replace('.', ',') # SAP ondalık ayırıcı genellikle virgüldür
        logger.info("ZMM0020: Ekran maksimize ediliyor.")
        session.findById("wnd[0]").maximize() # maximize() olarak düzeltildi
        time.sleep(0.5)

        logger.info("ZMM0020: 'Model' sekmesine (TAB2) geçiliyor ve bilgiler dolduruluyor.")
        
        # Sekme kontrolü: Eğer TAB2 zaten aktif değilse, önce ona tıklamamız gerekebilir.
        # Scriptte sekme geçişi komutu yok, varsayalım ki zaten TAB2 açık veya otomatik geçiyor.
        # Eğer manuel tıklama gerekiyorsa, buraya eklemeliyiz:
        # session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB2").select()
        # time.sleep(0.5)

        # PRDHA (Ürün Hiyerarşisi) - sapProductCode
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB2/ssubSUB2:ZPP_001_P_MDC:0120/ctxtGS_MDC_SCRN_0120-PRDHA").text = sap_product_code
        logger.info(f"ZMM0020: PRDHA (Ürün Hiyerarşisi) '{sap_product_code}' olarak girildi.")
        
        if not order_type == "set":
            # MTART (Malzeme Tipi)
            session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB2/ssubSUB2:ZPP_001_P_MDC:0120/ctxtGS_MDC_SCRN_0120-MTART").text = "3010"
            logger.info("ZMM0020: MTART (Malzeme Tipi) '3010' olarak girildi.")
        
        # STPRS (Standart Fiyat) - fob_price_usd
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB2/ssubSUB2:ZPP_001_P_MDC:0120/txtGS_MDC_SCRN_0120-STPRS").text = fob_price_usd
        logger.info(f"ZMM0020: STPRS (Standart Fiyat) '{fob_price_usd}' olarak girildi.")
        
        # PEINH (Fiyat Birimi)
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB2/ssubSUB2:ZPP_001_P_MDC:0120/txtGS_MDC_SCRN_0120-PEINH").text = "1"
        logger.info("ZMM0020: PEINH (Fiyat Birimi) '1' olarak girildi.")
        
        # PEINH alanına odaklan ve caretPosition'ı ayarla
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB2/ssubSUB2:ZPP_001_P_MDC:0120/txtGS_MDC_SCRN_0120-PEINH").setFocus()
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB2/ssubSUB2:ZPP_001_P_MDC:0120/txtGS_MDC_SCRN_0120-PEINH").caretPosition = 1

        logger.info("ZMM0020: Model sekmesi bilgileri girildi, Enter tuşuna basılıyor.")
        session.findById("wnd[0]").sendVKey(0) # Enter'a bas
        time.sleep(1) # Enter sonrası ekranın değişmesini/validation'ı bekle

        logger.info("ZMM0020: Model sekmesi girişi başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.error(f"ZMM0020 Model sekmesi girişi sırasında kritik hata: {e}")
        return False

# ... (zmm0020_beden_secimi fonksiyonu aşağıda tanımlı veya boş kalıyor) .
def find_alv_control(session, base_path):
    """ALV kontrolünü recursive olarak bul"""
    try:
        base_control = session.findById(base_path)
        
        # Eğer bu kontrol ALV ise
        if hasattr(base_control, 'RowCount') and hasattr(base_control, 'getCellValue'):
            return base_control
            
        # Alt yolları dene
        common_subpaths = [
            "/usr",
            "/usr/cntlGRID1/shellcont/shell",
            "/usr/subSUB_GRID/cntlGRID/shellcont/shell",
            "/usr/cntlCONTAINER/shellcont/shell",
            "/usr/tabsTAB/tabpTAB1/ssubSUB/cntlGRID/shellcont/shell"
        ]
        
        for subpath in common_subpaths:
            try:
                full_path = base_path + subpath
                control = session.findById(full_path)
                
                if hasattr(control, 'RowCount') and hasattr(control, 'getCellValue'):
                    print(f"ALV bulundu: {full_path}")
                    return control
                    
            except:
                continue
                
        return None
        
    except Exception as e:
        print(f"ALV arama hatası: {e}")
        return None
def zmm0020_beden_secimi(session, data):
    """
    ZMM0020 ekranındaki "Varyant (Renk/Beden)" sekmesinde beden grubu seçimi ve
    JSON'dan gelen sıra numaralarına göre çoklu beden seçimi yapar.
    """
    try:
        # JSON'dan gerekli verileri al
        size_group_to_select = data['size_group']
        sequence_numbers_to_select = data['selected_size_sequence_numbers']

        if not sequence_numbers_to_select:
            logger.warning(f"ZMM0020: '{size_group_to_select}' grubu için seçilecek beden bulunamadı. Beden seçimi adımı atlanıyor.")
            return True # Seçilecek bir şey yoksa True dön, hata değil

        session.findById("wnd[0]").maximize()

        logger.info("ZMM0020: 'Varyant (Renk/Beden)' sekmesine (TAB1) geçiliyor.")
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1").select() # Varyant (Renk/Beden) sekmesine geçiş
        time.sleep(1) # Sekmenin yüklenmesini bekle

        logger.info("ZMM0020: 'Beden Grubu' seçimi için butona basılıyor.")
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1/ssubSUB1:ZPP_001_P_MDC:0110/btnBTN_BEDEN_GRUP").press()
        time.sleep(1) # Pop-up penceresinin açılmasını bekle

        #beden_grubu_alv = session.findById("wnd[1]/usr/cntlTREE/shellcont/shell/shellcont[1]/shell[1]")
        raw_tree = session.findById("wnd[1]/usr/cntlTREE/shellcont/shell/shellcont[1]/shell[1]")

        # 2. DYNAMIC DISPATCH ile sarmala (Hata alan kullanıcıyı kurtaran kritik hamle)
        beden_grubu_alv = win32com.client.dynamic.Dispatch(raw_tree)
        
        control_type = beden_grubu_alv.Type
        print(f"Kontrol tipi: {control_type}")

        group_node_key = None
        
        try:
            methods = dir(beden_grubu_alv)
            #column_methods = [m for m in methods if 'column' in m.lower()]
            #print(json.dumps(methods, indent=4, ensure_ascii=False))
            target_column_id = "C          1"
            all_node_keys = beden_grubu_alv.GetAllNodeKeys() 
            for node_key in all_node_keys:
                node_text_in_column = beden_grubu_alv.GetItemText(node_key, target_column_id)
                #print(f"NodeKey: {node_key}, Text: {node_text_in_column}")
                if node_text_in_column == size_group_to_select:
                    print(f"Eşleşen NodeKey bulundu: {node_key} için '{size_group_to_select}'")
                    group_node_key = node_key
                    break
        except Exception as e:
            logger.error(f"ZMM0020: Beden Grubu ALV'de '{size_group_to_select}' aranırken hata oluştu: {e}")
              
        beden_grubu_alv.expandNode(group_node_key) # Node'u genişlet
        
        logger.debug(f"ZMM0020: '{size_group_to_select}' grubu (NodeKey: {group_node_key}) genişletildi.")
        time.sleep(1) # Genişlemesi için bekle

        logger.info(f"ZMM0020: Genişletilen grupta '{size_group_to_select}' için bedenler seçiliyor: {sequence_numbers_to_select}")
        
        
        nodes_to_select = [] # Seçilecek node key'leri
        try:            
            found_node_key_for_seq = None
            target_seq_column_id = "C          5"
            all_seq_node_keys = beden_grubu_alv.GetAllNodeKeys() 
            for node_key in all_seq_node_keys:
                try:
                    node_text_in_column = beden_grubu_alv.GetItemText(node_key, target_seq_column_id)
                    #print(f"NodeKey: {node_key}, Text: {node_text_in_column}")    
                    for seq_num in sequence_numbers_to_select:               
                        if node_text_in_column == seq_num:
                            found_node_key_for_seq = node_key
                            nodes_to_select.append(found_node_key_for_seq)
                except Exception as e:
                    logger.debug(f"ALV satır {node_key} okunurken hata: {e}")
                    continue
                
            if not found_node_key_for_seq:
                logger.warning(f"Sıra numarası '{seq_num}' ALV Tree'de bulunamadı. Atlanıyor.")

        except Exception as e:
            logger.error(f"ZMM0020: ALV Tree'de sıra numarası '{seq_num}' bulunamadı. Hata: {e}")

        for node_key_to_select in nodes_to_select:
            beden_grubu_alv.selectNode(node_key_to_select) # Node'u seç

        logger.info(f"ZMM0020: ALV Tree'de {len(nodes_to_select)} adet beden başarıyla seçildi.")
        
        time.sleep(1)

        logger.info("ZMM0020: Seçim tamamlandı, 'Devam/Onayla' butona basılıyor.")
        session.findById("wnd[1]/tbar[0]/btn[19]").press() # Seçim sonrası butona bas
        time.sleep(1) # İşlemin tamamlanmasını bekle

        logger.info("ZMM0020: Beden seçimi adımı başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.error(f"ZMM0020 beden seçimi adımı sırasında kritik hata: {e}")
        return False

import re

def normalize_size(size_str):
    """
    Beden kodunu normalize eder:
    - Eğer sayı içeriyorsa: Sadece sayıları döndürür (12m-18m -> 1218, 3y-4y -> 34).
    - Sayı içermiyorsa: Temizler ve büyük harfe çevirir (s -> S, m -> M).
    """
    if not size_str:
        return ""
    
    # 1. String içindeki tüm rakamları ayıkla
    digits_only = re.sub(r'\D', '', size_str)
    
    if digits_only:
        # Sayı varsa sadece sayıları döndür (SAP'deki 3Y4Y ile JSON'daki 3y-4y ikisi de '34' olur)
        return digits_only
    else:
        # Sayı yoksa (S, M, L, XL) boşlukları at ve büyük harf yap
        return size_str.strip().upper()

def ensure_target_sizes_selected(session, data):
    """
    ZPP_001_P_MDC ekranındaki Tablo 03'te (Bedenler), sadece data['sizes'] 
    listesinde bulunan bedenlerin seçili olmasını sağlar.
    """
    try:
        # 1. Hedef beden listesini al ve her birini normalize et
        raw_sizes = data.get('sizes', [])
        if not raw_sizes:
            logger.warning("Hedef beden listesi boş, seçim işlemi yapılmadı.")
            return False
        
        # JSON'dan gelenleri normalize edip bir set'e atalım (Hızlı arama için)
        target_normalized_sizes = {normalize_size(s) for s in raw_sizes}
        logger.info(f"Normalize edilmiş hedef bedenler: {target_normalized_sizes}")

        # 2. Tabloyu tanımla (TBL_03)
        table_03_id = "wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1/ssubSUB1:ZPP_001_P_MDC:0110/tblZPP_001_P_MDCTC_0110_TBL_03"
        table_03 = session.findById(table_03_id)
        row_count = table_03.RowCount
        
        logger.info(f"Beden tablosu taranıyor (Toplam Satır: {row_count})")
        
        selected_count = 0
        found_normalized_sizes = set()

        for i in range(row_count):
            try:
                # Beden kodunu oku (ID senin verdiğin gibi: BEDEN_KODU[1,i])
                cell_id = f"{table_03_id}/txtGS_MDC_SCRN_0110_TBL_03-BEDEN_KODU[1,{i}]"
                sap_size_raw = session.findById(cell_id).text.strip()
                
                if sap_size_raw:
                    # SAP'den geleni de normalize et
                    sap_size_normalized = normalize_size(sap_size_raw)
                    
                    # EŞLEŞME KONTROLÜ
                    if sap_size_normalized in target_normalized_sizes:
                        if not table_03.getAbsoluteRow(i).selected:
                            table_03.getAbsoluteRow(i).selected = True
                            logger.info(f"Tablo 03 - Satır {i}: '{sap_size_raw}' (Norm: {sap_size_normalized}) seçildi.")
                        else:
                            logger.debug(f"Tablo 03 - Satır {i}: '{sap_size_raw}' zaten seçili.")
                        
                        selected_count += 1
                        found_normalized_sizes.add(sap_size_normalized)
                    else:
                        # Listede yoksa seçimi kaldır (Opsiyonel: manage_color'daki gibi tersine kontrol)
                        if table_03.getAbsoluteRow(i).selected:
                            table_03.getAbsoluteRow(i).selected = False
                            logger.debug(f"Tablo 03 - Satır {i}: '{sap_size_raw}' listede yok, seçim kaldırıldı.")

            except Exception as e:
                # Satır boş olabilir veya scroll dışında kalmış olabilir
                continue

        # Eksik kontrolü
        missing = target_normalized_sizes - found_normalized_sizes
        if missing:
            logger.warning(f"DİKKAT: Şu normalize bedenler SAP tablosunda bulunamadı: {missing}")
            raise Exception("SAP tablosunda eksik bedenler var!")
            
        
        logger.info(f"Beden seçim işlemi tamamlandı. {selected_count} beden doğrulandı.")
        return True

    except Exception as e:
        logger.error(f"ensure_target_sizes_selected hatası: {e}")
        return False    
def zmm0020_renk_secimi(session, data):
    """
    ZMM0020 ekranındaki "Varyant (Renk/Beden)" sekmesinden renk seçimi yapar.
    JSON'dan gelen renk kodlarını kullanır.
    """
    try:
        # JSON'dan renk kodlarını al
        # Varsayım: data['order_color_code'] bir sözlüktür ve anahtarları renk kodlarıdır.
        colors_to_select = list(data['order_color_code'])
        if not colors_to_select:
            logger.warning("ZMM0020: Seçilecek renk kodu bulunamadı. Renk seçimi adımı atlanıyor.")
            return True
        # 2. Tablodaki mevcut renkleri tara ve listele
        table_02_id = "wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1/ssubSUB1:ZPP_001_P_MDC:0110/tblZPP_001_P_MDCTC_0110_TBL_02"
        table_02 = session.findById(table_02_id)
        existing_colors = []

        logger.info("Tablo 02 taranıyor, mevcut renk kodları kontrol ediliyor...")
        for i in range(table_02.RowCount):
            try:
                cell_val = session.findById(f"{table_02_id}/txtGS_MDC_SCRN_0110_TBL_02-RENK_KODU[1,{i}]").text.strip()
                if cell_val:
                    existing_colors.append(cell_val)
            except:
                break # Boş satıra gelindiğinde döngüden çık

        # 3. Kontrol: Hedef renklerin TAMAMI mevcut listede var mı?
        # all() fonksiyonu, listedeki her bir renk existing_colors içindeyse True döner.
        all_colors_already_exist = all(color in existing_colors for color in colors_to_select)

        if all_colors_already_exist:
            logger.info(f"Tüm hedef renkler ({colors_to_select}) tabloda zaten mevcut. 'Tüm Renkler' adımı atlanıyor.")
        else:
            session.findById("wnd[0]").maximize()
            logger.info("ZMM0020: 'Varyant (Renk/Beden)' sekmesine (TAB1) geçiliyor (Renk seçimi için).")
            session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1").select() # Zaten bu sekmedeydik, ama garanti olsun
            logger.info("ZMM0020: 'Tüm Renkler' butonuna basılıyor.")
            session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1/ssubSUB1:ZPP_001_P_MDC:0110/btnBTN_TUM_RENKLER").press()
            time.sleep(0.5) # Pop-up penceresinin (wnd[1]) açılmasını bekle

            logger.info("ZMM0020: Renk seçimi pop-up'ında 'Çoklu Seçim' butonuna basılıyor (wnd[1]).")
            session.findById("wnd[1]/tbar[0]/btn[29]").press()
            time.sleep(0.5) # Yeni pop-up penceresinin (wnd[2]) açılmasını bekle

            # --- Renk Kodu Seçim Alanı (wnd[2]) ---
            logger.info("ZMM0020: Renk kodu seçim listesinde 'Malzeme No' sütununda seçim yapılıyor (wnd[2]).")

            # getAbsoluteRow(2) ile doğrudan 3. satırı seçiyoruz. Bu satırın "Renk kodu" olduğunu varsayıyoruz.
            # Eğer bu satır değişebilirse, metinsel olarak "Renk kodu"yu bulup ona göre satır seçmeliyiz.
            session.findById("wnd[2]/usr/tblSAPLSKBHTC_FIELD_LIST_820").getAbsoluteRow(2).selected = True
            session.findById("wnd[2]/usr/tblSAPLSKBHTC_FIELD_LIST_820/txtGT_FIELD_LIST-SELTEXT[0,2]").setFocus()
            session.findById("wnd[2]/usr/tblSAPLSKBHTC_FIELD_LIST_820/txtGT_FIELD_LIST-SELTEXT[0,2]").caretPosition = 0
            #time.sleep(0.5)
            session.findById("wnd[2]/usr/btnAPP_WL_SING").press()
            session.findById("wnd[2]/tbar[0]/btn[0]").press() # Seçilen alanla devam et


            session.findById("wnd[2]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/btn%_%%DYN001_%_APP_%-VALU_PUSH").press()
            time.sleep(0.5) # Yeni pop-up penceresinin (wnd[3]) açılmasını bekle

            # --- Renk Kodu Değer Girişi (wnd[3]) ---
            logger.info("ZMM0020: Renk kodu değerleri giriliyor (wnd[3]).")

            # Renk kodlarını dinamik olarak gir

            for i, color_code in enumerate(colors_to_select):
                target_cell_id = f"wnd[3]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,{i}]" # Satır 1, sütun i
                logger.info(f"ZMM0020: Renk kodu '{color_code}' için tablo hücresi '{target_cell_id}' hazırlanıyor.")
                # Eğer i, tablo kolon sayısını aşarsa, yeni bir satır eklemek gerekebilir.
                # SAP GUI'de bu genelde otomatik olur ama bazen manuel insert tuşuna basmak gerekir.
                # Şimdilik varsayalım ki tablo otomatik genişliyor.
                session.findById(target_cell_id).text = color_code

                logger.debug(f"ZMM0020: Renk kodu '{color_code}' girildi (Hücre: {target_cell_id}).")
                time.sleep(0.2) # Her giriş arası kısa bekleme

                # Son girilen renge odaklan ve caretPosition'ı ayarla
                if i == len(colors_to_select) - 1: # Sadece son renkte
                    session.findById(target_cell_id).setFocus()
                    session.findById(target_cell_id).caretPosition = len(color_code)
                    time.sleep(0.5)

            logger.info("ZMM0020: Renk kodları girişi tamamlandı, 'Devam' butonuna basılıyor (wnd[3]).")
            session.findById("wnd[3]/tbar[0]/btn[0]").press() # Devam
            time.sleep(1)

            logger.info("ZMM0020: Renk kodları seçimi tamamlandı, 'Execute' butonuna basılıyor (wnd[3]).")
            session.findById("wnd[3]/tbar[0]/btn[8]").press() # Execute
            time.sleep(1) # İşlemin tamamlanmasını bekle

            logger.info("ZMM0020: Renk kodu seçim pop-up'ı kapatılıyor (wnd[2]).")
            session.findById("wnd[2]/tbar[0]/btn[0]").press() # Geri veya Kapat
            time.sleep(1)

            # --- Checkbox Kontrolü ve Seçimi (wnd[1]) ---
            logger.info("ZMM0020: Renk seçim ekranındaki (wnd[1]) checkbox'lar kontrol ediliyor.")

            # checkbox [1,3] kontrolü
            start_checkbox_col_index = 3 

            # Toplam seçilecek checkbox sayısı, JSON'dan gelen renk sayısı kadardır.
            num_checkboxes_to_check = len(colors_to_select)

            last_checked_checkbox = None

            for i in range(num_checkboxes_to_check):
                current_col_index = start_checkbox_col_index + i
                checkbox_id = f"wnd[1]/usr/chk[1,{current_col_index}]" # Örn: chk[1,3], chk[1,4], chk[1,5] ...

                try:
                    current_checkbox = session.findById(checkbox_id)
                    if not current_checkbox.selected:
                        current_checkbox.selected = True
                        logger.debug(f"ZMM0020: Checkbox {checkbox_id} seçili değildi, seçildi.")
                    else:
                        logger.debug(f"ZMM0020: Checkbox {checkbox_id} zaten seçili.")

                    last_checked_checkbox = current_checkbox # Son seçilen checkbox'ı takip et
                    time.sleep(0.2) # Her checkbox arası kısa bekleme

                except Exception as e:
                    logger.warning(f"ZMM0020: Checkbox {checkbox_id} bulunamadı veya seçilirken hata oluştu: {e}. Bu renk için checkbox atlanıyor.")
                    # Eğer bir checkbox bulunamazsa veya seçilemezse, otomasyonu durdurmak yerine uyarı verip devam edebiliriz.
                    # Ancak bu checkbox'ların seçilmesi kritikse, burada raise Exception yapabiliriz.

            # Scriptteki gibi, son seçilen checkbox'a odaklan
            if last_checked_checkbox:
                last_checked_checkbox.setFocus()
                time.sleep(0.5)
            else:
                logger.warning("ZMM0020: Hiçbir renk checkbox'ı seçilemedi veya odaklanılacak bir checkbox bulunamadı.")


            logger.info("ZMM0020: Renk seçim ekranındaki (wnd[1]) 'Devam/Onayla' butonuna basılıyor.")
            session.findById("wnd[1]/tbar[0]/btn[0]").press() # Devam/Onayla
            time.sleep(0.5)

            logger.info("ZMM0020: Renk seçimi adımı başarıyla tamamlandı.")
        
        # Varyant ekleme
        #session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1/ssubSUB1:ZPP_001_P_MDC:0110/btnBTN_EKLE").press()
        time.sleep(0.5)
        return True

    except Exception as e:
        logger.exception(f"ZMM0020 renk seçimi adımı sırasında kritik hata: {e}")
        return False


def press_add_variant_button(session):
    """
    ZPP_001_P_MDC ekranındaki 'Varyant Ekle' (BTN_EKLE) butonuna basar.
    """
    try:
        button_id = "wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1/ssubSUB1:ZPP_001_P_MDC:0110/btnBTN_EKLE"
        
        # Butonu bul ve bas
        logger.info("SAP: 'Varyant Ekle' butonuna basılıyor...")
        session.findById(button_id).press()
        
        # SAP'nin satırı eklemesi için kısa bir es (Opsiyonel)
        time.sleep(0.5)
        time.sleep(5)
        
        logger.info("SAP: Yeni varyant satırı başarıyla eklendi.")
        return True

    except Exception as e:
        logger.error(f"SAP: 'Varyant Ekle' butonuna basılırken hata oluştu: {e}")
        # Eğer buton bulunamazsa veya o an aktif değilse (örn. yanlış sekme) buraya düşer
        return False
def manage_color_selections(session, data):
    """
    ZPP_001_P_MDC ekranındaki iki farklı tabloda renk kodlarını kontrol eder
    ve listede olmayan renklerin seçimini kaldırır.
    """
    try:
        # 1. Seçilmesi gereken renk listesini al
        colors_to_select = list(data.get('order_color_code', []))
        logger.info(f"İşlem yapılacak hedef renkler: {colors_to_select}")

        if not colors_to_select:
            logger.warning("data['order_color_code'] listesi boş! Hiçbir renk seçilmeyecek.")

        # --- TABLO 02 İŞLEMLERİ (RENK_KODU - Tam Eşleşme) ---
        table_02_id = "wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1/ssubSUB1:ZPP_001_P_MDC:0110/tblZPP_001_P_MDCTC_0110_TBL_02"
        table_02 = session.findById(table_02_id)
        row_count_02 = table_02.RowCount

        logger.info(f"Tablo 02 taranıyor (Toplam Satır: {row_count_02})")
        for i in range(row_count_02):
            try:
                # RENK_KODU hücresinden değeri al (ID yapısı: ...-RENK_KODU[kolon, satır])
                # Senin verdiğin örnekte kolon 1, satır i
                cell_id = f"{table_02_id}/txtGS_MDC_SCRN_0110_TBL_02-RENK_KODU[1,{i}]"
                current_color_code = session.findById(cell_id).text.strip()

                if current_color_code:
                    if current_color_code not in colors_to_select:
                        # Listede yoksa seçimi kaldır
                        table_02.getAbsoluteRow(i).selected = False
                        logger.debug(f"Tablo 02 - Satır {i}: '{current_color_code}' listede yok, seçim kaldırıldı.")
                    else:
                        logger.debug(f"Tablo 02 - Satır {i}: '{current_color_code}' listede var, seçim korundu.")
            except Exception:
                # Satır boş olabilir veya yüklenmemiş olabilir
                continue

        # --- TABLO 01 İŞLEMLERİ (RENK_ADI - İçerik Eşleşmesi) ---
        table_01_id = "wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1/ssubSUB1:ZPP_001_P_MDC:0110/tblZPP_001_P_MDCTC_0110_TBL_01"
        table_01 = session.findById(table_01_id)
        row_count_01 = table_01.RowCount

        logger.info(f"Tablo 01 taranıyor (Toplam Satır: {row_count_01})")
        for j in range(row_count_01):
            try:
                # RENK_ADI hücresinden değeri al (Örn: "EKRU MELANJ DM0")
                # Senin verdiğin örnekte kolon 0, satır j
                cell_id_01 = f"{table_01_id}/txtGS_MDC_SCRN_0110_TBL_01-RENK_ADI[0,{j}]"
                full_color_name = session.findById(cell_id_01).text.strip()

                if full_color_name:
                    # Renk adının içinde hedef renklerden herhangi biri geçiyor mu?
                    # Örn: "DM0" in "EKRU MELANJ DM0" -> True
                    is_allowed = any(color in full_color_name for color in colors_to_select)

                    if not is_allowed:
                        # Listeden hiçbir renk bu metnin içinde geçmiyorsa seçimi kaldır
                        table_01.getAbsoluteRow(j).selected = False
                        logger.debug(f"Tablo 01 - Satır {j}: '{full_color_name}' hedef renkleri içermiyor, seçim kaldırıldı.")
                    else:
                        logger.debug(f"Tablo 01 - Satır {j}: '{full_color_name}' geçerli renk içeriyor.")
            except Exception:
                continue

        logger.info("Renk seçim yönetimi başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.error(f"manage_color_selections fonksiyonunda hata: {e}")
        return False
def ensure_target_colors_selected(session, data):
    """
    ZPP_001_P_MDC ekranındaki Tablo 02'de, sadece data['order_color_code'] 
    listesinde bulunan renklerin seçili (selected = True) olmasını sağlar.
    """
    try:
        # 1. Hedef renk listesini al
        colors_to_select = list(data.get('order_color_code', []))
        if not colors_to_select:
            logger.warning("Hedef renk listesi boş, seçim işlemi yapılmadı.")
            return False

        # 2. Tabloyu tanımla
        table_02_id = "wnd[0]/usr/tabsTAB_CONTROL/tabpTAB1/ssubSUB1:ZPP_001_P_MDC:0110/tblZPP_001_P_MDCTC_0110_TBL_02"
        table_02 = session.findById(table_02_id)
        row_count = table_02.RowCount

        logger.info(f"Hedef renklerin seçimi kontrol ediliyor (Toplam Satır: {row_count})")
        
        selected_count = 0
        found_colors = []

        for i in range(row_count):
            try:
                # Renk kodunu oku (Kolon 1)
                cell_id = f"{table_02_id}/txtGS_MDC_SCRN_0110_TBL_02-RENK_KODU[1,{i}]"
                current_color_code = session.findById(cell_id).text.strip()

                if current_color_code and current_color_code in colors_to_select:
                    # Eğer listede varsa ve seçili değilse seç
                    if not table_02.getAbsoluteRow(i).selected:
                        table_02.getAbsoluteRow(i).selected = True
                        logger.info(f"Tablo 02 - Satır {i}: '{current_color_code}' seçildi.")
                    else:
                        logger.debug(f"Tablo 02 - Satır {i}: '{current_color_code}' zaten seçili.")
                    
                    selected_count += 1
                    found_colors.append(current_color_code)

            except Exception:
                continue

        # Eksik renk kontrolü (Listede olup tabloda olmayanlar)
        missing = set(colors_to_select) - set(found_colors)
        if missing:
            logger.warning(f"DİKKAT: Hedef listedeki şu renkler SAP tablosunda bulunamadı: {missing}")
        
        logger.info(f"Seçim işlemi tamamlandı. Toplam {selected_count} satır doğrulandı.")
        return True

    except Exception as e:
        logger.error(f"ensure_target_colors_selected hatası: {e}")
        return False
def get_material_code_from_zmm0020(session):
    """
    Mevcut malzeme kodunu ZMM0020 ekranından alır.
    """
    try:
        material_code_field = session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-MODEL_KODU")
        material_code = material_code_field.text.strip()
        logger.info(f"ZMM0020: Mevcut malzeme kodu alındı: {material_code}")
        if not material_code:
            raise Exception("ZMM0020: Kayıt sonrası Material Code alanı boş döndü.")
        return material_code
        
    except Exception as e:
        logger.error(f"ZMM0020 malzeme kodu alınırken hata oluştu: {e}")
        return None
    
def zmm0020_is_plani_sekmesi_giris(session):
    """
    ZMM0020 ekranında 'İş Planı' sekmesine geçer ve ekranın 'Değiştir' modunda olduğundan emin olur.
    """
    try:
        session.findById("wnd[0]").maximize()
        time.sleep(0.5)

        handle_sap_popups(session)
        logger.info("ZMM0020: 'İş Planı' sekmesine (TAB4) geçiliyor.")
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB4").select()
        time.sleep(1) # Sekmenin yüklenmesini bekle
        # Ekranın 'Değiştir' modunda olduğundan emin ol
        # "wnd[0]/tbar[1]/btn[14]" ID'si 'Görüntüle/Değiştir' butonu için kullanılacak.
        if not ensure_change_mode(session, change_button_id="wnd[0]/tbar[1]/btn[14]"):
            raise Exception("ZMM0020: İş Planı sekmesi 'Değiştir' moduna geçilemedi.")
        handle_sap_popups(session)
        logger.info("ZMM0020: 'İş Planı' sekmesi girişi ve mod kontrolü başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.exception(f"ZMM0020 İş Planı sekmesi girişi sırasında kritik hata: {e}")
        return False
    
def zmm0020_is_plani_adimlari(session, data):
    """
    ZMM0020 ekranında 'İş Planı' sekmesindeki operasyon adımlarını (Kesim, Dikim, Baskı)
    JSON'dan gelen 'is_printed' bilgisine göre doldurur.
    UKP adımı default olarak gelir ve sadece dakika değeri güncellenir.
    """
    try:
        # JSON'dan 'is_printed' bilgisini al
        # Varsayım: data['order_details']['is_printed'] boolean veya string "yes"/"no"
        is_printed = data['isPrinted']
        order_type = data['orderType']
        
        if not data.get('main_plm_id'):
            plm_id = data.get('plm_code') # JSON'dan PLM ID'yi al
        else:
            plm_id = data.get('main_plm_id')
            child_plm_id = data.get('plm_code')
            
        style_name = data.get('styleName')
        if not plm_id:
            raise Exception("JSON verisinde 'plm_code' bulunamadı, ")
        file_name = f"{style_name}_BOM_Template_{plm_id}.xlsx"
        output_directory= ConfigManager.OUTPUT_EXCEL_DIR
        input_path = os.path.join(output_directory, file_name)

        logger.info(f"ZMM0020: İş Planı adımları dolduruluyor. Baskı var mı: {is_printed}")
        
        if order_type == "single_from_set":
            operations_to_add = read_work_plan_from_excel(input_path, child_plm_id)
        else: 
            # İşlem adımları listesini oluştur (UKP hariç, o default geliyor)
            operations_to_add = read_work_plan_from_excel(input_path)
            
        operations_to_add = [op for op in operations_to_add if str(op['operation']).strip() not in ["Harici Ütü Paket", "External Packaging"]]


        # ALV Grid objesini al
        alv_grid = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB4/ssubSUB4:ZPP_001_P_MDC:0140/cntlCONT_SCRN_0140_ALV_01/shellcont/shell")
        
        # Kaç adet yeni satır eklememiz gerektiğini belirle
        num_new_rows_needed = len(operations_to_add)

        logger.info(f"ZMM0020: {num_new_rows_needed} adet yeni operasyon satırı ekleniyor.")
        for _ in range(num_new_rows_needed):
            alv_grid.pressToolbarButton("ROW_ADD")
            time.sleep(0.5) # Her satır ekleme sonrası kısa bekleme

        # Yeni eklenen operasyon satırlarını doldur
        for i, item in enumerate(operations_to_add):
            row_index = i # Yeni eklenen satırlar üstten 0, 1, 2... indekslerine sahip olacak.
            op_name = item['operation']
            seq_no = item['step']
            ktsch_code = KTSCH_MAP.get(op_name)

            if not ktsch_code:
                logger.error(f"ZMM0020: '{op_name}' operasyonu için KTSCH kodu bulunamadı. Adım atlanıyor.")
                raise Exception(f"Tanımsız operasyon: {op_name}")

            logger.debug(f"ZMM0020: Satır {row_index} için '{op_name}' ({ktsch_code}) operasyonu giriliyor.")
            
            # YMSIRA (Sıra)
            alv_grid.modifyCell(row_index, "YMSIRA", str(seq_no))
            
            # KTSCH (Metin Anahtarı)
            alv_grid.currentCellColumn = "KTSCH" # Odaklan
            alv_grid.triggerModified() # Değişikliği tetikle (SAP'nin varsayılanları getirmesi için)
            alv_grid.modifyCell(row_index, "KTSCH", ktsch_code)
            
            # ARBPL (İş Merkezi) - Scriptteki gibi sadece odaklanıp tetikle, değer girme
            alv_grid.currentCellColumn = "ARBPL"
            alv_grid.triggerModified()
            
            # VGW01 (Dakika)
            alv_grid.modifyCell(row_index, "VGW01", "1") # Kesim, Baskı, Dikim için 1 dakika
            
            time.sleep(0.2) # Her satır girişi sonrası bekleme

        # UKP satırını güncelle
        # UKP satırının indeksi, eklenen operasyon sayısı kadar kayacaktır.
        ukp_row_index = num_new_rows_needed 
        
        logger.info(f"ZMM0020: UKP operasyon satırı (index: {ukp_row_index}) güncelleniyor.")
        
        # Scriptteki gibi VGW01 değerini "1,000" olarak gir
        alv_grid.setCurrentCell(ukp_row_index, "PREIS") # Scriptteki gibi önce PREIS'e odaklan
        alv_grid.triggerModified()
        alv_grid.modifyCell(ukp_row_index, "VGW01", "1,000") # UKP için 1,000 dakika
        
        # Son olarak VGW01'e odaklan ve Enter'a bas
        alv_grid.currentCellColumn = "VGW01"
        alv_grid.pressEnter()
        time.sleep(0.4) # Enter sonrası SAP'nin işlemi tamamlamasını bekle

        logger.info("ZMM0020: İş Planı adımları başarıyla dolduruldu.")
        return True

    except Exception as e:
        logger.exception(f"ZMM0020 İş Planı adımları doldurulurken kritik hata: {e}")
        return False

def zmm0020_press_create_material_button(session):
    """
    ZMM0020 ekranında 'Malzeme Kodu Yarat' butonuna basar,
    çıkan bilgilendirme pop-up'ını kapatır ve işlemin sonucunu kontrol eder.
    """
    try:
        logger.info("ZMM0020: 'Malzeme Kodu Yarat' butonuna basılıyor.")
        
        # ALV Grid objesini al (buton onun toolbar'ında)
        alv_grid = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB4/ssubSUB4:ZPP_001_P_MDC:0140/cntlCONT_SCRN_0140_ALV_01/shellcont/shell")
        alv_grid.pressToolbarButton("CREATE_MATERIAL")
        time.sleep(0.4) # Butona basıldıktan sonra pop-up'ın açılmasını bekle

        # Pop-up penceresini kontrol et (wnd[1])
        try:
            popup_window = session.findById("wnd[1]")
            popup_title = popup_window.Text
            logger.info(f"ZMM0020: Malzeme yaratma pop-up'ı açıldı. Başlık: '{popup_title}'")
            
            # Pop-up'ın durum çubuğu varsa onu da okuyabiliriz
            popup_status_info = read_sap_status_bar(session) # Bu common_actions'taki read_sap_status_bar, wnd[0] için çalışır.
                                                              # wnd[1] için ayrı bir read_popup_status_bar yazılabilir.
                                                              # Şimdilik sadece wnd[1] başlığını loglamak yeterli.

            # Pop-up'ı kapat
            logger.info("ZMM0020: Malzeme yaratma pop-up'ı kapatılıyor (btn[0]).")
            session.findById("wnd[1]/tbar[0]/btn[0]").press()
            time.sleep(2) # Pop-up'ın kapanmasını bekle

        except Exception as e_popup:
            logger.warning(f"ZMM0020: Malzeme yaratma sonrası pop-up bekleniyordu ancak bulunamadı veya kapatılırken hata oluştu: {e_popup}")
            # Pop-up çıkmaması bir hata veya özel bir durum olabilir, loglayıp devam edelim.
            # Veya burada bir hata fırlatabiliriz eğer pop-up'ın her zaman çıkması gerekiyorsa.

        # Ana ekranın durum çubuğunu kontrol et
        # Bu, malzemenin oluşturulup oluşturulmadığına dair nihai mesajı verecektir.
        status_after_creation = read_sap_status_bar(session)
        if status_after_creation["type"] == "S":
            logger.info("ZMM0020: 'Malzeme Kodu Yarat' işlemi başarıyla tamamlandı (Durum çubuğu onayı).")
            return True
        elif status_after_creation["type"] == "E":
            logger.error(f"ZMM0020: 'Malzeme Kodu Yarat' işlemi başarısız oldu. Hata: {status_after_creation['text']}")
            return False
        else:
            logger.warning(f"ZMM0020: 'Malzeme Kodu Yarat' işlemi sonrası durum çubuğunda başarı/hata mesajı alınamadı. Mesaj: {status_after_creation['text']}")
            # Başarı/hata durumu net değilse, Material Code alanını kontrol ederek devam edebiliriz.
         
            return True

    except Exception as e:
        logger.exception(f"ZMM0020 'Malzeme Kodu Yarat' butonu basılırken kritik hata: {e}")
        return False

def zmm0020_press_create_routing_button(session, timeout_seconds=5):
    """
    ZMM0020 ekranında 'İş Planı Yarat' butonuna basar ve işlemin sonucunu durum çubuğundan kontrol eder.
    """
    try:
        logger.info("ZMM0020: 'İş Planı Yarat' butonuna basılıyor.")
        
        # ALV Grid objesini al (buton onun toolbar'ında)
        alv_grid = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB4/ssubSUB4:ZPP_001_P_MDC:0140/cntlCONT_SCRN_0140_ALV_01/shellcont/shell")
        alv_grid.pressToolbarButton("CREATE_ROUTING")
        time.sleep(2) # Butona basıldıktan sonra SAP'nin işlemi başlatmasını bekle

        start_time = time.time()
        last_message_text = "" # Mesajın değişip değişmediğini kontrol etmek için
        
        while time.time() - start_time < timeout_seconds:
            status_info = read_sap_status_bar(session)
            
            # Mesaj değiştiyse veya yeni bir mesaj geldiyse kontrol et
            if status_info["text"] and status_info["text"] != last_message_text:
                last_message_text = status_info["text"]
                
                # Başarı mesajı ('S') veya kesin hata mesajı ('E') kontrolü
                if status_info["type"] == "S":
                    logger.info(f"ZMM0020: 'İş Planı Yarat' işlemi başarıyla tamamlandı. Mesaj: {status_info['text']}")
                    handle_sap_popups(session)
                    return True
                elif status_info["type"] == "E":
                    logger.error(f"ZMM0020: 'İş Planı Yarat' işlemi başarısız oldu. Hata Mesajı: {status_info['text']}")
                    handle_sap_popups(session)
                    return False
            
            # Eğer belirli bir süre boyunca hiçbir 'S' veya 'E' mesajı gelmezse,
            # veya mesaj değişmezse beklemeye devam et.
            time.sleep(1) # Her saniye durumu kontrol et
            

        logger.error(f"ZMM0020: 'İş Planı Yarat' işlemi {timeout_seconds} saniye içinde tamamlanmadı veya başarı mesajı alınamadı.")
        return False

    except Exception as e:
        logger.exception(f"ZMM0020 'İş Planı Yarat' butonu basılırken kritik hata: {e}")
        return False

def zmm0020_bom_sekmesi_matris_ekle(session):
    """
    ZMM0020 ekranında 'Ürün Ağacı (BOM)' sekmesine geçer,
    'Matris Ekle' butonuna basar ve açılan pop-up'ta tüm renkleri/bedenleri seçer.
    ***beden ve renk değerlerine göre dinamik seçim eklenebilir***
    2024-06 itibarıyla tüm renkler/bedenler için toplu
    """
    try:
        session.findById("wnd[0]").maximize()
        time.sleep(0.3)

        logger.info("ZMM0020: 'Ürün Ağacı (BOM)' sekmesine (TAB5) geçiliyor.")
        handle_sap_popups(session)
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB5").select()
        time.sleep(0.5) # Sekmenin yüklenmesini bekle
        # Ekranın 'Değiştir' modunda olduğundan emin ol (eğer bu sekmede de gerekiyorsa)
        # Genellikle bu tür ekleme işlemleri için Değiştir modunda olmak gerekir.
        # Buton ID'si "wnd[0]/tbar[1]/btn[14]" olarak varsayılmıştır.
        if not ensure_change_mode(session, change_button_id="wnd[0]/tbar[1]/btn[14]"):
            raise Exception("ZMM0020: Ürün Ağacı sekmesi 'Değiştir' moduna geçilemedi.")
        handle_sap_popups(session)
        
        logger.info("ZMM0020: 'Matris Ekle' butonuna basılıyor.")
        # ALV Grid objesini al (buton onun toolbar'ında)
        alv_grid_bom = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB5/ssubSUB5:ZPP_001_P_MDC:0150/cntlCONT_SCRN_0150_ALV_01/shellcont/shell")
        alv_grid_bom.pressToolbarButton("ADD_MATRIS")
        time.sleep(0.5) # Pop-up penceresinin (wnd[1]) açılmasını bekle

        logger.info("ZMM0020: Matris ekleme pop-up'ında tüm renkler (SLCTD_ALL_R) seçiliyor.")
        session.findById("wnd[1]/usr/cntlCONT_R_SCRN_0152_ALV_01/shellcont/shell").pressToolbarButton("SLCTD_ALL_R")
        time.sleep(0.2)

        logger.info("ZMM0020: Matris ekleme pop-up'ında tüm bedenler (SLCTD_ALL_B) seçiliyor.")
        session.findById("wnd[1]/usr/cntlCONT_B_SCRN_0152_ALV_01/shellcont/shell").pressToolbarButton("SLCTD_ALL_B")
        time.sleep(0.2)

        logger.info("ZMM0020: Matris ekleme pop-up'ında 'Devam' butonuna basılıyor (btn[5]).")
        session.findById("wnd[1]/tbar[0]/btn[5]").press()
        time.sleep(0.5) # İşlemin tamamlanmasını ve pop-up'ın kapanmasını bekle

        logger.info("ZMM0020: Ürün Ağacı sekmesi matris ekleme adımı başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.exception(f"ZMM0020 Ürün Ağacı sekmesi matris ekleme sırasında kritik hata: {e}")
        return False

def _handle_add_components_popupv1(session, components_to_add):
    """
    "Bileşen Ekle" pop-up'ında (wnd[1]) malzemeleri girer.

    Args:
        session: SAP GUI Scripting session objesi.
        components_to_add (list): Belirli bir operasyona ait eklenecek BOM kalemleri listesi.
                                  Her kalem bir dict olmalı: {'MALZEME_KODU': '...', 'KALEM_TIPI': '...', 'MİKTAR': ..., 'BİLEŞEN_ISKARTASI': ...}
    Returns:
        bool: İşlem başarılı ise True, aksi takdirde False.
    """
    try:
        # Pop-up penceresini bul
        popup_wnd = session.findById("wnd[1]")
        popup_wnd.maximize()
        time.sleep(0.5)

        logger.info(f"Bileşen Ekle pop-up'ı açıldı. {len(components_to_add)} adet malzeme girilecek.")

        alv_grid_popup = session.findById("wnd[1]/usr/cntlCONT_SCRN_0150_ALV_21/shellcont/shell")
        time.sleep(1) # ALV gridin yüklenmesi için bekle

        # Mevcut boş satır sayısı (genellikle 1)
        initial_row_count = alv_grid_popup.RowCount
        logger.debug(f"Pop-up'ta başlangıçtaki satır sayısı: {initial_row_count}")

        # Eklenecek satır sayısı (mevcut boş satır hariç)
        # Eğer 3 malzeme eklenecekse ve 1 boş satır varsa, 2 satır daha eklenmeli.
        # alv_grid_popup.insertRows("0") metodu tek bir satır ekler.
        # İstenen satır sayısına ulaşana kadar tekrarlamak daha güvenlidir.
        target_row_count = len(components_to_add)
        rows_to_insert = target_row_count - initial_row_count
        
        if rows_to_insert > 0:
            logger.info(f"{rows_to_insert} adet boş satır ekleniyor...")
            # Mevcut satırın üstüne eklemek için "0" kullanırız.
            # Her "insertRows" çağrısı sadece bir satır ekler.
            for _ in range(rows_to_insert):
                alv_grid_popup.insertRows("0") 
                time.sleep(0.8) # Her eklemeden sonra küçük bir bekleme
            time.sleep(1)
            logger.debug(f"Satır ekleme sonrası ALV grid satır sayısı: {alv_grid_popup.RowCount}")
        elif rows_to_insert < 0:
             logger.warning(f"Eklenecek malzeme sayısı ({len(components_to_add)}) mevcut satır sayısından ({initial_row_count}) az. Fazla satırlar kullanılmayacak.")

        # Malzeme bilgilerini her satıra gir
        for idx, component_item in enumerate(components_to_add):
            current_row_count = alv_grid_popup.RowCount
            if current_row_count <= idx:
                missing_rows = (idx + 1) - current_row_count
                logger.info(f"Satır {idx} yazılacak ancak ALV grid satır sayısı {current_row_count}. {missing_rows} adet satır ekleniyor...")
                for _ in range(missing_rows):
                    try:
                        alv_grid_popup.pressToolbarButton("ROW_ADD")
                    except Exception:
                        alv_grid_popup.insertRows("0")
                    time.sleep(0.3)
                time.sleep(0.3)

            logger.info(f"Satır {idx}: Malzeme '{component_item['MALZEME_KODU']}' bilgileri giriliyor...")

            # 13 haneli malzeme kodundan 10 haneli ana kodu al
            full_material_code = str(component_item['MALZEME_KODU'])
            main_material_code = full_material_code[:10] if len(full_material_code) >= 10 else full_material_code
            
            # COMPONENT (Malzeme Kodu)
            alv_grid_popup.modifyCell(idx, "COMPONENT", main_material_code)

            # ITEM_CATEG (Kalem Tipi)
            alv_grid_popup.modifyCell(idx, "ITEM_CATEG", str(component_item['KALEM_TIPI']).lower()) # SAP genellikle küçük harf bekler

            # MIKTAR (Miktar)
            # SAP'de ondalık ayırıcı genellikle virgüldür (,)
            miktar_str = str(component_item['MİKTAR']).replace('.', ',')
            alv_grid_popup.modifyCell(idx, "MIKTAR", miktar_str)

            # COMP_SCRAP_MENGE (Bileşen Iskartası)
            # Iskartanın da ondalık ayırıcısını kontrol et
            iskarta_str = str(component_item['BİLEŞEN_ISKARTASI']).replace('.', ',')
            alv_grid_popup.modifyCell(idx, "COMP_SCRAP_MENGE", iskarta_str)

        # Tüm malzeme satırları doldurulduktan sonra grid değişikliğini tek seferde tetikle
        alv_grid_popup.currentCellColumn = "COMP_SCRAP_MENGE"
        try:
            alv_grid_popup.triggerModified()
        except Exception as trg_err:
            logger.debug(f"triggerModified uyarısı: {trg_err}")
        time.sleep(0.3)

        # --- EKSİK MALZEME KONTROLÜ VE YENİDEN EKLEME ---
        logger.info("Tetikleme sonrası ALV grid'deki malzemeler ve eksiklikler kontrol ediliyor...")
        existing_grid_materials = []
        for r in range(alv_grid_popup.RowCount):
            try:
                cell_val = str(alv_grid_popup.GetCellValue(r, "COMPONENT")).strip()
                if cell_val:
                    existing_grid_materials.append(cell_val)
            except Exception as cell_err:
                logger.warning(f"Grid satır {r} COMPONENT okunurken hata: {cell_err}")

        logger.info(f"Grid'de mevcut malzeme kodları ({len(existing_grid_materials)} adet): {existing_grid_materials}")

        missing_items = []
        for item in components_to_add:
            raw_code = str(item.get('ANA_MALZEME_KODU') or item.get('MALZEME_KODU') or '')
            code_10 = raw_code[:10] if len(raw_code) >= 10 else raw_code
            if code_10 not in existing_grid_materials:
                missing_items.append(item)

        if missing_items:
            logger.warning(f"Tetikleme sonrası {len(missing_items)} adet malzeme eksik bulundu! Yeniden ekleniyor...")
            for missing_item in missing_items:
                raw_code = str(missing_item.get('ANA_MALZEME_KODU') or missing_item.get('MALZEME_KODU') or '')
                code_10 = raw_code[:10] if len(raw_code) >= 10 else raw_code
                
                try:
                    alv_grid_popup.pressToolbarButton("ROW_ADD")
                except Exception:
                    alv_grid_popup.insertRows("0")
                time.sleep(0.3)

                # Grid'deki boş satırın indeksini dinamik olarak bul (insertRows("0") 0. satıra ekler, ROW_ADD son satıra ekler)
                insert_row_idx = -1
                for r in range(alv_grid_popup.RowCount):
                    try:
                        cell_v = str(alv_grid_popup.GetCellValue(r, "COMPONENT")).strip()
                        if not cell_v:
                            insert_row_idx = r
                            break
                    except Exception:
                        pass
                
                if insert_row_idx == -1:
                    insert_row_idx = alv_grid_popup.RowCount - 1

                logger.info(f"Eksik malzeme '{code_10}' tespit edilen boş satır {insert_row_idx}'ye ekleniyor...")

                first_sub = missing_item['ITEMS'][0] if 'ITEMS' in missing_item and missing_item['ITEMS'] else missing_item
                alv_grid_popup.modifyCell(insert_row_idx, "COMPONENT", code_10)
                alv_grid_popup.modifyCell(insert_row_idx, "ITEM_CATEG", str(first_sub.get('KALEM_TIPI', '')).lower())
                
                qty_val = str(first_sub.get('MİKTAR', '')).replace('.', ',')
                alv_grid_popup.modifyCell(insert_row_idx, "MIKTAR", qty_val)

                raw_sc = first_sub.get('BİLEŞEN_ISKARTASI')
                sc_str = "0" if raw_sc is None or str(raw_sc).strip() in ("", "nan") else str(raw_sc).replace('.', ',')
                alv_grid_popup.modifyCell(insert_row_idx, "COMP_SCRAP_MENGE", sc_str)

            alv_grid_popup.currentCellColumn = "COMP_SCRAP_MENGE"
            try:
                alv_grid_popup.triggerModified()
            except Exception as trg_err:
                logger.debug(f"Yeniden tetikleme uyarısı: {trg_err}")
            time.sleep(0.3)
        else:
            logger.info("Tüm eklenecek malzemelerin grid'de olduğu başarıyla doğrulandı.")

        # Tüm veriler girildikten sonra pop-up'ı kapat
        logger.info("Tüm malzemeler girildi. Pop-up kapatılıyor (Enter tuşu gönderiliyor).")
        session.findById("wnd[1]").sendVKey(0) # 0 = Enter tuşu
        session.findById("wnd[1]/tbar[0]/btn[13]").press() 
        time.sleep(1)

        status_after_popup = read_sap_status_bar(session)
        if status_after_popup["type"] == "E":
            logger.error(f"Bileşen Ekle pop-up'ı sonrası hata: {status_after_popup['text']}")
            return False
        elif status_after_popup["text"]:
            logger.info(f"Bileşen Ekle pop-up'ı sonrası mesaj: {status_after_popup['text']}")

        return True

    except Exception as e:
        logger.exception(f"Bileşen Ekle pop-up'ı yönetilirken hata oluştu: {e}")
        return False


def _handle_add_components_popup(session, components_to_add):
    """
    "Bileşen Ekle" pop-up'ında (wnd[1]) malzemeleri girer ve pop-up'ı kapatır.
    Eğer mevcut pop-up'ta tüm malzemeler girilemezse, pop-up yine de onaylanıp kapatılır
    ve eklenemeyen eksik malzemeler listelenerek ana akışta tekrar 'MULTI_ADD_COMP' yapılması sağlanır.

    Args:
        session: SAP GUI Scripting session objesi.
        components_to_add (list): [{'ANA_MALZEME_KODU': '...', 'ITEMS': [...]}, ...] formatında liste.

    Returns:
        tuple: (success: bool, remaining_components: list)
    """
    try:
        # Pop-up penceresini bul
        popup_wnd = session.findById("wnd[1]")
        popup_wnd.maximize()
        time.sleep(0.5)

        logger.info(f"Bileşen Ekle pop-up'ı açıldı. {len(components_to_add)} adet malzeme girilmeye çalışılacak.")

        alv_grid_popup = session.findById("wnd[1]/usr/cntlCONT_SCRN_0150_ALV_21/shellcont/shell")
        time.sleep(1) # ALV gridin yüklenmesi için bekle

        initial_row_count = alv_grid_popup.RowCount
        logger.debug(f"Pop-up'ta başlangıçtaki satır sayısı: {initial_row_count}")

        target_row_count = len(components_to_add)
        rows_to_insert = target_row_count - initial_row_count
        
        if rows_to_insert > 0:
            logger.info(f"Pop-up için {rows_to_insert} adet boş satır ekleme deneniyor...")
            for _ in range(rows_to_insert):
                try:
                    alv_grid_popup.insertRows("0")
                except Exception as ins_e:
                    logger.debug(f"Satır ekleme uyarısı: {ins_e}")
                time.sleep(0.3)
            time.sleep(0.5)

        added_components = []
        remaining_components = []

        # Malzeme bilgilerini mevcut satırlara sırayla gir
        for idx, component_item in enumerate(components_to_add):
            current_row_count = alv_grid_popup.RowCount
            if idx >= current_row_count:
                # Pop-up grid kapasitesi doldu, kalan malzemeler bir sonraki MULTI_ADD_COMP turuna bırakılır
                logger.info(f"Pop-up satır kapasitesi doldu ({idx}/{current_row_count}). Kalan {len(components_to_add) - idx} adet malzeme sonraki tura bırakılıyor.")
                remaining_components.extend(components_to_add[idx:])
                break

            main_material_code = str(component_item['ANA_MALZEME_KODU'])
            first_item = component_item['ITEMS'][0]

            logger.info(f"Pop-up Satır {idx}: Malzeme '{main_material_code}' giriliyor...")
            
            alv_grid_popup.modifyCell(idx, "COMPONENT", main_material_code)
            alv_grid_popup.modifyCell(idx, "ITEM_CATEG", str(first_item['KALEM_TIPI']).lower())

            miktar_str = str(first_item['MİKTAR']).replace('.', ',')
            alv_grid_popup.modifyCell(idx, "MIKTAR", miktar_str)

            raw_iskarta = first_item.get('BİLEŞEN_ISKARTASI')
            if raw_iskarta is None or str(raw_iskarta).strip() == "" or str(raw_iskarta).lower() == "nan":
                iskarta_str = "0"
            else:
                iskarta_str = str(raw_iskarta).replace('.', ',')

            alv_grid_popup.modifyCell(idx, "COMP_SCRAP_MENGE", iskarta_str)
            added_components.append(component_item)

        # Değişiklikleri tetikle
        alv_grid_popup.currentCellColumn = "COMP_SCRAP_MENGE"
        try:
            alv_grid_popup.triggerModified()
        except Exception as trg_err:
            logger.debug(f"triggerModified uyarısı: {trg_err}")
        time.sleep(0.3)

        # Pop-up'ı kapat
        logger.info(f"Girilen {len(added_components)} malzeme kaydediliyor. Pop-up kapatılıyor (Enter tuşu gönderiliyor).")
        session.findById("wnd[1]").sendVKey(0) # 0 = Enter tuşu
        session.findById("wnd[1]/tbar[0]/btn[13]").press() 
        time.sleep(1) # Pop-up kapandıktan sonra ekranın stabilize olmasını bekle

        # Pop-up kapandıktan sonra durum çubuğunu kontrol et
        status_after_popup = read_sap_status_bar(session)
        if status_after_popup["type"] == "E":
            logger.error(f"Bileşen Ekle pop-up'ı sonrası hata: {status_after_popup['text']}")
            return False, components_to_add
        elif status_after_popup["text"]:
            logger.info(f"Bileşen Ekle pop-up'ı sonrası mesaj: {status_after_popup['text']}")

        return True, remaining_components

    except Exception as e:
        logger.exception(f"Bileşen Ekle pop-up'ı yönetilirken hata oluştu: {e}")
        return False, components_to_add


ALV_COLUMN_TECHNICAL_NAME_FOR_OPERATION_KEY = "KTSCH"    
ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE = "COMPONENT"
ALV_COLUMN_TECHNICAL_NAME_FOR_AFS = "AFS"


def _get_existing_materials_in_main_bom_grid(alv_grid_bom):
    """
    Ana BOM ALV gridindeki (wnd[0]) mevcut malzemelerin 10 haneli ana kodlarını toplar.
    """
    existing_materials = set()
    for row in range(alv_grid_bom.RowCount):
        try:
            cell_val = str(alv_grid_bom.GetCellValue(row, ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE)).strip()
            if cell_val:
                code_10 = cell_val[:10] if len(cell_val) >= 10 else cell_val
                existing_materials.add(code_10)
        except Exception:
            pass
    return existing_materials


def zmm0020_select_bom_operation_and_add_components(session, excel_bom_file_path, available_colors, available_sizes, afs_column_metadata_from_prod_versions, plm_id):
    """
    ZMM0020 ekranında Ürün Ağacı (BOM) sekmesine geçer,
    Excel'den okunan operasyonlara göre SAP'deki ilgili BOM satırını seçer
    ve "Bileşen Ekle" (MULTI_ADD_COMP) butonuna basar, ardından pop-up'ı yönetir.

    Args:
        session: SAP GUI Scripting session objesi.
        excel_bom_file_path (str): Kullanıcı tarafından doldurulmuş BOM Excel dosyasının yolu.
        available_colors (list): Excel'i oluştururken kullanılan mevcut renk kodları listesi.
        available_sizes (list): Excel'i oluştururken kullanılan mevcut beden kodları listesi.

    Returns:
        list: Excel'den okunan ve işlenecek BOM verileri. None: Hata durumunda.
    """
    try:
        session.findById("wnd[0]").maximize()

        logger.info("ZMM0020: 'Ürün Ağacı (BOM)' sekmesine (TAB5) geçiliyor.")
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB5").select()
        time.sleep(0.5) # Sekme değişiminden sonra bekleme

        # Ekranın 'Değiştir' modunda olduğundan emin ol
        if not ensure_change_mode(session, change_button_id="wnd[0]/tbar[1]/btn[14]"):
            raise Exception("ZMM0020: Ürün Ağacı sekmesi 'Değiştir' moduna geçilemedi.")
        
        # Excel dosyasını oku
        bom_data_from_excel = read_bom_from_excel(excel_bom_file_path, available_colors, available_sizes, plm_id)
        if not bom_data_from_excel:
            logger.error("BOM Excel dosyasından veri okunamadı veya boş.")
            return None
        
        # Operasyonlara göre BOM kalemlerini grupla
        grouped_bom_by_operation = {}
        for item in bom_data_from_excel:
            operation = item['OPERASYON']
            if operation not in grouped_bom_by_operation:
                grouped_bom_by_operation[operation] = []
            grouped_bom_by_operation[operation].append(item)
        
        # Yeni yapıyı tutacak ana sözlük
        final_grouped_bom = {}        
        for operation, items in grouped_bom_by_operation.items():
            # Her operasyon için geçici bir gruplandırma sözlüğü (10 haneli koda göre)
            temp_material_groups = {}

            for item in items:
                # Malzeme kodunun ilk 10 hanesini al (Ana Malzeme Kodu)
                material_code = str(item.get('MALZEME_KODU', ''))
                ana_kod = material_code[:10]
                if ana_kod not in temp_material_groups:
                    temp_material_groups[ana_kod] = []
                # Öğeyi ilgili ana kod grubuna ekle
                temp_material_groups[ana_kod].append(item)
            # Geçici sözlüğü istenen liste formatına dönüştür: 
            # [{"ANA_MALZEME_KODU": "...", "ITEMS": [...]}, ...]
            operation_list = []
            for ana_kod, grouped_items in temp_material_groups.items():
                operation_list.append({
                    "ANA_MALZEME_KODU": ana_kod,
                    "ITEMS": grouped_items
                })

            # Ana sözlüğe operasyon bazlı ekle
            final_grouped_bom[operation] = operation_list
        # Sonuç çıktısını kontrol etmek istersen:
        import json
        print(json.dumps(final_grouped_bom, indent=2, ensure_ascii=False))

        alv_grid_bom = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB5/ssubSUB5:ZPP_001_P_MDC:0150/cntlCONT_SCRN_0150_ALV_01/shellcont/shell")
        time.sleep(0.1) # ALV grid objesine erişmeden önce kısa bir bekleme

        # Her bir operasyon grubu için SAP'de işlem yap
        for excel_operation, components_for_operation in final_grouped_bom.items():
            sap_operation_key = KTSCH_MAP.get(excel_operation) # KTSCH_MAP kullanılıyor
            if not sap_operation_key:
                logger.warning(f"Excel operasyonu '{excel_operation}' için SAP Standart Metin Anahtarı eşlemesi bulunamadı. Atlanıyor.")
                continue

            logger.info(f"SAP'de '{excel_operation}' (Anahtar: {sap_operation_key}) operasyon satırı aranıyor...")
            
            found_row = -1
            for row in range(alv_grid_bom.RowCount):
                try:
                    cell_value = alv_grid_bom.GetCellValue(row, ALV_COLUMN_TECHNICAL_NAME_FOR_OPERATION_KEY) # "KTSCH" kullanılıyor
                    if str(cell_value) == sap_operation_key:
                        found_row = row
                        break
                except Exception as cell_e:
                    logger.warning(f"ALV grid satır {row}, sütun '{ALV_COLUMN_TECHNICAL_NAME_FOR_OPERATION_KEY}' okunurken hata: {cell_e}")
                    continue # Hata durumunda bu satırı atla
            
            if found_row != -1:
                logger.info(f"Operasyon '{excel_operation}' için SAP'de {found_row}. satır bulundu.")
                
                attempt_count = 0
                max_attempts = 5

                while attempt_count < max_attempts:
                    attempt_count += 1

                    # Ana BOM ekranında (wnd[0]) bu operasyon için eksik malzemeleri kontrol et
                    existing_in_main = _get_existing_materials_in_main_bom_grid(alv_grid_bom)
                    logger.info(f"Ana BOM gridinde mevcut malzeme kodları ({len(existing_in_main)} adet): {list(existing_in_main)}")

                    missing_components_for_op = []
                    for comp in components_for_operation:
                        raw_code = str(comp['ANA_MALZEME_KODU'])
                        code_10 = raw_code[:10] if len(raw_code) >= 10 else raw_code
                        if code_10 not in existing_in_main:
                            missing_components_for_op.append(comp)

                    if not missing_components_for_op:
                        logger.info(f"Operasyon '{excel_operation}' için tüm malzemeler ({len(components_for_operation)} adet) SAP ana BOM ekranında başarıyla doğrulandı!")
                        break

                    logger.info(f"Operasyon '{excel_operation}' için {len(missing_components_for_op)} adet eksik malzeme var: {[c['ANA_MALZEME_KODU'] for c in missing_components_for_op]}. Tur {attempt_count} başlatılıyor...")

                    alv_grid_bom.setCurrentCell(found_row, ALV_COLUMN_TECHNICAL_NAME_FOR_OPERATION_KEY) # "KTSCH" kullanılıyor
                    alv_grid_bom.selectedRows = str(found_row) 
                    time.sleep(0.5) # Hızlandırma

                    logger.info(f"Operasyon '{excel_operation}' için 'Bileşen Ekle' (MULTI_ADD_COMP) butonuna basılıyor.")
                    alv_grid_bom.pressToolbarButton("MULTI_ADD_COMP")
                    time.sleep(0.5) # Hızlandırma
                    print(f"Bileşen ekle pop-up'ına gönderilecek eksik malzemeler: {missing_components_for_op}")

                    success, _ = _handle_add_components_popup(session, missing_components_for_op)
                    if not success:
                        logger.error(f"Operasyon '{excel_operation}' için Bileşen Ekle pop-up'ı yönetilirken hata oluştu. Akış durduruluyor.")
                        return None
                    
                    status_after_add = read_sap_status_bar(session)
                    if status_after_add["type"] == "E":
                        logger.error(f"Operasyon '{excel_operation}' için 'Bileşen Ekle' sonrası ana ekranda hata: {status_after_add['text']}")
                        return None

                    time.sleep(0.5)

            else:
                logger.warning(f"Operasyon '{excel_operation}' (Anahtar: {sap_operation_key}) için SAP BOM gridinde satır bulunamadı. Bu operasyona ait malzemeler atlanıyor.")
        
        logger.info("Tüm operasyonlar için SAP BOM satırı seçme ve bileşen ekleme adımları tamamlandı.")
        return final_grouped_bom 

    except Exception as e:
        logger.exception(f"ZMM0020 BOM operasyon satırı seçilirken veya 'Bileşen Ekle' butonuna basılırken kritik hata: {e}")
        return None 

    except Exception as e:
        logger.exception(f"ZMM0020 BOM operasyon satırı seçilirken veya 'Bileşen Ekle' butonuna basılırken kritik hata: {e}")
        return None
    
# --- YARDIMCI FONKSİYON: "Üretim Versiyonları" sekmesinden AFS sütun metadata'sını alma ---
def _get_afs_column_metadata_from_prod_versions_tab(session):
    """
    "Üretim Versiyonları" sekmesinden (TAB6) AFS pop-up'ı için gerekli olan
    malzeme kodu, renk ve beden bilgilerini toplar.
    Bu fonksiyon AFS pop-up'ı açılmadan önce çağrılmalıdır.
    """
    logger.info("Üretim Versiyonları sekmesinden AFS sütun metadata'sı alınıyor...")
    
    # Mevcut sekmeyi kaydet, böylece geri dönebiliriz
    current_tab_id = session.findById("wnd[0]/usr/tabsTAB_CONTROL").selectedTab

    try:
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB6").select()
        time.sleep(2)

        alv_grid_prod_versions = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB6/ssubSUB6:ZPP_001_P_MDC:0160/cntlCONT_SCRN_0160_ALV_01/shellcont/shell")
        
        total_rows = alv_grid_prod_versions.RowCount
        logger.info(f"ALV Grid bulundu. Toplam Satır Sayısı: {total_rows}")

        prod_versions_data = []
        
        for row in range(total_rows):
            # SAP'nin bazen görünmeyen satırları yüklemesi için her 20 satırda bir 'scroll' yapabiliriz (opsiyonel)
            if row % 20 == 0: alv_grid_prod_versions.firstVisibleRow = row
            
            try:
                matnr = str(alv_grid_prod_versions.GetCellValue(row, "MATNR")).strip()
                full_color_text = str(alv_grid_prod_versions.GetCellValue(row, "COLOR_ATWTB")).strip()
                size = str(alv_grid_prod_versions.GetCellValue(row, "SIZE_ATWTB")).strip()
                
                # Regex işlemi
                color_code_match = re.search(r'([A-Z0-9]{3,})$', full_color_text)
                color = color_code_match.group(1) if color_code_match else full_color_text
                
                # KRİTİK DEĞİŞİKLİK: Neden atlandığını anlamak için log ekle
                if not (matnr and color and size):
                    logger.warning(f"Satır {row} eksik veri nedeniyle atlandı: MATNR='{matnr}', COLOR='{color}', SIZE='{size}'")
                    continue

                prod_versions_data.append({
                    'full_material_code': matnr,
                    'color': color,
                    'size': size
                })
                
            except Exception as cell_read_e:
                logger.error(f"Satır {row} okunurken hata oluştu: {cell_read_e}")
                continue
        
        logger.info(f"İşlem tamamlandı. Toplam: {total_rows} satırdan {len(prod_versions_data)} adet geçerli veri alındı.")
        return prod_versions_data

    except Exception as e:
        logger.exception(f"Üretim Versiyonları sekmesinden AFS sütun metadata'sı alınırken kritik hata oluştu: {e}")
        raise # Hata durumunda akışı durdur
    finally:
        # Orijinal sekmeye geri dön
        try:
            session.findById("wnd[0]/usr/tabsTAB_CONTROL").select(current_tab_id)
            time.sleep(1)
            logger.info(f"Orijinal sekme ({current_tab_id}) geri dönüldü.")
        except Exception as e_nav_back:
            logger.error(f"Orijinal sekmeye geri dönülürken hata: {e_nav_back}")

# --- YARDIMCI FONKSİYON: AFS Pop-up'ındaki Miktar Hücrelerini Temizleme ---
def _clear_afs_quantity_cells_optimized_modifycell(session, afs_alv_grid, parsed_columns_info):
    """
    AFS pop-up'ındaki miktar hücrelerini optimize edilmiş bir şekilde temizler.
    Sadece parsed_columns_info'da bulunan dinamik AFS sütunlarını hedefler
    ve yalnızca dolu olan hücreleri temizler.
    """
    logger.info("AFS pop-up'ındaki miktar hücreleri optimize edilmiş modifyCell ile temizleniyor...")

    try:
        # Tüm satırları gez
        for row_idx in range(afs_alv_grid.RowCount):
            # Sadece miktar girilen (dinamik) sütunları gez
            for col_info in parsed_columns_info:
                col_id_to_clear = col_info['col_id'] # Bu, VM_... teknik ID'si olmalı
                
                try:
                    # Hücrenin mevcut değerini oku
                    current_value = afs_alv_grid.GetCellValue(row_idx, col_id_to_clear)
                    
                    # Eğer hücre boş değilse (sayı veya başka bir değer içeriyorsa) temizle
                    if str(current_value).strip() != "":
                        logger.debug(f"Satır {row_idx}, Sütun '{col_id_to_clear}' dolu ('{current_value}'). Temizleniyor.")
                        afs_alv_grid.modifyCell(row_idx, col_id_to_clear, "") # Hücreyi boş string ile güncelle
                        # Değişikliği tetiklemek için currentCellColumn ve triggerModified kullanmak önemlidir
                        afs_alv_grid.currentCellColumn = col_id_to_clear 
                        afs_alv_grid.triggerModified()
                        time.sleep(0.01) # Çok hızlı olmamak için küçük bir bekleme
                    else:
                        logger.debug(f"Satır {row_idx}, Sütun '{col_id_to_clear}' zaten boş. Atlanıyor.")

                except Exception as get_cell_or_modify_e:
                    logger.warning(f"Satır {row_idx}, Sütun '{col_id_to_clear}' işlenirken hata oluştu: {get_cell_or_modify_e}. Atlanıyor.")
                    # Bu hata genellikle GetCellValue veya modifyCell'in başarısız olduğunu gösterir.

        logger.info("AFS pop-up'ındaki miktar hücreleri optimize edilmiş modifyCell ile temizleme işlemi tamamlandı.")
        return True

    except Exception as e:
        logger.exception(f"AFS pop-up'ındaki miktar hücreleri optimize edilmiş modifyCell ile temizlenirken genel hata oluştu: {e}")
        return False

def _clear_afs_quantity_cells_by_delete_key(session, afs_alv_grid):
    """
    AFS pop-up'ındaki miktar hücrelerini "Del" tuşuna basarak temizler.
    Önce tüm hücreleri seçer, ardından belirli sütunların seçimini kaldırır.
    """
    logger.info("AFS pop-up'ındaki miktar hücreleri 'Del' tuşu ile temizleniyor...")

    try:
        # Tüm satır ve sütunları seç
        afs_alv_grid.selectAll()
        time.sleep(0.5)
        logger.debug("Tüm hücreler seçildi.")

        # Temizlenmeyecek sütunların seçimini kaldır
        deselect_columns = ["BEDEN", "COMPONENT", "COMPONENT_T", "RENK", "MATKL"]
        for col_name in deselect_columns:
            try:
                afs_alv_grid.deselectColumn(col_name)
                time.sleep(0.1)
                logger.debug(f"Sütun '{col_name}' seçimi kaldırıldı.")
            except Exception as e_deselect:
                logger.warning(f"Sütun '{col_name}' seçimi kaldırılamadı (muhtemelen mevcut değil veya zaten seçili değil): {e_deselect}")
        
        time.sleep(0.5) # Seçimlerin uygulanması için bekleme

        # Seçili hücreleri silmek için "Del" tuşuna bas
        # VKey(70) Del tuşunun kodudur. Bunu doğrudan GuiShell'e gönderiyoruz.
        logger.info("Seçili miktar hücrelerini silmek için 'Del' tuşuna basılıyor...")
        afs_alv_grid.sendVKey(70) 
         
        time.sleep(1) 


        logger.info("AFS pop-up'ındaki miktar hücreleri 'Del' tuşu ile temizleme işlemi tamamlandı.")
        return True

    except Exception as e:
        logger.exception(f"AFS pop-up'ındaki miktar hücreleri 'Del' tuşu ile temizlenirken hata oluştu: {e}")
        return False

# --- YARDIMCI FONKSİYON: AFS Pop-up'ını Yönetme ---
def _handle_afs_popupv1(session, bom_item, available_colors, available_sizes, afs_column_metadata_from_prod_versions):
    """
    AFS pop-up'ında (wnd[1]) renk ve bedenlere göre miktarları girer.
    Sütun teknik ID'leri, önceden alınan afs_column_metadata_from_prod_versions'dan oluşturulur.
    """
    try:
        popup_wnd = session.findById("wnd[1]")
        popup_wnd.maximize()
        time.sleep(0.5) 
        logger.info(f"AFS pop-up'ı açıldı. Malzeme: {bom_item['MALZEME_KODU']}")

        afs_alv_grid = session.findById("wnd[1]/usr/cntlCONT_SCRN_0150_ALV_02/shellcont/shell")
        time.sleep(0.3) 
        
        full_material_code = str(bom_item['MALZEME_KODU'])
        operation = bom_item['OPERASYON']
        is_13_digit_material = (len(full_material_code) == 13)
        selected_colors = bom_item['SEÇİLİ_RENKLER']
        selected_sizes = bom_item['SEÇİLİ_BEDENLER']
        is_color_different = bom_item['MALZEME_RENGI_FARKLI_MI']
        quantity_str = str(bom_item['MİKTAR']).replace('.', ',') # SAP için virgül formatı

        # Senaryo 1: Renk: TÜMÜ, Beden: TÜMÜ (Hem 10 hem 13 haneli için aynı)
        if (sorted(selected_colors) == sorted(available_colors) or not selected_colors) and \
           (sorted(selected_sizes) == sorted(available_sizes) or not selected_sizes) and \
           is_color_different is False:
               
            logger.info("AFS: Renk: TÜMÜ, Beden: TÜMÜ senaryosu. Otomatik devam ediliyor.")
            session.findById("wnd[1]").sendVKey(0) # Enter'a bas
            time.sleep(0.2)
            session.findById("wnd[1]/tbar[0]/btn[13]").press() # "Devam" veya "Kaydet" butonu
            time.sleep(0.3)
            return True
            
       
        # YENİ: Operasyon bilgisine göre afs_column_metadata_from_prod_versions listesini filtrele
        expected_prefix = OPERATION_PREFIX_MAP.get(operation)
        filtered_metadata = []

        if not expected_prefix:
            logger.warning(f"Operasyon '{operation}' için malzeme kodu ön eki bulunamadı. Tüm Üretim Versiyonları metadata'sı kullanılacak.")
            filtered_metadata = afs_column_metadata_from_prod_versions
        else:
            filtered_metadata = [
                item for item in afs_column_metadata_from_prod_versions
                if item['full_material_code'].startswith(expected_prefix)
            ]
            logger.info(f"Operasyon '{operation}' için '{expected_prefix}*' ön ekiyle {len(filtered_metadata)} adet malzeme bulundu.")
            if not filtered_metadata:
                logger.warning(f"Operasyon '{operation}' ({expected_prefix}*) için Üretim Versiyonları'nda eşleşen malzeme bulunamadı. AFS girişi atlanıyor.")
       
        # --- AFS Sütun Bilgilerini Kullanma ---
        # afs_column_metadata_from_prod_versions zaten dışarıdan geldi.
        # Bu listeyi kullanarak parsed_columns_info'yu oluşturacağız.
        
        parsed_columns_info = [] # [{'col_id': 'VM_...', 'color': 'DWP', 'size': 'S'}, ...]

        for item in filtered_metadata:
            full_mat_code_from_prod_version = item['full_material_code']
            color = item['color']
            size = item['size']

            # AFS sütun teknik ID'sini oluştur
            # Pattern: "VM_000002" + 13_digit_material_code[1:]
            # Örneğin: 2014054675008 -> VM_000002014054675008
            # Bu teknik ID'ler, afs_alv_grid.modifyCell için kullanılacak.
            afs_tech_id = "VM_00000" + full_mat_code_from_prod_version 
            

            parsed_columns_info.append({
                'col_id': afs_tech_id, 
                'color': color, 
                'size': size
            })
        
        logger.debug(f"AFS pop-up'ı için oluşturulan sütun metadata'sı: {parsed_columns_info}")

        if not parsed_columns_info:
            raise Exception("AFS pop-up'ında renk/beden sütunları parse edilemedi, işlem iptal ediliyor.")
        
        if not _clear_afs_quantity_cells_optimized_modifycell(session, afs_alv_grid, parsed_columns_info):
            logger.error("AFS miktar hücreleri temizlenirken hata oluştu. Akış durduruluyor.")
            return False
        #if not _clear_afs_quantity_cells_by_delete_key(session, afs_alv_grid):
        #    logger.error("AFS miktar hücreleri 'Del' tuşu ile temizlenirken hata oluştu. Akış durduruluyor.")
        #    return False
        # --- Temizleme işlemi sonu ---
        
        # Eğer 13 haneli malzeme kodu ise, önce ALV gridi filtrele
        if is_13_digit_material:
            logger.info(f"13 haneli malzeme kodu ({full_material_code}) için AFS pop-up'ında filtreleme yapılıyor.")
            afs_alv_grid.currentCellRow = -1 # Seçimi kaldır
            afs_alv_grid.selectColumn(ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE) # "COMPONENT" sütununu seç
            afs_alv_grid.pressToolbarButton("&MB_FILTER") # Filtre butonuna bas
            time.sleep(0.5) # Filtre pop-up'ının açılmasını bekle
            
            # Filtre pop-up'ı (wnd[2])
            session.findById("wnd[2]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/ctxt%%DYN001-LOW").text = full_material_code
            session.findById("wnd[2]").sendVKey(0) # Enter'a basarak filtreyi uygula
            time.sleep(0.5) # Filtrenin uygulanıp ALV'nin güncellenmesini bekle
            logger.info(f"AFS pop-up'ı filtreleme tamamlandı. Kalan satır sayısı: {afs_alv_grid.RowCount}")
            
            
        # Her bir satır ve sütun için miktarları gir
        for row_idx in range(afs_alv_grid.RowCount):
            for col_info in parsed_columns_info:
                col_id = col_info['col_id'] # Teknik ID kullanılıyor
                col_color = col_info['color']
                col_size = col_info['size']
                cs = col_size.lower().strip()
                # Kural 1: "X-Y yaş" formatını "Xy-Yy" formatına dönüştür (örn: "2-3 yaş" -> "2y-3y")
                match_range_yas = re.match(r'(\d+)\s*-\s*(\d+)\s*yaş', cs)
                if match_range_yas:
                    num1 = match_range_yas.group(1)
                    num2 = match_range_yas.group(2)
                    col_size = f"{num1}y-{num2}y" # Burası güncellendi
                #print(f"Renk: {col_color}, Beden: {col_size}")
                #print(f" SELECTED Renk: {selected_colors}, selected Beden: {selected_sizes}")
                should_fill_cell = False

                # Senaryo 2: Renk: SEÇİMLİ, Beden: TÜMÜ
                if col_color in selected_colors and \
                   (sorted(selected_sizes) == sorted(available_sizes) or not selected_sizes):
                    print("# Senaryo 2: Renk: SEÇİMLİ, Beden: TÜMÜ")
                    should_fill_cell = True
                # Senaryo 3: Renk: TÜMÜ, Beden: SEÇİMLİ
                elif (sorted(selected_colors) == sorted(available_colors) or not selected_colors) and \
                     col_size in selected_sizes:
                    print("# Senaryo 3:  Renk: TÜMÜ, Beden: SEÇİMLİ")
                    should_fill_cell = True
                # Senaryo 4: Renk: SEÇİMLİ, Beden: SEÇİMLİ
                elif col_color in selected_colors and col_size in selected_sizes:
                    print("# Senaryo 4: Renk: SEÇİMLİ, Beden: SEÇİMLİ")
                    should_fill_cell = True
                # Senaryo 5: Renk: TÜMÜ, Beden: TÜMÜ isDifferent true 
                elif (sorted(selected_colors) == sorted(available_colors) or not selected_colors) and \
                    (sorted(selected_sizes) == sorted(available_sizes) or not selected_sizes):
                    print("# Senaryo 5: Renk: TÜMÜ, Beden: TÜMÜ isdif true")
                    should_fill_cell = True
                print(f"should_fill_cell: {should_fill_cell}")
                if should_fill_cell:
                    afs_alv = session.findById("wnd[1]/usr/cntlCONT_SCRN_0150_ALV_02/shellcont/shell")
                    logger.info(f"AFS: Satır {row_idx}, Sütun {col_id} ({col_color}/{col_size}) için miktar giriliyor: {quantity_str}")
                    afs_alv.modifyCell(row_idx, col_id, quantity_str) 
                    afs_alv.currentCellColumn = col_id
                    afs_alv.triggerModified()
                    time.sleep(0.1) 
                    


            #logger.info("AFS pop-up'ında veri girişi tamamlandı. Pop-up kapatılıyor (Enter tuşu gönderiliyor).")
            #session.findById("wnd[1]").sendVKey(0) 

            session.findById("wnd[1]/tbar[0]/btn[13]").press()
            time.sleep(0.5)

        status_after_popup = read_sap_status_bar(session)
        if status_after_popup["type"] == "E":
            logger.error(f"AFS pop-up'ı sonrası hata: {status_after_popup['text']}")
            return False
        elif status_after_popup["text"]:
            logger.info(f"AFS pop-up'ı sonrası mesaj: {status_after_popup['text']}")

        return True

    except Exception as e:
        logger.exception(f"AFS pop-up'ı yönetilirken hata oluştu: {e}")
        return False
    
def _handle_afs_popup(session, variant_items, available_colors, available_sizes, afs_column_metadata_from_prod_versions):
    """
    AFS pop-up'ında (wnd[1]) verileri girer.
    Senaryo-1: Filtreleme yapmadan onaylar.
    Diğer Senaryolar: Önce temizler, sonra filtreler, sonra doldurur.
    """
    try:
        if not variant_items:
            return False

        first_item = variant_items[0]
        operation = first_item['OPERASYON']
        # Gruptaki herhangi bir item'da renk farklılığı işaretlenmiş mi?
        is_color_different = any(item.get('MALZEME_RENGI_FARKLI_MI', False) for item in variant_items)
        
        # Senaryo-1 Kontrolü (Sadece tek bir grup/item varsa ve her şey 'TÜMÜ' ise)
        is_all_colors = (sorted(first_item['SEÇİLİ_RENKLER']) == sorted(available_colors) or not first_item['SEÇİLİ_RENKLER'])
        is_all_sizes = (sorted(first_item['SEÇİLİ_BEDENLER']) == sorted(available_sizes) or not first_item['SEÇİLİ_BEDENLER'])
        
        # SENARYO-1 KOŞULU
        if len(variant_items) == 1 and is_all_colors and is_all_sizes and not is_color_different:
            logger.info("AFS: Senaryo-1 (Tümü/Tümü) algılandı. Filtreleme yapılmadan onaylanıyor.")
            session.findById("wnd[1]").sendVKey(0) # Enter
            time.sleep(0.2)
            session.findById("wnd[1]/tbar[0]/btn[13]").press() # Devam
            return True

        # --- BURADAN SONRASI FİLTRELEME GEREKTİREN DURUMLAR ---
        popup_wnd = session.findById("wnd[1]")
        popup_wnd.maximize()
        time.sleep(0.5)

        afs_alv_grid = session.findById("wnd[1]/usr/cntlCONT_SCRN_0150_ALV_02/shellcont/shell")
        #logger.info(f"afs_column_metadata_from_prod_versions: {afs_column_metadata_from_prod_versions}")
        # 1. Sütun Metadata Hazırlığı
        expected_prefix = OPERATION_PREFIX_MAP.get(operation)
        filtered_metadata = [
            item for item in afs_column_metadata_from_prod_versions
            if not expected_prefix or item['full_material_code'].startswith(expected_prefix)
        ]
        #logger.info(f"filtered: {filtered_metadata}")
        parsed_columns_info = [{'col_id': "VM_00000" + i['full_material_code'], 'color': i['color'], 'size': i['size']} for i in filtered_metadata]
        #logger.info(f"parsed_columns_info: {parsed_columns_info}")
        # 2. TEMİZLEME (Filtreleme işleminden ÖNCE yapılıyor)
        logger.info("AFS: Filtreleme öncesi hücreler temizleniyor...")
        if not _clear_afs_quantity_cells_optimized_modifycell(session, afs_alv_grid, parsed_columns_info):
            return False

        # 3. FİLTRELEME
        unique_material_codes = list(set(str(item['MALZEME_KODU']) for item in variant_items))
        has_13_digit_code = any(len(code) == 13 for code in unique_material_codes)
        if has_13_digit_code:
            logger.info(f"AFS: Filtreleme yapılıyor. Kodlar: {unique_material_codes}")
        
            afs_alv_grid.currentCellRow = -1
            afs_alv_grid.selectColumn(ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE)
            afs_alv_grid.pressToolbarButton("&MB_FILTER")
            time.sleep(0.5)

            if len(unique_material_codes) == 1:
                session.findById("wnd[2]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/ctxt%%DYN001-LOW").text = unique_material_codes[0]
                session.findById("wnd[2]").sendVKey(0)
            else:
                # Çoklu Seçim
                session.findById("wnd[2]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/btn%_%%DYN001_%_APP_%-VALU_PUSH").press()
                time.sleep(0.5)
                for idx, code in enumerate(unique_material_codes):
                    cell_id = f"wnd[3]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE/ctxtRSCSEL_255-SLOW_I[1,{idx}]"
                    session.findById(cell_id).text = code
                session.findById("wnd[3]/tbar[0]/btn[0]").press() # Enter
                session.findById("wnd[3]/tbar[0]/btn[8]").press() # Aktar
                time.sleep(0.3)
                session.findById("wnd[2]/tbar[0]/btn[0]").press() # Onayla
        else:
            logger.info("AFS: 10 haneli kodlar mevcut, filtreleme adımı atlanıyor.")
        
        time.sleep(0.5)

#        # 4. VERİ GİRİŞİ (Filtrelenmiş Grid Üzerinde)
#        for row_idx in range(afs_alv_grid.RowCount):
#            row_material_code = afs_alv_grid.GetCellValue(row_idx, ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE)
#            matching_item = next((i for i in variant_items if str(i['MALZEME_KODU']) == str(row_material_code)), None)
#            
#            if not matching_item: continue
#
#            selected_colors = matching_item['SEÇİLİ_RENKLER']
#            selected_sizes = matching_item['SEÇİLİ_BEDENLER']
#            quantity_str = str(matching_item['MİKTAR']).replace('.', ',')
#
#            for col_info in parsed_columns_info:
#                # Beden formatı ve eşleşme kontrolü (Regex vb.)
#                col_size = col_info['size']
#                cs = col_size.lower().strip()
#                match_range_yas = re.match(r'(\d+)\s*-\s*(\d+)\s*yaş', cs)
#                if match_range_yas:
#                    col_size = f"{match_range_yas.group(1)}y-{match_range_yas.group(2)}y"
#
#                should_fill = False
#                cur_is_all_colors = (sorted(selected_colors) == sorted(available_colors) or not selected_colors)
#                cur_is_all_sizes = (sorted(selected_sizes) == sorted(available_sizes) or not selected_sizes)
#
#                if col_info['color'] in selected_colors and cur_is_all_sizes: should_fill = True
#                elif cur_is_all_colors and col_size in selected_sizes: should_fill = True
#                elif col_info['color'] in selected_colors and col_size in selected_sizes: should_fill = True
#                elif cur_is_all_colors and cur_is_all_sizes: should_fill = True
#
#                if should_fill:
#                    afs_alv_grid.modifyCell(row_idx, col_info['col_id'], quantity_str)
#                    afs_alv_grid.currentCellColumn = col_info['col_id']
#                    afs_alv_grid.triggerModified()
        # 4. VERİ GİRİŞİ (Filtrelenmiş Grid Üzerinde)
        for row_idx in range(afs_alv_grid.RowCount):
            row_material_code = afs_alv_grid.GetCellValue(row_idx, ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE)

            #logger.info(f"[{row_idx}/{afs_alv_grid.RowCount - 1}] Satır işleniyor. Malzeme Kodu: {row_material_code}")

            matching_item = next((i for i in variant_items if str(i['MALZEME_KODU']) == str(row_material_code)), None)

            if not matching_item:
                logger.info(f"  Malzeme kodu '{row_material_code}' için eşleşen bir öğe bulunamadı. Bu satır atlanıyor.")
                continue
            
            logger.info(f"  Eşleşen öğe bulundu: {matching_item['MALZEME_KODU']}")

            selected_colors = matching_item['SEÇİLİ_RENKLER']
            selected_sizes = matching_item['SEÇİLİ_BEDENLER']
            quantity_str = str(matching_item['MİKTAR']).replace('.', ',')

            #logger.info(f"  Seçili Renkler: {selected_colors}, Seçili Bedenler: {selected_sizes}, Miktar: {quantity_str}")

            for col_info in parsed_columns_info:
                col_id = col_info['col_id']
                col_color = col_info['color']
                original_col_size = col_info['size'] # Regex öncesi boyutu loglamak için

                #logger.info(f"    Sütun işleniyor: ID={col_id}, Renk='{col_color}', Orijinal Beden='{original_col_size}'")

                # Beden formatı ve eşleşme kontrolü (Regex vb.)
                col_size = original_col_size.lower().strip()
                match_range_yas = re.match(r'(\d+)\s*-\s*(\d+)\s*yaş', col_size)
                if match_range_yas:
                    col_size = f"{match_range_yas.group(1)}y-{match_range_yas.group(2)}y"
                #    logger.info(f"    Beden regex ile dönüştürüldü: '{original_col_size}' -> '{col_size}'")
                #else:
                #    logger.info(f"    Beden regex ile dönüştürülmedi: '{col_size}'")


                should_fill = False

                # Bu kısımda available_colors ve available_sizes değişkenlerinin tanımlı olduğunu varsayıyoruz.
                # Eğer tanımlı değillerse, bu loglar hata verecektir.
                cur_is_all_colors = (sorted(selected_colors) == sorted(available_colors) or not selected_colors)
                cur_is_all_sizes = (sorted(selected_sizes) == sorted(available_sizes) or not selected_sizes)

                #logger.info(f"    Hesaplanan 'cur_is_all_colors': {cur_is_all_colors} (Selected: {selected_colors}, Available: {available_colors})")
                #logger.info(f"    Hesaplanan 'cur_is_all_sizes': {cur_is_all_sizes} (Selected: {selected_sizes}, Available: {available_sizes})")

                # Karar verme mantığı
                if col_color in selected_colors and cur_is_all_sizes:
                    should_fill = True
                    logger.info(f"    Karar: (Renk eşleşti '{col_color}', tüm bedenler seçili)")
                elif cur_is_all_colors and col_size in selected_sizes:
                    should_fill = True
                    logger.info(f"    Karar: (Tüm renkler seçili, beden eşleşti '{col_size}')")
                elif col_color in selected_colors and col_size in selected_sizes:
                    should_fill = True
                    logger.info(f"    Karar: (Renk eşleşti '{col_color}', beden eşleşti '{col_size}')")
                elif cur_is_all_colors and cur_is_all_sizes:
                    should_fill = True
                    logger.info(f"    Karar:  (Tüm renkler ve tüm bedenler seçili)")
                #else:
                #    logger.info(f"    Karar: should_fill=False (Hiçbir koşul sağlanmadı)")

                if should_fill:
                    #logger.info(f"      Hücre dolduruluyor: Satır={row_idx}, Sütun={col_id}, Miktar='{quantity_str}'")
                    afs_alv_grid.modifyCell(row_idx, col_id, quantity_str)
                    afs_alv_grid.currentCellColumn = col_id
                    afs_alv_grid.triggerModified()
                    #logger.info(f"      Hücre '{row_idx},{col_id}' için 'triggerModified' çağrıldı.")
                #else:
                #    logger.info(f"      Hücre '{row_idx},{col_id}' doldurulmadı.")

        # 5. KAYDET VE ÇIK
        session.findById("wnd[1]/tbar[0]/btn[13]").press()
        time.sleep(0.5)
        return True

    except Exception as e:
        logger.exception(f"AFS pop-up hatası: {e}")
        return False
    
def zmm0020_set_bom_afs_datav1(session, processed_bom_data, available_colors, available_sizes, afs_column_metadata_from_prod_versions):
    """
    ZMM0020 ekranında, eklenmiş BOM kalemleri için AFS (Allocation Field Selection) verilerini girer.

    Args:
        session: SAP GUI Scripting session objesi.
        processed_bom_data (list): Excel'den okunan ve işlenecek BOM verileri.
        available_colors (list): Excel'i oluştururken kullanılan mevcut renk kodları listesi.
        available_sizes (list): Excel'i oluştururken kullanılan mevcut beden kodları listesi.
    Returns:
        bool: Tüm AFS girişleri başarılı ise True, aksi takdirde False.
    """
    try:
        logger.info("ZMM0020: AFS verileri giriş süreci başlatılıyor.")
        
        # Ana BOM ALV gridini bul
        alv_grid_main_bom = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB5/ssubSUB5:ZPP_001_P_MDC:0150/cntlCONT_SCRN_0150_ALV_01/shellcont/shell")
        time.sleep(0.2)

        # "COMPONENT" sütununu seç (görsel olarak)
        #alv_grid_main_bom.selectColumn(ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE) 
        time.sleep(0.2)
         

        for bom_item in processed_bom_data:
            full_material_code = str(bom_item['MALZEME_KODU'])
            
            main_material_code = full_material_code[:10] if len(full_material_code) >= 10 else full_material_code

            logger.info(f"AFS için ana malzeme kodu '{main_material_code}' aranıyor (tam kod: {full_material_code}).")

            found_row = -1
            for row in range(alv_grid_main_bom.RowCount):
                try:
                    cell_value = alv_grid_main_bom.GetCellValue(row, ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE)
                    if str(cell_value) == main_material_code:
                        # Eğer bu satırda birden fazla varyant olabilirse,
                        # AFS pop-up'ı içinde doğru varyantı filtreleyeceğimiz için bu satırı kullanabiliriz.
                        found_row = row
                        break
                except Exception as cell_e:
                    logger.warning(f"Ana BOM ALV grid satır {row}, sütun '{ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE}' okunurken hata: {cell_e}")
                    continue
            
            if found_row != -1:
                logger.info(f"Ana malzeme kodu '{main_material_code}' için SAP'de {found_row}. satır bulundu. AFS sütununa tıklanıyor.")
                alv_grid_main_bom.setCurrentCell(found_row, ALV_COLUMN_TECHNICAL_NAME_FOR_AFS) # AFS sütununu seç
                alv_grid_main_bom.clickCurrentCell() # AFS hücresine tıkla
                time.sleep(0.6) # Pop-up'ın açılmasını bekle

                 # AFS pop-up'ını yönetirken, toplanan metadata'yı argüman olarak geçir
                if not _handle_afs_popup(session, bom_item, available_colors, available_sizes, afs_column_metadata_from_prod_versions):
                    logger.error(f"Malzeme '{full_material_code}' için AFS pop-up'ı yönetilirken hata oluştu. Akış durduruluyor.")
                    return False
                
                # AFS pop-up'ı kapandıktan sonra ana ekranın durum çubuğunu kontrol et
                status_after_afs = read_sap_status_bar(session)
                if status_after_afs["type"] == "E":
                    logger.error(f"Malzeme '{full_material_code}' için AFS sonrası ana ekranda hata: {status_after_afs['text']}")
                    return False
                elif status_after_afs["text"]:
                    logger.info(f"Malzeme '{full_material_code}' için AFS sonrası ana ekranda mesaj: {status_after_afs['text']}")
            else:
                logger.warning(f"Malzeme kodu '{main_material_code}' (tam kod: {full_material_code}) için ana BOM gridinde satır bulunamadı. AFS girişi atlanıyor.")
        
        logger.info("Tüm BOM kalemleri için AFS verileri girişi tamamlandı.")
        return True

    except Exception as e:
        logger.exception(f"ZMM0020 AFS verileri girilirken kritik hata: {e}")
        return False

def zmm0020_set_bom_afs_data(session, final_grouped_bom, available_colors, available_sizes, afs_column_metadata_from_prod_versions):
    """
    ZMM0020 ekranında, gruplanmış BOM kalemleri için AFS verilerini girer.
    
    Args:
        final_grouped_bom (dict): Operasyon bazlı ve 10 haneli kodlara göre gruplanmış veri.
                                  { "Operasyon": [ {"ANA_MALZEME_KODU": "...", "ITEMS": [...]}, ... ] }
    """
    try:
        logger.info("ZMM0020: AFS verileri giriş süreci (Gruplanmış Yapı) başlatılıyor.")
        
        alv_grid_main_bom = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB5/ssubSUB5:ZPP_001_P_MDC:0150/cntlCONT_SCRN_0150_ALV_01/shellcont/shell")
        time.sleep(0.2)

        # 1. Operasyonlar üzerinden dön
        for excel_operation, groups_for_operation in final_grouped_bom.items():
            logger.info(f"'{excel_operation}' operasyonu altındaki malzemeler için AFS süreci işleniyor.")

            # 2. Her bir 10 haneli ana malzeme grubu üzerinden dön
            for group_data in groups_for_operation:
                main_material_code = group_data['ANA_MALZEME_KODU']
                variant_items = group_data['ITEMS'] # Bu grubun altındaki tüm renk/beden varyantları

                logger.info(f"AFS için ana malzeme kodu '{main_material_code}' aranıyor. (Grupta {len(variant_items)} varyant var)")

                found_row = -1
                # SAP gridinde bu ana kodu bul
                for row in range(alv_grid_main_bom.RowCount):
                    try:
                        cell_value = alv_grid_main_bom.GetCellValue(row, ALV_COLUMN_TECHNICAL_NAME_FOR_MATERIAL_CODE)
                        if str(cell_value) == main_material_code:
                            found_row = row
                            break
                    except Exception as cell_e:
                        continue
                
                if found_row != -1:
                    logger.info(f"Ana malzeme '{main_material_code}' için SAP'de {found_row}. satır bulundu. AFS'ye giriliyor.")
                    alv_grid_main_bom.setCurrentCell(found_row, ALV_COLUMN_TECHNICAL_NAME_FOR_AFS)
                    alv_grid_main_bom.clickCurrentCell()
                    time.sleep(0.6)

                    # YENİ: Tek bir item yerine, o ana koda ait TÜM varyant listesini (variant_items) gönderiyoruz.
                    # _handle_afs_popup fonksiyonunun bu listeyi karşılayacak şekilde güncellenmesi gerekecek.
                    if not _handle_afs_popup(session, variant_items, available_colors, available_sizes, afs_column_metadata_from_prod_versions):
                        logger.error(f"Ana malzeme '{main_material_code}' AFS pop-up yönetimi başarısız.")
                        return False
                    
                    status_after_afs = read_sap_status_bar(session)
                    if status_after_afs["type"] == "E":
                        logger.error(f"AFS sonrası hata: {status_after_afs['text']}")
                        return False
                else:
                    logger.warning(f"Ana malzeme kodu '{main_material_code}' gridde bulunamadı. Atlanıyor.")
        
        logger.info("Tüm gruplar için AFS verileri girişi tamamlandı.")
        return True

    except Exception as e:
        logger.exception(f"ZMM0020 AFS verileri girilirken kritik hata: {e}")
        return False
    
        
    # --- YENİ BAĞIMSIZ FONKSİYON: Üretim Versiyonlarının Oluşturulduğundan Emin Olma ---
def zmm0020_ensure_production_versions_created(session):
    """
    Üretim versiyonlarını kontrol eder. 
    İlerleme (boş hücre sayısında azalma) olduğu sürece deneme hakkı harcamaz.
    Sadece ilerleme durduğunda deneme sayısını artırır (Max: 5 deneme).
    """
    logger.info("Üretim versiyonları kontrol süreci başlatıldı (Dinamik İlerleme Modu)...")
   
    try:
        session.findById("wnd[0]").maximize()
        handle_sap_popups(session)
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB6").select()
        time.sleep(0.5)
        handle_sap_popups(session)
        max_failed_attempts = 3
        failed_attempts = 0
        last_empty_count = float('inf') # Başlangıçta sonsuz kabul ediyoruz

        while failed_attempts < max_failed_attempts:
            # 1. ALV Grid'i bul ve mevcut boş hücreleri say
            alv_grid = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB6/ssubSUB6:ZPP_001_P_MDC:0160/cntlCONT_SCRN_0160_ALV_01/shellcont/shell")
            
            current_empty_count = 0
            for row_idx in range(alv_grid.RowCount):
                pv_x = str(alv_grid.GetCellValue(row_idx, "PV_X")).strip().upper()
                bom_x = str(alv_grid.GetCellValue(row_idx, "BOM_X")).strip().upper()
                if pv_x != "X" or bom_x != "X":
                    current_empty_count += 1

            # 2. Başarı Kontrolü
            if current_empty_count == 0:
                logger.info("Tüm üretim versiyonları ('X') başarıyla tamamlandı. ✅")
                return True

            # 3. İlerleme Kontrolü (Attempt Mantığı)
            if current_empty_count < last_empty_count:
                # İlerleme var! Boş hücre sayısı azaldı.
                logger.info(f"İlerleme tespit edildi: {last_empty_count} -> {current_empty_count} boş hücre kaldı. Deneme hakkı harcanmadı.")
                # failed_attempts artırılmıyor.
            else:
                # İlerleme yok! Boş hücre sayısı değişmedi.
                failed_attempts += 1
                logger.warning(f"İlerleme yok! Boş hücre sayısı hala {current_empty_count}. Deneme: {failed_attempts}/{max_failed_attempts}")

            last_empty_count = current_empty_count

            # 4. İşlemi Tetikle (CREATE_PV)
            logger.info("'Üretim Versiyonu Oluştur' butonuna basılıyor...")
            alv_grid.pressToolbarButton("CREATE_PV")
            time.sleep(0.5)
            
            # Pop-up onayı
            try:
                session.findById("wnd[1]/tbar[0]/btn[0]").press() # Enter
                time.sleep(0.5)
                
                status = read_sap_status_bar(session)
                if status["type"] == "E":
                    logger.error(f"SAP Hatası: {status['text']}")
                    return False
            except Exception:
                # Pop-up gelmemiş olabilir, devam et
                pass

        logger.error(f"3 başarısız deneme sonunda hala {last_empty_count} adet boş hücre var.")
        return False

    except Exception as e:
        logger.error(f"Üretim versiyonu kontrolü sırasında kritik hata: {e}")
        return False 
    
    # --- YARDIMCI FONKSİYON: Maliyetlendirme İşlemlerini Yönetme ---
def _process_costing_action(session, alv_grid_costing, button_id, check_column_id, max_attempts=3):
    """
    Maliyetlendirme işlemi için dinamik yürütücü.
    İlerleme (X olmayan satır sayısında azalma) olduğu sürece deneme hakkı harcamaz.
    Sadece ilerleme durduğunda deneme sayısını artırır (Max: 3 deneme).
    """
    logger.info(f"Maliyetlendirme işlemi başlatılıyor: Buton '{button_id}', Sütun '{check_column_id}'")

    failed_attempts = 0
    last_missing_count = float('inf')
    
    # Grid nesnesini tazelemek için kullanılacak ID yolu
    grid_id = "wnd[0]/usr/tabsTAB_CONTROL/tabpTAB7/ssubSUB7:ZPP_001_P_MDC:0170/cntlCONT_SCRN_0170_ALV_01/shellcont/shell"

    while failed_attempts < max_attempts:
        # 1. 'X' olmayan satırları tespit et
        rows_to_process = []
        for row_idx in range(alv_grid_costing.RowCount):
            try:
                cell_value = str(alv_grid_costing.GetCellValue(row_idx, check_column_id)).strip().upper()
                if cell_value != "X":
                    rows_to_process.append(row_idx)
            except Exception:
                rows_to_process.append(row_idx) # Okunamazsa da işleme al

        current_missing_count = len(rows_to_process)

        # 2. Başarı Kontrolü
        if current_missing_count == 0:
            logger.info(f"Tüm satırlarda '{check_column_id}' sütunu 'X' oldu. İşlem başarılı. ✅")
            return True

        # 3. İlerleme ve Attempt Mantığı
        if current_missing_count < last_missing_count:
            logger.info(f"İlerleme var: {last_missing_count} -> {current_missing_count} satır kaldı. Deneme hakkı korunuyor.")
            # failed_attempts artırılmıyor
        else:
            failed_attempts += 1
            logger.warning(f"İlerleme yok! Hala {current_missing_count} satır eksik. Deneme: {failed_attempts}/{max_attempts}")

        last_missing_count = current_missing_count

        # 4. İşlemi Uygula
        logger.info(f"Eksik {current_missing_count} satır seçiliyor ve '{button_id}' butonuna basılıyor.")
        
        # Satırları seç ve butona bas
        alv_grid_costing.selectedRows = ",".join(map(str, rows_to_process))
        time.sleep(0.5)
        alv_grid_costing.pressToolbarButton(button_id)
        time.sleep(1)

        # 5. Pop-up Onayı
        try:
            if session.Children.Count > 1:
                popup = session.findById("wnd[1]")
                logger.info(f"Pop-up onaylanıyor: {popup.Text}")
                popup.sendVKey(0) # Enter
                time.sleep(2)
                
                status = read_sap_status_bar(session)
                if status["type"] == "E":
                    logger.error(f"SAP Hata Mesajı: {status['text']}")
                    return False
        except Exception:
            pass # Pop-up yoksa devam et

        # 6. Grid Nesnesini Yenile (Stale object hatasını önlemek için)
        time.sleep(1)
        alv_grid_costing = session.findById(grid_id)

    logger.error(f"{max_attempts} başarısız deneme sonunda '{button_id}' işlemi tamamlanamadı.")
    return False

# --- YENİ BAĞIMSIZ FONKSİYON: Maliyetlendirme Sekmesini Yönetme ---
def zmm0020_handle_costing_tab(session):
    """
    ZMM0020 ekranında "Maliyetlendirme" sekmesindeki (TAB7) maliyetlendirme adımlarını yönetir:
    1. Detay butonuna basar ve ALV'yi genişletir.
    2. Malzeme Maliyetini Tahmin Et (ESTIMATE_MATERIAL_COST) işlemini "MLYT_HSP_X" sütununu kontrol ederek yapar.
    3. Maliyetlendirmeyi İşaretle (MARK_COST_ESTIMATE) işlemini "ISARETLEME_X" sütununu kontrol ederek yapar.
    4. Maliyetlendirmeyi Serbest Bırak (RELEASE_COST_ESTIMATE) işlemini "ONAYLAMA_X" sütununu kontrol ederek yapar.
    Her adımda 'X' olmayan satırları seçip işlemi tekrarlar (maksimum 2 kez).
    """
    logger.info("ZMM0020: Maliyetlendirme sekmesi işlemleri başlatılıyor.")
    

    try:
        session.findById("wnd[0]").maximize()
        

        # "Maliyetlendirme" sekmesine git
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB7").select()
        time.sleep(0.5) # Sekmenin yüklenmesini bekle

        # Maliyetlendirme ALV gridini bul
        alv_grid_costing = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB7/ssubSUB7:ZPP_001_P_MDC:0170/cntlCONT_SCRN_0170_ALV_01/shellcont/shell")
        time.sleep(0.5) # ALV gridin yüklenmesini bekle

        # 1. "DETAY" butonuna bas ve ALV'yi genişlet
        logger.info("Maliyetlendirme ALV gridinde 'DETAY' butonuna basılıyor.")
        alv_grid_costing.pressToolbarButton("DETAY")
        time.sleep(0.5) # ALV'nin genişlemesini bekle
        alv_grid_costing = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB7/ssubSUB7:ZPP_001_P_MDC:0170/cntlCONT_SCRN_0170_ALV_01/shellcont/shell") # ALV gridi yenile
        time.sleep(0.5)

        # 2. Malzeme Maliyetini Tahmin Et (ESTIMATE_MATERIAL_COST)
        if not _process_costing_action(session, alv_grid_costing, "ESTIMATE_MATERIAL_COST", "MLYT_HSP_X", max_attempts=2):
            logger.error("Malzeme Maliyeti Tahmin Etme işlemi başarısız oldu.")
            

        # 3. Maliyetlendirmeyi İşaretle (MARK_COST_ESTIMATE)
        if not _process_costing_action(session, alv_grid_costing, "MARK_COST_ESTIMATE", "ISARETLEME_X", max_attempts=2):
            logger.error("Maliyetlendirmeyi İşaretle işlemi başarısız oldu.")
            

        # 4. Maliyetlendirmeyi Serbest Bırak (RELEASE_COST_ESTIMATE)
        if not _process_costing_action(session, alv_grid_costing, "RELEASE_COST_ESTIMATE", "ONAYLAMA_X", max_attempts=2):
            logger.error("Maliyetlendirmeyi Serbest Bırak işlemi başarısız oldu.")
            
        
        logger.info("Tüm Maliyetlendirme sekmesi işlemleri başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.exception(f"ZMM0020 Maliyetlendirme sekmesi yönetilirken kritik hata: {e}")
        return False

def _calculate_piece_count_for_set_order(childrens) -> int:
    """
    Verilen kurallara göre set siparişinin toplam parça sayısını hesaplar.
    
    Kurallar:
    1. Eğer sadece bir çocuk varsa (len(childrens) == 1):
       Parça sayısı = o tek çocuğun componentColor listesinin uzunluğu.
    2. Eğer birden fazla çocuk varsa (len(childrens) > 1):
       a. Tüm çocukların componentColor listelerinin uzunlukları AYNI ise:
          Parça sayısı = çocuk sayısı (yani childrens listesinin uzunluğu).
       b. Çocukların componentColor listelerinin uzunlukları FARKLI ise:
          Parça sayısı = tüm çocukların componentColor listelerinin toplam uzunluğu.
    """
    if not childrens:
        logger.warning("Parça sayısı hesaplamak için çocuk (childrens) bilgisi bulunamadı, 0 döndürülüyor.")
        return 0

    if len(childrens) == 1:
        # Normal Şart 2: Tek plm kodunda birden fazla farklı renk olması.
        # Parça sayısı = o tek çocuğun componentColor listesinin uzunluğu
        piece_count = len(childrens[0].get("componentColor", []))
        logger.info(f"Set siparişinde tek çocuk var. Hesaplanan parça sayısı (Normal Şart 2): {piece_count}")
        return piece_count
    else:
        # Birden fazla çocuk var
        
        # componentColor listelerinin boş olup olmadığını kontrol edelim
        if any(not child.get("componentColor") for child in childrens):
             logger.warning("Bazı çocukların 'componentColor' listesi boş veya eksik. Bu durum parça sayısı hesaplamasını etkileyebilir.")
             # İsteğe bağlı: Burada bir hata fırlatabilir veya boş listeyi 0 renk olarak saymaya devam edebilirsiniz.
             # Şimdilik, boş listeyi 0 renk olarak saymaya devam edeceğiz.

        first_child_color_count = len(childrens[0].get("componentColor", []))
        
        # Tüm çocukların renk sayıları aynı mı kontrol et
        all_same_color_count = all(
            len(child.get("componentColor", [])) == first_child_color_count 
            for child in childrens
        )

        if all_same_color_count:
            # Normal Şart 1: Her çocuk için (farklı plm kodunda) aynı sayıda renk olması.
            # Parça sayısı = çocuk sayısı (yani PLM kodu sayısı)
            piece_count = len(childrens)
            logger.info(f"Set siparişinde birden fazla çocuk var ve hepsi aynı sayıda renge sahip. Hesaplanan parça sayısı (Normal Şart 1): {piece_count}")
            return piece_count
        else:
            # Diğer koşullar: Çocukların renk sayıları birbirinden farklıysa
            # Her bir renk kodu bir parça olarak sayılmalı. Toplam renk sayısı.
            total_colors = sum(len(child.get("componentColor", [])) for child in childrens)
            logger.info(f"Set siparişinde birden fazla çocuk var ve farklı sayıda renge sahipler. Hesaplanan parça sayısı (Diğer Koşullar): {total_colors}")
            return total_colors


def handle_set_order_olcu_donusumu(session, main_order_data):
    """
    Set siparişleri için ZMM0020 ekranındaki "Ölçü Dönüşümü" adımını gerçekleştirir.
    Parça sayısını main_order_data'daki childrens bilgisine göre dinamik olarak hesaplar.
    Bu adım tüm set siparişi için bir kez yapılır.
    """
    logger.info("ZMM0020: Set siparişi için 'Ölçü Dönüşümü' adımı başlatılıyor.")
    style_name = main_order_data.get("styleName")
    plm_id = main_order_data.get("plm_code")

    childrens = main_order_data.get("childrens", [])
    if not childrens:
        logger.error("Set siparişi için çocuk (childrens) bilgisi bulunamadı. Ölçü Dönüşümü yapılamıyor.")
        raise ValueError("Set siparişi için 'childrens' bilgisi eksik.")
    
    file_name = f"{style_name}_BOM_Template_{plm_id}.xlsx"
    output_directory= ConfigManager.OUTPUT_EXCEL_DIR
    input_path = os.path.join(output_directory, file_name)
    if not os.path.exists(input_path):
        raise Exception(f"BOM şablon dosyası bulunamadı: {input_path}. Lütfen dosyanın mevcut olduğundan emin olun.")            
    variant_data = read_variant_values_from_excel(input_path)
    
    # variant_data'nın içindeki değerleri (values) listeye çevir ve ilkini ([0]) al
    first_color_data = list(variant_data.values())[0]

    # Bu ilk elemanın içindeki TOTAL_PIECES değerini oku
    total_piece = first_color_data["TOTAL_PIECES"]
    
    #pieces = _calculate_piece_count_for_set_order(childrens)
    logger.info(f"ZMM0020: 'Ölçü Dönüşümü' için hesaplanan parça sayısı: {total_piece}")

    try:
        # 1. "Ölçü Dönüşümü" butonuna bas
        session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB2/ssubSUB2:ZPP_001_P_MDC:0120/btnBTN_OLCU_DONUSUMU").press()
        logger.info("ZMM0020: 'Ölçü Dönüşümü' butonuna basıldı.")

        # 2. Pop-up penceresinde "Satır Ekle" butonuna bas
        # wnd[1] yeni açılan pop-up penceresidir.
        shell = session.findById("wnd[1]/usr/cntlCONT_SCRN_0120_ALV_01/shellcont/shell")
        shell.pressToolbarButton("ROW_ADD")
        logger.info("ZMM0020: Ölçü Dönüşümü pop-up'ında 'Satır Ekle' butonuna basıldı.")

        # 3. UMREN sütununu doldur ("parça sayısı")
        shell.modifyCell(0, "UMREN", str(total_piece)) # parca_sayisi int, SAP string bekler
        logger.info(f"ZMM0020: UMREN hücresine '{total_piece}' değeri girildi.")
        
        # 4. MEINH sütununu doldur (TR: ADT / EN: PC)
        unit_symbol = get_unit_symbol()
        shell.currentCellColumn = "MEINH"
        shell.triggerModified() # Hücre değişimi sonrası tetikleme
        shell.modifyCell(0, "MEINH", unit_symbol)
        logger.info(f"ZMM0020: MEINH hücresine '{unit_symbol}' değeri girildi.")

        # 5. UMREZ sütununu doldur ("1")
        shell.currentCellColumn = "UMREZ"
        shell.triggerModified() # Hücre değişimi sonrası tetikleme
        shell.modifyCell(0, "UMREZ", "1") # Sabit değer 1
        logger.info("ZMM0020: UMREZ hücresine '1' değeri girildi.")

        # 6. Enter tuşuna bas (muhtemelen girişi onaylamak için)
        shell.triggerModified() # Hücre değişimi sonrası tetikleme
        session.findById("wnd[1]").sendVKey(0) # VKey 0 genellikle Enter tuşudur.
        logger.info("ZMM0020: Ölçü Dönüşümü pop-up'ında Enter tuşuna basıldı.")
        
        # 7. Kaydet butonuna bas (wnd[1]/tbar[0]/btn[13] genellikle kaydet butonudur)
        session.findById("wnd[1]/tbar[0]/btn[13]").press()
        logger.info("ZMM0020: Ölçü Dönüşümü pop-up'ında Kaydet butonuna basıldı.")
        time.sleep(0.2)
        session.findById("wnd[0]/tbar[0]/btn[11]").press()
        
        logger.info("ZMM0020: 'Ölçü Dönüşümü' adımı başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.error(f"ZMM0020: 'Ölçü Dönüşümü' adımı sırasında kritik hata oluştu: {e}", exc_info=True)
        raise # Hatayı yukarıya fırlat ki workflow durdurulsun  

def get_color_variant_data_from_zmm0020_tab3(session) -> list:
    """
    ZMM0020 ekranında TABP3 sekmesindeki tablodan dolu olan satırların
    RENK_KODU ve VARYANT_KODU bilgilerini çeker.

    Args:
        session (Any): SAP GUI Scripting session objesi.

    Returns:
        List[Dict[str, str]]: Her bir sözlükte 'RENK_KODU' ve 'VARYANT_KODU'
                               anahtarlarını içeren dolu satırların listesi.
                               Hata durumunda veya veri bulunamazsa boş liste döner.
    """
    logger.info("ZMM0020: TABP3 sekmesinden renk ve varyant kodu verileri çekiliyor.")
    extracted_data = []

    try:
        # 1. TABP3 sekmesine geç
        tab_control = session.findById("wnd[0]/usr/tabsTAB_CONTROL/tabpTAB3")
        tab_control.select() # 'tabpTAB3' ID'si yerine 'TAB3' sekme anahtarını kullanırız.
        logger.info("ZMM0020: 'TAB3' sekmesine geçildi.")
        time.sleep(1) # Ekranın yüklenmesini bekle

        # 2. Tabloyu bul
        # Belirtilen ID'ye göre bir GuiTableControl veya GuiShell olmalı.
        # Genellikle 'tbl' ile başlayanlar GuiTableControl'dür.
        table_path = "wnd[0]/usr/tabsTAB_CONTROL/tabpTAB3/ssubSUB3:ZPP_001_P_MDC:0130/tblZPP_001_P_MDCTC_0130_TBL_01"
        sap_table = session.findById(table_path)
        logger.info(f"ZMM0020: Tablo '{table_path}' bulundu.")
        logger.info(f"ZMM0020: SAP Tablo objesinin tipi: {type(sap_table)}")
        
        # Tablodaki satır sayısını al
        row_count = sap_table.RowCount
        logger.info(f"ZMM0020: Tabloda {row_count} satır bulundu.")

        # Renk ve varyant kodu sütunlarının indexleri
        RENK_KODU_SCREEN_COL_IDX = 1 
        VARYANT_KODU_SCREEN_COL_IDX = 3 

        # Her bir hücreye erişmek için kullanılan alan adları
        RENK_KODU_FIELD_NAME = "txtGS_MDC_SCRN_0130_TBL_01-RENK_KODU"
        VARYANT_KODU_FIELD_NAME = "txtGS_MDC_SCRN_0130_TBL_01-VARYANT_KODU"


        # Tabloyu gez ve dolu satırları al
        for i in range(row_count):
            try:
                # Her bir hücre için tam SAP GUI Scripting ID'sini oluştur
                full_renk_kodu_id = f"wnd[0]/usr/tabsTAB_CONTROL/tabpTAB3/ssubSUB3:ZPP_001_P_MDC:0130/tblZPP_001_P_MDCTC_0130_TBL_01/txtGS_MDC_SCRN_0130_TBL_01-RENK_KODU[0,{i}]"
                full_varyant_kodu_id = f"wnd[0]/usr/tabsTAB_CONTROL/tabpTAB3/ssubSUB3:ZPP_001_P_MDC:0130/tblZPP_001_P_MDCTC_0130_TBL_01/txtGS_MDC_SCRN_0130_TBL_01-VARYANT_KODU[3,{i}]"

                # `session.findById` ile doğrudan hücre kontrolünü bul ve metnini çek
                # Eğer satır boşsa veya kontrol görünür değilse, `findById` hata fırlatabilir.
                varyant_kodu_obj = session.findById(full_varyant_kodu_id)
                renk_kodu_obj = session.findById(full_renk_kodu_id)

                renk_kodu = renk_kodu_obj.Text
                varyant_kodu = varyant_kodu_obj.Text
                
                # Sadece dolu olan satırları al (renk kodu boş değilse)
                if renk_kodu and str(renk_kodu).strip() != "" and "_" not in renk_kodu and "_" not in varyant_kodu:
                    extracted_data.append({
                        "RENK_KODU": str(renk_kodu).strip(),
                        "VARYANT_KODU": str(varyant_kodu).strip() if varyant_kodu else ""
                    })
                    logger.debug(f"ZMM0020: Satır {i} -> Renk: '{renk_kodu}', Varyant: '{varyant_kodu}' çekildi.")
            except Exception as cell_err:
                # `findById` bir kontrolü bulamazsa veya kontrolün `Text` özelliği yoksa bu hatayı yakalarız.
                # Bu durum genellikle tablonun sonundaki boş veya görünür olmayan satırlar için normaldir.
                logger.debug(f"ZMM0020: Satır {i} okunurken hata oluştu (muhtemelen boş/görünür olmayan satır veya kontrol bulunamadı): {cell_err}. Bu satır atlanıyor.")
                continue # Hata olsa bile diğer satırlara devam et
        if not extracted_data:
            logger.warning("ZMM0020: TABP3 sekmesindeki tablodan hiçbir dolu renk/varyant kodu verisi çekilemedi.")
            
        logger.info(f"ZMM0020: TABP3 sekmesinden {len(extracted_data)} adet renk/varyant kodu verisi çekildi.")
        return extracted_data

    except Exception as e:
        logger.error(f"ZMM0020: TABP3 sekmesinden renk/varyant kodu verisi çekilirken kritik hata oluştu: {e}", exc_info=True)
        return [] # Hata durumunda boş liste dön  

def fetch_material_code_from_zmm0021(session, data):
    """ZMM0021 ekranına giderek PLM kodu ile Malzeme Kodunu sorgular."""
    try:
        
        plm_code = data.get('plm_code')
        if not plm_code:
            logger.error("ZMM0021: JSON verisinde 'plm_code' bulunamadı.")
            return False
        logger.info(f"ZMM0021: {plm_code} için malzeme kodu sorgulanıyor...")
        session.startTransaction("ZMM0021")
        
        # Model Kodu alanına odaklan ve F4 (Arama) yap
        model_field = session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-MODEL_KODU")
        model_field.text = ""
        model_field.setFocus()
        session.findById("wnd[0]").sendVKey(4) # F4
        
        # Arama yardımında 'PLM No' alanını bulmak için (btn[17] - Çoklu arama kriteri)
        session.findById("wnd[1]/tbar[0]/btn[17]").press()
        
        # PLM Kodunu ilgili alana yaz (Senin verdiğin ID)
        # Not: Bu ID SAP versiyonuna göre değişebileceği için try-except içinde olması güvenlidir
        plm_search_field = session.findById("wnd[1]/usr/tabsG_SELONETABSTRIP/tabpTAB001/ssubSUBSCR_PRESEL:SAPLSDH4:0220/sub:SAPLSDH4:0220/txtG_SELFLD_TAB-LOW[0,24]")
        plm_search_field.text = str(plm_code)
        session.findById("wnd[1]").sendVKey(0) # Enter
        
        # Sonuç listesinden ilk satırı seç (lbl[20,3])
        try:
            result_label = session.findById("wnd[1]/usr/lbl[20,3]")
            result_label.setFocus()
            session.findById("wnd[1]").sendVKey(2) # F2 (Seç ve Kapat)
            
            # Ana ekrana düşen malzeme kodunu oku
            found_material_code = session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-MODEL_KODU").text
            logger.info(f"ZMM0021: {plm_code} -> {found_material_code} bulundu.")
            return found_material_code.strip()
        except:
            logger.warning(f"ZMM0021: {plm_code} için sonuç bulunamadı.")
            return None

    except Exception as e:
        logger.error(f"ZMM0021 sorgulama hatası: {e}")
        return None
def fetch_main_material_code_from_zmm0020(session, plm_code):
    """Ana PLM için ZMM0020 ekranından malzeme kodunu sorgular."""
    try:
        logger.info(f"ZMM0020: Ana PLM {plm_code} sorgulanıyor...")
        session.startTransaction("ZMM0020")
        
        # PLM Kodunu gir ve Enter'a bas
        plm_field = session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-PLMKODU")
        plm_field.text = str(plm_code)
        session.findById("wnd[0]").sendVKey(0) # Enter
        
        time.sleep(1.5) # SAP'nin veriyi getirmesi için bekle
        
        # Model Kodu alanındaki bilgiyi oku
        model_code = session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-MODEL_KODU").text
        
        if model_code and model_code.strip():
            logger.info(f"ZMM0020: Ana PLM {plm_code} -> {model_code} bulundu.")
            return model_code.strip()
        else:
            logger.warning(f"ZMM0020: Ana PLM {plm_code} için malzeme kodu boş döndü.")
            return None

    except Exception as e:
        logger.error(f"ZMM0020 Ana PLM sorgulama hatası: {e}")
        return None
    
def ensure_zmm_session_active(session, data, is_step_1_active=True, cache_file_path=None, target_child=None):
    """
    Robotun ZMM0020 veya ZMM0021 ekranında doğru PLM/Model ile 
    açık olduğunu garanti eder.
    """
    current_tx = session.Info.Transaction # O anki T-Code (ZMM0020 veya ZMM0021)
    model_code = data.get('sap_material_code')    
    werks = data['sale_group'] if 'sale_group' in data else "2000" # Varsayılan değer
    
    # 1. ADIM: Zaten doğru ekranda ve doğru modelde miyiz?
    if not is_step_1_active:
        if current_tx in ["ZMM0021", "ZMM0020"]:
            # Ekrandaki kodu oku
            model_field = session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-MODEL_KODU", False)
            if model_field and model_code and model_field.text == model_code:
                logger.info(f"ZMM: Zaten {model_code} modelindeyiz. İşlemlere devam ediliyor.")
                return True

    # 2. ADIM: S1 (Yaratma) Modu
    if is_step_1_active:
        logger.info("S1 Seçili: ZMM0020 ekranına giriş yapılıyor.")
        return zmm0020_ilk_ekran_giris(session, data)
    
    # JSON'da model kodu var mı bak (3010... veya sap_material_code)
    logger.info(f"ZMM0021'e giriş için model kodu: {model_code}, werks: {werks}")
    
    if model_code:
        # ZMM0021'e direkt kodla gir
        session.startTransaction("ZMM0021")
        session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-MODEL_KODU").text = model_code     
        time.sleep(0.2) # SAP'nin modeli getirmesi için bekle
        session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-WERKS").text = werks
        session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-MODEL_KODU").setFocus()
        
        session.findById("wnd[0]").sendVKey(0) # Enter
        return True
    else:
        # KOD RAM'DE YOK: F4 fonksiyonunu çağır (Bu fonksiyon 3010... döner)
        logger.info("Model kodu RAM'de yok, F4 ile sorgulanıyor...")
        found_code = fetch_material_code_from_zmm0021(session, data)
        
        if found_code: # Eğer None değilse, yani kod bulunduysa
            # RAM ve JSON Güncelleme
            if data.get('orderType') == "single_from_set" and target_child is not None:
                # Set çocuğu için güncelleme
                target_child["sap_material_code"] = found_code
                childrens = data.get("childrens", [])
                update_json_cache(cache_file_path, "childrens", childrens)
                logger.info(f"Set Çocuğu JSON Güncellendi: {found_code}")
            else:
                # Single ürün için güncelleme
                data['sap_material_code'] = found_code
                update_json_cache(cache_file_path, "sap_material_code", found_code)
                logger.info(f"Single Ürün JSON Güncellendi: {found_code}")
            
            # Bulunan kodla içeri gir (F4 fonksiyonu zaten ZMM0021'de bırakıyor)
            session.findById("wnd[0]/usr/ctxtGS_MDC_SCRN_0100-WERKS").text = werks
            session.findById("wnd[0]").sendVKey(0) # Enter
            return True
            
        logger.error("Model kodu F4 ile de bulunamadı!")
        return False

# --- MODÜLER ADIM S1 ---
def zmm0020_step_1_variants(session, data, cache_file_path, target_child=None):
    """
    S1: Varyant & Model Girişi
    Model sekmesi, Beden/Renk seçimi ve Varyant Ekleme.
    """
    try:
        logger.info("--- [S1] Varyant & Model Girişi Başladı ---")
        
        # 1. Giriş Kontrolü (S1 aktif olduğu için ZMM0020'den girer)
        if not ensure_zmm_session_active(session, data, is_step_1_active=True, cache_file_path=cache_file_path):
            return False

        # 2. Model Sekmesi Giriş
        if not zmm0020_model_sekmesi_giris(session, data):
            return False

        # 3. Beden Seçimi
        if not zmm0020_beden_secimi(session, data):
            return False
        if not ensure_target_sizes_selected(session, data):
            return False

        # 4. Renk Seçimi ve Varyant Kontrol
        if not manage_color_selections(session, data):
            return False
        if not zmm0020_renk_secimi(session, data):
            return False
        if not ensure_target_colors_selected(session, data):
            return False

        # 5. Varyant Ekle Butonu
        if not press_add_variant_button(session):
            return False

        # 6. Kaydet (S1 sonunda kaydetmek şart, çünkü 3010 kodu oluşmalı)
        if not save_sap_screen(session):
            return False

        logger.info("--- [S1] Başarıyla Tamamlandı ---")
        return True

    except Exception as e:
        logger.error(f"S1 Hatası: {e}")
        return False
def zmm0020_step_2_routing(session, data, cache_file_path=None, target_child=None):
    """
    S2: İş Planı & Rota Oluşturma
    Material ve Routing yaratma butonları.
    """
    try:
        logger.info("--- [S2] İş Planı & Rota Başladı ---")

        # 1. Giriş/Ekran Kontrolü (S1 seçili değilse ZMM0021 üzerinden girer)
        # Not: Eğer S1 zaten yapıldıysa ve robot o ekrandaysa, bu fonksiyon 
        # mevcut oturumu bozmadan devam edecek şekilde ayarlanmalı.
        if not ensure_zmm_session_active(session, data, is_step_1_active=False, cache_file_path=cache_file_path, target_child=target_child):
            return False
                

        # 2. İş Planı Sekmesine Geçiş (Tab 4)
        if not zmm0020_is_plani_sekmesi_giris(session):
            return False
        

        # 3. İş Planı Adımları/Operasyonlar
        if not zmm0020_is_plani_adimlari(session, data):
            return False

        # 4. Create Material Butonu
        if not zmm0020_press_create_material_button(session):
            return False

        # 5. Create Routing Butonu
        if not zmm0020_press_create_routing_button(session):
            return False
        handle_sap_popups(session)
        # 6. Kaydet
        if not save_sap_screen(session):
            return False
        
        handle_sap_popups(session)
        logger.info("--- [S2] Başarıyla Tamamlandı ---")
        return True

    except Exception as e:
        #İŞPLANI YARAT SONRASI POP-UP
        
        logger.error(f"S2 Hatası: {e}")
        return False

def zmm0020_step_3_bom(session, data, cache_file_path=None, target_child=None):
    """
    S3: BOM (Excel) Yükleme ve AFS Verileri
    Excel şablonunu okur, SAP'ye aktarır ve AFS detaylarını girer.
    """
    try:
        logger.info("--- [S3] BOM (Excel) Yükleme Adımı Başladı ---")

        # 1. Giriş/Ekran Kontrolü (S1 seçili değilse ZMM0021 üzerinden girer)
        if not ensure_zmm_session_active(session, data, is_step_1_active=False, cache_file_path=cache_file_path, target_child=target_child):
            return False
        
        # 2. BOM Sekmesine Geçiş ve Matris Ekleme (Tab 3)
        if not zmm0020_bom_sekmesi_matris_ekle(session):
             return False

        # 3. Excel Dosya Yolu ve Kimlik Belirleme
        order_type = data.get('orderType')
        if order_type == "single_from_set":
            plm_id = data.get('main_plm_id') # Şablon ana PLM adına göredir
            child_plm_id = data.get('plm_code')
        else:
            plm_id = data.get('plm_code') 
            child_plm_id = plm_id
            
        style_name = data.get('styleName')
        if not plm_id:
            logger.error("JSON verisinde 'plm_code' bulunamadı.")
            return False

        file_name = f"{style_name}_BOM_Template_{plm_id}.xlsx"
        input_path = os.path.join(ConfigManager.OUTPUT_EXCEL_DIR, file_name)

        if not os.path.exists(input_path):
            logger.error(f"BOM şablon dosyası bulunamadı: {input_path}")
            return False

        # 4. Renk ve Beden Hazırlığı
        available_colors = list(data['order_color_code']) if 'order_color_code' in data else []
        available_sizes = [str(s) for s in data['sizes']] if 'sizes' in data else []

        # 5. AFS Sütun Metadata'sını Al (Üretim Versiyonları sekmesinden)
        afs_column_metadata = _get_afs_column_metadata_from_prod_versions_tab(session)
        if not afs_column_metadata:
            logger.error("Üretim Versiyonları sekmesinden AFS metadata'sı alınamadı.")
            return False

        # 6. Excel Verilerini SAP'ye Ekleme
        processed_bom_data = zmm0020_select_bom_operation_and_add_components(
            session, input_path, available_colors, available_sizes, afs_column_metadata, child_plm_id
        )
        
        if processed_bom_data is None:
            logger.error("Excel BOM verileri SAP'ye eklenirken hata oluştu.")
            return False
            
        data['processed_bom_data'] = processed_bom_data # Runner için sakla
        logger.info(f"{len(processed_bom_data)} adet BOM kalemi Excel'den okundu ve SAP'ye eklendi.")

        # 7. BOM AFS Verilerini (Matris) Girme
        if not zmm0020_set_bom_afs_data(session, processed_bom_data, available_colors, available_sizes, afs_column_metadata):
            logger.error("BOM AFS verilerinin SAP'ye aktarılması başarısız.")
            return False

        # 8. Kaydet
        if not save_sap_screen(session):
            return False

        logger.info("--- [S3] Başarıyla Tamamlandı ---")
        return True

    except Exception as e:
        logger.error(f"S3 Hatası: {e}")
        return False
    
def zmm0020_step_4_costing(session, data, cache_file_path=None, target_child=None):
    """
    S4: Üretim Versiyonu Kontrolü ve Maliyet Hesaplama
    Üretim versiyonlarının oluştuğundan emin olur ve maliyetlendirme sekmesini tetikler.
    """
    try:
        logger.info("--- [S4] Üretim Versiyonu & Maliyet Adımı Başladı ---")

        # 1. Giriş/Ekran Kontrolü (S1 seçili değilse ZMM0021 üzerinden girer)
        if not ensure_zmm_session_active(session, data, is_step_1_active=False, cache_file_path=cache_file_path, target_child=target_child):
            return False
        handle_sap_popups(session)
        # 2. Üretim Versiyonlarının Oluşturulması (Sekme 6 civarı)
        # Bu fonksiyon genellikle versiyonların otomatik oluşup oluşmadığını kontrol eder.
        if not zmm0020_ensure_production_versions_created(session):
            logger.error("Üretim versiyonları oluşturulamadı veya kontrol başarısız.")
            
        
        # 3. Maliyetlendirme Sekmesi İşlemleri
        # Bu adımda robot maliyet sekmesine geçer ve hesaplama butonuna basar.
        if not zmm0020_handle_costing_tab(session):
            logger.error("Maliyetlendirme sekmesi işlemleri başarısız.")
            


        logger.info("--- [S4] Başarıyla Tamamlandı ---")
        return True

    except Exception as e:
        logger.error(f"S4 Hatası: {e}")
        return False