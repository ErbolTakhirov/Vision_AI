import speech_recognition as sr
from colorama import Fore

class STTService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Calibrate energy threshold for ambient noise
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = sr.Microphone()
        
        print(f"{Fore.CYAN}[STT] Calibrating microphone for noise...{Fore.RESET}")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print(f"{Fore.CYAN}[STT] Ready.{Fore.RESET}")

    def listen_and_transcribe(self):
        """
        Listens to the microphone and returns text.
        Returns None if nothing valid was heard.
        """
        with self.microphone as source:
            print(f"{Fore.YELLOW}🎤 Listening...{Fore.RESET}", end="\r")
            try:
                # Listen with a timeout to prevent hanging forever
                audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=10.0)
                
                print(f"{Fore.BLUE}⚡ Transcribing...{Fore.RESET}", end="\r")
                # Using Google Speech Recognition (free, requires internet)
                # For offline: use recognizer.recognize_whisper(audio) (requires installing openai-whisper)
                text = self.recognizer.recognize_google(audio, language="ru-RU") 
                
                return text.lower()
            
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f"{Fore.RED}[STT] API Error: {e}{Fore.RESET}")
                return None
