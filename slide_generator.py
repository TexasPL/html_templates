import json
import os
import shutil
from typing import Dict, Any, Optional

class SlideGenerator:
    def __init__(self):
        self.templates_dir = 'templates'
        self.presets_dir = 'templates/presets'
        self.slides_dir = 'slides'
        self.img_slides_dir = 'img_slides'
        
    def load_preset(self, preset_name: str) -> Dict[str, Any]:
        """Ładuje preset z pliku JSON."""
        preset_path = os.path.join(self.presets_dir, f'{preset_name}.json')
        if not os.path.exists(preset_path):
            raise FileNotFoundError(f"Preset {preset_name} nie istnieje")
        
        with open(preset_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_next_slide_number(self) -> int:
        """Zwraca numer następnego slajdu."""
        try:
            with open('number.txt', 'r') as f:
                current_count = int(f.read().strip())
            return current_count + 1
        except FileNotFoundError:
            return 1
    
    def update_slide_count(self, new_count: int):
        """Aktualizuje liczbę slajdów w number.txt."""
        with open('number.txt', 'w') as f:
            f.write(str(new_count))
    
    def copy_image_to_slides(self, image_filename: str, slide_number: int) -> str:
        """Kopiuje obraz z img_slides do slides z nową nazwą."""
        if not image_filename:
            return ""
        
        src_path = os.path.join(self.img_slides_dir, image_filename)
        if not os.path.exists(src_path):
            print(f"Ostrzeżenie: Obraz {image_filename} nie istnieje")
            return ""
        
        # Pobierz rozszerzenie z oryginalnego pliku
        _, ext = os.path.splitext(image_filename)
        dst_filename = f"{slide_number}{ext}"
        dst_path = os.path.join(self.slides_dir, dst_filename)
        
        shutil.copy2(src_path, dst_path)
        print(f"Skopiowano obraz: {image_filename} → {dst_filename}")
        return dst_filename
    
    def convert_to_simple_html(self, preset_config: Dict[str, Any], 
                              images: Dict[str, str], 
                              slide_number: int) -> str:
        """Konwertuje konfigurację presetu do prostego HTML (format głównego projektu)."""
        
        # Skopiuj obrazy do folderu slides
        bg_image = ""
        if images.get('green'):
            bg_image = self.copy_image_to_slides(images['green'], slide_number)
        
        # Podstawowy template HTML (kompatybilny z istniejącym systemem)
        html_template = '''<!DOCTYPE html>
<html>
<head>
    <title>Slajd {slide_number}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        table {{
            border-collapse: collapse;
            background-color: transparent;
            width: 100%;
            height: 100%;
            position: relative;
        }}
        td {{
            {bg_style}
            background-size: cover;
            background-position: center;
        }}
        .text-box {{
            position: absolute;
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid #ccc;
            padding: 10px;
            box-sizing: border-box;
            line-height: 1.5;
        }}
        #header-box {{
            left: {header_x}px;
            top: {header_y}px;
            font-size: {header_size}px;
            font-family: {header_font};
            {header_style}
        }}
        #content-box {{
            left: {content_x}px;
            top: {content_y}px;
            font-size: {content_size}px;
            font-family: {content_font};
            {content_style}
        }}
    </style>
</head>
<body>
    <table>
        <tr>
            <td>
                {header_html}
                {content_html}
            </td>
        </tr>
    </table>
</body>
</html>'''
        
        # Przygotuj style tła
        bg_style = f"background-image: url('/slides/{bg_image}');" if bg_image else "background-color: #f0f0f0;"
        
        # Przygotuj style tekstu
        header_config = preset_config.get('header', {})
        content_config = preset_config.get('content', {})
        
        header_style = []
        if header_config.get('bold', False):
            header_style.append('font-weight: bold;')
        if header_config.get('italic', False):
            header_style.append('font-style: italic;')
        if header_config.get('underline', False):
            header_style.append('text-decoration: underline;')
        
        content_style = []
        if content_config.get('bold', False):
            content_style.append('font-weight: bold;')
        if content_config.get('italic', False):
            content_style.append('font-style: italic;')
        if content_config.get('underline', False):
            content_style.append('text-decoration: underline;')
        
        # Przygotuj HTML elementów
        header_html = ""
        content_html = ""
        
        if not header_config.get('hidden', False):
            header_html = f'<div id="header-box" class="text-box">{header_config.get("text", "Nagłówek")}</div>'
        
        if not content_config.get('hidden', False):
            content_html = f'<div id="content-box" class="text-box">{content_config.get("text", "Treść slajdu")}</div>'
        
        # Wypełnij template
        html_content = html_template.format(
            slide_number=slide_number,
            bg_style=bg_style,
            header_x=header_config.get('x', 50),
            header_y=header_config.get('y', 50),
            header_size=header_config.get('fontSize', 32),
            header_font=header_config.get('fontFamily', 'Arial, sans-serif'),
            header_style=' '.join(header_style),
            content_x=content_config.get('x', 50),
            content_y=content_config.get('y', 150),
            content_size=content_config.get('fontSize', 18),
            content_font=content_config.get('fontFamily', 'Arial, sans-serif'),
            content_style=' '.join(content_style),
            header_html=header_html,
            content_html=content_html
        )
        
        return html_content
    
    def create_slide(self, preset_name: str, images: Dict[str, str], 
                    custom_texts: Optional[Dict[str, str]] = None) -> int:
        """Tworzy nowy slajd na podstawie presetu."""
        
        # Załaduj preset
        preset_config = self.load_preset(preset_name)
        
        # Nadpisz teksty jeśli podano
        if custom_texts:
            if 'header' in custom_texts:
                preset_config['header']['text'] = custom_texts['header']
            if 'content' in custom_texts:
                preset_config['content']['text'] = custom_texts['content']
        
        # Pobierz numer następnego slajdu
        slide_number = self.get_next_slide_number()
        
        # Konwertuj do prostego HTML
        html_content = self.convert_to_simple_html(preset_config, images, slide_number)
        
        # Zapisz plik HTML
        slide_filename = f's{slide_number}.html'
        slide_path = os.path.join(self.slides_dir, slide_filename)
        
        with open(slide_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Aktualizuj liczbę slajdów
        self.update_slide_count(slide_number)
        
        print(f"Utworzono slajd: {slide_filename}")
        return slide_number

# Przykład użycia
if __name__ == "__main__":
    generator = SlideGenerator()
    
    # Test tworzenia slajdu
    slide_num = generator.create_slide(
        preset_name="preset-1",
        images={"green": "1.jpg"},  # Użyj obrazu z img_slides
        custom_texts={
            "header": "Testowy nagłówek",
            "content": "Testowa treść slajdu"
        }
    )
    
    print(f"Utworzono slajd numer: {slide_num}")