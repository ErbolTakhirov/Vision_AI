from django.apps import AppConfig


class VisionConfig(AppConfig):
    name = 'vision'

    def ready(self):
        import threading
        from .tts_engine import TTSBrain
        
        def load_models():
            print("🚀 Starting background model loading (KaniTTS)...")
            TTSBrain.init_kani()
            
        threading.Thread(target=load_models, daemon=True).start()
