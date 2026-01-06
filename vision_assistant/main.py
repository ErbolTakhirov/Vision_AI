import time
from enum import Enum
from colorama import init, Fore, Style

import config
from stt_service import STTService
from tts_service import TTSService
from wake_word_detector import WakeWordDetector
from brain import Brain

# Initialize Colorama
init()

class State(Enum):
    IDLE = 0    # Passive listening for wake word
    ACTIVE = 1  # Active dialog mode

class Assistant:
    def __init__(self):
        self.state = State.IDLE
        self.last_interaction_time = 0
        
        # Initialize Modules
        self.stt = STTService()
        self.tts = TTSService()
        self.detector = WakeWordDetector()
        self.brain = Brain()
        
    def run(self):
        print(f"{Fore.GREEN}=== A-Vision Assistant Started ==={Fore.RESET}")
        print(f"{Fore.GREEN}Waiting for Wake Word: '{config.WAKE_WORDS[0]}'...{Fore.RESET}")

        while True:
            # 1. Capture Audio & Transcribe
            # Note: listen_and_transcribe blocks until audio is heard or timeout
            text = self.stt.listen_and_transcribe()
            
            if not text:
                # Silence or noise. Check timeout if in ACTIVE mode
                if self.state == State.ACTIVE:
                    if time.time() - self.last_interaction_time > config.ACTIVE_MODE_TIMEOUT:
                        print(f"\n{Fore.YELLOW}[State] Timeout. Going IDLE.{Fore.RESET}")
                        self.state = State.IDLE
                        # Optional: play a closing sound
                continue

            print(f"\n{Fore.WHITE}Header: {text}{Fore.RESET}")

            # 2. State Machine Logic
            if self.state == State.IDLE:
                # Check for Wake Word
                if self.detector.detect(text):
                    print(f"{Fore.MAGENTA}✨ Wake Word Detected!{Fore.RESET}")
                    
                    # Clean the command (remove "a vision")
                    command = self.detector.clean_command(text)
                    
                    # Be polite
                    # self.tts.speak("Слушаю.") 
                    
                    self.state = State.ACTIVE
                    self.last_interaction_time = time.time()
                    
                    # If user said "A-Vision what time is it?", process immediately
                    if command: 
                        self.process_command(command)
                    else:
                        # Just "A-Vision". Play sound or wait for next loop
                        pass
                        
            elif self.state == State.ACTIVE:
                # In active mode, we process EVERYTHING as a command
                self.process_command(text)
                self.last_interaction_time = time.time()
                
                # Check if user wants to stop
                if "стоп" in text or "хватит" in text or "пока" in text:
                     self.state = State.IDLE
                     self.tts.speak("До связи.")

    def process_command(self, text):
        """Send text to Brain and speak response"""
        response = self.brain.process(text)
        print(f"{Fore.CYAN}AI: {response}{Fore.RESET}")
        self.tts.speak(response)

if __name__ == "__main__":
    try:
        app = Assistant()
        app.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
