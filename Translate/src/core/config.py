import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_file: str = 'translator_settings.json'):
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {
            'theme': 'dark',
            'recent_files': [],
            'custom_dictionary': {},
            'translation_engines': {
                'google': {
                    'api_key': None,
                    'default': True
                },
                'deepl': {
                    'api_key': None,
                    'default': False
                }
            },
            'max_recent_files': 5,
            'default_target_language': 'hi',
            'default_output_format': 'Same as Input'
        }
        self.load_config()
    
    def load_config(self) -> None:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    stored_config = json.load(f)
                    self.config.update(stored_config)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self.config_file}. Using default configuration.")
    
    def save_config(self) -> None:
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save_config()
    
    def add_recent_file(self, file_path: str) -> None:
        if file_path in self.config['recent_files']:
            self.config['recent_files'].remove(file_path)
        self.config['recent_files'].insert(0, file_path)
        
        if len(self.config['recent_files']) > self.config['max_recent_files']:
            self.config['recent_files'].pop()
        
        self.save_config()
    
    def set_api_key(self, engine: str, api_key: str) -> None:
        if engine not in self.config['translation_engines']:
            raise ValueError(f"Unknown translation engine: {engine}")
        
        self.config['translation_engines'][engine]['api_key'] = api_key
        self.save_config()
    
    def get_api_key(self, engine: str) -> Optional[str]:
        if engine not in self.config['translation_engines']:
            return None
        return self.config['translation_engines'][engine].get('api_key')