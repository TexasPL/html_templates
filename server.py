#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import threading
import webbrowser
import random
from flask import Flask, send_from_directory, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time

class SlideScreenshotApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Slide Screenshot Tool")
        self.root.geometry("300x150")
        self.root.resizable(False, False)
        
        self.port = random.randint(8000, 9999)
        self.server_running = False
        self.flask_app = None
        self.driver = None  # Persistent Chrome instance
        self.setup_gui()
        self.setup_flask()
        
    def setup_gui(self):
        # Główna ramka
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Przycisk otwórz
        self.open_button = ttk.Button(main_frame, text="Otwórz", command=self.open_browser)
        self.open_button.grid(row=0, column=0, pady=10)
        
        # Status połączenia
        self.status_label = ttk.Label(main_frame, text="Status: Nie uruchomiono")
        self.status_label.grid(row=1, column=0, pady=5)
        
        # Port info
        self.port_label = ttk.Label(main_frame, text=f"Port: {self.port}")
        self.port_label.grid(row=2, column=0, pady=5)
        
    def setup_flask(self):
        self.flask_app = Flask(__name__)
        
        @self.flask_app.route('/')
        def index():
            return send_from_directory('.', 'index.html')
            
        @self.flask_app.route('/slides/s<int:slide_num>.html')
        def serve_slide(slide_num):
            try:
                with open(f'slides/s{slide_num}.html', 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return "Slajd nie znaleziony", 404
                
        @self.flask_app.route('/number.txt')
        def serve_number():
            try:
                with open('number.txt', 'r') as f:
                    content = f.read()
                    print(f"[SERVER] Serwowanie number.txt: '{content}'")
                    return content
            except FileNotFoundError:
                print("[SERVER] BŁĄD: number.txt nie znaleziono, zwracam domyślną wartość 3")
                return "3"
                
        @self.flask_app.route('/slides/<path:filename>')
        def serve_slide_static(filename):
            return send_from_directory('slides', filename)
        
        @self.flask_app.route('/img_slides/<path:filename>')
        def serve_img_slide_static(filename):
            return send_from_directory('img_slides', filename)
        
        @self.flask_app.route('/slides/<path:slide_dir>/<path:filename>')
        def serve_slide_assets(slide_dir, filename):
            if slide_dir.startswith('p') and slide_dir[1:].isdigit():
                return send_from_directory(f'slides/{slide_dir}', filename)
            else:
                return "Not found", 404
        
        @self.flask_app.route('/templates/<path:filename>')
        def serve_template_static(filename):
            return send_from_directory('templates', filename)
        
        @self.flask_app.route('/api/template-images')
        def get_template_images():
            try:
                import os
                img_dir = 'img_slides'
                print(f"[API] Sprawdzam katalog: {img_dir}")
                if not os.path.exists(img_dir):
                    print(f"[API] Katalog {img_dir} nie istnieje")
                    return jsonify({'images': []})
                
                images = []
                for filename in os.listdir(img_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        images.append(filename)
                
                print(f"[API] Znaleziono {len(images)} obrazów: {images[:5]}...")
                return jsonify({'images': sorted(images)})
            except Exception as e:
                print(f"[API] Błąd template-images: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/create-slide', methods=['POST'])
        def create_slide():
            try:
                from slide_generator import SlideGenerator
                from flask import request
                
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Brak danych'}), 400
                
                preset = data.get('preset', 'preset-1')
                header = data.get('header', 'Nagłówek')
                content = data.get('content', 'Treść slajdu')
                image = data.get('image', None)
                
                generator = SlideGenerator()
                
                # Przygotuj dane obrazów
                images = {}
                if image:
                    images['green'] = image
                
                # Przygotuj teksty
                custom_texts = {
                    'header': header,
                    'content': content
                }
                
                # Utwórz slajd
                slide_number = generator.create_slide(preset, images, custom_texts)
                
                print(f"Utworzono slajd przez API: s{slide_number}.html")
                
                return jsonify({
                    'success': True, 
                    'slide_number': slide_number,
                    'message': f'Slajd {slide_number} został utworzony'
                })
                
            except Exception as e:
                print(f"Błąd tworzenia slajdu: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.flask_app.route('/api/presets/<path:filename>')
        def serve_preset(filename):
            return send_from_directory('templates/presets', filename)
        
        @self.flask_app.route('/api/save-preset', methods=['POST'])
        def save_preset():
            try:
                from flask import request
                import json
                
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Brak danych'}), 400
                
                preset_number = data.get('presetNumber')
                preset_data = data.get('presetData')
                
                if not preset_number or not preset_data:
                    return jsonify({'success': False, 'error': 'Nieprawidłowe dane'}), 400
                
                # Zapisz preset do pliku
                preset_filename = f'preset-{preset_number}.json'
                preset_path = os.path.join('templates/presets', preset_filename)
                
                with open(preset_path, 'w', encoding='utf-8') as f:
                    json.dump(preset_data, f, indent=4, ensure_ascii=False)
                
                print(f"Zapisano preset: {preset_filename}")
                
                return jsonify({
                    'success': True,
                    'message': f'Preset {preset_number} został zapisany',
                    'filename': preset_filename
                })
                
            except Exception as e:
                print(f"Błąd zapisu presetu: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.flask_app.route('/api/delete-preset', methods=['POST'])
        def delete_preset():
            try:
                from flask import request
                import os
                
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Brak danych'}), 400
                
                preset_number = data.get('presetNumber')
                
                if not preset_number:
                    return jsonify({'success': False, 'error': 'Nie podano numeru presetu'}), 400
                
                # Usuń walidację preset 1 - teraz można usunąć każdy preset
                
                # Usuń plik presetu
                preset_filename = f'preset-{preset_number}.json'
                preset_path = os.path.join('templates/presets', preset_filename)
                
                if os.path.exists(preset_path):
                    os.remove(preset_path)
                    print(f"Usunięto preset: {preset_filename}")
                    
                    return jsonify({
                        'success': True,
                        'message': f'Preset {preset_number} został usunięty'
                    })
                else:
                    return jsonify({'success': False, 'error': 'Plik presetu nie istnieje'}), 404
                
            except Exception as e:
                print(f"Błąd usuwania presetu: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.flask_app.route('/api/available-presets')
        def get_available_presets():
            try:
                import os
                presets_dir = 'templates/presets'
                presets = []
                
                if os.path.exists(presets_dir):
                    for filename in os.listdir(presets_dir):
                        if filename.startswith('preset-') and filename.endswith('.json'):
                            # Wyciągnij numer presetu z nazwy pliku
                            preset_num = filename.replace('preset-', '').replace('.json', '')
                            try:
                                presets.append(int(preset_num))
                            except ValueError:
                                continue
                
                return jsonify({'presets': sorted(presets)})
            except Exception as e:
                print(f"Błąd pobierania dostępnych presetów: {str(e)}")
                return jsonify({'presets': []})
        
        @self.flask_app.route('/api/export-slide', methods=['POST'])
        def export_slide():
            try:
                from flask import request
                import json
                import os
                import shutil
                
                data = request.get_json()
                if not data:
                    return jsonify({'success': False, 'error': 'Brak danych'}), 400
                
                # Znajdź następny numer katalogu p{n}
                slides_dir = 'slides'
                if not os.path.exists(slides_dir):
                    os.makedirs(slides_dir)
                
                next_num = 1
                existing_dirs = [d for d in os.listdir(slides_dir) if d.startswith('p') and d[1:].isdigit()]
                if existing_dirs:
                    existing_nums = [int(d[1:]) for d in existing_dirs]
                    next_num = max(existing_nums) + 1
                
                export_dir = os.path.join(slides_dir, f'p{next_num}')
                os.makedirs(export_dir, exist_ok=True)
                
                # Skopiuj obrazy jeśli są używane
                images_to_copy = []
                if data['green']['image']:
                    images_to_copy.append(data['green']['image'])
                if data['orange']['image']:
                    images_to_copy.append(data['orange']['image'])
                
                for image_name in images_to_copy:
                    src_path = os.path.join('img_slides', image_name)
                    dst_path = os.path.join(export_dir, image_name)
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, dst_path)
                
                # Generuj HTML
                html_content = generate_slide_html(data, f'p{next_num}')
                
                # Zapisz HTML
                html_path = os.path.join(export_dir, 's1.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                return jsonify({
                    'success': True,
                    'path': f'slides/p{next_num}/s1.html',
                    'directory': f'p{next_num}',
                    'message': f'Slajd wyeksportowany do {export_dir}'
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        def generate_slide_html(data, slide_dir):
            # Pomocnicze funkcje
            def get_border_radius(element_data):
                if element_data.get('circle'):
                    return '50%'
                elif element_data.get('rounded'):
                    w, h = element_data['w'], element_data['h']
                    radius = min(w, h) * 0.05
                    return f'{radius}px'
                return '0px'
            
            def get_text_decoration(styles):
                return 'underline' if styles.get('underline') else 'none'
            
            def get_font_weight(styles):
                return 'bold' if styles.get('bold') else 'normal'
            
            def get_font_style(styles):
                return 'italic' if styles.get('italic') else 'normal'
            
            def get_background_image(image_name, zoom):
                if image_name:
                    return f"background-image: url('slides/{slide_dir}/{image_name}'); background-size: {zoom}%; background-position: center; background-repeat: no-repeat;"
                return ""
            
            def load_html_snippet(snippet_file):
                """Ładuje snippet HTML z foldera presets"""
                try:
                    snippet_path = os.path.join('templates/presets', snippet_file)
                    if os.path.exists(snippet_path):
                        with open(snippet_path, 'r', encoding='utf-8') as f:
                            return f.read()
                    return ""
                except Exception as e:
                    print(f"Błąd ładowania snippetu {snippet_file}: {e}")
                    return ""
            
            def parse_snippet_content(snippet_html):
                """Parsuje snippet HTML i wydziela CSS oraz HTML"""
                import re
                
                # Wyciągnij CSS z <style>
                css_match = re.search(r'<style>(.*?)</style>', snippet_html, re.DOTALL)
                css_content = css_match.group(1).strip() if css_match else ""
                
                # Wyciągnij HTML bez <style>
                html_content = re.sub(r'<style>.*?</style>', '', snippet_html, flags=re.DOTALL).strip()
                
                return css_content, html_content
            
            # Generuj style CSS
            styles = f"""
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: {data['slide']['backgroundColor']};
                    font-family: Arial, sans-serif;
                }}
                .container {{
                    width: 1536px;
                    height: 864px;
                    position: relative;
                    margin: 0 auto;
                    background-color: {data['slide']['backgroundColor']};
                }}
            """
            
            # Green box
            if not data['green']['hidden']:
                # Sprawdź czy używa HTML snippet
                if data['green'].get('snippetFile'):
                    
                    # Załaduj i parsuj snippet
                    snippet_html = load_html_snippet(data['green']['snippetFile'])
                    if snippet_html:
                        snippet_css, snippet_html_content = parse_snippet_content(snippet_html)
                        
                        # Dodaj podstawowe style dla green-box z pozycjonowaniem
                        styles += f"""
                        .box2 {{
                            position: absolute;
                            left: {data['green']['x']}px;
                            top: {data['green']['y']}px;
                            width: {data['green']['w']}px;
                            height: {data['green']['h']}px;
                            border-radius: {get_border_radius(data['green'])};
                        }}
                        """
                        
                        # Dodaj CSS ze snippetu
                        styles += snippet_css
                    else:
                        # Fallback - zwykły green box
                        styles += f"""
                        .box2 {{
                            position: absolute;
                            left: {data['green']['x']}px;
                            top: {data['green']['y']}px;
                            width: {data['green']['w']}px;
                            height: {data['green']['h']}px;
                            background-color: #81c784;
                            border-radius: {get_border_radius(data['green'])};
                            {get_background_image(data['green']['image'], data['green']['zoom'])}
                        }}
                        """
                else:
                    # Standardowy green box
                    styles += f"""
                    .box2 {{
                        position: absolute;
                        left: {data['green']['x']}px;
                        top: {data['green']['y']}px;
                        width: {data['green']['w']}px;
                        height: {data['green']['h']}px;
                        background-color: #81c784;
                        border-radius: {get_border_radius(data['green'])};
                        {get_background_image(data['green']['image'], data['green']['zoom'])}
                    }}
                    """
                
                # Green caption (tylko jeśli nie używa snippet)
                if not data['green'].get('snippetFile') and data['green']['captionEnabled'] and data['green']['captionText']:
                    caption_x = data['green']['x'] + data['green']['w'] // 2
                    caption_y = data['green']['y'] + data['green']['h'] + 10
                    styles += f"""
                    .green-caption {{
                        position: absolute;
                        left: {caption_x}px;
                        top: {caption_y}px;
                        transform: translateX(-50%);
                        font-size: {data['green']['captionSize']}px;
                        background-color: {data['green']['captionBackgroundColor']};
                        color: {data['green']['captionColor']};
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-family: {data['content']['fontFamily']};
                    }}
                    """
            
            # Orange box  
            if not data['orange']['hidden']:
                # Sprawdź czy używa HTML snippet
                if data['orange'].get('snippetFile'):
                    
                    # Załaduj i parsuj snippet
                    snippet_html = load_html_snippet(data['orange']['snippetFile'])
                    if snippet_html:
                        snippet_css, snippet_html_content = parse_snippet_content(snippet_html)
                        
                        # Dodaj podstawowe style dla orange-box z pozycjonowaniem
                        styles += f"""
                        .box1 {{
                            position: absolute;
                            left: {data['orange']['x']}px;
                            top: {data['orange']['y']}px;
                            width: {data['orange']['w']}px;
                            height: {data['orange']['h']}px;
                            border-radius: {get_border_radius(data['orange'])};
                        }}
                        """
                        
                        # Dodaj CSS ze snippetu
                        styles += snippet_css
                    else:
                        # Fallback - zwykły orange box
                        styles += f"""
                        .box1 {{
                            position: absolute;
                            left: {data['orange']['x']}px;
                            top: {data['orange']['y']}px;
                            width: {data['orange']['w']}px;
                            height: {data['orange']['h']}px;
                            background-color: #ff9800;
                            border-radius: {get_border_radius(data['orange'])};
                            {get_background_image(data['orange']['image'], data['orange']['zoom'])}
                        }}
                        """
                else:
                    # Standardowy orange box
                    styles += f"""
                    .box1 {{
                        position: absolute;
                        left: {data['orange']['x']}px;
                        top: {data['orange']['y']}px;
                        width: {data['orange']['w']}px;
                        height: {data['orange']['h']}px;
                        background-color: #ff9800;
                        border-radius: {get_border_radius(data['orange'])};
                        {get_background_image(data['orange']['image'], data['orange']['zoom'])}
                    }}
                    """
                
                # Orange caption (tylko jeśli nie używa snippet)
                if not data['orange'].get('snippetFile') and data['orange']['captionEnabled'] and data['orange']['captionText']:
                    caption_x = data['orange']['x'] + data['orange']['w'] // 2
                    caption_y = data['orange']['y'] + data['orange']['h'] + 10
                    styles += f"""
                    .orange-caption {{
                        position: absolute;
                        left: {caption_x}px;
                        top: {caption_y}px;
                        transform: translateX(-50%);
                        font-size: {data['orange']['captionSize']}px;
                        background-color: {data['orange']['captionBackgroundColor']};
                        color: {data['orange']['captionColor']};
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-family: {data['content']['fontFamily']};
                    }}
                    """
            
            # Header
            if not data['header']['hidden']:
                styles += f"""
                .header {{
                    position: absolute;
                    left: {data['header']['x']}px;
                    top: {data['header']['y']}px;
                    font-size: {data['header']['fontSize']}px;
                    font-family: {data['header']['fontFamily']};
                    font-weight: {get_font_weight(data['header'])};
                    font-style: {get_font_style(data['header'])};
                    text-decoration: {get_text_decoration(data['header'])};
                    background-color: {data['header']['backgroundColor']};
                    color: {data['header']['color']};
                    padding-left: {data['header']['marginLeft']}px;
                    padding-right: {data['header']['marginRight']}px;
                    padding-top: 8px;
                    padding-bottom: 8px;
                    display: inline-block;
                }}
                """
            
            # Content
            if not data['content']['hidden']:
                styles += f"""
                .content {{
                    position: absolute;
                    left: {data['content']['x']}px;
                    top: {data['content']['y']}px;
                    font-size: {data['content']['fontSize']}px;
                    font-family: {data['content']['fontFamily']};
                    font-weight: {get_font_weight(data['content'])};
                    font-style: {get_font_style(data['content'])};
                    text-decoration: {get_text_decoration(data['content'])};
                    background-color: {data['content']['backgroundColor']};
                    color: {data['content']['color']};
                    padding-left: {data['content']['marginLeft']}px;
                    padding-right: {data['content']['marginRight']}px;
                    padding-top: 8px;
                    padding-bottom: 8px;
                    display: inline-block;
                    white-space: pre-wrap;
                    line-height: 1.2;
                }}
                """
            
            # Generuj HTML
            html_body = '<div class="container">'
            
            # Dodaj elementy
            if not data['green']['hidden']:
                # Sprawdź czy używa HTML snippet
                if data['green'].get('snippetFile'):
                    # Załaduj snippet HTML
                    snippet_html = load_html_snippet(data['green']['snippetFile'])
                    if snippet_html:
                        snippet_css, snippet_html_content = parse_snippet_content(snippet_html)
                        # Dodaj div z klasą box2-snippet i wewnętrznym HTML ze snippetu
                        html_body += f'<div class="green-box box2-snippet">{snippet_html_content}</div>'
                    else:
                        # Fallback - zwykły green box
                        html_body += '<div class="green-box"></div>'
                else:
                    # Standardowy green box
                    html_body += '<div class="green-box"></div>'
                    # Caption tylko dla standardowego green box
                    if data['green']['captionEnabled'] and data['green']['captionText']:
                        html_body += f'<div class="green-caption">{data["green"]["captionText"]}</div>'
            
            if not data['orange']['hidden']:
                # Sprawdź czy używa HTML snippet
                if data['orange'].get('snippetFile'):
                    # Załaduj snippet HTML
                    snippet_html = load_html_snippet(data['orange']['snippetFile'])
                    if snippet_html:
                        snippet_css, snippet_html_content = parse_snippet_content(snippet_html)
                        # Dodaj div z klasą box1-snippet i wewnętrznym HTML ze snippetu
                        html_body += f'<div class="orange-box box1-snippet">{snippet_html_content}</div>'
                    else:
                        # Fallback - zwykły orange box
                        html_body += '<div class="orange-box"></div>'
                else:
                    # Standardowy orange box
                    html_body += '<div class="orange-box"></div>'
                    # Caption tylko dla standardowego orange box
                    if data['orange']['captionEnabled'] and data['orange']['captionText']:
                        html_body += f'<div class="orange-caption">{data["orange"]["captionText"]}</div>'
            
            if not data['header']['hidden']:
                html_body += f'<div class="header">{data["header"]["text"]}</div>'
            
            if not data['content']['hidden']:
                html_body += f'<div class="content">{data["content"]["text"]}</div>'
            
            html_body += '</div>'
            
            # Kompletny HTML
            return f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eksportowany slajd</title>
    <style>
        {styles}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""
            
        @self.flask_app.route('/<path:filename>')
        def serve_static(filename):
            return send_from_directory('.', filename)
            
        @self.flask_app.route('/screenshot')
        def take_screenshot():
            try:
                # Pobierz aktualny slajd z sesji użytkownika
                from flask import request
                current_slide = request.args.get('slide', '1')
                self.capture_screenshot(current_slide)
                return jsonify({"status": "success", "message": f"Screenshot slajdu {current_slide} zapisany"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)})
    
    def ensure_driver_ready(self):
        """Upewnij się, że persistent Chrome driver jest gotowy"""
        if self.driver is None:
            print("Inicjalizacja Chrome...")
            
            # Konfiguracja Chrome
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--force-device-scale-factor=1')
            options.add_argument('--window-size=1600,1200')
            options.add_argument('--no-first-run')
            options.add_argument('--disable-default-apps')
            
            self.driver = webdriver.Chrome(options=options)
            
            self.driver.get(f'http://localhost:{self.port}')
            time.sleep(0.7)  # Skrócone z 1s
            print("Chrome persistent gotowy")

    def capture_screenshot(self, slide_number='1'):
        from PIL import Image
        import io
        import numpy as np
        
        # Upewnij się że driver jest gotowy
        self.ensure_driver_ready()
        
        try:
            # Przejdź do odpowiedniego slajdu
            if slide_number.startswith('p'):
                # Slajd z katalogu p{n}
                self.driver.execute_script(f"""
                    loadSlideFromP1();
                """)
                time.sleep(0.2)
            elif slide_number != '1':
                # Normalny slajd
                self.driver.execute_script(f"""
                    // Symuluj przejście do slajdu {slide_number}
                    currentSlide = {slide_number};
                    loadSlide(currentSlide);
                """)
                time.sleep(0.2)
            
            # Wymuszenie dokładnych rozmiarów + fix dla tabel snippetów
            self.driver.execute_script("""
                const slideWindow = document.getElementById('slide-window');
                slideWindow.style.width = '1536px';
                slideWindow.style.height = '864px';
                slideWindow.style.minHeight = '864px';
                slideWindow.style.maxHeight = '864px';
                slideWindow.style.overflow = 'hidden';
                slideWindow.style.backgroundColor = 'white';
                slideWindow.style.position = 'relative';
                
                // Fix specjalny dla snippet tables
                const snippetTables = slideWindow.querySelectorAll('.box1-snippet table, .box2-snippet table');
                snippetTables.forEach(table => {
                    table.style.display = 'table';
                    table.style.width = '100%';
                    table.style.height = '100%';
                    table.style.tableLayout = 'fixed';
                    table.style.borderCollapse = 'collapse';
                    
                    // Force rows to show
                    const rows = table.querySelectorAll('tr');
                    rows.forEach((row, index) => {
                        row.style.display = 'table-row';
                        row.style.height = '50%';
                        row.style.minHeight = '50%';
                    });
                    
                    // Force cells to show
                    const cells = table.querySelectorAll('td');
                    cells.forEach(cell => {
                        cell.style.display = 'table-cell';
                        cell.style.width = '50%';
                        cell.style.height = '50%';
                        cell.style.minHeight = '50%';
                        cell.style.verticalAlign = 'middle';
                    });
                });
            """)
            
            time.sleep(0.5)  # Zwiększone dla stabilności layout tabeli
            
            # Screenshot całej strony
            screenshot_png = self.driver.get_screenshot_as_png()
            img = Image.open(io.BytesIO(screenshot_png))
            
            # Znajdź element slajdu
            slide_element = self.driver.find_element("id", "slide-window")
            location = slide_element.location
            
            # Poprawka dla ujemnych pozycji
            left = location['x']
            top = location['y']
            
            # Jeśli pozycja Y jest ujemna, skoryguj ją
            if top < 0:
                top = 0
            
            # Jeśli pozycja X jest ujemna, skoryguj ją  
            if left < 0:
                left = 0
                
            right = left + 1536
            bottom = top + 864
            
            # Sprawdź czy nie wychodzimy poza granice
            if right > img.size[0]:
                right = img.size[0]
                left = right - 1536
                
            if bottom > img.size[1]:
                bottom = img.size[1]
                top = bottom - 864
                # Sprawdź czy top nie jest ujemne po korekcie
                if top < 0:
                    top = 0
                    bottom = min(864, img.size[1])
            
            cropped_img = img.crop((left, top, right, bottom))
            
            # Wymuszenie dokładnego rozmiaru 1536x864
            final_img = Image.new('RGB', (1536, 864), 'white')
            final_img.paste(cropped_img, (0, 0))
            
            timestamp = int(time.time())
            filename = f'screenshot_slide_{slide_number}_{timestamp}.png'
            final_img.save(filename, 'PNG')
            
        except Exception as e:
            # Nie zamykaj drivera - zostanie persistent
            raise
    
    def start_server(self):
        import logging
        from werkzeug.serving import WSGIRequestHandler
        
        print(f"[SERVER] Uruchamiam serwer na porcie {self.port}")
        
        # Sprawdź zawartość number.txt przy starcie
        try:
            with open('number.txt', 'r') as f:
                content = f.read()
                print(f"[SERVER] Zawartość number.txt przy starcie: '{content}'")
        except FileNotFoundError:
            print("[SERVER] OSTRZEŻENIE: number.txt nie istnieje przy starcie")
        
        # Własny handler który blokuje tylko request logi
        class QuietWSGIRequestHandler(WSGIRequestHandler):
            def log_request(self, code='-', size='-'):
                pass  # Blokuj logi requestów
        
        self.flask_app.run(
            host='localhost', 
            port=self.port, 
            debug=False, 
            use_reloader=False,
            request_handler=QuietWSGIRequestHandler
        )
    
    def open_browser(self):
        if not self.server_running:
            # Uruchom serwer w osobnym wątku
            server_thread = threading.Thread(target=self.start_server, daemon=True)
            server_thread.start()
            self.server_running = True
            self.status_label.config(text="Status: Uruchomiono")
            time.sleep(1)  # Krótkie opóźnienie na uruchomienie serwera
        
        # Otwórz przeglądarkę
        webbrowser.open(f'http://localhost:{self.port}')
    
    def run(self):
        try:
            self.root.mainloop()
        finally:
            # Zamknij persistent Chrome przy wyjściu
            if self.driver:
                print("Zamykanie Chrome...")
                self.driver.quit()

if __name__ == '__main__':
    app = SlideScreenshotApp()
    app.run()