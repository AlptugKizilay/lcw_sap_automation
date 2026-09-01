import logging
import time
from typing import Any, Dict, Optional

# SAP GUI Scripting için gerekli import
from src.sap_automation.screens.common_actions import read_sap_status_bar, handle_sap_popup_ok


logger = logging.getLogger(__name__)

# --- YARDIMCI FONKSİYON: MPROD kolonu boş olan satırların checkbox'ını işaretle ---
def _check_and_select_empty_mprod_rows(session: Any) -> bool:
    """
    ZPP0030 ekranındaki ALV gridde 'MPROD' kolonu boş olan satırların
    'SLCTD' (seçim) checkbox'ını işaretler.
    """
    logger.info("MPROD kolonu boş olan satırların checkbox'ları kontrol ediliyor ve işaretleniyor.")
    try:
        main_alv_grid = session.findById("wnd[0]/usr/cntlCC_0100/shellcont/shell")
        main_alv_grid.pressToolbarButton("BT003")
        time.sleep(0.5)
        rows_modified = 0
        for row_idx in range(main_alv_grid.RowCount):
            try:
                mprod_value = str(main_alv_grid.GetCellValue(row_idx, "MPROD")).strip()
                mtart_value = str(main_alv_grid.GetCellValue(row_idx, "MTART")).strip()
                raw_slctd = main_alv_grid.GetCellValue(row_idx, "SLCTD")
                is_selected = str(raw_slctd).strip().upper() == "X"
                #print(f"Satır {row_idx}: MPROD = '{mprod_value}', MTART = '{mtart_value}', SLCTD = {is_selected}")
                if mtart_value != '3030'and mtart_value:
                    if not mprod_value and not is_selected: # MPROD boş VE seçili değilse
                        logger.info(f"Satır {row_idx}: MPROD boş. Checkbox işaretleniyor.")
                        try:
                            main_alv_grid.modifyCheckbox(row_idx, "SLCTD", True)
                        except:
                            main_alv_grid.modifyCell(row_idx, "SLCTD", "X")
                        # Değişikliği SAP'ye bildirmek için
                        main_alv_grid.currentCellRow = row_idx
                        main_alv_grid.currentCellColumn = "SLCTD" # Odaklanma için
                        main_alv_grid.triggerModified()
                        time.sleep(0.1) # Her değişiklik arası kısa bekleme
                        rows_modified += 1
                    elif not mprod_value and is_selected:
                        logger.debug(f"Satır {row_idx}: MPROD boş ama zaten seçili. Atlanıyor.")
                    else:
                        logger.debug(f"Satır {row_idx}: MPROD dolu ('{mprod_value}'). Atlanıyor.")

            except Exception as e_cell:
                logger.warning(f"Satır {row_idx} işlenirken hata oluştu: {e_cell}. Bu satır atlanıyor.")
                continue
        
        if rows_modified > 0:
            logger.info(f"{rows_modified} adet boş 'MPROD' hücresi olan satır işaretlendi.")
            conversion_alv_grid = session.findById("wnd[0]/usr/cntlCC_0100/shellcont/shell")
            #conversion_alv_grid.pressToolbarButton("BT003") # yenile butonu
            time.sleep(0.5)
            conversion_alv_grid.pressToolbarButton("BT001") # Dönüştür butonu
            for i in range(rows_modified):
                try:
                    logger.info(f"Dönüştürme pop-up'ı {i+1}/{rows_modified} bekleniyor...")
                    
                    # wnd[1] (Pop-up) gelene kadar bekle (Maksimum 10 saniye)
                    popup_found = False
                    for _ in range(20): # 20 * 0.5sn = 10 saniye
                        if session.Children.Count > 1: # wnd[1] varsa Children sayısı 1'den büyüktir
                            popup_found = True
                            break
                        time.sleep(0.5)
                    
                    if popup_found:
                        popup = session.findById("wnd[1]")
                        
                        # Pop-up içindeki mesajı logla (Hata var mı görmek için)
                        try:
                            # Standart SAP mesaj kutusu metin alanı
                            msg_text = popup.findById("usr/txtS_POPUP-TEXT").text
                            logger.info(f"Pop-up Mesajı: {msg_text}")
                        except:
                            msg_text = "Metin okunamadı"

                        # "Tamam" butonuna bas (Genellikle tbar[0]/btn[0] veya Enter VKey 0)
                        # Bazı pop-up'larda 'Evet' butonu 'usr/btnBUTTON_1' olabilir.
                        # En garanti yol VKey 0 (Enter) göndermektir.
                        popup.sendVKey(0) 
                        logger.info(f"Pop-up {i+1} onaylandı (Enter).")
                        
                        # Pop-up'ın kapanması ve bir sonrakinin tetiklenmesi için kısa bekleme
                        time.sleep(1.5) 
                        try:
                            # Pencerenin hala açık olup olmadığını ve butonun varlığını kontrol et
                            extra_btn = session.findById("wnd[1]/usr/btnBUTTON_1")
                            extra_btn.press()
                            logger.info("ZSD0010: Ekstra onay butonu (BUTTON_1) bulundu ve basıldı.")
                        except Exception:
                            # Buton bulunamazsa veya pencere zaten kapandıysa buraya düşer
                            # Hata vermez, sadece loga yazar ve devam eder
                            logger.info("ZSD0010: Ekstra onay butonu bulunamadı veya gerekmedi, devam ediliyor.")
                    else:
                        logger.warning(f"Pop-up {i+1} beklenen sürede gelmedi.")
                        # Eğer pop-up gelmediyse ama döngü devam ediyorsa bir sorun olabilir, 
                        # ESC basarak döngüyü kurtarmaya çalışabiliriz.
                        session.findById("wnd[0]").sendVKey(12) 

                except Exception as e_pop:
                    logger.error(f"Pop-up {i+1} işlenirken hata: {e_pop}")
                    # Hata durumunda Enter basmayı dene
                    try: session.findById("wnd[1]").sendVKey(0)
                    except: pass
            time.sleep(1.5) 
            try:
                # Pencerenin hala açık olup olmadığını ve butonun varlığını kontrol et
                extra_btn = session.findById("wnd[1]/tbar[0]/btn[0]")
                extra_btn.press()
                logger.info("ZSD0010: Ekstra onay butonu (BUTTON_1) bulundu ve basıldı.")
            except Exception:
                # Buton bulunamazsa veya pencere zaten kapandıysa buraya düşer
                # Hata vermez, sadece loga yazar ve devam eder
                logger.info("ZSD0010: Ekstra onay butonu bulunamadı veya gerekmedi, devam ediliyor.")
            
            
        else:
            logger.info("MPROD kolonu boş olan ve işaretlenmesi gereken satır bulunamadı.")
        
        return True

    except Exception as e:
        logger.exception(f"MPROD kolonu boş olan satırları kontrol ederken kritik hata: {e}")
        return False


# --- ZPP0030 Üretim Siparişlerini İşleme ---
def zpp0030_process_production_orders(data, session, collected_data) -> bool:
    """
    Automates the ZPP0030 screen in SAP GUI to process production orders.

    Args:
        session (Any): The SAP GUI Scripting session object.
        plant (str): The plant code (S_WERKS-LOW).
        production_order (str): The production order number (S_BSANA-LOW).
        sales_office (str): The sales office code (S_VKBUR-LOW).
        sales_group (str): The sales group code (S_VKGRP-LOW).

    Returns:
        bool: True if the process is successful, False otherwise.
    """
    
    try:
        production_order = data.get('po_no')
        order_type = data.get('orderType')
        if order_type == "set":
            first_val = list(collected_data.values())[0]
            second_val = list(collected_data.values())[1]
            sales_office = second_val['sales_office']
            sales_group = second_val['sales_group']
            plant =second_val['sales_organization']
        else:
            sales_office = collected_data.get('sales_office')
            sales_group = collected_data.get('sales_group') 
            plant = collected_data.get('sales_organization')
        logger.info(f"ZPP0030: Üretim Siparişleri işleme başlatılıyor. Plant: {collected_data.get}, PO: {production_order}")
        
        time.sleep(4)
        session.startTransaction("ZPP0030")
        session.findById("wnd[0]").maximize()
        time.sleep(0.5)

        # 1. Filtre alanlarını doldur
        # Filtreleri Doldur
        session.findById("wnd[0]/usr/ctxtS_WERKS-LOW").text = plant
        session.findById("wnd[0]/usr/txtS_BSANA-LOW").text = production_order
        session.findById("wnd[0]/usr/ctxtS_VKBUR-LOW").text = sales_office
        session.findById("wnd[0]/usr/ctxtS_VKGRP-LOW").text = sales_group

        session.findById("wnd[0]/usr/ctxtS_VKGRP-LOW").setFocus()
        
        
        # 2. Yürüt butonuna bas
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        logger.info("Yürüt butonuna basıldı. Yeni sayfanın yüklenmesi bekleniyor.")
        time.sleep(0.5) # Yeni sayfanın yüklenmesini bekle

        status_after_execute = read_sap_status_bar(session)
        if status_after_execute["type"] == "E":
            logger.error(f"ZPP0030 Yürütme sonrası hata: {status_after_execute['text']}")
            return False
        elif status_after_execute["text"]:
            logger.info(f"ZPP0030 Yürütme sonrası mesaj: {status_after_execute['text']}")

        # 3. İlk ALV Grid ekranı işlemleri
        main_alv_grid = session.findById("wnd[0]/usr/cntlCC_0100/shellcont/shell")
        
        if main_alv_grid.RowCount == 0:
            logger.warning(f"ZPP0030 gridinde işlenecek öğe bulunamadı.")
            return False

        main_alv_grid.selectAll()
        logger.info("ALV griddeki tüm öğeler seçildi.")
        time.sleep(0.2)

        main_alv_grid.pressToolbarButton("BT002") # Master Order Dönüştürme butonu
        logger.info("'Master Order Dönüştürme' butonuna basıldı. Yeni sayfanın yüklenmesi bekleniyor.")
        time.sleep(1) # Yeni sayfanın yüklenmesini bekle

        status_after_bt002 = read_sap_status_bar(session)
        if status_after_bt002["type"] == "E":
            logger.error(f"ZPP0030 'Master Order Dönüştürme' sonrası hata: {status_after_bt002['text']}")
            return False
        elif status_after_bt002["text"]:
            logger.info(f"ZPP0030 'Master Order Dönüştürme' sonrası mesaj: {status_after_bt002['text']}")

        # 4. İkinci ALV Grid ekranı (Dönüştürme ekranı) işlemleri
        # Grid nesnesinin aynı ID'ye sahip olduğu varsayımıyla devam ediyoruz
        conversion_alv_grid = session.findById("wnd[0]/usr/cntlCC_0100/shellcont/shell") 
        time.sleep(0.5) # Grid'in tam olarak yüklenmesini bekle    
        conversion_alv_grid.pressToolbarButton("BT003") # yenile butonu        
        conversion_alv_grid.pressToolbarButton("BT004") # Tümünü Seç butonu
        logger.info("'Tümünü Seç' butonuna basıldı.")     
        conversion_alv_grid.pressToolbarButton("BT001") # Dönüştür butonu
        logger.info("'Dönüştür' butonuna basıldı. İşlemin tamamlanması bekleniyor.")
        

        # Pop-up kontrolü (common_actions'dan veya yerel olarak tanımlanmış)
        handle_sap_popup_ok(session) # Eğer pop-up çıkarsa kapatır

        status_after_convert = read_sap_status_bar(session)
        if status_after_convert["type"] == "E":
            logger.error(f"ZPP0030 'Dönüştür' sonrası hata: {status_after_convert['text']}")
            return False
        elif status_after_convert["text"]:
            logger.info(f"ZPP0030 'Dönüştür' sonrası mesaj: {status_after_convert['text']}")
        
        time.sleep(1) # Sayfanın yenilenmesini bekle
        
        # 5. Seçimleri Temizle
        # ALV grid nesnesini tekrar al, önceki işlemlerden sonra yenilenmiş olabilir
        main_alv_grid_after_conversion = session.findById("wnd[0]/usr/cntlCC_0100/shellcont/shell")
        main_alv_grid_after_conversion.pressToolbarButton("BT005")
        logger.info("'Seçimleri Temizle' butonuna basıldı.")
        time.sleep(1)

        # 6. MPROD kontrolü ve checkbox işaretleme
        if not _check_and_select_empty_mprod_rows(session):
            logger.error("MPROD kolonu boş olan satırların işaretlenmesi başarısız oldu.")
            return False
        
        
        logger.info("ZPP0030 Üretim Siparişleri işleme başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.exception(f"ZPP0030 Üretim Siparişleri işlenirken kritik hata oluştu: {e}")
        return False
