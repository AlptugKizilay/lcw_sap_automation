import logging
import tkinter as tk

class GuiLogHandler(logging.Handler):
    """Log kayıtlarını bir CustomTkinter Textbox'a yönlendiren handler."""
    def __init__(self, textbox):
        super().__init__()
        self.textbox = textbox

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.textbox.configure(state="normal")
            self.textbox.insert("end", msg + "\n")
            self.textbox.see("end") # Otomatik aşağı kaydır
            self.textbox.configure(state="disabled")
        
        # Thread-safe (GUI thread'inde çalıştır)
        self.textbox.after(0, append)

def setup_gui_logging(textbox):
    # Mevcut logger'ı al
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # GUI Handler'ı ekle
    gui_handler = GuiLogHandler(textbox)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
    gui_handler.setFormatter(formatter)
    logger.addHandler(gui_handler)
    
    return logger