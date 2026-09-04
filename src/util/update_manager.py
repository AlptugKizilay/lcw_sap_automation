import os
import sys
import json
import threading
import subprocess
import tempfile
import requests
import customtkinter as ctk
from src.util.config_manager import ConfigManager, APP_VERSION

def parse_version(v_str):
    """'1.0.1' gibi metin versiyonlarını karşılaştırılabilir tuple'a çevirir."""
    try:
        clean_v = v_str.lstrip('vV').strip()
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
    def check_for_updates_async(app):
        """Arka planda (Thread) versiyon kontrolünü başlatır."""
        if not ConfigManager.get_setting("AUTO_UPDATE_ENABLED"):
            return
            
        thread = threading.Thread(target=UpdateManager._check_worker, args=(app,), daemon=True)
        thread.start()

    @staticmethod
    def _check_worker(app):
        url = ConfigManager.get_setting("UPDATE_CHECK_URL")
        if not url:
            return

        try:
            response = requests.get(url, timeout=5, headers={"User-Agent": "LCW_SAP_Automation_App"})
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
            print(f"[UpdateManager] Güncelleme kontrolü sırasında hata: {e}")

    @staticmethod
    def _show_update_dialog(app, update_data):
        remote_version = update_data.get("version", "Bilinmiyor")
        changelog = update_data.get("changelog", "Yeni geliştirmeler ve performans iyileştirmeleri.")
        download_url = update_data.get("download_url", "")

        dialog = ctk.CTkToplevel(app)
        dialog.title("Yeni Güncelleme Mevcut")
        dialog.geometry("450x260")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        # Pencereyi ekranın ortasına güvenli biçimde hizala
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = max(0, (screen_width - 450) // 2)
        y = max(0, (screen_height - 260) // 2)
        dialog.geometry(f"450x260+{x}+{y}")
        dialog.lift()
        dialog.focus_force()

        title_label = ctk.CTkLabel(
            dialog, 
            text=f"🚀 Yeni Sürüm Mevcut: v{remote_version}", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(padx=20, pady=(15, 5))

        current_label = ctk.CTkLabel(
            dialog, 
            text=f"Mevcut Sürümünüz: v{APP_VERSION}", 
            font=ctk.CTkFont(size=12), text_color="gray"
        )
        current_label.pack(padx=20, pady=(0, 10))

        textbox = ctk.CTkTextbox(dialog, width=410, height=100)
        textbox.pack(padx=20, pady=5)
        textbox.insert("1.0", f"Yenilikler:\n{changelog}")
        textbox.configure(state="disabled")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(padx=20, pady=10, fill="x")

        def start_update():
            dialog.destroy()
            UpdateManager._download_and_install(app, download_url)

        update_btn = ctk.CTkButton(
            btn_frame, text="Şimdi Güncelle", command=start_update, 
            fg_color="#2563eb", hover_color="#1d4ed8"
        )
        update_btn.pack(side="right", padx=5)

        later_btn = ctk.CTkButton(
            btn_frame, text="Daha Sonra", command=dialog.destroy, 
            fg_color="transparent", border_width=1, border_color="gray"
        )
        later_btn.pack(side="right", padx=5)

    @staticmethod
    def _download_and_install(app, download_url):
        if not download_url:
            return

        progress_dialog = ctk.CTkToplevel(app)
        progress_dialog.title("Güncelleniyor")
        progress_dialog.geometry("380x140")
        progress_dialog.resizable(False, False)
        progress_dialog.attributes("-topmost", True)

        progress_label = ctk.CTkLabel(
            progress_dialog, 
            text="Güncelleme paketi indiriliyor, lütfen bekleyin...", 
            font=ctk.CTkFont(size=12)
        )
        progress_label.pack(padx=20, pady=(20, 10))

        progressbar = ctk.CTkProgressBar(progress_dialog, width=320)
        progressbar.pack(padx=20, pady=10)
        progressbar.set(0)

        def download_worker():
            try:
                temp_dir = tempfile.gettempdir()
                zip_path = os.path.join(temp_dir, "lcw_update.zip")

                res = requests.get(download_url, stream=True, timeout=30)
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

                # İndirme bitti, updater scriptini çalıştır
                updater_bat = resource_path(os.path.join("assets", "updater.bat"))
                
                if getattr(sys, 'frozen', False):
                    target_dir = os.path.dirname(sys.executable)
                else:
                    target_dir = os.path.abspath(".")

                if os.path.exists(updater_bat) and os.path.exists(zip_path):
                    subprocess.Popen(['cmd.exe', '/c', updater_bat, zip_path, target_dir], creationflags=subprocess.CREATE_NO_WINDOW)
                    progress_dialog.after(0, lambda: app.destroy())
                else:
                    progress_dialog.after(0, lambda: progress_label.configure(text="Hata: Güncelleme scripti bulunamadı."))
            except Exception as e:
                progress_dialog.after(0, lambda err=e: progress_label.configure(text=f"İndirme hatası: {err}"))

        threading.Thread(target=download_worker, daemon=True).start()

