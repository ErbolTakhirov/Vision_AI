
import os
import threading
import struct
import pyaudio
import pvporcupine
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class WakeWordListener:
    _instance = None
    _running = False
    _thread = None

    def __init__(self):
        self.access_key = os.getenv("PICOVOICE_ACCESS_KEY")
        self.keyword_path = os.path.join(settings.BASE_DIR, "Way-Finder_en_windows_v4_0_0.ppn")
        self.porcupine = None
        self.pa = None
        self.audio_stream = None

    @classmethod
    def start(cls):
        if cls._instance is None:
            cls._instance = WakeWordListener()
        
        if not cls._instance.access_key:
            logger.warning("⚠️ PICOVOICE_ACCESS_KEY not found. Wake word listener disabled.")
            return

        if not os.path.exists(cls._instance.keyword_path):
            logger.warning(f"⚠️ Wake word file not found at {cls._instance.keyword_path}")
            return

        if not cls._running:
            cls._running = True
            cls._thread = threading.Thread(target=cls._instance._run_loop, daemon=True)
            cls._thread.start()
            logger.info("🎤 Wake Word Listener Started (Background)")

    def _run_loop(self):
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=[self.keyword_path]
            )

            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )

            print(f"👂 Listening for wake word: Way Finder...")

            while self._running:
                pcm = self.audio_stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    print(f"🔥 Wake Word Detected!")
                    # TODO: Trigger logic here. For now, beep or log.
                    # We can trigger a callback or event.
                    
        except Exception as e:
            logger.error(f"Wake word error: {e}")
        finally:
            if self.porcupine:
                self.porcupine.delete()
            if self.audio_stream:
                self.audio_stream.close()
            if self.pa:
                self.pa.terminate()
            self._running = False
