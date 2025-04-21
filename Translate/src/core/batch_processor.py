from typing import List, Callable, Dict, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .document_handler import DocumentHandler, DocumentWriter
from .translator import TranslationManager
from .quality import QualityChecker

class BatchProcessor:
    def __init__(self):
        self.document_handler = DocumentHandler()
        self.document_writer = DocumentWriter()
        self.translation_manager = TranslationManager()
        self.quality_checker = QualityChecker()
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None
        self.cancel_flag = False
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """Set callback for progress updates: (current, total, message)"""
        self.progress_callback = callback
    
    def cancel(self) -> None:
        self.cancel_flag = True
    
    def process_files(self, 
                      files: List[str], 
                      target_lang: str,
                      output_dir: Optional[str] = None,
                      max_workers: int = 4) -> Dict[str, str]:
        self.cancel_flag = False
        total_files = len(files)
        results: Dict[str, str] = {}
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {}
            
            for file_path in files:
                if self.cancel_flag:
                    break
                    
                future = executor.submit(
                    self._process_single_file,
                    file_path,
                    target_lang,
                    output_dir
                )
                future_to_file[future] = file_path
            
            completed = 0
            for future in as_completed(future_to_file):
                if self.cancel_flag:
                    break
                    
                file_path = future_to_file[future]
                try:
                    output_path = future.result()
                    results[file_path] = output_path
                    completed += 1
                    
                    if self.progress_callback:
                        self.progress_callback(
                            completed,
                            total_files,
                            f"Processed {Path(file_path).name}"
                        )
                except Exception as e:
                    results[file_path] = str(e)
                    if self.progress_callback:
                        self.progress_callback(
                            completed,
                            total_files,
                            f"Error processing {Path(file_path).name}: {str(e)}"
                        )
        
        return results
    
    def _process_single_file(self,
                            file_path: str,
                            target_lang: str,
                            output_dir: Optional[str] = None) -> str:
        # Read document
        text = self.document_handler.read_document(file_path)
        
        # Translate
        translated_text = self.translation_manager.translate(text, target_lang)
        
        # Quality check
        issues = self.quality_checker.check_translation(text, translated_text)
        if issues:
            print(f"Quality issues in {file_path}:")
            for issue in issues:
                print(f"- {issue}")
        
        # Determine output path
        input_path = Path(file_path)
        if output_dir:
            output_path = Path(output_dir) / input_path.name
        else:
            stem = input_path.stem
            output_path = input_path.with_name(f"{stem}_translated{input_path.suffix}")
        
        # Write output with target language
        self.document_writer.write_document(translated_text, str(output_path), target_lang=target_lang)
        
        return str(output_path)