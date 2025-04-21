from abc import ABC, abstractmethod
from typing import Dict, Optional
from deep_translator import GoogleTranslator

class TranslationEngine(ABC):
    @abstractmethod
    def translate(self, text: str, target_lang: str) -> str:
        pass

class GoogleTranslationEngine(TranslationEngine):
    def translate(self, text: str, target_lang: str) -> str:
        # Sanitize input text to ensure XML compatibility
        sanitized_text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        translator = GoogleTranslator(source='auto', target=target_lang)
        result = translator.translate(sanitized_text)
        
        # Ensure output is also XML compatible
        return ''.join(char for char in result if ord(char) >= 32 or char in '\n\r\t')

class TranslationManager:
    def __init__(self):
        self.engines: Dict[str, TranslationEngine] = {
            'google': GoogleTranslationEngine()
        }
        self.current_engine = 'google'
        self.translation_memory: Dict[str, Dict[str, str]] = {}
    
    def set_engine(self, engine_name: str) -> None:
        if engine_name not in self.engines:
            raise ValueError(f"Unknown translation engine: {engine_name}")
        self.current_engine = engine_name
    
    def translate(self, text: str, target_lang: str) -> str:
        # Check translation memory first
        if text in self.translation_memory and target_lang in self.translation_memory[text]:
            return self.translation_memory[text][target_lang]
        
        # Perform translation
        result = self.engines[self.current_engine].translate(text, target_lang)
        
        # Store in translation memory
        if text not in self.translation_memory:
            self.translation_memory[text] = {}
        self.translation_memory[text][target_lang] = result
        
        return result
    
    def get_available_engines(self) -> list[str]:
        return list(self.engines.keys())