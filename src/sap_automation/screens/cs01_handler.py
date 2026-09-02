# src/sap_automation/screens/cs01_handler.py

import logging
from typing import Dict, Any, List
import time 
import os
from src.file_management.excel_reader import read_variant_values_from_excel
from src.util.config_manager import ConfigManager
from src.util.localizer import _, get_unit_symbol

logger = logging.getLogger(__name__)
def get_plm_based_counts(color_data):
    """
    Belirli bir rengin verilerini alır ve PLM koduna göre adetleri toplar.
    Giriş: {"Şort-1048625-JM3": 1, "Şort-1048625-R93": 1, "Sweat-1048626-QVK": 1, "TOTAL_PIECES": 2}
    Çıkış: {'1048625': 2, '1048626': 1}
    """
    plm_counts = {}

    for key, value in color_data.items():
        # "TOTAL_PIECES" anahtarını atlıyoruz, sadece bileşenlere bakıyoruz
        if key == "TOTAL_PIECES":
            continue
        
        # Anahtarı '-' işaretinden parçala: ['Şort', '1048625', 'JM3']
        parts = key.split('-')
        
        if len(parts) >= 2:
            plm_code = parts[1] # Ortadaki değer PLM kodudur
            
            # Eğer bu PLM kodu daha önce eklendiyse üzerine topla, yoksa yeni aç
            if plm_code in plm_counts:
                plm_counts[plm_code] += value
            else:
                plm_counts[plm_code] = value
                
    return plm_counts

def _fill_variant_matrix_grid(session: Any, main_order_data: Dict[str, Any], variant_data: Dict[str, Any], row_mapping: Dict[str, int]):
    """
    YARDIMCI FONKSİYON: Izgara görünümüne girer ve varyantları filtreleyerek doldurur.
    """
    logger.info("CS01: Varyant matrisi doldurma işlemi başlatılıyor.")
    
    childrens = main_order_data.get("childrens", [])
    sizes = main_order_data.get("sizes", [])
    size_count = len(sizes)
    table_id = "wnd[0]/usr/tabsTS_ITOV/tabpTCMA/ssubSUBPAGE:SAPLCSDI:0152/tblSAPLCSDITCMAT"

    for child in childrens:
        child_plm = str(child.get("plm_code"))
        target_index = row_mapping.get(child_plm)

        if target_index is None: continue

        # 1. Satırı Seç ve Izgara Butonuna Bas
        session.findById(table_id).getAbsoluteRow(target_index).selected = True
        session.findById("wnd[0]/tbar[1]/btn[18]").press() # Izgara Görünüm Butonu
        time.sleep(1)

        # 2. Ana Renkler Üzerinden Döngü
        for main_color, comp_details in variant_data.items():
            # Ana Renk Filtresi
            session.findById("wnd[0]/usr/subFLTR_SUBSCR:SAPLFSH_PP_BD_BOM:0111/ctxtGS_HDR_FILTER-DIM1").text = main_color
            
            # 3. Bu Ana Renk Altındaki Bileşen Renkleri Üzerinden Döngü
            for label, qty in comp_details.items():
                if label == "TOTAL_PIECES": continue
                
                # Sadece bu PLM'e ait olan rengi filtrele
                if child_plm in label:
                    comp_color = label.split('-')[-1].strip()
                    
                    # Bileşen Renk Filtresi
                    session.findById("wnd[0]/usr/subFLTR_SUBSCR:SAPLFSH_PP_BD_BOM:0111/ctxtGS_COMP_FILTER-DIM1").text = comp_color
                    session.findById("wnd[0]/usr/subFLTR_SUBSCR:SAPLFSH_PP_BD_BOM:0111/btnCMDFILTER").press()
                    time.sleep(0.5)

                    # 4. Matrisi (Bedenleri) Doldur
                    matrix_shell = session.findById("wnd[0]/usr/subFLTR_SUBSCR:SAPLFSH_PP_BD_BOM:0111/subMATRIX:SAPLFSH_PP_BD_BOM:0112/cntlFSH_SKUCHAR/shellcont/shell")
                    
                    for s_idx in range(size_count):
                        matrix_shell.modifyCell(s_idx, "MATNR1", str(qty))
                    
                    # Son satıra focus yap (Gerekiyorsa)
                    matrix_shell.setCurrentCell(size_count - 1, "MATNR1")

        # Bu PLM bitti, Onayla ve Ana Tabloya Dön
        session.findById("wnd[0]").sendVKey(0) 
        session.findById("wnd[0]/tbar[1]/btn[5]").press() 
        time.sleep(1)
        
        
        # Seçimi temizle
        session.findById(table_id).getAbsoluteRow(target_index).selected = False
        
def handle_cs01_for_set_order(session: Any, main_order_data: Dict[str, Any]) -> bool:
    """
    Set siparişleri için CS01 ekranında (BOM oluşturma) gerekli adımları gerçekleştirir.
    Ana ürünün BOM'unu oluşturur ve çocuk ürünlerini bileşen olarak ekler.
    
    Args:
        session (Any): SAP GUI Scripting session objesi.
        main_order_data (Dict[str, Any]): Ana set sipariş verisi (JSON formatında).
    """
    logger.info(_("LOG_CS01_SET_BOM_START"))
    style_name = main_order_data.get("styleName")
    plm_id = main_order_data.get("plm_code")
    file_name = f"{style_name}_BOM_Template_{plm_id}.xlsx"
    output_directory= ConfigManager.OUTPUT_EXCEL_DIR
    input_path = os.path.join(output_directory, file_name)
    if not os.path.exists(input_path):
        raise Exception(f"BOM şablon dosyası bulunamadı: {input_path}. Lütfen dosyanın mevcut olduğundan emin olun.")            
    variant_data = read_variant_values_from_excel(input_path)
    # variant_data'nın içindeki değerleri (values) listeye çevir ve ilkini ([0]) al
    first_color_data = list(variant_data.values())[0]
    comp_piece_counter =get_plm_based_counts(first_color_data)
    

    main_material_code = main_order_data.get("main_material_code") # Ana ürünün malzeme kodu
    production_plant = main_order_data.get("sale_group", "2000") # Sabit üretim yeri
    
    childrens = main_order_data.get("childrens", [])

    if not main_material_code:
        logger.error(_("LOG_CS01_MAIN_MAT_NOT_FOUND"))
        raise ValueError("Ana malzeme kodu eksik.")
    
    if not childrens:
        logger.error(_("LOG_CS01_CHILDREN_NOT_FOUND"))
        raise ValueError("Çocuk ürünleri eksik.")

    # Her çocuğun SAP malzeme kodunun çekildiğinden emin olalım
    for child in childrens:
        if "sap_material_code" not in child or not child["sap_material_code"]:
            logger.error(f"CS01: Çocuk PLM {child.get('plm_code')} için SAP malzeme kodu bulunamadı. BOM oluşturulamıyor.")
            raise ValueError(f"Çocuk PLM {child.get('plm_code')} için SAP malzeme kodu eksik.")
    
    row_mapping = {}
    try:
        session.findById("wnd[0]").maximize()
        session.startTransaction("CS01")

        # CS01 ekranına giriş bilgileri
        session.findById("wnd[0]/usr/ctxtRC29N-MATNR").text = main_material_code
        session.findById("wnd[0]/usr/ctxtRC29N-WERKS").text = production_plant
        session.findById("wnd[0]/usr/ctxtRC29N-STLAN").text = "5" # BOM kullanımı
        session.findById("wnd[0]/usr/txtRC29N-STLAL").text = "1" # Alternatif BOM
        session.findById("wnd[0]/usr/txtRC29N-STLAL").setFocus()
        session.findById("wnd[0]/usr/txtRC29N-STLAL").caretPosition = 1
        session.findById("wnd[0]").sendVKey(0) # Enter
        logger.info(_("LOG_CS01_MAIN_MAT_ENTERED", mat_code=main_material_code))
        time.sleep(1.5) # Ekranın yüklenmesini bekle

        # Tabloya çocuk ürünlerini ekle
        table_id = "wnd[0]/usr/tabsTS_ITOV/tabpTCMA/ssubSUBPAGE:SAPLCSDI:0152/tblSAPLCSDITCMAT"
        table = session.findById(table_id)

        for i, child in enumerate(childrens):
            child_plm = str(child.get("plm_code"))
            child_material_code = child["sap_material_code"] 
            child_menge = comp_piece_counter.get(child_plm, 1)
            

            logger.info(_("LOG_CS01_CHILD_ROW_ADDING", plm=child_plm, mat_code=child_material_code, qty=child_menge))

            try:
                # Hücrelere doğrudan erişim: [Sütun_Adı, Satır_İndeksi]
                # CS01'de sütun teknik isimleri genellikle RC29P- ile başlar
                
                # Kalem Tipi (L)
                session.findById(f"{table_id}/ctxtRC29P-POSTP[1,{i}]").text = "L"
                
                # Bileşen (Malzeme Kodu)
                session.findById(f"{table_id}/ctxtRC29P-IDNRK[2,{i}]").text = child_material_code
                
                # Miktar
                session.findById(f"{table_id}/txtRC29P-MENGE[4,{i}]").text = str(child_menge)
                
                # Ölçü Birimi (TR: ADT / EN: PC)
                session.findById(f"{table_id}/ctxtRC29P-MEINS[5,{i}]").text = get_unit_symbol()
                
                row_mapping[child_plm] = i

            except Exception as e_cell:
                logger.error(f"CS01: Satır {i} doldurulurken hata: {e_cell}")
                # Eğer 0152 ekranı değilse, SAP bazen 0150 kullanabilir. 
                # Hata alırsan Tracker ile ID'yi tekrar kontrol etmelisin.
                raise

            
        # Tüm satırlar girildikten sonra Enter ile onayla
        session.findById("wnd[0]").sendVKey(0) # Enter
        logger.info(_("LOG_CS01_ALL_ROWS_ENTERED"))
        time.sleep(1) # Ekranın yüklenmesini bekle
        
        # --- ADIM 2: Matris Görünümünü Doldur (Yeni Modüler Fonksiyon) ---
        _fill_variant_matrix_grid(session, main_order_data, variant_data, row_mapping)

        session.findById("wnd[0]/tbar[0]/btn[11]").press()
        logger.info(_("LOG_CS01_BOM_SAVED"))
        time.sleep(1) # Kayıt işleminin tamamlanmasını bekle

        logger.info(_("LOG_CS01_BOM_SET_SUCCESS"))
        return True
    except Exception as e:
        logger.error(_("LOG_CS01_ERROR", error=e), exc_info=True)
        raise # Hatayı yukarıya fırlat ki workflow durdurulsun

create_bom_for_set_order = handle_cs01_for_set_order
