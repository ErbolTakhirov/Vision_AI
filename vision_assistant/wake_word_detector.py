import config

class WakeWordDetector:
    def detect(self, text: str) -> bool:
        """
        Checks if any of the configured wake words are present in the text.
        """
        if not text:
            return False
            
        cleaned_text = text.lower().strip()
        
        for word in config.WAKE_WORDS:
            if word in cleaned_text:
                return True
                
        return False

    def clean_command(self, text: str) -> str:
        """
        Removes the wake word from the prompt to get the clean command.
        Example: "A-Vision what time is it" -> "what time is it"
        """
        if not text:
            return ""
            
        cleaned_text = text.lower()
        for word in config.WAKE_WORDS:
            cleaned_text = cleaned_text.replace(word, "")
            
        return cleaned_text.strip()
