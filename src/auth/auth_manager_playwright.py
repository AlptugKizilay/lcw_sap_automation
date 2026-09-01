# src/auth/auth_manager_playwright.py

import asyncio
from playwright.async_api import async_playwright
import os
import logging
import time
import json
from dotenv import load_dotenv
from src.util.config_manager import ConfigManager
from src.util.helpers import get_resource_path

load_dotenv()
cfg = ConfigManager()
_cached_token = None
_token_expiry_time = 0

# --- Ayarlar ---
# BURAYI KENDİ LOGIN SAYFANIZIN GERÇEK URL'SİYLE GÜNCELLEYİN!
# Örneğin: "https://supplierportal.lcwaikiki.com/login" veya "https://sso.lcwaikiki.com/login"
LOGIN_URL = cfg.get_setting("LCW_LOGIN_URL") or os.getenv("LCW_LOGIN_URL", "https://supplierportal.lcwaikiki.com/home") # <-- Önceki çıktınızda bu vardı, doğrulayın!
XIR_URL = cfg.get_setting("XIR_URL") or os.getenv("XIR_URL", "https://tr.xir.lcwaikiki.com/") #
# Sizin verdiğiniz URL: https://pars.lcwaikiki.com/sts/issue/oidc/
TOKEN_API_ENDPOINT_PART = cfg.get_setting("LCW_TOKEN_API_ENDPOINT_PART") or os.getenv("LCW_TOKEN_API_ENDPOINT_PART", "/sts/issue/oidc/") 

# Kullanıcı adı, parola alanlarının ve login butonunun CSS selector'ları
USERNAME_SELECTOR = cfg.get_setting("LCW_USERNAME_SELECTOR") or os.getenv("LCW_USERNAME_SELECTOR", "#UserName") 
PASSWORD_SELECTOR = cfg.get_setting("LCW_PASSWORD_SELECTOR") or os.getenv("LCW_PASSWORD_SELECTOR", "#loginFieldPassword")
LOGIN_BUTTON_SELECTOR = cfg.get_setting("LCW_LOGIN_BUTTON_SELECTOR") or os.getenv("LCW_LOGIN_BUTTON_SELECTOR", "#loginBtn")
logger = logging.getLogger(__name__)
def clear_cached_token():
    global _cached_token, _token_expiry_time
    logger.info("Önbellekteki token temizleniyor (401 / Yetkisiz erişim veya zorunlu yenileme)...")
    _cached_token = None
    _token_expiry_time = 0

async def get_auth_token_playwright(username=None, password=None, force_refresh=False):
    global _cached_token, _token_expiry_time

    if force_refresh:
        clear_cached_token()
    elif _cached_token and _token_expiry_time > time.time() + 300: # 5 dakika tampon
        logger.info("Önbellekten geçerli token kullanılıyor (Playwright).")
        return _cached_token

    username = username or cfg.get_setting("LCW_PORTAL_USER") or os.getenv("LCW_USERNAME")
    password = password or cfg.get_password("LCW_PORTAL_PASS") or os.getenv("LCW_PASSWORD")

    if not username or not password:
        print("Hata: Kimlik doğrulama için kullanıcı adı ve parola sağlanmadı (ortam değişkenleri veya parametreler).")
        return None

    logger.info("Playwright ile token alınmaya çalışılıyor...")
    chrome_exe = get_resource_path(os.path.join("browsers", "chromium-1200", "chrome-win64", "chrome.exe"))
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chrome_exe, headless=True)
        page = await browser.new_page()

        captured_token = None

        def handle_request(request):
            nonlocal captured_token
            if captured_token:
                return
            try:
                headers = request.headers
                auth_header = headers.get("authorization") or headers.get("Authorization")
                if auth_header and "bearer" in auth_header.lower():
                    parts = auth_header.split()
                    if len(parts) >= 2:
                        possible_token = parts[1].strip()
                        if possible_token and possible_token.lower() not in ("undefined", "null", "none"):
                            captured_token = possible_token
                            logger.info(f"Token Authorization header'ından başarıyla yakalandı! (URL: {request.url[:80]}...)")
            except Exception:
                pass

        async def handle_response(response):
            nonlocal captured_token
            if captured_token:
                return
            try:
                url_lower = response.url.lower()
                if (TOKEN_API_ENDPOINT_PART in url_lower or "token" in url_lower or "shipmentrequest" in url_lower or "oidc" in url_lower) and response.status == 200:
                    content_type = response.headers.get("content-type", "")
                    if "json" in content_type:
                        data = await response.json()
                        if isinstance(data, dict):
                            tok = data.get("access_token") or data.get("token") or data.get("id_token")
                            if tok and str(tok).lower() not in ("undefined", "null", "none"):
                                captured_token = tok
                                logger.info(f"Token API yanıtından (JSON) başarıyla yakalandı! (URL: {response.url[:80]}...)")
            except Exception:
                pass

        # Ağ dinleyicilerini bağla
        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            print(f"Login sayfasına gidiliyor: {LOGIN_URL}")
            await page.goto(LOGIN_URL, wait_until='networkidle')

            print(f"Kullanıcı adı ({username}) dolduruluyor: {USERNAME_SELECTOR}")
            await page.fill(USERNAME_SELECTOR, username)
            print(f"Parola dolduruluyor: {PASSWORD_SELECTOR}")
            await page.fill(PASSWORD_SELECTOR, password)

            print(f"Login butonuna tıklanıyor: {LOGIN_BUTTON_SELECTOR}")
            await page.click(LOGIN_BUTTON_SELECTOR)

            # Token'ın yakalanması için esnek bekleme döngüsü (maksimum 45 saniye)
            start_wait = time.time()
            max_wait_seconds = 45

            while not captured_token and (time.time() - start_wait) < max_wait_seconds:
                await asyncio.sleep(0.5)

            if captured_token:
                _cached_token = captured_token
                _token_expiry_time = time.time() + 28800 # 8 saat önbellek
                logger.info("Token başarıyla alındı ve önbelleğe kaydedildi (Playwright).")
                return _cached_token

            print(f"Hata: {max_wait_seconds} saniye içinde token (Authorization Header veya JSON yanıtı) yakalanamadı.")
            await page.screenshot(path="error_screenshot_no_token_response.png")
            print("Hata ekran görüntüsü 'error_screenshot_no_token_response.png' olarak kaydedildi.")
            return None

        except Exception as e:
            print(f"Playwright ile token alma sırasında genel bir hata oluştu: {e}")
            try:
                await page.screenshot(path="error_screenshot_general.png")
                print("Hata ekran görüntüsü 'error_screenshot_general.png' olarak kaydedildi.")
            except Exception as se:
                print(f"Ekran görüntüsü alınırken hata oluştu: {se}")
            return None
        finally:
            await browser.close()
            print("Tarayıcı kapatıldı.")
            
async def get_xir(username=None, password=None):
    username = username or os.getenv("XIR_USERNAME")
    password = password or os.getenv("XIR_PASSWORD")
    chrome_exe = get_resource_path(os.path.join("browsers", "chromium-1200", "chrome-win64", "chrome.exe"))
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chrome_exe, headless=True)
        page = await browser.new_page()
        try:
                print(f"Login sayfasına gidiliyor: {XIR_URL}")
                await page.goto(XIR_URL, wait_until='networkidle')

                print(f"Kullanıcı adı ({username}) dolduruluyor: {USERNAME_SELECTOR}")
                await page.fill(USERNAME_SELECTOR, username)
                print(f"Parola dolduruluyor: {PASSWORD_SELECTOR}")
                await page.fill(PASSWORD_SELECTOR, password)

                print(f"Login butonuna tıklanıyor: {LOGIN_BUTTON_SELECTOR}")
                await page.click(LOGIN_BUTTON_SELECTOR)
                await page.wait_for_load_state('networkidle')
                return page
        except Exception as e:
            print(f"Playwright ile XIR alma sırasında genel bir hata oluştu: {e}")
            return None
        finally:
            await browser.close()
            print("Tarayıcı kapatıldı.")
    

def get_token_sync(username=None, password=None, force_refresh=False):
    return asyncio.run(get_auth_token_playwright(username, password, force_refresh=force_refresh))
def get_xir_sync(username=None, password=None):
    return asyncio.run(get_xir(username, password))


if __name__ == "__main__":
    print("--- Playwright Token Alma Testi ---")
    
    token = get_token_sync()
    
    if token:
        print(f"\nBaşarıyla Alınan Token: {token[:30]}...")
    else:
        print("\nToken alınamadı.")