import os
import re
import sys
import time
import json
import threading
import subprocess
import tempfile
import webbrowser
import zipfile
import requests
import customtkinter as ctk
from tkinter import filedialog, messagebox
from src.util.config_manager import ConfigManager, APP_VERSION
from src.util.localizer import _

def parse_version(v_str):
    """'1.0.1' gibi metin versiyonlarını karşılaştırılabilir tuple'a çevirir."""
    try:
        match = re.search(r'(\d+(?:\.\d+)+)', str(v_str))
        if match:
            return tuple(map(int, match.group(1).split('.')))
        clean_v = str(v_str).lstrip('\ufeffvV').strip()
        return tuple(map(int, clean_v.split('.')))
    except Exception:
        return (0, 0, 0)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class UpdateManager:
    @staticmethod
    def open_onedrive_download_page():
        """Kurumsal OneDrive indirme sayfasını varsayılan tarayıcıda açar."""
        url = ConfigManager.get_setting("ONEDRIVE_UPDATE_URL")
        if url:
            webbrowser.open(url)

    @staticmethod
    def install_local_zip_package(app=None):
        """Kullanıcının seçtiği indirilen ZIP paketini 3 kademeli doğrulamadan geçirip updater.bat ile kurar."""
        zip_path = filedialog.askopenfilename(
            title=_("SELECT_ZIP_TITLE"),
            filetypes=[("Zip Paketleri", "*.zip"), ("Tüm Dosyalar", "*.*")]
        )
        if not zip_path:
            return

        # 1. Aşama: Dosya var mı?
        if not os.path.exists(zip_path):
            messagebox.showerror(_("INVALID_ZIP_ERR").split("!")[0], _("INVALID_ZIP_ERR"))
            return

        # 2. Aşama: Geçerli bir ZIP arşivi mi?
        if not zipfile.is_zipfile(zip_path):
            messagebox.showerror(_("INVALID_ZIP_ERR").split("!")[0], _("INVALID_ZIP_ERR"))
            return

        # 3. Aşama: İçerik Doğrulama (LCW_SAP_Automation uygulamasını içeriyor mu?)
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                members = z.namelist()
                valid_signatures = ["LCW_SAP_Automation.exe", "main.py", "main_gui.py", "src/"]
                has_app = any(sig in member or member.startswith("src/") for member in members for sig in valid_signatures)
                if not has_app:
                    messagebox.showerror(_("INVALID_ZIP_ERR").split("!")[0], _("INVALID_ZIP_ERR"))
                    return
        except Exception:
            messagebox.showerror(_("INVALID_ZIP_ERR").split("!")[0], _("INVALID_ZIP_ERR"))
            return

        filename = os.path.basename(zip_path)
        confirm = messagebox.askyesno(
            _("SELECT_ZIP_TITLE"),
            _("ZIP_INSTALL_CONFIRM", filename=filename)
        )
        if not confirm:
            return

        updater_bat = resource_path(os.path.join("assets", "updater.bat"))
        if getattr(sys, 'frozen', False):
            target_dir = os.path.dirname(sys.executable)
        else:
            target_dir = os.path.abspath(".")

        if os.path.exists(updater_bat):
            subprocess.Popen(['cmd.exe', '/c', updater_bat, zip_path, target_dir], creationflags=subprocess.CREATE_NO_WINDOW)
            if app:
                app.destroy()
        else:
            messagebox.showerror(_("INVALID_ZIP_ERR").split("!")[0], _("UPDATE_SCRIPT_NOT_FOUND"))

    @staticmethod
    def _show_network_error_dialog(app):
        """Ağ engeli nedeniyle otomatik indirme başarısız olduğunda Ayarlar sayfasına yönlendiren diyalog."""
        dialog = ctk.CTkToplevel(app)
        dialog.title(_("NETWORK_ERR_REDIRECT_TITLE"))
        dialog.geometry("460x250")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        dialog.update_idletasks()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = max(0, (sw - 460) // 2)
        y = max(0, (sh - 250) // 2)
        dialog.geometry(f"460x250+{x}+{y}")
        dialog.lift()
        dialog.focus_force()

        lbl_title = ctk.CTkLabel(
            dialog,
            text=_("NETWORK_ERR_REDIRECT_TITLE"),
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#eab308"
        )
        lbl_title.pack(padx=20, pady=(20, 10))

        lbl_msg = ctk.CTkLabel(
            dialog,
            text=_("NETWORK_ERR_REDIRECT_MSG"),
            font=ctk.CTkFont(size=12),
            wraplength=420,
            justify="center"
        )
        lbl_msg.pack(padx=20, pady=(0, 15))

        def go_settings():
            dialog.destroy()
            if hasattr(app, 'show_settings'):
                app.show_settings()
            UpdateManager.open_onedrive_download_page()

        btn_go = ctk.CTkButton(
            dialog,
            text=_("GO_TO_SETTINGS_BTN"),
            command=go_settings,
            fg_color="#0284c7", hover_color="#0369a1",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38
        )
        btn_go.pack(pady=10)

    @staticmethod
    def check_for_updates_async(app):
        """Arka planda (Thread) versiyon kontrolünü başlatır."""
        if not ConfigManager.get_setting("AUTO_UPDATE_ENABLED"):
            return
            
        thread = threading.Thread(target=UpdateManager._check_worker, args=(app,), daemon=True)
        thread.start()

    @staticmethod
    def _check_worker(app):
        # 1. ÖNCELİKLİ KONTROL: Şirket içi Ortak Klasördeki (UNC Path) versiyon dosyası
        shared_path = ConfigManager.get_setting("SHARED_VERSION_PATH")
        if shared_path and os.path.exists(shared_path):
            try:
                with open(shared_path, "r", encoding="utf-8-sig") as f:
                    content = f.read().strip()
                
                # 'APP_VERSION = "1.0.2"' veya direkt '1.0.2' formatını ayrıştır
                match = re.search(r'(\d+(?:\.\d+)+)', content)
                if match:
                    remote_version_str = match.group(1)
                elif "=" in content:
                    remote_version_str = content.split("=")[-1].strip().strip('"\'')
                else:
                    remote_version_str = content.strip()

                remote_v = parse_version(remote_version_str)
                local_v = parse_version(APP_VERSION)

                if remote_v > local_v:
                    github_release_url = f"https://github.com/AlptugKizilay/lcw_sap_automation/releases/download/v{remote_version_str}/LCW_SAP_Automation_v{remote_version_str}.zip"
                    data = {
                        "version": remote_version_str,
                        "changelog": f"Ortak klasör üzerinden yeni güncelleme yayınlandı (v{remote_version_str}).",
                        "download_url": github_release_url
                    }
                    app.after(0, lambda: UpdateManager._show_update_dialog(app, data))
                    return
            except Exception as e:
                print(f"[UpdateManager] Ortak klasör (UNC) okuma hatası: {e}")

        # 2. İKİNCİL KONTROL (Fallback): GitHub Gist
        url = ConfigManager.get_setting("UPDATE_CHECK_URL")
        if not url:
            return

        try:
            sep = "&" if "?" in url else "?"
            bust_url = f"{url}{sep}t={int(time.time())}"
            response = requests.get(
                bust_url,
                timeout=5,
                headers={
                    "User-Agent": "LCW_SAP_Automation_App",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                },
            )
            if response.status_code == 200:
                data = response.json()
                remote_version_str = data.get("version", "0.0.0")
                
                remote_v = parse_version(remote_version_str)
                local_v = parse_version(APP_VERSION)

                if remote_v > local_v:
                    # GUI thread'inde onay penceresini aç
                    app.after(0, lambda: UpdateManager._show_update_dialog(app, data))
            else:
                print(f"[UpdateManager] Güncelleme sunucusu HTTP {response.status_code} döndürdü. (Erişim engeli veya gizli repo olabilir)")
        except Exception as e:
            # Ağ kısıtlaması (Mısır / Gist engeli) olan lokasyonlarda sessizce yakala
            print(f"[UpdateManager] Otomatik güncelleme kontrolü atlandı (Ağ/Erişim Engeli): {e}")

    @staticmethod
    def _show_update_dialog(app, update_data):
        remote_version = update_data.get("version", "Bilinmiyor")
        changelog = update_data.get("changelog", "Yeni geliştirmeler ve performans iyileştirmeleri.")
        download_url = update_data.get("download_url", "")

        dialog = ctk.CTkToplevel(app)
        dialog.title(_("UPDATE_DIALOG_TITLE"))
        dialog.geometry("460x320")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        # Pencereyi ekranın ortasına güvenli biçimde hizala
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = max(0, (screen_width - 460) // 2)
        y = max(0, (screen_height - 320) // 2)
        dialog.geometry(f"460x320+{x}+{y}")
        dialog.lift()
        dialog.focus_force()

        title_label = ctk.CTkLabel(
            dialog, 
            text=_("UPDATE_NEW_VERSION_AVAIL", version=remote_version), 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(padx=20, pady=(15, 3))

        current_label = ctk.CTkLabel(
            dialog, 
            text=_("UPDATE_CURRENT_VERSION", version=APP_VERSION), 
            font=ctk.CTkFont(size=12), text_color="gray"
        )
        current_label.pack(padx=20, pady=(0, 8))

        textbox = ctk.CTkTextbox(dialog, width=420, height=90)
        textbox.pack(padx=20, pady=5)
        textbox.insert("1.0", f"{_('UPDATE_CHANGELOG_HEADER')}\n{changelog}")
        textbox.configure(state="disabled")

        notice_label = ctk.CTkLabel(
            dialog,
            text=_("UPDATE_AUTO_RELAUNCH_NOTICE"),
            font=ctk.CTkFont(size=11, weight="normal"),
            text_color="#2563eb",
            wraplength=420,
            justify="left"
        )
        notice_label.pack(padx=20, pady=(6, 4))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(5, 10), fill="x")

        def start_update():
            dialog.destroy()
            if download_url:
                UpdateManager._download_and_install(app, download_url)
            else:
                UpdateManager.open_onedrive_download_page()
                UpdateManager.install_local_zip_package(app)

        update_btn = ctk.CTkButton(
            btn_frame, text=_("UPDATE_NOW_BTN"), command=start_update, 
            fg_color="#2563eb", hover_color="#1d4ed8"
        )
        update_btn.pack(side="right", padx=5)

        later_btn = ctk.CTkButton(
            btn_frame, text=_("UPDATE_LATER_BTN"), command=dialog.destroy, 
            fg_color="transparent", border_width=1, border_color="gray"
        )
        later_btn.pack(side="right", padx=5)

    @staticmethod
    def _download_and_install(app, download_url):
        if not download_url:
            UpdateManager.open_onedrive_download_page()
            UpdateManager.install_local_zip_package(app)
            return

        progress_dialog = ctk.CTkToplevel(app)
        progress_dialog.title(_("UPDATING_TITLE"))
        progress_dialog.geometry("400x150")
        progress_dialog.resizable(False, False)
        progress_dialog.attributes("-topmost", True)

        # Pencereyi ekranın ortasına hizala
        progress_dialog.update_idletasks()
        sw = progress_dialog.winfo_screenwidth()
        sh = progress_dialog.winfo_screenheight()
        px = max(0, (sw - 400) // 2)
        py = max(0, (sh - 150) // 2)
        progress_dialog.geometry(f"400x150+{px}+{py}")

        progress_label = ctk.CTkLabel(
            progress_dialog, 
            text=_("UPDATE_DOWNLOADING_MSG"), 
            font=ctk.CTkFont(size=12),
            wraplength=360,
            justify="center"
        )
        progress_label.pack(padx=20, pady=(15, 10))

        progressbar = ctk.CTkProgressBar(progress_dialog, width=340)
        progressbar.pack(padx=20, pady=5)
        progressbar.set(0)

        def download_worker():
            try:
                temp_dir = tempfile.gettempdir()
                zip_path = os.path.join(temp_dir, "lcw_update.zip")

                res = requests.get(download_url, stream=True, timeout=10)
                total_length = int(res.headers.get('content-length', 0))

                downloaded = 0
                with open(zip_path, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_length > 0:
                                percent = downloaded / total_length
                                progress_dialog.after(0, lambda p=percent: progressbar.set(p))

                # İndirilen dosyanın geçerli bir ZIP olduğunu doğrula
                if not zipfile.is_zipfile(zip_path):
                    raise ValueError(f"İndirilen dosya geçerli bir ZIP arşivi değil: {download_url}")

                updater_bat = resource_path(os.path.join("assets", "updater.bat"))
                
                if getattr(sys, 'frozen', False):
                    target_dir = os.path.dirname(sys.executable)
                else:
                    target_dir = os.path.abspath(".")

                if os.path.exists(updater_bat) and os.path.exists(zip_path):
                    subprocess.Popen(['cmd.exe', '/c', updater_bat, zip_path, target_dir], creationflags=subprocess.CREATE_NO_WINDOW)
                    progress_dialog.after(0, lambda: app.destroy())
                else:
                    progress_dialog.after(0, lambda: progress_label.configure(text=_("UPDATE_SCRIPT_NOT_FOUND")))
            except Exception as e:
                # İndirme başarısız (Ağ Kısıtlaması / Mısır ofisi vb.) -> Ayarlar sayfasına yönlendir!
                print(f"[UpdateManager] Otomatik indirme hatası (Ağ kısıtlaması): {e}")
                progress_dialog.after(0, lambda: progress_dialog.destroy())
                if app:
                    app.after(0, lambda: UpdateManager._show_network_error_dialog(app))

        threading.Thread(target=download_worker, daemon=True).start()

