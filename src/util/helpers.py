# Örnek Kullanım:
import os
import sys

def get_resource_path(relative_path):
    """PyInstaller paketli dosya içindeki yolu bulur."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# TAM YOL: browsers/chromium-1200/chrome-win/chrome.exe
#chrome_exe = get_resource_path(os.path.join("browsers", "chromium-1200", "chrome-win", "chrome.exe"))

# Playwright Başlatma:
# browser = p.chromium.launch(executable_path=chrome_exe, headless=True)