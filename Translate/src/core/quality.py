from typing import List, Dict, Optional
import re

class QualityChecker:
    def __init__(self):
        self.custom_dictionary: Dict[str, str] = {}
        self.formatting_rules = [
            self._check_double_spaces,
            self._check_punctuation,
            self._check_capitalization
        ]
    
    def set_custom_dictionary(self, dictionary: Dict[str, str]) -> None:
        self.custom_dictionary = dictionary
    
    def check_translation(self, original: str, translated: str) -> List[str]:
        issues = []
        
        # Check formatting
        for rule in self.formatting_rules:
            issue = rule(translated)
            if issue:
                issues.extend(issue)
        
        # Check custom dictionary terms
        issues.extend(self._check_custom_terms(translated))
        
        # Check for missing placeholders/variables
        issues.extend(self._check_placeholders(original, translated))
        
        return issues
    
    def _check_double_spaces(self, text: str) -> List[str]:
        issues = []
        if '  ' in text:
            issues.append("Found double spaces in translation")
        return issues
    
    def _check_punctuation(self, text: str) -> List[str]:
        issues = []
        if text.count('.') > 1 and not text[-1] in '.!?':
            issues.append("Missing end punctuation")
        if text.count('(') != text.count(')'):
            issues.append("Mismatched parentheses")
        return issues
    
    def _check_capitalization(self, text: str) -> List[str]:
        issues = []
        sentences = re.split('[.!?]+', text)
        for sentence in sentences:
            if sentence.strip() and not sentence.strip()[0].isupper():
                issues.append(f"Sentence should start with capital letter: {sentence.strip()}")
        return issues
    
    def _check_custom_terms(self, text: str) -> List[str]:
        issues = []
        for term, expected in self.custom_dictionary.items():
            if term.lower() in text.lower() and expected not in text:
                issues.append(f"Custom term '{term}' should be translated as '{expected}'")
        return issues
    
    def _check_placeholders(self, original: str, translated: str) -> List[str]:
        issues = []
        # Check for common placeholder patterns
        placeholders = re.findall(r'\{[\w\d_]+\}|%[sd]|\$\w+', original)
        for placeholder in placeholders:
            if placeholder not in translated:
                issues.append(f"Missing placeholder: {placeholder}")
        return issues
    
    def suggest_improvements(self, text: str) -> List[str]:
        suggestions = []
        
        # Check for common translation issues
        if len(text.split()) < 3:
            suggestions.append("Translation seems too short")
        
        # Check for repeated words
        words = text.lower().split()
        for i in range(len(words)-1):
            if words[i] == words[i+1]:
                suggestions.append(f"Found repeated word: {words[i]}")
        
        return suggestions