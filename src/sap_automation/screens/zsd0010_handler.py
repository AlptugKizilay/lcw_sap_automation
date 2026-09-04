import logging
import re
import os
from playwright.sync_api import sync_playwright, Playwright, Browser, Page
import time
from typing import Dict
from src.sap_automation.screens.common_actions import read_sap_status_bar
from src.util.helpers import get_resource_path
from src.util.localizer import _

logger = logging.getLogger(__name__)

def fiori_login(url: str, username: str, password: str) -> tuple[Page, Browser, Playwright] | tuple[None, None, None]:
    """
    Logs into the SAP Fiori Launchpad using Playwright.

    Args:
        url (str): The URL of the SAP Fiori Launchpad.
        username (str): The SAP username.
        password (str): The SAP password.

    Returns:
        tuple[playwright.sync_api.Page, playwright.sync_api.Browser, playwright.sync_api.Playwright]:
            A tuple containing the Playwright Page object, Browser object, and Playwright context
            after successful login. The caller is responsible for closing the browser and stopping
            the Playwright context when done.
        tuple[None, None, None]: If login fails.
    """
    chrome_exe = get_resource_path(os.path.join("browsers", "chromium-1200", "chrome-win64", "chrome.exe"))
    p = None
    browser = None
    page = None
    try:
        logger.info(_("LOG_FIORI_START_BROWSER"))
        p = sync_playwright().start()
        browser = p.chromium.launch(executable_path=chrome_exe, headless=False) # Test için tarayıcıyı görünür aç
        page = browser.new_page()

        logger.info(_("LOG_FIORI_GOTO_LOGIN", url=url))
        # Sayfanın tamamen yüklenmesini bekleyelim (networkidle yerine 'load' daha genel ve güvenli olabilir)
        page.goto(url, wait_until='load', timeout=60000) 

        # Login form elementlerinin görünür olmasını bekleyelim
        logger.info(_("LOG_FIORI_WAIT_FORM"))
        page.wait_for_selector("#USERNAME_FIELD-inner", timeout=30000)
        page.wait_for_selector("#PASSWORD_FIELD-inner", timeout=30000)
        page.wait_for_selector("#LANGUAGE_SELECT", timeout=30000)
        page.wait_for_selector("#LOGIN_LINK", timeout=30000)
        logger.info(_("LOG_FIORI_FORM_FOUND"))

        logger.info(_("LOG_FIORI_ENTER_CRED"))
        page.fill("#USERNAME_FIELD-inner", username)
        page.fill("#PASSWORD_FIELD-inner", password)

        logger.info(_("LOG_FIORI_SELECT_LANG", lang="TR - Türkçe"))
        page.select_option("#LANGUAGE_SELECT", "TR")

        logger.info(_("LOG_FIORI_CLICK_LOGIN"))
        page.click("#LOGIN_LINK")

        # Fiori Launchpad'in tamamen yüklenmesini bekleyelim.
        # Fiori'de genellikle ana kabuk (shell) yüklendiğinde işlem tamamlanmıştır.
        # '#shell-header' veya 'div.sapUshellShell' gibi elementler kullanılabilir.
        logger.info(_("LOG_FIORI_WAIT_LAUNCHPAD"))
        page.wait_for_selector('#shell-header', timeout=60000) # 60 saniye bekleyelim

        if page.locator('#shell-header').is_visible():
            logger.info(_("LOG_FIORI_LOGIN_SUCCESS"))
            return page, browser, p
        else:
            logger.error(_("LOG_FIORI_LOGIN_FAIL"))
            page.screenshot(path="fiori_login_failed_no_shell_header.png")
            browser.close()
            p.stop()
            return None, None, None

    except Exception as e:
        logger.exception(_("LOG_FIORI_CRITICAL_ERR", error=str(e)))

        if browser:
            browser.close()
        if p:
            p.stop()
        return None, None, None
    
# --- ZSD0010 Ekranında PLM Öğelerini İşleme Fonksiyonu ---
def zsd0010_process_plm_items(page: Page, plm_code_to_filter: str, expected_price_from_data: float) -> str | None:
    """
    Processes PLM items on the ZSD0010 screen in SAP Fiori.
    Filters by PLM code, verifies item details, performs conditional actions,
    and extracts the Standard Bid Number.

    Args:
        page (Page): The Playwright Page object after Fiori login.
        plm_code_to_filter (str): The PLM code to filter by.
        expected_price_from_data (float): The expected sales price (e.g., 2.340).

    Returns:
        str | None: The extracted collected data if successful, None otherwise.
    """
    try:
        logger.info(_("LOG_ZSD0010_FILTER_START", plm_code=plm_code_to_filter))

        # 1. PLM Kodu Input Alanını Bul ve Doldur
        plm_input_selector = "#application-Action-SD001-component---Main--smartFilterBar-filterItemControl_BASIC-IvPlmkodu-inner"
        page.wait_for_selector(plm_input_selector, timeout=30000)
        page.fill(plm_input_selector, plm_code_to_filter)
        page.press(plm_input_selector, "Enter") # Enter tuşuna basarak filtreyi uygula
        logger.info(_("LOG_ZSD0010_FILTER_APPLIED", plm_code=plm_code_to_filter))
        time.sleep(3) # Filtreleme sonuçlarının yüklenmesini bekle (Fiori yükleme durumunu kontrol etmek daha iyi olabilir)

        # 2. Listelenen Öğeleri Bul ve Üzerinde Gezin
        table_body_selector = "#__table0-tblBody"
        page.wait_for_selector(table_body_selector, timeout=30000)
        
        # Get all rows. Using a more generic selector for rows as IDs can be dynamic.
        # Assuming each row is a 'tr' element directly under the table body.
        rows_locator = page.locator(f"{table_body_selector} > tr[id^='__item']") 
        row_count = rows_locator.count()
        logger.info(_("LOG_ZSD0010_ROWS_FOUND", count=row_count))

        if row_count == 0:
            logger.warning(_("LOG_ZSD0010_NO_ITEMS", plm_code=plm_code_to_filter))
            return None

        collected_data = None

        # Iterate through each row
        for i in range(row_count):
            row = rows_locator.nth(i)
            logger.debug(_("LOG_ZSD0010_ROW_PROCESSING", row=i+1))

            # 3. Bilgileri Çek
            # Fiyat
            price_selector = "td[data-sap-ui-column='application-Action-SD001-component---Main--LineItemsSmartTable-SatisFiyati'] span.sapMText"
            price_text = row.locator(price_selector).text_content().strip()
            # Fiyatı virgül yerine nokta ile float'a çevir
            extracted_price = float(price_text.replace('.', '').replace(',', '.'))
            logger.debug(_("LOG_ZSD0010_EXTRACTED_PRICE", row=i+1, price=extracted_price))

            # Onay Durum Bilgisi
            approval_status_selector = "span[id^='__status0-'][id$='-text']"
            approval_status = row.locator(approval_status_selector).text_content().strip()
            logger.debug(_("LOG_ZSD0010_APPROVAL_STATUS", row=i+1, status=approval_status))

            # PLM Durum Bilgisi
            plm_status_selector = "span[id^='__status1-'][id$='-text']"
            plm_status = row.locator(plm_status_selector).text_content().strip()
            logger.debug(_("LOG_ZSD0010_PLM_STATUS", row=i+1, status=plm_status))

            # 4. Fiyat Karşılaştırması ve Detay Sayfasına Gitme
            if extracted_price == expected_price_from_data:
                logger.info(f"Satır {i+1}: Fiyat eşleşti ({extracted_price}). Detay sayfasına gidiliyor.")
                
                # Navigation button click
                nav_button_selector = "td[id$='-TypeCell'] span[id$='-imgNav']"
                
                # Use expect_navigation to wait for the URL change after clicking
                
                row.locator(nav_button_selector).click()
                
                logger.info("Detay sayfasına geçildi.")
                time.sleep(3) # Sayfanın tamamen yüklenmesini bekle (veya daha spesifik bir elementin yüklenmesini bekle)                
                
                # 5. Standart Teklif Numarasını Al
                standard_bid_input_selector = "#application-Action-SD001-component---Detail--inpStandardBid-inner"
                page.wait_for_selector(standard_bid_input_selector, timeout=30000)
                standard_bid_number = page.locator(standard_bid_input_selector).get_attribute("value")
                logger.info(f"Standart Teklif Numarası: {standard_bid_number}")
                # 6. "Organizasyonel Veriler" butonuna bas ve verileri çek
                organizational_data_button_selector = "#__button13" # Butonun kendi ID'si
                page.wait_for_selector(organizational_data_button_selector, timeout=15000)
                logger.info("Organizasyonel Veriler butonuna tıklanıyor.")
                page.click(organizational_data_button_selector)
                time.sleep(2) # Yeni bölümün yüklenmesi için bekle

                # Organizasyonel Verileri Çek
                sales_org_selector = "#application-Action-SD001-component---Detail--inpSalesOrg-inner"
                sales_office_selector = "#application-Action-SD001-component---Detail--inpSalesOffice-inner"
                sales_group_selector = "#application-Action-SD001-component---Detail--inpSalesGroup-inner"

                page.wait_for_selector(sales_org_selector, timeout=15000) # Inputların yüklenmesini bekle
                sales_org = page.locator(sales_org_selector).get_attribute("value")
                sales_office = page.locator(sales_office_selector).get_attribute("value")
                sales_group = page.locator(sales_group_selector).get_attribute("value")

                logger.info(f"Organizasyonel Veriler: Satış Organizasyonu: {sales_org}, Satış Ofisi: {sales_office}, Satış Grubu: {sales_group}")

                # Tüm toplanan verileri bir sözlükte sakla
                collected_data = {
                    'standard_bid_number': standard_bid_number,
                    'sales_organization': sales_org,
                    'sales_office': sales_office,
                    'sales_group': sales_group
                }
                org_okay_button_selector = "#__button42" 
                page.wait_for_selector(org_okay_button_selector, timeout=15000)
                page.click(org_okay_button_selector)
                time.sleep(1)

                # 6. Koşullu Onay ve PLM Gönder İşlemleri
                # "eğer onay durum bilgisi "Onaylandı" ve plm durum bilgisi "Beklemede" ise"
                is_approved = str(approval_status).strip().lower() in ["onaylandı", "approved", "completed"]
                is_pending = str(plm_status).strip().lower() in ["beklemede", "pending"]
                if not (is_approved and not is_pending):
                    logger.info("Onay durumu 'Onaylandı' değil veya PLM durumu 'Beklemede'. İşlemler yapılıyor.")

                    # PLM Gönder Butonu
                    plm_send_button_selector = "#__button6"
                    if page.locator(plm_send_button_selector).is_visible():
                        logger.info("PLM Gönder butonuna tıklanıyor.")
                        page.click(plm_send_button_selector)
                        # Pop-up onayı
                        confirm_popup_selector = "span[id^='__mbox-btn-'][id$='-inner']" # Generic selector for "Tamam" button in pop-up
                        
                        try:
                            page.wait_for_selector(confirm_popup_selector, timeout=15000)
                            logger.info("PLM Gönder onay pop-up'ı tespit edildi. 'Tamam' butonuna basılıyor.")
                            page.click(confirm_popup_selector)
                            time.sleep(2) # İşlemin tamamlanmasını bekle
                            
                            page.wait_for_selector(confirm_popup_selector, timeout=15000)
                            logger.info("PLM Gönder onay pop-up'ı tespit edildi. 'Tamam' butonuna basılıyor.")
                            page.click(confirm_popup_selector)
                            time.sleep(2) # İşlemin tamamlanmasını bekle
                            
                        except Exception as pop_e:
                            logger.warning(f"PLM Gönder sonrası onay pop-up'ı beklenenden farklıydı veya hiç gelmedi: {pop_e}. Devam ediliyor.")
                    else:
                        logger.warning("PLM Gönder butonu görünür değil.")

                    # Müşteri Onayı Butonu
                    customer_approval_button_selector = "#__button2"
                    if page.locator(customer_approval_button_selector).is_visible():
                        logger.info("Müşteri Onayı butonuna tıklanıyor.")
                        page.click(customer_approval_button_selector)
                        # Pop-up onayı
                        confirm_popup_selector = "span[id^='__mbox-btn-'][id$='-inner']" # Generic selector for "Tamam" button in pop-up
                        try:
                            page.wait_for_selector(confirm_popup_selector, timeout=15000)
                            logger.info("Müşteri Onayı onay pop-up'ı tespit edildi. 'Tamam' butonuna basılıyor.")
                            page.click(confirm_popup_selector)
                            time.sleep(2) # İşlemin tamamlanmasını bekle
                            
                            page.wait_for_selector(confirm_popup_selector, timeout=15000)
                            logger.info("Müşteri Onayı onay pop-up'ı tespit edildi. 'Tamam' butonuna basılıyor.")
                            page.click(confirm_popup_selector)
                            time.sleep(2) # İşlemin tamamlanmasını bekle
                            
                        except Exception as pop_e:
                            logger.warning(f"Müşteri Onayı sonrası onay pop-up'ı beklenenden farklıydı veya hiç gelmedi: {pop_e}. Devam ediliyor.")
                    else:
                        logger.warning("Müşteri Onayı butonu görünür değil.")
                else:
                    logger.info("Onay durumu 'Onaylandı' ve PLM durumu 'Tamamlandı'. Ek işlem gerekmiyor.")

                # Başarılı işlem sonrası Standard Bid Number'ı döndür
                return collected_data 

            else:
                logger.debug(f"Satır {i+1}: Fiyat eşleşmedi (Beklenen: {expected_price_from_data}, Çekilen: {extracted_price}). Sonraki satıra geçiliyor.")
        
        logger.warning(f"PLM kodu '{plm_code_to_filter}' için beklenen fiyat ({expected_price_from_data}) ile eşleşen öğe bulunamadı.")
        return None

    except Exception as e:
        logger.exception(f"ZSD0010 PLM öğeleri işlenirken kritik hata oluştu: {e}")
        if page:
            try:
                logger.info("Hata anında ekran görüntüsü alınmaya çalışılıyor...")
            except Exception as ss_e:
                logger.warning(f"Hata ekran görüntüsü alınırken hata: {ss_e}")
        return None

def zsd0010_process_order_integration_gui(session, data, collected_data) -> bool:

    """
    Handles the ZSD0010 Order Integration Cockpit in SAP GUI.
    Filters by PO number, selects an item, opens a pop-up, fills organizational data
    and standard bid number, then confirms the pop-up.
 po_number, sales_office, sales_group, standard_bid_number
    Args:
        session (Any): The SAP GUI Scripting session object.
        po_number (str): The Purchase Order number to filter by.
        sales_office (str): The Sales Office value to enter in the pop-up.
        sales_group (str): The Sales Group value to enter in the pop-up.
        standard_bid_number (str): The Standard Bid Number to enter in the pop-up.

    Returns:
        bool: True if the process is successful, False otherwise.
    """
    po_number = data.get('po_no')
    sales_office = collected_data.get('sales_office')
    sales_group = collected_data.get('sales_group') 
    standard_bid_number = collected_data.get('standard_bid_number')
    if not po_number or not sales_office or not sales_group or not standard_bid_number:
        logger.error("Gerekli tüm veriler sağlanmadı. İşlem iptal ediliyor.")
        return False
    
    try:
        logger.info(f"ZSD0010 SAP GUI: Sipariş Entegrasyon Kokpiti başlatılıyor. PO No: {po_number}")
        session.startTransaction("ZSD0010")
        # 1. "Tümünü Göster" (P_ALL) radio butonunu seç
        session.findById("wnd[0]/usr/radP_ALL").setFocus()
        session.findById("wnd[0]/usr/radP_ALL").select()
        logger.info("P_ALL radio butonu seçildi.")
        time.sleep(0.5)

        # 2. PO Numarasını gir
        session.findById("wnd[0]/usr/txtS_BSTNK-LOW").text = po_number
        logger.info(f"PO Numarası '{po_number}' girildi.")
        time.sleep(0.5)

        # 3. "Yürüt" (Execute) butonuna bas (Genellikle tbar[1]/btn[8])
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        logger.info("Yürüt butonuna basıldı. Sonuçların yüklenmesi bekleniyor.")
        time.sleep(3) # Sonuçların yüklenmesini bekle

        # Durum çubuğunu kontrol et
        status_after_execute = read_sap_status_bar(session)
        if status_after_execute["type"] == "E":
            logger.error(f"ZSD0010 Yürütme sonrası hata: {status_after_execute['text']}")
            return False
        elif status_after_execute["text"]:
            logger.info(f"ZSD0010 Yürütme sonrası mesaj: {status_after_execute['text']}")

        # 4. ALV Grid'den öğeyi seç ve "RUN_POPUP" butonuna bas
        alv_grid = session.findById("wnd[0]/usr/cntlSCR_CONT/shellcont/shell")
        
        # Gridde en az bir satır olduğundan emin ol
        if alv_grid.RowCount == 0:
            logger.warning(f"PO Numarası '{po_number}' için ZSD0010 gridinde hiçbir öğe bulunamadı.")
            return False

        # İlk satırı seç (veya belirli bir satırı seçmek için buraya mantık ekle)
        # Genellikle XFELD sütunu bir checkbox veya seçim alanı olur
        alv_grid.currentCellRow = 0 # İlk satırı aktif hale getir
        alv_grid.currentCellColumn = "XFELD" # XFELD sütununu hedefle
        alv_grid.clickCurrentCell() # Hücreye tıklayarak seçimi yap
        logger.info(f"ALV gridde ilk satırın 'XFELD' sütunu seçildi.")
        time.sleep(1)

        alv_grid.pressToolbarButton("RUN_PO PUP")
        logger.info("'RUN_POPUP' butonuna basıldı. Pop-up'ın açılması bekleniyor.")
        time.sleep(2) # Pop-up'ın açılmasını bekle

        # 5. Yeni açılan pop-up'ı (wnd[1]) yönet
        popup_wnd1 = session.findById("wnd[1]")
        
        session.findById("wnd[1]/usr/txtZSD_003_S_POPUP_HEADER-SATIS_BUROSU").text = sales_office
        logger.info(f"Pop-up: Satış Bürosu '{sales_office}' girildi.")
        time.sleep(0.2)

        session.findById("wnd[1]/usr/ctxtZSD_003_S_POPUP_HEADER-SATIS_GRUBU").text = sales_group
        logger.info(f"Pop-up: Satış Grubu '{sales_group}' girildi.")
        time.sleep(0.2)

        session.findById("wnd[1]/usr/ctxtZSD_003_S_POPUP_HEADER-TEKLIF_NO").text = standard_bid_number
        logger.info(f"Pop-up: Teklif Numarası '{standard_bid_number}' girildi.")
        time.sleep(0.2)

        session.findById("wnd[1]/usr/ctxtZSD_003_S_POPUP_HEADER-TEKLIF_NO").setFocus()
        session.findById("wnd[1]/usr/ctxtZSD_003_S_POPUP_HEADER-TEKLIF_NO").caretPosition = len(standard_bid_number) # Teklif numarasının uzunluğuna ayarla
        logger.debug("Teklif Numarası alanına odaklanıldı ve caret pozisyonu ayarlandı.")
        time.sleep(0.5)

        # Pop-up'ı onaylamak için Enter tuşuna bas
        popup_wnd1.sendVKey(0) 
        logger.info("Pop-up onaylamak için Enter tuşuna basıldı.")
        
        if not _fill_kaynak_kalem_in_popup_grid(session):
            logger.error("KAYNAK_KALEM sütunu doldurulurken hata oluştu. İşlem durduruluyor.")
            return False
        time.sleep(1) # Gridin güncellenmesi ve SAP'nin değişikliği işlemesi için bekle
        
        session.findById("wnd[1]/tbar[0]/btn[8]").press() # Pop-up'taki Onay butonuna bas
        time.sleep(0.5)
        session.findById("wnd[2]/usr/btnBUTTON_1").press()
        time.sleep(0.3)
        session.findById("wnd[2]/tbar[0]/btn[0]").press()
        time.sleep(5)

        status_after_popup_confirm = read_sap_status_bar(session)
        if status_after_popup_confirm["type"] == "E":
            logger.error(f"ZSD0010 Pop-up onayı sonrası hata: {status_after_popup_confirm['text']}")
            return False
        elif status_after_popup_confirm["text"]:
            logger.info(f"ZSD0010 Pop-up onayı sonrası mesaj: {status_after_popup_confirm['text']}")

        logger.info("ZSD0010 SAP GUI Sipariş Entegrasyon Kokpiti işlemleri başarıyla tamamlandı.")
        return True

    except Exception as e:
        logger.exception(f"ZSD0010 SAP GUI Sipariş Entegrasyon Kokpiti yönetilirken kritik hata oluştu: {e}")
        return False
    
def _fill_kaynak_kalem_in_popup_grid(session) -> bool:
    """
    ZSD0010 Sipariş Entegrasyon Kokpiti pop-up'ındaki ALV gridde
    'KAYNAK_KALEM' sütununu 'RENK'e göre gruplayarak ve en küçük 'KALEM_NO'yu baz alarak doldurur.
    """
    logger.info("ZSD0010 Pop-up gridindeki 'KAYNAK_KALEM' sütunu dolduruluyor.")
    try:
        # Pop-up'taki ALV grid nesnesini bul
        popup_alv_grid = session.findById("wnd[1]/usr/cntlSCR_CONT/shellcont/shell")

        # 1. Gerekli verileri grid'den çek: RENK, KALEM_NO
        grid_data = []
        for row_idx in range(popup_alv_grid.RowCount):
            try:
                # Sütun isimlerinin teknik isimler olduğunu varsayıyoruz
                renk = str(popup_alv_grid.GetCellValue(row_idx, "RENK")).strip()
                kalem_no = int(popup_alv_grid.GetCellValue(row_idx, "KALEM_NO")) 
                grid_data.append({'row_idx': row_idx, 'RENK': renk, 'KALEM_NO': kalem_no})
            except Exception as e_get_cell:
                logger.warning(f"Satır {row_idx} verileri okunurken hata: {e_get_cell}. Bu satır atlanıyor.")
                continue
        
        if not grid_data:
            logger.warning("Gridde işlenecek veri bulunamadı.")
            return True # Hata yok, sadece veri yok

        # 2. Veriyi RENK'e göre grupla ve her gruptaki en küçük KALEM_NO'yu bul
        # Yapı: {"RENK_KODU": {"min_kalem_no": int, "row_indices": [int, ...]}}
        grouped_by_color = {}
        for item in grid_data:
            color = item['RENK']
            kalem_no = item['KALEM_NO']
            row_idx = item['row_idx']

            if color not in grouped_by_color:
                grouped_by_color[color] = {'min_kalem_no': kalem_no, 'row_indices': []}
            
            # Bu renkteki en küçük KALEM_NO'yu güncelle
            if kalem_no < grouped_by_color[color]['min_kalem_no']:
                grouped_by_color[color]['min_kalem_no'] = kalem_no
            
            grouped_by_color[color]['row_indices'].append(row_idx)
        
        logger.debug(f"Renk gruplaması tamamlandı: {grouped_by_color}")

        # 3. KAYNAK_KALEM sütununu doldur
        for color, data in grouped_by_color.items():
            min_kalem_no_for_color = str(data['min_kalem_no']) # SAP'ye string olarak yazılacak
            for row_idx in data['row_indices']:
                logger.debug(f"Renk '{color}' için satır {row_idx} 'KAYNAK_KALEM' değeri '{min_kalem_no_for_color}' olarak ayarlanıyor.")
                popup_alv_grid.modifyCell(row_idx, "KAYNAK_KALEM", min_kalem_no_for_color)
                
                # Değişikliğin SAP tarafından algılanması için gerekli adımlar
                popup_alv_grid.currentCellColumn = "KAYNAK_KALEM"
                popup_alv_grid.triggerModified()
                time.sleep(0.05) # Her hücre değişikliği arasında kısa bir bekleme, gerekirse ayarlanabilir

        logger.info("ZSD0010 Pop-up gridindeki 'KAYNAK_KALEM' sütunu başarıyla dolduruldu.")
        return True

    except Exception as e:
        logger.exception(f"ZSD0010 Pop-up gridindeki 'KAYNAK_KALEM' sütunu doldurulurken hata oluştu: {e}")
        return False
    
    
######### V.2 #########

def zsd0010_process_plm_items_v2(page: Page, plm_code_to_filter: str, expected_price: float, po_no: str, is_child: bool, order_type: str) -> dict | None:
    try:
        logger.info(_("LOG_ZSD0010_QUERY_PLM", plm_code=plm_code_to_filter, is_child=is_child, po_no=po_no))
        
        # 1. Filtrele
        plm_input_selector = "#application-Action-SD001-component---Main--smartFilterBar-filterItemControl_BASIC-IvPlmkodu-inner"
        # --- TEMİZLEME ADIMI (Garantili Yöntem) ---
        page.click(plm_input_selector) # Önce odağı al
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        time.sleep(0.5) # Kısa bir bekleme
        page.fill(plm_input_selector, str(plm_code_to_filter))
        page.press(plm_input_selector, "Enter")
        time.sleep(4)

        # 2. Ana Satırları Bul (tr.sapMListTblRow sınıfı ana satırlardır)
        table_body = page.locator("#__table0-tblBody")
        primary_rows = table_body.locator("tr.sapMListTblRow")
        try:
            # Satırların görünür olmasını kısa bir süre bekle
            primary_rows.first.wait_for(state="visible", timeout=5000)
            # İlk satırın metnine bak
            first_row_text = primary_rows.first.inner_text().strip()            
            # Eğer satır metni "No data" veya "Veri bulunamadı" içeriyorsa row_count'u 0 say
            if "No data" in first_row_text or "değil" in first_row_text or not first_row_text:
                row_count = 0
            else:
                row_count = primary_rows.count()
        except:
            row_count = 0

        if row_count == 0:
            # KULLANICIYA ANLAMLI HATA MESAJI
            error_msg = _("LOG_ZSD0010_NO_OFFER_ERR", plm_code=plm_code_to_filter)
            logger.error(error_msg)
            # Bu hatayı yukarıdaki fonksiyonlara iletmek için özel bir Exception fırlatabiliriz
            raise Exception(error_msg)
        
        for i in range(primary_rows.count()):
            primary_row = primary_rows.nth(i)
            primary_id = primary_row.get_attribute("id") # Örn: __item7-__clone0
            sub_row_id = f"{primary_id}-sub" # Eşleşen alt satır: __item7-__clone0-sub
            sub_row = table_body.locator(f"#{sub_row_id}")

            # --- VERİ ÇEKME (SUB-ROW'DAN) ---
            # Açıklama / Not (PO Numarası buradadır)
            po_element = sub_row.locator("div.sapMListTblSubCntRow").filter(has_text="Açıklama / Not").locator(".sapMText")
            desc_text = po_element.text_content().strip() if po_element.count() > 0 else ""


            # --- VERİ ÇEKME (PRIMARY-ROW'DAN) ---
            # Fiyat
            price_selector = "td[data-sap-ui-column*='SatisFiyati'] span.sapMText"
            price_text = primary_row.locator(price_selector).text_content().strip()
            extracted_price = float(price_text.replace('.', '').replace(',', '.'))
            
            # --- DURUM VE FİYAT BİLGİLERİ (ANA SATIR / ROW'DAN) ---
            # Senin verdiğin Onay Durum selectorı
            approval_status = primary_row.locator("span[id^='__status0-'][id$='-text']").text_content().strip()
            # Senin verdiğin PLM Durum selectorı
            plm_status = primary_row.locator("span[id^='__status1-'][id$='-text']").text_content().strip()

            # --- EŞLEŞME KONTROLÜ ---
            po_match = str(po_no) in desc_text
            if primary_row.count() == 1 and po_match == False:
                po_match = True
            
            price_match = extracted_price == expected_price

            if po_match and (is_child or price_match):
                logger.info(_("LOG_ZSD0010_MATCH_FOUND", primary_id=primary_id))
                
                # Navigasyon (Primary row üzerindeki ok işareti)
                primary_row.locator("span[id$='-imgNav']").click()
                time.sleep(1)
                # --- JS İLE DOĞRULAMA VE VERİ ÇEKME DÖNGÜSÜ ---
                # Fiori veriyi getirene kadar kısa bir döngü ile JS sorgusu atıyoruz
                bid_no = ""
                plm_check = ""
                
                for attempt in range(15): # Maksimum 7.5 saniye (15 * 0.5s)
                    # Tarayıcı içinde JS çalıştırıp canlı değerleri alıyoruz
                    result = page.evaluate("""() => {
                        const plmEl = document.getElementById("application-Action-SD001-component---Detail--inpPlmCode-inner");
                        const bidEl = document.getElementById("application-Action-SD001-component---Detail--inpStandardBid-inner");
                        return {
                            current_plm: plmEl ? plmEl.value : "",
                            current_bid: bidEl ? bidEl.value : ""
                        };
                    }""")
                    
                    plm_check = result['current_plm']
                    bid_no = result['current_bid']       
                    # Eğer ekrandaki PLM kodu bizim aradığımız kod ise ve Bid No boş değilse dur
                    if plm_check == str(plm_code_to_filter) and bid_no != "":
                        logger.info(_("LOG_ZSD0010_JS_SUCCESS", plm_check=plm_check, bid_no=bid_no))
                        break
                    
                    time.sleep(0.5) # Yarım saniye bekle ve tekrar sor      
                # Döngü bittiğinde hala yanlış veri varsa uyar
                if plm_check != str(plm_code_to_filter):
                    logger.warning(_("LOG_ZSD0010_PLM_MISMATCH", plm_check=plm_check, expected=plm_code_to_filter))   

                print(f"Bid no: {bid_no}")
                # Organizasyonel Veriler
                # Değişkenleri varsayılan olarak boş tanımlayalım
                sales_org, sales_office, sales_group = "", "", ""

                try:
                    # Butona tıkla
                    org_btn = page.locator("#__button13").filter(visible=True).first
                    if org_btn.count() > 0:
                        org_btn.click(force=True)
                        time.sleep(2) # Pop-up'ın açılması için kısa bir es

                        # Alanların gelip gelmediğini kontrol et (Kısa timeout: 5sn)
                        sales_org_el = page.locator("input[id*='inpSalesOrg']").first
                        
                        if sales_org_el.is_visible(timeout=5000):
                            # Eğer alan görünürse verileri çek
                            sales_org = sales_org_el.get_attribute("value") or ""
                            sales_office = page.locator("input[id*='inpSalesOffice']").first.get_attribute("value") or ""
                            sales_group = page.locator("input[id*='inpSalesGroup']").first.get_attribute("value") or ""
                            logger.info(_("LOG_ZSD0010_ORG_FETCHED", sales_org=sales_org))
                            
                        # --- POP-UP KAPATMA (Tamam / ID / ESC) ---
                        logger.info(_("LOG_ZSD0010_POPUP_CLOSE_TRY"))
                        # Selector tanımları
                        ok_by_text = page.locator("button").filter(has_text="Tamam").filter(visible=True).first
                        ok_by_id = page.locator("button[id^='__mbox-btn-']").filter(visible=True).first
                        try:
                            # 1. Önce 'Tamam' metni olan butona bak
                            if ok_by_text.count() > 0:
                                ok_by_text.click(force=True)
                                logger.info(_("LOG_ZSD0010_POPUP_CLOSED_OK"))
                            # 2. Yoksa senin verdiğin ID kalıbına (__mbox-btn-0 vb.) bak
                            elif ok_by_id.count() > 0:
                                ok_by_id.click(force=True)
                                logger.info(_("LOG_ZSD0010_POPUP_CLOSED_ID", id=ok_by_id.get_attribute('id')))
                            # 3. Hiçbiri yoksa Klavyeden ESC tuşuna bas
                            else:
                                logger.warning(_("LOG_ZSD0010_POPUP_ESC"))
                                page.keyboard.press("Escape")
                                time.sleep(1) # Pencerenin kapanması için kısa süre bekle
                        except Exception as e_btn:
                            logger.error(_("LOG_ZSD0010_POPUP_CLOSE_ERR", error=str(e_btn)))
                            # Son çare yine ESC denenebilir
                            page.keyboard.press("Escape")
                        time.sleep(1) # İşlemin oturması için bekle                        
                        
                    else:
                        logger.warning(_("LOG_ZSD0010_ORG_BTN_NOT_FOUND"))

                except Exception as e_org:
                    logger.warning(_("LOG_ZSD0010_ORG_FETCH_FAIL", error=str(e_org)))
                    # Her ihtimale karşı ESC basarak ekranı temizle
                    page.keyboard.press("Escape")

                time.sleep(1) # İşlemin oturması için bekle
                collected_data = {
                    'standard_bid_number': bid_no,
                    'sales_organization': sales_org,
                    'sales_office': sales_office,
                    'sales_group': sales_group,
                    'price': price_text
                }

                # ONAY VE PLM GÖNDER (Orijinal Çift Pop-up Mantığı)
                is_approved = str(approval_status).strip().lower() in ["onaylandı", "approved", "completed"]
                is_pending = str(plm_status).strip().lower() in ["beklemede", "pending"]
                if not (is_approved and not is_pending):
                    # PLM Gönder
                    if page.locator("#__button6").is_visible():
                        page.click("#__button6")
                        for _ in range(2):
                            btn = "span[id^='__mbox-btn-'][id$='-inner']"
                            page.wait_for_selector(btn, timeout=10000)
                            page.click(btn)
                            time.sleep(2)
                    
                    # Müşteri Onayı
                    if page.locator("#__button2").is_visible():
                        page.click("#__button2")
                        for _ in range(2):
                            btn = "span[id^='__mbox-btn-'][id$='-inner']"
                            page.wait_for_selector(btn, timeout=10000)
                            page.click(btn)
                            time.sleep(2)
               
                # --- ANA SAYFAYA DÖN (Garantili Yöntem) ---
                logger.info(_("LOG_ZSD0010_NAV_BACK"))
                
                # Senin HTML yapına uygun selectorlar:
                # 1. #backBtn (Senin paylaştığın ID)
                # 2. a[title='Geriye'] (Senin paylaştığın başlık)
                # 3. .sapUshellShellHeadItm (CSS Class)
                back_selector = "#backBtn, a[title='Geriye'], .sapUshellShellHeadItm"

                try:
                    # Butonun görünür ve tıklanabilir olmasını bekle
                    back_btn = page.locator(back_selector).first
                    back_btn.wait_for(state="visible", timeout=15000)
                    
                    # Bazı durumlarda click() yerine force=True gerekebilir (overlay varsa)
                    back_btn.click(force=True)
                    logger.info(_("LOG_ZSD0010_BACK_CLICKED"))
                    
                except Exception as e_back:
                    logger.warning(_("LOG_ZSD0010_BACK_ERR", error=str(e_back)))
                    page.go_back()
                
                if order_type == "set": 
                    try:
                        logger.info(_("LOG_ZSD0010_WAIT_NEXT_PLM"))
                        page.wait_for_load_state("networkidle")
                        page.wait_for_selector(plm_input_selector, timeout=20000)
                        time.sleep(2) # Kısa bir es
                    except Exception as e:
                        # Hata alsa bile 'return True' diyeceği için akış bozulmaz
                        logger.warning(_("LOG_ZSD0010_NEXT_FIELD_NOT_READY", error=str(e)))
                
                return collected_data              
                

        return None
    except Exception as e:
        logger.exception(_("LOG_ZSD0010_FIORI_ERR", error=str(e)))
        return None
 
def safe_press_grid_button(grid, button_id, description):
    try:
        # Butona basmayı dene
        grid.pressToolbarButton(button_id)
        logger.info(_("LOG_ZSD0010_BTN_PRESSED", desc=description, btn_id=button_id))
        time.sleep(1.5) # İşlem için SAP'ye zaman ver
        return True
    except Exception:
        # Buton yoksa veya o an basılamıyorsa buraya düşer
        logger.warning(_("LOG_ZSD0010_BTN_INACTIVE", desc=description, btn_id=button_id))
        return False   

def _handle_set_bom_size_sub_grid(session, data, fiori_map):
    """
    wnd[2] üzerinde açılan alt griddeki her bir child ürünü (SATNR) 
    PLM eşleşmesiyle bulur ve Teklif No/Fiyat bilgilerini girer.
    """
    try:
        # Alt Grid (wnd[2]) nesnesi
        child_grid = session.findById("wnd[2]/usr/cntlGRID1/shellcont/shell")
        childrens = data.get('childrens', [])

        for r in range(child_grid.RowCount):
            # SATNR (Malzeme No) al
            sap_mat = str(child_grid.GetCellValue(r, "SATNR")).strip()
            logger.info(_("LOG_ZSD0010_SUBGRID_ROW", row=r, mat=sap_mat))
            
            # JSON'dan bu Malzeme No'ya ait PLM'i bul
            target_plm = None
            for c in childrens:
                if str(c.get('sap_material_code')) == sap_mat:
                    target_plm = str(c.get('plm_code'))
                    break
            
            # Fiori'den topladığımız verileri bas
            if target_plm and target_plm in fiori_map:
                bid = fiori_map[target_plm]['standard_bid_number']
                price = fiori_map[target_plm]['price']
                logger.info(_("LOG_ZSD0010_SUBGRID_DATA", row=r, plm=target_plm, bid=bid, price=price))
                try:
                    child_grid.firstVisibleColumn = "COLOR"
                    time.sleep(0.2)
                    child_grid.modifyCell(r, "VBELN", bid)
                    time.sleep(0.2)
                    child_grid.modifyCell(r, "FIYAT", price)
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.error(_("LOG_ZSD0010_SUBGRID_ERR", row=r, plm=target_plm, bid=bid, price=price, error=str(e)))
                

        # Bilgileri girince Enter'a bas (SAP doğrulasın)
        child_grid.pressEnter()
        time.sleep(0.5)
        try:
            sub_grid = session.findById("wnd[2]/usr/cntlGRID1/shellcont/shell")
            
            # 1. &ETA (Hesapla/Dağıt) Butonuna Bas
            logger.info(_("LOG_ZSD0010_CHECK_ETA"))
            safe_press_grid_button(sub_grid, "&ETA", "Hesapla/Dağıt")
            
            # 2. &CHECK (Kontrol Et) Butonuna Bas
            logger.info(_("LOG_ZSD0010_CHECK_CHECK"))
            safe_press_grid_button(sub_grid, "&CHECK", "Kontrol Et")

            # 3. STATUS BAR KONTROLÜ
            # Not: SAP'de pop-up (wnd[2]) açık olsa bile hata mesajları ana pencerenin (wnd[0]) sbar'ına düşer.
            sbar = session.findById("wnd[0]/sbar")
            msg_type = sbar.messageType # 'E' (Hata), 'W' (Uyarı), 'S' (Başarı)
            msg_text = sbar.text

            if msg_type == "E":
                # Eğer Status Bar'da bir hata ("E") varsa işlemi durdur ve hata fırlat
                logger.error(_("LOG_ZSD0010_SUBGRID_MSG_ERR", msg=msg_text))
                # Hata anında ekran görüntüsü (Opsiyonel)
                # page.screenshot(path="alt_grid_error.png") 
                raise Exception(f"SAP Alt Grid Doğrulama Hatası: {msg_text}")
            
            elif msg_type == "W":
                # Uyarı ("W") varsa logla ama devam et (veya duruma göre raise et)
                logger.warning(_("LOG_ZSD0010_SUBGRID_MSG_WARN", msg=msg_text))
            
            else:
                logger.info(_("LOG_ZSD0010_SUBGRID_MSG_SUCCESS", msg=msg_text))

            # 4. Her şey yolundaysa alt gridi onayla/kapat
            session.findById("wnd[2]/tbar[0]/btn[0]").press() # Tamam (Enter)
            logger.info(_("LOG_ZSD0010_BTN0_PRESSED"))
            time.sleep(1)

        except Exception as e:
            if "SAP Alt Grid Doğrulama Hatası" in str(e):
                raise
            logger.error(_("LOG_ZSD0010_SUBGRID_VAL_ERR", error=str(e)))
            raise Exception(f"Alt grid doğrulama başarısız: {e}")
        
    except Exception as e:
       
        raise Exception(f"Alt grid (wnd[2]) işlenirken hata: {e}")
        
def zsd0010_process_order_integration_gui_v2(session, data, collected_data) -> bool:
    """
    ZSD0010 Sipariş Entegrasyon Kokpiti (SAP GUI).
    Hem Single hem Set siparişleri destekler.
    """
    po_number = str(data.get('po_no'))
    is_set = data.get('orderType') == 'set'
    
    # Veriyi Normalize Et: Single ise sözlüğü PLM anahtarıyla sar, Set ise zaten öyledir.
    if not is_set:
        main_plm = str(data.get('plm_code'))
        fiori_map = {main_plm: collected_data}
    else:
        fiori_map = collected_data # Set durumunda zaten {plm: {data}} formatında
    values_list = list(fiori_map.values())
    # İlk geçerli veriyi genel Sales Office/Group bilgileri için al
    first_val = values_list[0]
    second_val = values_list[1] if len(values_list) > 1 else first_val
    
    try:
        logger.info(_("LOG_ZSD0010_GUI_START", po=po_number, order_type=data.get('orderType')))
        session.startTransaction("ZSD0010")

        # 1. Başlangıç Ekranı Filtreleri
        session.findById("wnd[0]/usr/radP_ALL").select()
        session.findById("wnd[0]/usr/txtS_BSTNK-LOW").text = po_number
        session.findById("wnd[0]/tbar[1]/btn[8]").press() # Yürüt (F8)
        time.sleep(2)

        # 2. ALV Grid Seçimi
        alv_grid = session.findById("wnd[0]/usr/cntlSCR_CONT/shellcont/shell")
        if alv_grid.RowCount == 0:
            logger.error(_("LOG_ZSD0010_PO_NOT_FOUND", po=po_number))
            return False

        alv_grid.currentCellRow = 0
        alv_grid.currentCellColumn = "XFELD"
        alv_grid.clickCurrentCell()
        alv_grid.pressToolbarButton("RUN_POPUP")
        time.sleep(2)

        # 3. Pop-up (wnd[1]) Üst Bilgiler
        if not is_set:
            session.findById("wnd[1]/usr/ctxtZSD_003_S_POPUP_HEADER-SATIS_BUROSU").text = first_val['sales_office']
            session.findById("wnd[1]/usr/ctxtZSD_003_S_POPUP_HEADER-SATIS_GRUBU").text = first_val['sales_group']
        else:
            session.findById("wnd[1]/usr/ctxtZSD_003_S_POPUP_HEADER-SATIS_BUROSU").text = second_val['sales_office']
            session.findById("wnd[1]/usr/ctxtZSD_003_S_POPUP_HEADER-SATIS_GRUBU").text = second_val['sales_group']
        session.findById("wnd[1]/usr/ctxtZSD_003_S_POPUP_HEADER-TEKLIF_NO").text = first_val['standard_bid_number']
        
        # Enter ve olası uyarı pop-up'larını (wnd[2]) geç
        session.findById("wnd[1]").sendVKey(0) 
        time.sleep(1)
        try:
            if session.Children.Count > 2: # Eğer wnd[2] açıldıysa (bilgi mesajı)
                session.findById("wnd[2]/tbar[0]/btn[0]").press()
                time.sleep(0.5)
        except: pass

        # 4. Kaynak Kalem İşlemi (Helper Fonksiyon)
        _fill_kaynak_kalem_in_popup_grid(session)

        # 5. --- SET SİPARİŞİ ÖZEL ADIMI (BOM_SIZE_BTN DÖNGÜSÜ) ---
        if is_set:
            logger.info(_("LOG_ZSD0010_SET_BOM_SIZE_START"))
            
            popup_grid = session.findById("wnd[1]/usr/cntlSCR_CONT/shellcont/shell")
            row_count = popup_grid.RowCount

            # wnd[1] üzerindeki her bir satır için döngü başlatıyoruz
            for i in range(row_count):
                logger.info(_("LOG_ZSD0010_POPUP_ROW_PROCESSING", current=i+1, total=row_count))
                
                # İlgili satıra odaklan ve BOM_SIZE butonuna bas
                popup_grid.currentCellRow = i
                popup_grid.currentCellColumn = "BOM_SIZE_BTN"
                
                # Butona bas (Bu işlem wnd[2] alt gridini açar)
                try:
                    time.sleep(2)
                    popup_grid.pressButtonCurrentCell()
                    time.sleep(2)
                    
                    # Alt Gridi (wnd[2]) dolduran yardımcı fonksiyonu çağır
                    # Bu fonksiyon wnd[2]'yi doldurup kapatacak (btn[0] ile)
                    _handle_set_bom_size_sub_grid(session, data, fiori_map)
                    
                    logger.info(_("LOG_ZSD0010_ROW_SUBGRID_DONE", row=i))
                except Exception as e_row:
                    logger.warning(_("LOG_ZSD0010_BOM_SIZE_BTN_ERR", row=i, error=str(e_row)))
                    continue
                
        # 6. Final Kayıt (Pop-up üzerindeki Onay butonu)
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
        time.sleep(1)
        

                # --- FINAL ONAY POP-UP (wnd[2]) İŞLEME ---
        try:
            # 1. wnd[2] penceresinin varlığını kontrol et (Hata fırlatmadan kontrol et)
            popup_wnd = session.findById("wnd[2]", False) 
            
            if popup_wnd:
                # 2. Pop-up içindeki metni oku
                # SAP standart mesaj kutularında metin genellikle 'usr/txtS_POPUP-TEXT' içindedir.
                # Eğer bulunamazsa pencerenin genel başlığını/metnini alalım.
                try:
                    msg_text = popup_wnd.findById("usr/txtS_POPUP-TEXT").text
                except:
                    msg_text = popup_wnd.Text # Fallback: Pencere başlığı veya genel text

                logger.info(_("LOG_ZSD0010_POPUP_MSG", msg=msg_text))

                # 3. Hata Kelimeleri Kontrolü
                # Mesajda hata belirten kritik kelimeler geçiyorsa durdur ve hata fırlat
                error_keywords = ["hata", "error", "başarısız", "eksik", "uygun değil", "bulunamadı", "yetki"]
                if any(key in msg_text.lower() for key in error_keywords):
                    logger.error(_("LOG_ZSD0010_SAP_INTEG_ERR", msg=msg_text))
                    raise Exception(f"SAP Entegrasyon Hatası: {msg_text}")

                # 4. Onay İşlemi (Eğer mesaj bir soruysa: '... oluşturulsun mu?')
                # btnBUTTON_1 genellikle 'Evet' (Yes) butonudur.
                logger.info(_("LOG_ZSD0010_POPUP_CONFIRM"))
                popup_wnd.findById("usr/btnBUTTON_1").press()
                time.sleep(1)

                # 5. İkinci bir Bilgi Pop-up'ı (wnd[2]) gelirse (Örn: "Sipariş X numarasıyla oluşturuldu")
                try:
                    # Yeni wnd[2] gelmiş mi kontrol et
                    info_popup = session.findById("wnd[2]", False)
                    if info_popup:
                        final_msg = info_popup.findById("usr/txtS_POPUP-TEXT", False).text if info_popup.findById("usr/txtS_POPUP-TEXT", False) else info_popup.Text
                        logger.info(_("LOG_ZSD0010_FINAL_INFO", msg=final_msg))
                        # Tamam (btn[0]) butonuna basarak kapat
                        if info_popup.findById("tbar[0]/btn[0]", False): 
                            info_popup.findById("tbar[0]/btn[0]").press()
                except:
                    pass # Bilgi pop-up'ı gelmezse sorun değil
            else:
                # Eğer hiç pop-up çıkmadıysa, bazen alttaki status bar'da hata yazıyor olabilir
                status_text = session.findById("wnd[0]/sbar").text
                if session.findById("wnd[0]/sbar").messageType == "E": # 'E' = Error
                    raise Exception(f"SAP Status Bar Hatası: {status_text}")
                
                logger.warning(_("LOG_ZSD0010_NO_CONFIRM_POPUP"))
                time.sleep(1) # Kısa bir bekleme, SAP'nin durumu güncellemesi için
            return True
        
        except Exception as e:
            if "SAP Entegrasyon Hatası" in str(e) or "Status Bar Hatası" in str(e):
                raise # Kendi fırlattığımız hatayı yukarı ilet
            logger.error(_("LOG_ZSD0010_POPUP_UNEXPECTED_ERR", error=str(e)))
            raise Exception(f"ZSD0010 Pop-up aşamasında hata: {e}")

    except Exception as e:
        logger.error(_("LOG_ZSD0010_GUI_ERR", error=str(e)), exc_info=True)
        return False

