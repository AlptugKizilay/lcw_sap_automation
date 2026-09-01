import logging
import time
from typing import List, Any

logger = logging.getLogger(__name__)

def run_md01n_mrp(session: Any, main_material: str, children_materials: List[str], production_plant):
    """
    MD01N ekranında ana malzeme ve çocuk malzemeler için MRP Live çalıştırır.
    
    Args:
        session (Any): SAP GUI session objesi.
        main_material (str): Ana ürünün SAP malzeme kodu.
        children_materials (List[str]): Çocuk ürünlerin SAP malzeme kodları listesi.
    """
    try:
        logger.info("MD01N: MRP Live çalıştırma işlemi başlatılıyor.")
        session.startTransaction("MD01N")
        
        # 1. Seçenekleri ve Parametreleri Ayarla
        session.findById("wnd[0]/usr/chkPA_COMPS").selected = True
        session.findById("wnd[0]/usr/chkPA_PLALL").selected = True
        session.findById("wnd[0]/usr/chkPA_TRANS").selected = True
        session.findById("wnd[0]/usr/chkPA_REGEN").selected = True
        
        session.findById("wnd[0]/usr/ctxtSO_WERKS-LOW").text = production_plant
        session.findById("wnd[0]/usr/ctxtSO_MATNR-LOW").text = "" # Ana ekranı boş bırak, çoklu seçim kullanacağız
        session.findById("wnd[0]/usr/ctxtPA_SCHED").text = "1"
        session.findById("wnd[0]/usr/ctxtPA_PLMOD").text = "3"
        
        # 2. Çoklu Malzeme Seçim Ekranına Git
        session.findById("wnd[0]/usr/btn%_SO_MATNR_%_APP_%-VALU_PUSH").press()
        
        # Eğer senin kaydında olduğu gibi bir onay butonu gerekiyorsa (wnd[1] ilk açıldığında)
        try:
            session.findById("wnd[1]/tbar[0]/btn[0]").press()
        except:
            pass

        # 3. Tüm Malzemeleri (Ana + Çocuklar) Listeye Ekle
        all_materials = [main_material] + children_materials
        logger.info(f"MD01N: Toplam {len(all_materials)} malzeme listeye giriliyor.")

        table_path = "wnd[1]/usr/tabsTAB_STRIP/tabpSIVA/ssubSCREEN_HEADER:SAPLALDB:3010/tblSAPLALDBSINGLE"
        
        for idx, mat_code in enumerate(all_materials):
            # SAP Grid'de satır indeksi 0'dan başlar. Sütun indeksi senin scriptinde 1 olarak görünüyor.
            cell_id = f"ctxtRSCSEL_255-SLOW_I[1,{idx}]"
            session.findById(f"{table_path}/{cell_id}").text = str(mat_code)
            
            # Eğer liste çok uzunsa (ekranı aşıyorsa) scroll gerekebilir, 
            # ama set siparişlerinde genellikle 10-15 satırı geçmez.
            if idx == len(all_materials) - 1:
                session.findById(f"{table_path}/{cell_id}").setFocus()

        # 4. Listeyi Onayla ve Geri Dön
        session.findById("wnd[1]/tbar[0]/btn[8]").press() # Kopyala/Aktar butonu (F8)
        time.sleep(1)

        # 5. MRP'yi Yürüt (F8)
        logger.info("MD01N: MRP Live yürütülüyor...")
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        
        # MRP Live'ın tamamlanması zaman alabilir, durum çubuğunu veya ekranın değişmesini bekleyelim
        time.sleep(5) 
        
        # Sonuç ekranında bir hata veya özet var mı kontrol edilebilir
        logger.info("MD01N: MRP Live işlemi tamamlandı.")
        return True

    except Exception as e:
        logger.error(f"MD01N: MRP çalıştırılırken hata oluştu: {e}", exc_info=True)
        return False

def step_md01n_single_mrp(session, data, cache_file_path) -> bool:
    """
    MD01N: Single siparişler için MRP çalıştırır.
    ZPP0030 öncesi planlı siparişlerin oluşmasını tetikler.
    """
    try:
        # 1. Verileri Hazırla
        material_code = data.get('sap_material_code')
        plant = data.get('sale_group') # Fiori'den gelen üretim yeri
        
        if not material_code:
            logger.error("MD01N: Malzeme kodu (sap_material_code) bulunamadı!")
            return False

        logger.info(f"MD01N: MRP Çalıştırılıyor. Malzeme: {material_code}, Üretim Yeri: {plant}")
        time.sleep(2)

        # 2. Transaction'ı Başlat
        session.startTransaction("MD01N")
        session.findById("wnd[0]").maximize()
        time.sleep(2)

        # 3. Parametreleri Doldur (Checkbox ve Text alanları)
        # Checkboxlar (Bileşenleri aç, Satınalma talepleri vb.)
        session.findById("wnd[0]/usr/chkPA_COMPS").selected = True
        session.findById("wnd[0]/usr/chkPA_PLALL").selected = True
        session.findById("wnd[0]/usr/chkPA_TRANS").selected = True
        session.findById("wnd[0]/usr/chkPA_REGEN").selected = True
        
        # Tesis ve Malzeme
        session.findById("wnd[0]/usr/ctxtSO_WERKS-LOW").text = plant
        session.findById("wnd[0]/usr/ctxtSO_MATNR-LOW").text = material_code
        
        # Planlama Parametreleri
        session.findById("wnd[0]/usr/ctxtPA_SCHED").text = "1" # Terminleme
        session.findById("wnd[0]/usr/ctxtPA_PLMOD").text = "3" # Planlama modu (Yeniden planla)
        
        # 4. Yürüt (F8)
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        
        # 5. Onay Pop-up'ı (MD01N genellikle 'Parametreleri kontrol edin' diye wnd[1] açar)
        time.sleep(1.5)
        # handle_sap_popups fonksiyonunu burada kullanabiliriz
        if session.Children.Count > 1:
            logger.info("MD01N: Onay pop-up'ı kapatılıyor.")
            session.findById("wnd[1]/tbar[0]/btn[0]").press() # Enter/Tamam
        
        # MRP'nin bitmesi için kısa bir bekleme (Arka plan işlemi değildir, ekranın dönmesini bekler)
        time.sleep(0.5)
        
        logger.info(f"MD01N: {material_code} için MRP başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.error(f"MD01N Hatası: {e}")
        return False