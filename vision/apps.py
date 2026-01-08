from django.apps import AppConfig


class VisionConfig(AppConfig):
    name = 'vision'

    def ready(self):
        # Avoid running in reloader thread to prevent duplicates (simple check)
        import os
        if os.environ.get('RUN_MAIN') == 'true':
            from .wake_word import WakeWordListener
            # WakeWordListener.start()
            pass
