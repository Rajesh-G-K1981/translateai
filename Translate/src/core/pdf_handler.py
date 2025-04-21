from typing import Dict, List, Tuple, Optional
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTAnno, LTTextLineHorizontal, LTImage
from collections import defaultdict
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib.utils import ImageReader as Image

class PDFHandler:
    def __init__(self):
        self.layout_info = defaultdict(list)
        self.font_info = defaultdict(dict)
        self.structure_info = defaultdict(dict)
        self.text_segments = defaultdict(list)
        self.image_elements = defaultdict(list)
        self.fallback_fonts = {
            'hi': 'Nirmala UI',  # Hindi
            'bn': 'Nirmala UI',  # Bengali
            'te': 'Nirmala UI',  # Telugu
            'ta': 'Nirmala UI',  # Tamil
            'mr': 'Nirmala UI',  # Marathi
            'gu': 'Nirmala UI',  # Gujarati
            'kn': 'Nirmala UI',  # Kannada
            'ml': 'Nirmala UI',  # Malayalam
            'pa': 'Nirmala UI'   # Punjabi
        }
    
    def detect_structure(self, file_path: str) -> Dict:
        """Detect document structure including headers, paragraphs, and columns"""
        structure = defaultdict(dict)
        
        for page_num, page_layout in enumerate(extract_pages(file_path)):
            # Track potential headers and columns
            headers = []
            columns = defaultdict(list)
            
            # Group text elements by their vertical and horizontal positions
            v_groups = defaultdict(list)
            h_groups = defaultdict(list)
            
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    bbox = element.bbox
                    font_info = self._extract_font_info(element)
                    
                    # Group by vertical position
                    v_pos = round(bbox[1])
                    v_groups[v_pos].append({
                        'text': element.get_text().strip(),
                        'bbox': bbox,
                        'font': font_info
                    })
                    
                    # Group by horizontal position for column detection
                    h_pos = round(bbox[0])
                    h_groups[h_pos].append({
                        'text': element.get_text().strip(),
                        'bbox': bbox,
                        'font': font_info
                    })
            
            # Detect headers based on font size and position
            sorted_v_pos = sorted(v_groups.keys(), reverse=True)
            for v_pos in sorted_v_pos:
                elements = v_groups[v_pos]
                for element in elements:
                    font_size = element['font'].get('size', 0)
                    if font_size > 12 or element['font'].get('is_bold', False):
                        headers.append(element)
            
            # Detect columns based on horizontal grouping
            sorted_h_pos = sorted(h_groups.keys())
            if len(sorted_h_pos) > 1:
                avg_gap = sum(sorted_h_pos[i+1] - sorted_h_pos[i] 
                            for i in range(len(sorted_h_pos)-1)) / (len(sorted_h_pos)-1)
                
                current_column = 0
                prev_pos = sorted_h_pos[0]
                
                for h_pos in sorted_h_pos[1:]:
                    if h_pos - prev_pos > avg_gap * 1.5:  # New column detected
                        current_column += 1
                    columns[current_column].extend(h_groups[h_pos])
                    prev_pos = h_pos
            
            structure[page_num] = {
                'headers': headers,
                'columns': dict(columns),
                'layout_type': 'multi_column' if len(columns) > 1 else 'single_column'
            }
        
        return dict(structure)

    def extract_text_with_layout(self, file_path: str, pages: Optional[List[int]] = None) -> Tuple[str, Dict]:
        """Extract text while preserving layout information and ensuring XML compatibility"""
        text_chunks = []
        layout_info = defaultdict(list)
        
        for page_num, page_layout in enumerate(extract_pages(file_path)):
            if pages is not None and page_num not in pages:
                continue
                
            page_text = []
            text_elements = []
            
            # First pass: collect all elements and their characteristics
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = self._sanitize_text(element.get_text().strip())
                    if text:
                        bbox = element.bbox
                        font_info = self._extract_font_info(element)
                        text_elements.append({
                            'text': text,
                            'bbox': bbox,
                            'font': font_info,
                            'y_pos': round(bbox[1]),
                            'x_pos': round(bbox[0]),
                            'width': round(bbox[2] - bbox[0]),
                            'height': round(bbox[3] - bbox[1])
                        })
                elif isinstance(element, LTImage):
                    # Store image elements for later reconstruction
                    self.image_elements[page_num].append({
                        'bbox': element.bbox,
                        'stream': element.stream,
                        'name': element.name
                    })
            
            # Second pass: group elements by logical blocks
            blocks = self._group_elements_into_blocks(text_elements)
            
            # Store layout information with block context
            for block in blocks:
                layout_info[page_num].extend(block['elements'])
                page_text.append(block['text'])
            
            text_chunks.append('\n'.join(page_text))
        
        return '\n\n'.join(text_chunks), dict(layout_info)
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to ensure XML compatibility while preserving meaningful whitespace"""
        if not text:
            return ""
        
        # Normalize whitespace while preserving meaningful spaces
        text = ' '.join(text.split())
        
        # Handle Unicode ranges and control characters
        return ''.join(
            char for char in text
            if char in ' \n\t\r'
            or (ord(char) >= 32 and ord(char) <= 55295)
            or (ord(char) >= 57344 and ord(char) <= 65533)
            or (ord(char) >= 65536 and ord(char) <= 1114111)
        )

    def _extract_font_info(self, text_container) -> Dict:
        """Extract detailed font information from text elements"""
        font_info = defaultdict(lambda: defaultdict(int))
        
        for text_line in text_container:
            if isinstance(text_line, LTTextLineHorizontal):
                for char in text_line:
                    if isinstance(char, LTChar):
                        font_name = char.fontname
                        font_size = round(char.size)
                        font_info[font_name][font_size] += 1
        
        if not font_info:
            return {}
        
        # Find most common font and size
        most_common_font = max(font_info.items(), key=lambda x: sum(x[1].values()))[0]
        most_common_size = max(font_info[most_common_font].items(), key=lambda x: x[1])[0]
        
        return {
            'name': most_common_font,
            'size': most_common_size,
            'is_bold': 'Bold' in most_common_font,
            'is_italic': 'Italic' in most_common_font
        }
    
    def write_pdf_with_layout(self, original_path: str, translated_text: str, output_path: str,
                           layout_info: Dict, target_lang: str = None) -> None:
        """Write translated text back to PDF while preserving layout and formatting"""
        reader = PdfReader(original_path)
        writer = PdfWriter()
        
        # Get document structure
        structure = self.detect_structure(original_path)
        
        # Split translated text into segments based on structure
        segments = self._split_translated_text(translated_text, structure)
        current_segment = 0
        
        # Get language-specific font if available
        target_font = self.fallback_fonts.get(target_lang, 'Helvetica')
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            writer.add_page(page)
            
            if str(page_num) in layout_info and current_segment < len(segments):
                packet = BytesIO()
                c = canvas.Canvas(packet, pagesize=(page.mediabox[2], page.mediabox[3]))
                
                page_structure = structure.get(page_num, {})
                layout_type = page_structure.get('layout_type', 'single_column')
                
                # Restore any images first
                self._restore_images(c, page_num)
                
                if layout_type == 'multi_column':
                    # Handle multi-column layout
                    columns = page_structure.get('columns', {})
                    for col_idx, col_elements in columns.items():
                        if current_segment < len(segments):
                            self._write_column(c, segments[current_segment], col_elements,
                                           target_font=target_font)
                            current_segment += 1
                else:
                    # Handle single-column layout with preserved formatting
                    for element in layout_info[str(page_num)]:
                        if current_segment < len(segments):
                            text = segments[current_segment]
                            bbox = element['bbox']
                            font_info = element.get('font', {})
                            
                            # Scale font size if needed
                            original_text_width = c.stringWidth(element['text'], font_info.get('name', target_font), font_info.get('size', 12))
                            translated_text_width = c.stringWidth(text, target_font, font_info.get('size', 12))
                            scale_factor = min(1.0, original_text_width / (translated_text_width + 0.001))
                            
                            # Set font properties with scaling
                            font_size = font_info.get('size', 12) * scale_factor
                            c.setFont(target_font, font_size)
                            
                            # Position and write text with proper wrapping and alignment
                            self._write_text_block_with_wrapping(c, text, bbox, target_font, font_size)
                            current_segment += 1
                
                c.save()
                packet.seek(0)
                overlay = PdfReader(packet)
                page.merge_page(overlay.pages[0])
        
        # Save the final PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

    def _split_translated_text(self, text: str, structure: Dict) -> List[str]:
        """Split translated text into segments based on document structure"""
        segments = []
        current_text = text
        
        for page_num in sorted(structure.keys()):
            page_structure = structure[page_num]
            
            # Split by headers first
            headers = page_structure.get('headers', [])
            if headers:
                for header in headers:
                    header_length = len(header['text'])
                    if len(current_text) > header_length:
                        segments.append(current_text[:header_length])
                        current_text = current_text[header_length:].strip()
            
            # Then split remaining text by columns if present
            columns = page_structure.get('columns', {})
            if columns:
                avg_col_length = len(current_text) // (len(columns) + 1)
                for _ in range(len(columns)):
                    if len(current_text) > avg_col_length:
                        segments.append(current_text[:avg_col_length])
                        current_text = current_text[avg_col_length:].strip()
            
            # Add remaining text as a segment
            if current_text:
                segments.append(current_text)
                current_text = ""
        
        return segments

    def _write_column(self, canvas, text: str, column_elements: List[Dict], target_font: str = 'Helvetica') -> None:
        """Write text in a column format"""
        if not column_elements:
            return
            
        # Calculate column boundaries
        left = min(elem['bbox'][0] for elem in column_elements)
        right = max(elem['bbox'][2] for elem in column_elements)
        top = max(elem['bbox'][3] for elem in column_elements)
        bottom = min(elem['bbox'][1] for elem in column_elements)
        
        # Set font based on first element
        font_info = column_elements[0].get('font', {})
        font_name = font_info.get('name', target_font)
        font_size = font_info.get('size', 12)
        canvas.setFont(font_name, font_size)
        
        # Write text in column bounds
        self._write_text_block(canvas, text, (left, bottom, right, top), 'left')

    def _write_text_block(self, canvas, text: str, bbox: tuple, alignment: str = 'left') -> None:
        """Write a block of text with proper alignment and wrapping"""
        x, y, right, top = bbox
        width = right - x
        height = top - y
        
        # Calculate text positioning based on alignment
        if alignment == 'center':
            x = x + (width / 2)
            canvas.drawCentredString(x, y, text)
        elif alignment == 'right':
            canvas.drawRightString(right, y, text)
        else:  # left alignment
            canvas.drawString(x, y, text)

    def _restore_images(self, canvas, page_num: int) -> None:
        """Restore images in their original positions"""
        for img in self.image_elements.get(page_num, []):
            try:
                # Convert image stream to reportlab image
                img_stream = BytesIO(img['stream'].get_data())
                img_obj = Image(img_stream)
                
                # Place image at original position
                bbox = img['bbox']
                canvas.drawImage(img_obj, bbox[0], bbox[1],
                               width=bbox[2]-bbox[0],
                               height=bbox[3]-bbox[1])
            except Exception:
                # Skip problematic images
                continue

    def _write_text_block_with_wrapping(self, canvas, text: str, bbox: tuple,
                                     font_name: str, font_size: float) -> None:
        """Write text with proper wrapping and alignment"""
        x, y, right, top = bbox
        width = right - x
        height = top - y
        
        # Create text object for wrapping
        text_obj = canvas.beginText()
        text_obj.setFont(font_name, font_size)
        
        # Calculate alignment
        if x < width / 3:  # Left third
            text_obj.setTextOrigin(x, top)
            alignment = 'left'
        elif x > (2 * width) / 3:  # Right third
            text_obj.setTextOrigin(right, top)
            alignment = 'right'
        else:  # Middle third
            text_obj.setTextOrigin(x + width/2, top)
            alignment = 'center'
        
        # Word wrap logic
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_width = canvas.stringWidth(word + ' ', font_name, font_size)
            if current_width + word_width <= width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Write wrapped text with proper alignment
        for line in lines:
            if alignment == 'center':
                line_width = canvas.stringWidth(line, font_name, font_size)
                text_obj.setTextOrigin(x + (width - line_width)/2, text_obj.getY() - font_size)
            elif alignment == 'right':
                line_width = canvas.stringWidth(line, font_name, font_size)
                text_obj.setTextOrigin(right - line_width, text_obj.getY() - font_size)
            text_obj.textLine(line)
        
        canvas.drawText(text_obj)

    def _group_elements_into_blocks(self, elements: List[Dict]) -> List[Dict]:
        """Group text elements into logical blocks based on layout analysis"""
        blocks = []
        
        # Sort elements by vertical position (top to bottom)
        sorted_elements = sorted(elements, key=lambda x: (-x['y_pos'], x['x_pos']))
        
        current_block = {'elements': [], 'text': [], 'y_pos': None}
        
        for element in sorted_elements:
            if current_block['y_pos'] is None:
                # Start new block
                current_block['y_pos'] = element['y_pos']
                
            # Check if element belongs to current block
            y_diff = abs(element['y_pos'] - current_block['y_pos'])
            if y_diff <= 5:  # Elements within 5 units are considered same line
                current_block['elements'].append(element)
                current_block['text'].append(element['text'])
            else:
                # Start new block
                if current_block['elements']:
                    blocks.append({
                        'elements': current_block['elements'],
                        'text': ' '.join(current_block['text'])
                    })
                current_block = {
                    'elements': [element],
                    'text': [element['text']],
                    'y_pos': element['y_pos']
                }
        
        # Add last block
        if current_block['elements']:
            blocks.append({
                'elements': current_block['elements'],
                'text': ' '.join(current_block['text'])
            })
        
        return blocks