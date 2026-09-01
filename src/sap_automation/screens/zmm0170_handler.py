import logging
import re  # Metin içinden sayıları ayıklamak için (Regular Expression)
from src.util.localizer import get_unit_symbol

class ZMM0170Handler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_accessory(self, session, data):
        """ZMM0170 ekranından Aksesuar malzemesi oluşturur"""
        tanim = str(data.get("tanim", "")).upper()
        
        try:
            matkl_map = {
                "Fermuar": "1040001", "Zipper": "1040001",
                "Düğme": "1040005", "Button": "1040005",
                "Yıkama Talimatı": "1040017", "Care Label": "1040017", "Washing Instructions": "1040017",
                "Kordon": "1050005", "Cord": "1050005"
            }
            tur_adi = data.get("tur", "Fermuar")
            matkl_kodu = matkl_map.get(tur_adi, "1040001")

            # 2. İşlem Kodunu Başlat ve Ekranı Büyüt
            session.StartTransaction("ZMM0170")
            session.findById("wnd[0]").maximize()

            fiyat_str = str(data.get("fiyat", "0,5")).replace(".", ",")

            # 3. Ana Bilgileri Doldur
            unit_symbol = get_unit_symbol()
            session.findById("wnd[0]/usr/ctxtZMM_017_S_ACCESSORY_CRT_HDR-PLMKOD").text = "ARGE"
            session.findById("wnd[0]/usr/ctxtZMM_017_S_ACCESSORY_CRT_HDR-MTART").text = "1040"
            session.findById("wnd[0]/usr/ctxtZMM_017_S_ACCESSORY_CRT_HDR-WERKS").text = str(data.get("uretim_yeri", "2000"))
            session.findById("wnd[0]/usr/txtZMM_017_S_ACCESSORY_CRT_HDR-PEINH").text = "1"
            session.findById("wnd[0]/usr/txtZMM_017_S_ACCESSORY_CRT_HDR-STPRS").text = fiyat_str
            session.findById("wnd[0]/usr/ctxtZMM_017_S_ACCESSORY_CRT_HDR-MATKL").text = matkl_kodu
            session.findById("wnd[0]/usr/ctxtZMM_017_S_ACCESSORY_CRT_HDR-MEINS").text = unit_symbol
            session.findById("wnd[0]/usr/txtZMM_017_S_ACCESSORY_CRT_HDR-ZZMODEL_ADI").text = str(data.get("model", ""))

            # 4. Otomatik Tanım Butonuna Bas
            session.findById("wnd[0]/usr/chkZMM_017_S_ACCESSORY_CRT_HDR-AUTO_TNM").setFocus()
            session.findById("wnd[0]/usr/chkZMM_017_S_ACCESSORY_CRT_HDR-AUTO_TNM").selected = True
            
            try:
                session.findById("wnd[1]/usr/btnDY_VAROPTION1").press()
            except:
                pass

            # 5. Malzeme Tanımını Gir
            session.findById("wnd[0]/usr/txtZMM_017_S_ACCESSORY_CRT_HDR-MAKTX").text = tanim
            session.findById("wnd[0]/usr/txtZMM_017_S_ACCESSORY_CRT_HDR-MAKTX").setFocus()

            # 6. Dil Çevirileri / Uzun Tanım
            session.findById("wnd[0]/usr/btnZMM_017_S_ACCESSORY_CRT_HDR-LANGU").press()
            session.findById("wnd[1]/usr/txtGS_SCREEN_0104-MALZEME_ADI").text = tanim
            session.findById("wnd[1]/usr/txtGS_SCREEN_0104-MALZEME_ADI_UZUN").text = tanim
            session.findById("wnd[1]/usr/btn%#AUTOTEXT001").press()

            # 7. KAYDET BUTONUNA BAS
            session.findById("wnd[0]/tbar[0]/btn[11]").press()
            # Pop-up onay butonlarına basıp ekranı kapat
            try:
                session.findById("wnd[1]/usr/btnDY_VAROPTION1").press()
            except:
                pass

            # ========================================================
            # GÜVENLİK ADIMI: POP-UP'TAN KODU YAKALA (BAPI MESSAGE)
            # ========================================================
            popup_matnr = None
            try:
                # Pop-up'taki mesaj hücresini oku
                msg_text = session.findById("wnd[1]/usr/tblSAPLRSCRMBW_TOOLSTC_BAPIRET2/txtGS_BAPIRET2-MESSAGE[1,0]").text
                self.logger.info(f"ZMM0170 Popup Mesajı: {msg_text}")
                
                # Metnin içindeki TÜM sayı gruplarını bul (Örn: "Malzeme 1040001 yaratıldı" -> ['1040001'])
                rakamlar = re.findall(r'\d+', msg_text)
                
                if rakamlar:
                    # İçinde birden fazla sayı varsa, en uzun olanı malzeme kodudur varsayımı yapıyoruz
                    popup_matnr = max(rakamlar, key=len)
                    self.logger.info(f"ZMM0170 Popup'tan ayıklanan Yedek Malzeme Kodu: {popup_matnr}")
            except Exception as e:
                self.logger.warning(f"ZMM0170 Popup mesajı okunamadı (Uyarı mesajı olabilir): {e}")


            try:
                session.findById("wnd[1]/tbar[0]/btn[0]").press()
            except:
                pass

            # ========================================================
            # 8. ANA EKRANDAN OLUŞAN KODU GERİ AL (ASIL HEDEF)
            # ========================================================
            main_matnr = None
            try:
                session.findById("wnd[0]/usr/ctxtZMM_017_S_ACCESSORY_CRT_HDR-MATNR").setFocus()
                main_matnr = session.findById("wnd[0]/usr/ctxtZMM_017_S_ACCESSORY_CRT_HDR-MATNR").text
            except Exception as e:
                self.logger.warning(f"ZMM0170 Ana ekrandan malzeme kodu okunamadı: {e}")

            # ========================================================
            # KONTROL MEKANİZMASI (DOUBLE CHECK)
            # ========================================================
            # Eğer ana ekrandaki kod boşsa, yedekteki pop-up kodunu kullan
            final_matnr = main_matnr if (main_matnr and main_matnr.strip() != "") else popup_matnr

            if not final_matnr:
                raise Exception("Malzeme başarıyla kaydedildi ancak kodu ekrandan veya pop-up'tan okunamadı!")

            self.logger.info(f"ZMM0170: {tanim} başarıyla açıldı -> FİNAL KOD: {final_matnr}")
            return {"status": "success", "matnr": final_matnr}

        except Exception as e:
            self.logger.error(f"ZMM0170 Ekran Hatası ({tanim}): {str(e)}")
            return {"status": "error", "message": str(e)}
