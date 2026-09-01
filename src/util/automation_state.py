import ctypes
import logging

logger = logging.getLogger(__name__)

class AutomationState:
    current_thread_id = None

    @classmethod
    def force_stop(cls):
        """Çalışan thread'in içine SystemExit hatası fırlatarak anında durdurur."""
        if cls.current_thread_id:
            logger.warning(f"!!! STOP: Otomasyon durduruluyor (Thread: {cls.current_thread_id}) !!!")
            
            # Python C-API kullanarak thread içine SystemExit enjekte et
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(cls.current_thread_id),
                ctypes.py_object(SystemExit)
            )
            
            if res > 1:
                # Hata oluşursa temizle
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(cls.current_thread_id), None)
                logger.error("Thread durdurulurken bir hata oluştu.")
            
            cls.current_thread_id = None
            return True
        return False