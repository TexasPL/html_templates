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
                    return f.read()
            except FileNotFoundError:
                return "3"
                
        @self.flask_app.route('/slides/<path:filename>')
        def serve_slide_static(filename):
            return send_from_directory('slides', filename)
            
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
                print(f"BŁĄD screenshot: {str(e)}")
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
            if slide_number != '1':
                self.driver.execute_script(f"""
                    // Symuluj przejście do slajdu {slide_number}
                    currentSlide = {slide_number};
                    loadSlide(currentSlide);
                """)
                time.sleep(0.2)  # Skrócone z 0.5s
            
            # Wymuszenie dokładnych rozmiarów
            self.driver.execute_script("""
                const slideWindow = document.getElementById('slide-window');
                slideWindow.style.width = '1536px';
                slideWindow.style.height = '864px';
                slideWindow.style.minHeight = '864px';
                slideWindow.style.maxHeight = '864px';
                slideWindow.style.overflow = 'hidden';
                slideWindow.style.backgroundColor = 'white';
                slideWindow.style.position = 'relative';
                
                // Wymuszenie rozmiaru dla całej zawartości
                const allElements = slideWindow.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el.tagName === 'TABLE') {
                        el.style.width = '100%';
                        el.style.height = '100%';
                        el.style.minHeight = '864px';
                    }
                    if (el.tagName === 'TD') {
                        el.style.width = '100%';
                        el.style.height = '100%';
                        el.style.minHeight = '864px';
                    }
                });
            """)
            
            time.sleep(0.15)  # Skrócone z 0.3s
            
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
            print(f"Screenshot zapisany: {filename}")
            
        except Exception as e:
            print(f"BŁĄD capture_screenshot: {str(e)}")
            # Nie zamykaj drivera - zostanie persistent
            raise
    
    def start_server(self):
        import logging
        from werkzeug.serving import WSGIRequestHandler
        
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