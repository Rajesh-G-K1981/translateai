from typing import Optional
from langdetect import detect, LangDetectException

class LanguageDetector:
    def __init__(self):
        self.supported_languages = {
            'hi': 'Hindi',
            'bn': 'Bengali',
            'te': 'Telugu',
            'ta': 'Tamil',
            'mr': 'Marathi',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'pa': 'Punjabi',
            'en': 'English'
        }
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of the given text.
        Returns the language code if detected, None otherwise."""
        try:
            detected_code = detect(text)
            return detected_code if detected_code in self.supported_languages else None
        except LangDetectException:
            return None
    
    def get_language_name(self, language_code: str) -> str:
        """Get the full name of a language from its code."""
        return self.supported_languages.get(language_code, 'Unknown')
    
    def get_supported_languages(self) -> dict:
        """Get a dictionary of supported languages and their codes."""
        return self.supported_languages.copy()