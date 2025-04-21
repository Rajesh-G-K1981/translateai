import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from ttkthemes import ThemedTk
from pathlib import Path
from typing import List, Optional

from core.translator import TranslationManager
from core.config import ConfigManager
from core.document_handler import DocumentHandler, DocumentWriter
from core.quality import QualityChecker
from core.batch_processor import BatchProcessor

class TranslatorApp:
    def __init__(self, root: ThemedTk):
        self.root = root
        self.root.title("Professional Document Translator")
        self.root.geometry("1200x800")
        self.root.set_theme("equilux")
        
        # Initialize core components
        self.config_manager = ConfigManager()
        self.translation_manager = TranslationManager()
        self.document_handler = DocumentHandler()
        self.document_writer = DocumentWriter()
        self.quality_checker = QualityChecker()
        self.batch_processor = BatchProcessor()
        
        # Set up batch processor callback
        self.batch_processor.set_progress_callback(self.update_progress)
        
        # Load settings
        self.load_settings()
        
        # Create UI
        self.create_widgets()
        self.update_recent_files()
    
    def load_settings(self) -> None:
        self.languages = {
            'Hindi': 'hi',
            'Bengali': 'bn',
            'Telugu': 'te',
            'Tamil': 'ta',
            'Marathi': 'mr',
            'Gujarati': 'gu',
            'Kannada': 'kn',
            'Malayalam': 'ml',
            'Punjabi': 'pa'
        }
    
    def create_widgets(self) -> None:
        # Main container with grid layout
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Left panel (30% width)
        left_panel = ttk.Frame(main_container)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=5)
        
        # Right panel (70% width)
        right_panel = ttk.Frame(main_container)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=5)
        
        main_container.columnconfigure(1, weight=7)
        main_container.columnconfigure(0, weight=3)
        
        # File Selection Section
        self.create_file_selection(left_panel)
        
        # Translation Settings Section
        self.create_translation_settings(left_panel)
        
        # Quality Settings Section
        self.create_quality_settings(left_panel)
        
        # Progress Section
        self.create_progress_section(left_panel)
        
        # Preview Section
        self.create_preview_section(right_panel)
    
    def create_file_selection(self, parent: ttk.Frame) -> None:
        file_frame = ttk.LabelFrame(parent, text="Document Selection", padding=10)
        file_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Single file selection
        ttk.Label(file_frame, text="Select Document:").grid(row=0, column=0, sticky="w")
        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2)
        
        # Batch processing
        ttk.Label(file_frame, text="Batch Directory:").grid(row=1, column=0, sticky="w", pady=5)
        self.batch_dir = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.batch_dir).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(file_frame, text="Select", command=self.browse_directory).grid(row=1, column=2)
        
        # Recent files
        ttk.Label(file_frame, text="Recent Files:").grid(row=2, column=0, sticky="w", pady=5)
        self.recent_listbox = tk.Listbox(file_frame, height=3)
        self.recent_listbox.grid(row=3, column=0, columnspan=3, sticky="ew")
        self.recent_listbox.bind('<Double-Button-1>', self.load_recent_file)
        
        file_frame.columnconfigure(1, weight=1)
    
    def create_translation_settings(self, parent: ttk.Frame) -> None:
        settings_frame = ttk.LabelFrame(parent, text="Translation Settings", padding=10)
        settings_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Language selection
        ttk.Label(settings_frame, text="Source Language:").grid(row=0, column=0, sticky="w")
        self.source_lang = tk.StringVar(value="Auto Detect")
        source_langs = ["Auto Detect"] + list(self.languages.keys())
        source_combo = ttk.Combobox(settings_frame, textvariable=self.source_lang, values=source_langs)
        source_combo.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(settings_frame, text="Target Language:").grid(row=1, column=0, sticky="w", pady=5)
        self.target_lang = tk.StringVar(value=self.config_manager.get('default_target_language'))
        lang_combo = ttk.Combobox(settings_frame, textvariable=self.target_lang,
                                 values=list(self.languages.keys()))
        lang_combo.grid(row=1, column=1, sticky="ew", padx=5)
        
        # Page selection for PDF
        ttk.Label(settings_frame, text="PDF Pages:").grid(row=2, column=0, sticky="w", pady=5)
        self.page_selection = tk.StringVar(value="All Pages")
        self.page_entry = ttk.Entry(settings_frame, textvariable=self.page_selection)
        self.page_entry.grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Label(settings_frame, text="(e.g., 1,3-5 or 'All Pages')").grid(row=2, column=2, sticky="w")

        # Translation engine
        ttk.Label(settings_frame, text="Translation Engine:").grid(row=3, column=0, sticky="w", pady=5)
        self.engine = tk.StringVar(value='google')
        engine_combo = ttk.Combobox(settings_frame, textvariable=self.engine,
                                   values=self.translation_manager.get_available_engines())
        engine_combo.grid(row=3, column=1, sticky="ew", padx=5)
        
        # Output format
        ttk.Label(settings_frame, text="Output Format:").grid(row=4, column=0, sticky="w", pady=5)
        self.output_format = tk.StringVar(value=self.config_manager.get('default_output_format'))
        format_combo = ttk.Combobox(settings_frame, textvariable=self.output_format,
                                   values=["Same as Input", "DOCX", "PDF", "TXT"])
        format_combo.grid(row=4, column=1, sticky="ew", padx=5)
        
        settings_frame.columnconfigure(1, weight=1)
    
    def create_quality_settings(self, parent: ttk.Frame) -> None:
        quality_frame = ttk.LabelFrame(parent, text="Quality Settings", padding=10)
        quality_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        # Quality checks
        self.check_formatting = tk.BooleanVar(value=True)
        ttk.Checkbutton(quality_frame, text="Check Formatting",
                       variable=self.check_formatting).grid(row=0, column=0, sticky="w")
        
        self.check_placeholders = tk.BooleanVar(value=True)
        ttk.Checkbutton(quality_frame, text="Check Placeholders",
                       variable=self.check_placeholders).grid(row=1, column=0, sticky="w")
        
        # Custom dictionary
        ttk.Button(quality_frame, text="Manage Custom Dictionary",
                  command=self.manage_dictionary).grid(row=2, column=0, sticky="w", pady=5)
    
    def create_progress_section(self, parent: ttk.Frame) -> None:
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding=10)
        progress_frame.grid(row=3, column=0, sticky="ew", pady=5)
        
        # Progress bar
        self.progress_var = tk.StringVar()
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky="w")
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(progress_frame)
        button_frame.grid(row=2, column=0, sticky="ew")
        
        ttk.Button(button_frame, text="Translate",
                   command=self.start_translation).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Preview",
                   command=self.preview_translation).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=self.cancel_translation).grid(row=0, column=2, padx=5)
        
        progress_frame.columnconfigure(0, weight=1)
    
    def create_preview_section(self, parent: ttk.Frame) -> None:
        preview_frame = ttk.LabelFrame(parent, text="Translation Preview", padding=10)
        preview_frame.grid(row=0, column=0, sticky="nsew")
        
        # Original text
        ttk.Label(preview_frame, text="Original Text:").grid(row=0, column=0, sticky="w")
        self.original_text = scrolledtext.ScrolledText(preview_frame, height=15)
        self.original_text.grid(row=1, column=0, sticky="nsew", pady=5)
        
        # Translated text
        ttk.Label(preview_frame, text="Translated Text:").grid(row=2, column=0, sticky="w")
        self.translated_text = scrolledtext.ScrolledText(preview_frame, height=15)
        self.translated_text.grid(row=3, column=0, sticky="nsew", pady=5)
        
        # Quality issues
        ttk.Label(preview_frame, text="Quality Issues:").grid(row=4, column=0, sticky="w")
        self.issues_text = scrolledtext.ScrolledText(preview_frame, height=5)
        self.issues_text.grid(row=5, column=0, sticky="nsew", pady=5)
        
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.rowconfigure(3, weight=1)
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
    
    def browse_file(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("All Supported Files", "*.docx;*.txt;*.pdf;*.rtf;*.odt"),
                ("Word Documents", "*.docx"),
                ("Text Files", "*.txt"),
                ("PDF Files", "*.pdf"),
                ("RTF Files", "*.rtf"),
                ("ODT Files", "*.odt")
            ])
        if file_path:
            self.file_path.set(file_path)
            self.config_manager.add_recent_file(file_path)
            self.update_recent_files()
    
    def browse_directory(self) -> None:
        directory = filedialog.askdirectory()
        if directory:
            self.batch_dir.set(directory)
    
    def load_recent_file(self, event) -> None:
        selection = self.recent_listbox.curselection()
        if selection:
            file_path = self.config_manager.get('recent_files')[selection[0]]
            self.file_path.set(file_path)
    
    def _parse_page_selection(self, total_pages: int) -> Optional[List[int]]:
        """Parse page selection string and return list of page numbers."""
        selection = self.page_selection.get().strip()
        if selection == "All Pages" or not selection:
            return None
        
        pages = set()
        try:
            # Split by comma and process each part
            for part in selection.split(','):
                if '-' in part:
                    # Handle page ranges (e.g., 1-5)
                    start, end = map(int, part.split('-'))
                    if 1 <= start <= end <= total_pages:
                        pages.update(range(start - 1, end))
                else:
                    # Handle single pages
                    page = int(part)
                    if 1 <= page <= total_pages:
                        pages.add(page - 1)
            return sorted(list(pages)) if pages else None
        except ValueError:
            messagebox.showerror("Error", f"Invalid page selection format. Please use format like '1,3-5' (max {total_pages} pages)")
            return None
    
    def update_recent_files(self) -> None:
        self.recent_listbox.delete(0, tk.END)
        for file in self.config_manager.get('recent_files'):
            self.recent_listbox.insert(tk.END, Path(file).name)
    
    def manage_dictionary(self) -> None:
        # TODO: Implement custom dictionary management dialog
        pass
    
    def update_progress(self, current: int, total: int, message: str) -> None:
        progress = (current / total) * 100 if total > 0 else 0
        self.progress_bar['value'] = progress
        self.progress_var.set(message)
        self.root.update_idletasks()
    
    def start_translation(self) -> None:
        if self.batch_dir.get():
            self.start_batch_translation()
        elif self.file_path.get():
            self.translate_single_file()
        else:
            messagebox.showerror("Error", "Please select a file or directory to translate")
    
    def translate_single_file(self) -> None:
        try:
            file_path = self.file_path.get()
            target_lang_code = self.languages[self.target_lang.get()]
            
            # Get page selection for PDF files
            pages = None
            if file_path.lower().endswith('.pdf'):
                with PdfReader(file_path) as reader:
                    pages = self._parse_page_selection(len(reader.pages))
            
            # Read document
            text, detected_lang = self.document_handler.read_document(file_path, pages)
            self.original_text.delete('1.0', tk.END)
            self.original_text.insert('1.0', text)
            
            # Update source language if auto-detect is enabled
            if self.source_lang.get() == "Auto Detect" and detected_lang:
                detected_name = self.document_handler.language_detector.get_language_name(detected_lang)
                if detected_name in self.languages:
                    self.source_lang.set(detected_name)
            
            # Translate
            translated = self.translation_manager.translate(text, target_lang_code)
            self.translated_text.delete('1.0', tk.END)
            self.translated_text.insert('1.0', translated)
            
            # Quality check
            issues = self.quality_checker.check_translation(text, translated)
            self.issues_text.delete('1.0', tk.END)
            if issues:
                self.issues_text.insert('1.0', '\n'.join(issues))
            else:
                self.issues_text.insert('1.0', 'No quality issues found')
            
            # Save translation
            input_path = Path(file_path)
            output_path = input_path.with_name(f"{input_path.stem}_translated{input_path.suffix}")
            self.document_writer.write_document(translated, str(output_path), target_lang=target_lang_code)
            
            messagebox.showinfo("Success", f"Translation saved to {output_path}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def start_batch_translation(self) -> None:
        directory = Path(self.batch_dir.get())
        if not directory.exists():
            messagebox.showerror("Error", "Selected directory does not exist")
            return
        
        files = [str(f) for f in directory.glob("*.*")
                if f.suffix.lower() in [".docx", ".txt", ".pdf", ".rtf", ".odt"]]
        
        if not files:
            messagebox.showerror("Error", "No supported files found in directory")
            return
        
        target_lang_code = self.languages[self.target_lang.get()]
        output_dir = directory / "translated"
        
        try:
            results = self.batch_processor.process_files(
                files,
                target_lang_code,
                str(output_dir)
            )
            
            success = sum(1 for v in results.values() if not str(v).startswith("Error"))
            messagebox.showinfo(
                "Batch Translation Complete",
                f"Successfully translated {success} out of {len(files)} files\n"
                f"Output directory: {output_dir}"
            )
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def preview_translation(self) -> None:
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a file to preview")
            return
        
        try:
            text = self.document_handler.read_document(self.file_path.get())
            self.original_text.delete('1.0', tk.END)
            self.original_text.insert('1.0', text)
            
            target_lang_code = self.languages[self.target_lang.get()]
            translated = self.translation_manager.translate(text[:1000], target_lang_code)
            
            self.translated_text.delete('1.0', tk.END)
            self.translated_text.insert('1.0', translated + "\n\n[Preview limited to first 1000 characters]")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def cancel_translation(self) -> None:
        self.batch_processor.cancel()

def main():
    root = ThemedTk()
    app = TranslatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()