import pyttsx3
import config

class TTSService:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', config.TTS_RATE)
        self.engine.setProperty('volume', config.TTS_VOLUME)

        # Try to select a Russian voice if possible
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'ru' in voice.id.lower() or 'russian' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break

    def speak(self, text):
        """
        Synthesizes text to speech. 
        Note: This is blocking by default in pyttsx3.
        """
        print(f"🗣 Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
