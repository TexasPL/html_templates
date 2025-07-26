import json
import os
from pathlib import Path
import time
from datetime import datetime, timedelta
from google import genai
from google.genai import types
import requests
import threading
import traceback
import socket
import webbrowser
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
from PIL import Image, UnidentifiedImageError
import io
import PyPDF2

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = SCRIPT_DIR / "config.json"
API_HISTORY_DIR = SCRIPT_DIR / "api-history"
LOG_FILE_ERROR = SCRIPT_DIR / "error-backend.txt"
GEMINI_MODEL_NAME_FILE = SCRIPT_DIR / "gemini_model_name.txt"
TOKEN_STATS_FILE = SCRIPT_DIR / "token_stats.json"
HOST = "0.0.0.0"
PORT = 8147
MAX_FILES = 5

def load_gemini_model_name():
    try:
        with open(GEMINI_MODEL_NAME_FILE, 'r', encoding='utf-8') as f:
            model_name = f.readline().strip()
            return model_name if model_name else "gemini-1.5-flash-latest"
    except FileNotFoundError:
        return "gemini-1.5-flash-latest"

GEMINI_MODEL_NAME = load_gemini_model_name()
MODEL_INFO_FILE = SCRIPT_DIR / "model_info.txt"

def load_model_info():
    """Ładuje informacje o modelach z pliku model_info.txt"""
    models = []
    try:
        with open(MODEL_INFO_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_category = None
        for line in lines:
            line = line.strip()
            if line.startswith('##'):
                current_category = line.replace('##', '').strip()
            elif ' - ' in line and not line.startswith('#'):
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    model_name = parts[0].strip()
                    description = parts[1].strip()
                    models.append({
                        'name': model_name,
                        'description': description,
                        'category': current_category
                    })
    except FileNotFoundError:
        print(f"Plik {MODEL_INFO_FILE} nie został znaleziony")
    except Exception as e:
        print(f"Błąd wczytywania model_info.txt: {e}")
    
    return models

class BackendApp:
    def __init__(self):
        self.config = self.load_config()
        self.gemini_api_key = self.config.get('api_key_gemini')

        self.active_threads = set()
        self.shutting_down = False

        self.gemini_client = None
        self.chat_sessions = {}
        self.current_model = GEMINI_MODEL_NAME
        self.model_info = load_model_info()
        self.api_connection_status = {self.current_model: None}
        self.token_usage_history = []  # Lista z timestampami i liczbą tokenów
        
        # Wczytaj statystyki tokenów z pliku
        self.load_token_stats()
        
        API_HISTORY_DIR.mkdir(exist_ok=True)

        if not self.gemini_api_key:
            self.log("BŁĄD: Brak klucza API Gemini w config.json.", is_error=True)
        else:
            self.initialize_api_clients()
            self.run_initial_connection_tests()

    def log(self, message, is_error=False):
        timestamped_message = f"{time.strftime('%H:%M:%S')} - {message}"
        
        if is_error:
            print(timestamped_message)
            try:
                with open(LOG_FILE_ERROR, "a", encoding="utf-8") as f:
                    f.write(timestamped_message + "\n")
            except Exception as e:
                print(f"BŁĄD zapisu do pliku logów: {e}")

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.log(f"BŁĄD: Nie można wczytać pliku konfiguracyjnego {CONFIG_FILE}: {e}", is_error=True)
            return {}

    def initialize_api_clients(self):
        if self.gemini_api_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                self.log(f"BŁĄD inicjalizacji Gemini: {e}", is_error=True)
                self.gemini_client = None

    def create_tracked_thread(self, target, args=()):
        if self.shutting_down:
            return None

        def wrapper():
            thread_id = threading.get_ident()
            self.active_threads.add(thread_id)
            try:
                target(*args)
            except Exception as e:
                self.log(f"Nieoczekiwany błąd w wątku {thread_id}: {e}\n{traceback.format_exc()}", is_error=True)
            finally:
                self.active_threads.discard(thread_id)

        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
        return thread

    def test_api_connection(self, model_name=None):
        if model_name is None:
            model_name = self.current_model
        
        test_prompt = "Podaj odp. 1 cyfrą. 2+1=?"
        status = False
        if not self.gemini_client:
             self.log(f"Test {model_name}: Klient niezainicjalizowany.", is_error=True)
        else:
            try:
                test_session = self.gemini_client.chats.create(model=model_name)
                response = test_session.send_message(test_prompt)
                status = "3" in response.text
                if not status:
                    self.log(f"Test połączenia API dla {model_name}: Nie powiódł się.", is_error=True)
            except Exception as e:
                self.log(f"Błąd podczas testu API dla {model_name}: {e}", is_error=True)

        self.api_connection_status[model_name] = status
        return status

    def run_initial_connection_tests(self):
        try:
            requests.get("https://www.google.com", timeout=5)
            self.create_tracked_thread(target=self.test_api_connection, args=(self.current_model,))
        except (requests.ConnectionError, Exception) as e:
            self.log(f"Brak połączenia z internetem lub błąd: {e}", is_error=True)
            self.api_connection_status[self.current_model] = False

    def save_api_communication(self, prompt, response_text, file_names, session_id=None, remember_conversation=False):
        try:
            if remember_conversation and session_id:
                # Tryb sesji - zapisz do jednego pliku z historią całej konwersacji
                date_timestamp = time.strftime("%Y%m%d")
                safe_session_name = session_id.replace("/", "_").replace(":", "_").replace(" ", "_")
                session_filename = f"{date_timestamp}_{safe_session_name}.txt"
                session_file_path = API_HISTORY_DIR / session_filename
                
                # Przygotuj content do zapisu - dokładnie to co zostało wysłane do API
                ask_content = f"###ASK### ({time.strftime('%H:%M:%S')})\n{prompt}\n"
                
                response_content = f"\n###RESPONSE### ({time.strftime('%H:%M:%S')})\n{response_text}\n"
                separator = "\n" + "="*80 + "\n\n"
                
                # Dopisz do istniejącego pliku lub utwórz nowy
                full_content = ask_content + response_content + separator
                if session_file_path.exists():
                    # Dopisz do istniejącego pliku
                    with open(session_file_path, 'a', encoding='utf-8') as f:
                        f.write(full_content)
                else:
                    # Utwórz nowy plik z nagłówkiem sesji
                    session_header = f"=== SESJA: {session_id} ===\n"
                    session_header += f"=== ROZPOCZĘTA: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n"
                    session_header += f"=== MODEL: {self.current_model} ===\n\n"
                    with open(session_file_path, 'w', encoding='utf-8') as f:
                        f.write(session_header + full_content)
                
                self.log(f"Zapisano do pliku sesji: {session_filename}")
            else:
                # Tryb jednorazowy - zachowaj oryginalny sposób zapisu
                timestamp_dir_name = time.strftime("%Y-%m-%d_%H-%M-%S")
                history_folder = API_HISTORY_DIR / timestamp_dir_name
                history_folder.mkdir(exist_ok=True, parents=True)

                ask_content = f"--- PROMPT ---\n{prompt}\n"

                (history_folder / "ask.txt").write_text(ask_content, encoding="utf-8")

                safe_model_name = self.current_model.replace("/", "_").replace(":", "_")
                response_filename = f"response_{safe_model_name}.txt"
                (history_folder / response_filename).write_text(str(response_text), encoding="utf-8")
                self.log(f"Zapisano historię zapytania w: {history_folder}")
                
        except Exception as e:
            self.log(f"Błąd podczas zapisywania komunikacji API: {e}", is_error=True)

    def verify_pdf(self, file_data):
        try:
            pdf_stream = io.BytesIO(file_data)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            # Sprawdź czy PDF ma co najmniej jedną stronę
            if len(pdf_reader.pages) == 0:
                return False
            pdf_stream.close()
            return True
        except Exception as e:
            self.log(f"BŁĄD weryfikacji PDF: {e}", is_error=True)
            return False

    def get_or_create_session(self, session_id):
        """Pobiera istniejącą sesję lub tworzy nową"""
        if session_id not in self.chat_sessions:
            try:
                session_obj = self.gemini_client.chats.create(model=self.current_model)
                self.chat_sessions[session_id] = session_obj
                self.log(f"Utworzono nową sesję: {session_id} z modelem {self.current_model}")
            except Exception as e:
                self.log(f"BŁĄD tworzenia sesji {session_id}: {e}", is_error=True)
                raise
        return self.chat_sessions[session_id]
    
    def reset_session(self, session_id):
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            self.log(f"Zresetowano sesję: {session_id}")
            return True
        return False

    def generate_response(self, prompt, files, session_id=None, remember_conversation=False):
        num_files = len(files)
        log_suffix = f" + {num_files} plik(ów)" if num_files > 0 else ""
        mode_suffix = f" (sesja: {session_id})" if remember_conversation and session_id else ""
        self.log(f"Otrzymano żądanie dla modelu: {self.current_model}{log_suffix}{mode_suffix}")
        
        response_data = {"message": ""}

        if not self.gemini_client:
            response_data["message"] = f"Błąd: Klient Gemini nie jest zainicjalizowany."
            self.log(response_data["message"], is_error=True)
            return response_data

        try:
            if remember_conversation and session_id:
                # Tryb sesji - użyj lub utwórz sesję
                chat_session = self.get_or_create_session(session_id)
                
                # Przygotuj zawartość wiadomości
                message_content = [prompt]
                processed_file_names = []
                
                # Dodaj pliki do wiadomości (są automatycznie zapamiętane w sesji)
                for file in files:
                    try:
                        file_data = file.read()
                        file_name = file.filename

                        if file.mimetype.startswith('image/'):
                            try:
                                # Zweryfikuj obraz
                                img = Image.open(io.BytesIO(file_data))
                                img.verify()
                                img.close()  # Zwolnij zasoby po weryfikacji
                                
                                # Utwórz obraz do użycia
                                pil_image = Image.open(io.BytesIO(file_data))
                                message_content.append(pil_image)
                                processed_file_names.append(file_name)
                                self.log(f"Dodano obraz do sesji: {file_name}")
                            except (UnidentifiedImageError, Exception) as img_err:
                                self.log(f"BŁĄD weryfikacji obrazu {file_name}: {img_err}. Pomijanie.", is_error=True)
                                continue

                        elif file.mimetype == 'application/pdf':
                            if self.verify_pdf(file_data):
                                pdf_part = types.Part.from_bytes(
                                    data=file_data,
                                    mime_type='application/pdf'
                                )
                                message_content.append(pdf_part)
                                processed_file_names.append(file_name)
                                self.log(f"Dodano PDF do sesji: {file_name}")
                            else:
                                self.log(f"BŁĄD: Plik {file_name} nie jest prawidłowym PDF. Pomijanie.", is_error=True)
                                continue
                        else:
                            self.log(f"OSTRZEŻENIE: Nieobsługiwany typ pliku: {file.mimetype} dla {file_name}. Pomijanie.", is_error=True)
                            continue
                        file.seek(0)
                    except Exception as e:
                        self.log(f"BŁĄD przetwarzania pliku {file.filename}: {e}. Pomijanie.", is_error=True)
                        continue
                
                # Wyślij wiadomość w sesji
                response = chat_session.send_message(message_content)
                
                # Pobierz historię sesji dla liczenia tokenów
                total_tokens = 0
                try:
                    history = chat_session.get_history(curated=True)
                    
                    # Liczenie tokenów - sprawdzamy każdy content w historii
                    for content in history:
                        if hasattr(content, 'usage_metadata') and content.usage_metadata:
                            total_tokens += content.usage_metadata.total_token_count
                    
                    # Jeśli historia nie ma metadanych tokenów, użyj danych z aktualnej odpowiedzi
                    if total_tokens == 0 and hasattr(response, 'usage_metadata') and response.usage_metadata:
                        total_tokens = response.usage_metadata.total_token_count
                    
                except Exception as e:
                    self.log(f"❌ BŁĄD: Problem z get_history: {e}", is_error=True)
                    # FALLBACK: Użyj danych z aktualnej odpowiedzi
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        total_tokens = response.usage_metadata.total_token_count
                
                self.log(f"📊 TOKENY SESJI: {total_tokens}")
                
                # Dodaj tokeny z aktualnego zapytania do historii
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    current_request_tokens = response.usage_metadata.total_token_count
                    self.add_token_usage(current_request_tokens)
                
                
            else:
                # Tryb jednorazowy - bez sesji
                self.log("Tryb jednorazowy (bez sesji)")
                
                # Utwórz tymczasową sesję
                temp_session = self.gemini_client.chats.create(model=self.current_model)
                
                # Przygotuj zawartość wiadomości
                message_content = [prompt]
                processed_file_names = []
                
                # Dodaj pliki
                for file in files:
                    try:
                        file_data = file.read()
                        file_name = file.filename

                        if file.mimetype.startswith('image/'):
                            try:
                                # Zweryfikuj obraz
                                img = Image.open(io.BytesIO(file_data))
                                img.verify()
                                img.close()  # Zwolnij zasoby po weryfikacji
                                
                                # Utwórz obraz do użycia
                                pil_image = Image.open(io.BytesIO(file_data))
                                message_content.append(pil_image)
                                processed_file_names.append(file_name)
                                self.log(f"Dodano obraz: {file_name}")
                            except (UnidentifiedImageError, Exception) as img_err:
                                self.log(f"BŁĄD weryfikacji obrazu {file_name}: {img_err}. Pomijanie.", is_error=True)
                                continue

                        elif file.mimetype == 'application/pdf':
                            if self.verify_pdf(file_data):
                                pdf_part = types.Part.from_bytes(
                                    data=file_data,
                                    mime_type='application/pdf'
                                )
                                message_content.append(pdf_part)
                                processed_file_names.append(file_name)
                                self.log(f"Dodano PDF: {file_name}")
                            else:
                                self.log(f"BŁĄD: Plik {file_name} nie jest prawidłowym PDF. Pomijanie.", is_error=True)
                                continue
                        else:
                            self.log(f"OSTRZEŻENIE: Nieobsługiwany typ pliku: {file.mimetype} dla {file_name}. Pomijanie.", is_error=True)
                            continue
                        file.seek(0)
                    except Exception as e:
                        self.log(f"BŁĄD przetwarzania pliku {file.filename}: {e}. Pomijanie.", is_error=True)
                        continue
                
                # Wyślij wiadomość
                response = temp_session.send_message(message_content)
                total_tokens = 0
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    total_tokens = response.usage_metadata.total_token_count
                    self.log(f"📊 TOKENY: {total_tokens}")
                    # Dodaj tokeny do historii
                    self.add_token_usage(total_tokens)

            response_text = ""
            try:
                response_text = response.text
            except ValueError as text_extract_err:
                response_text = f"Błąd: Odpowiedź zablokowana. ({text_extract_err})"
                self.log(f"BŁĄD: Odpowiedź zablokowana: {text_extract_err}", is_error=True)
            except Exception as text_extract_err:
                response_text = f"Błąd: Nie można wyodrębnić tekstu z odpowiedzi: {text_extract_err}"
                self.log(f"BŁĄD wyodrębniania tekstu: {text_extract_err}", is_error=True)

            response_data["message"] = response_text
            
            # Dodaj licznik tokenów
            if remember_conversation:
                response_data["sessionTokenCount"] = total_tokens
                response_data["sessionId"] = session_id
            else:
                # Tryb pojedynczej wiadomości - dodaj informacje o tokenach
                response_data["singleMessageTokens"] = total_tokens
                # Spróbuj wyodrębnić tokeny wejściowe i wyjściowe
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    metadata = response.usage_metadata
                    if hasattr(metadata, 'prompt_token_count') and hasattr(metadata, 'candidates_token_count'):
                        response_data["inputTokens"] = metadata.prompt_token_count
                        response_data["outputTokens"] = metadata.candidates_token_count
                    else:
                        response_data["inputTokens"] = "N/A"
                        response_data["outputTokens"] = "N/A"
            
            self.log(f"Gemini ({self.current_model}) odpowiedź wygenerowana.")
            self.create_tracked_thread(self.save_api_communication, args=(prompt, response_text, processed_file_names, session_id, remember_conversation))

        except Exception as e:
            error_message = f"Błąd podczas generowania odpowiedzi ({self.current_model}): {e}"
            self.log(error_message, is_error=True)
            self.log(traceback.format_exc(), is_error=True)
            response_data["message"] = f"Wystąpił błąd serwera podczas przetwarzania zapytania: {e}"

        return response_data

    def get_predefined_prompt(self, prompt_id):
        self.log(f"Żądanie predefiniowanego promptu: {prompt_id}")
        filepath = SCRIPT_DIR / f"Prompt{prompt_id}.txt"
        try:
            return {"success": True, "prompt_text": filepath.read_text(encoding='utf-8')}
        except FileNotFoundError:
            self.log(f"BŁĄD: Nie znaleziono pliku promptu: {filepath.name}", is_error=True)
            return {"success": False, "message": f"Plik {filepath.name} nie został znaleziony."}
        except Exception as e:
            self.log(f"BŁĄD: Odczyt pliku {filepath.name}: {e}", is_error=True)
            return {"success": False, "message": f"Błąd odczytu pliku {filepath.name}."}

    def check_session_name_availability(self, session_id):
        try:
            date_timestamp = time.strftime("%Y%m%d")
            safe_session_name = session_id.replace("/", "_").replace(":", "_").replace(" ", "_")
            session_filename = f"{date_timestamp}_{safe_session_name}.txt"
            session_file_path = API_HISTORY_DIR / session_filename
            
            return not session_file_path.exists()
        except Exception as e:
            self.log(f"Błąd sprawdzania dostępności nazwy sesji: {e}", is_error=True)
            return False

    def load_token_stats(self):
        """Wczytaj statystyki tokenów z pliku JSON"""
        try:
            if TOKEN_STATS_FILE.exists():
                with open(TOKEN_STATS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Przekonwertuj timestampy z string z powrotem na datetime
                for entry in data:
                    entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                
                # Usuń wpisy starsze niż 24 godziny
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(hours=24)
                self.token_usage_history = [
                    entry for entry in data 
                    if entry['timestamp'] > cutoff_time
                ]
                
                self.log(f"Wczytano {len(self.token_usage_history)} wpisów statystyk tokenów")
        except Exception as e:
            self.log(f"BŁĄD wczytywania statystyk tokenów: {e}", is_error=True)
            self.token_usage_history = []

    def save_token_stats(self):
        """Zapisz statystyki tokenów do pliku JSON"""
        try:
            # Przekonwertuj datetime na string dla JSON
            data = []
            for entry in self.token_usage_history:
                data.append({
                    'timestamp': entry['timestamp'].isoformat(),
                    'tokens': entry['tokens']
                })
            
            with open(TOKEN_STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.log(f"BŁĄD zapisu statystyk tokenów: {e}", is_error=True)

    def add_token_usage(self, token_count):
        """Dodaj użycie tokenów do historii"""
        if token_count > 0:
            current_time = datetime.now()
            self.token_usage_history.append({
                'timestamp': current_time,
                'tokens': token_count
            })
            
            # Usuń wpisy starsze niż 24 godziny
            cutoff_time = current_time - timedelta(hours=24)
            self.token_usage_history = [
                entry for entry in self.token_usage_history 
                if entry['timestamp'] > cutoff_time
            ]
            
            # Zapisz zaktualizowane statystyki
            self.save_token_stats()

    def get_token_statistics(self):
        """Pobierz statystyki tokenów dla różnych przedziałów czasowych"""
        if not self.token_usage_history:
            return {
                'last_minute': 0,
                'last_hour': 0,
                'last_day': 0
            }
        
        current_time = datetime.now()
        minute_ago = current_time - timedelta(minutes=1)
        hour_ago = current_time - timedelta(hours=1)
        day_ago = current_time - timedelta(hours=24)
        
        stats = {
            'last_minute': sum(entry['tokens'] for entry in self.token_usage_history 
                              if entry['timestamp'] > minute_ago),
            'last_hour': sum(entry['tokens'] for entry in self.token_usage_history 
                            if entry['timestamp'] > hour_ago),
            'last_day': sum(entry['tokens'] for entry in self.token_usage_history 
                           if entry['timestamp'] > day_ago)
        }
        
        return stats

    def cleanup_threads(self):
        self.shutting_down = True
        # Zapisz statystyki tokenów przed zamknięciem
        self.save_token_stats()
        
        # Wyczyść wszystkie sesje
        self.chat_sessions.clear()
        self.log("Zamykanie wątków i czyszczenie sesji...")
        
        # Poczekaj na zakończenie wszystkich wątków
        import time
        max_wait = 5  # maksymalnie 5 sekund
        wait_time = 0.1
        while self.active_threads and max_wait > 0:
            time.sleep(wait_time)
            max_wait -= wait_time
            
        if self.active_threads:
            self.log(f"OSTRZEŻENIE: {len(self.active_threads)} wątków nie zostało zakończonych", is_error=True)




def get_ip_address():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.1)
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    backend_app = BackendApp()

    flask_app = Flask(__name__)
    CORS(flask_app)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    @flask_app.route('/')
    def serve_index():
        try:
            return send_from_directory(SCRIPT_DIR, 'index.html')
        except FileNotFoundError:
            backend_app.log("BŁĄD: Nie znaleziono pliku index.html", is_error=True)
            return "Error: index.html not found.", 404

    @flask_app.route('/api/config', methods=['GET'])
    def get_config():
        return jsonify({
            "model": backend_app.current_model,
            "connection_status": backend_app.api_connection_status.get(backend_app.current_model),
            "max_files": MAX_FILES
        })
    
    @flask_app.route('/api/models', methods=['GET'])
    def get_models():
        return jsonify({
            "models": backend_app.model_info,
            "current_model": backend_app.current_model
        })
    
    @flask_app.route('/api/change-model', methods=['POST'])
    def change_model():
        try:
            data = request.get_json()
            new_model = data.get('model')
            
            if not new_model:
                return jsonify({"success": False, "message": "Brak nazwy modelu"}), 400
            
            # Sprawdź czy model istnieje w liście
            model_names = [m['name'] for m in backend_app.model_info]
            if new_model not in model_names:
                return jsonify({"success": False, "message": "Nieznany model"}), 400
            
            # Zmień aktualny model
            backend_app.current_model = new_model
            
            # Ustaw status na None (testowanie w toku)
            backend_app.api_connection_status[new_model] = None
            
            # Uruchom test API w osobnym wątku
            backend_app.create_tracked_thread(target=backend_app.test_api_connection, args=(new_model,))
            
            return jsonify({
                "success": True, 
                "message": f"Model zmieniony na {new_model}",
                "model": new_model,
                "testing": True
            })
            
        except Exception as e:
            backend_app.log(f"Błąd zmiany modelu: {e}", is_error=True)
            return jsonify({"success": False, "message": f"Błąd: {e}"}), 500

    @flask_app.route('/api/generate', methods=['POST'])
    def generate():
        try:
            if 'prompt' not in request.form:
                return jsonify({"message": "Brakujące dane 'prompt' w formularzu"}), 400

            prompt = request.form['prompt']
            files = request.files.getlist('files')
            remember_conversation = request.form.get('rememberConversation') == 'true'
            session_id = request.form.get('sessionId', 'default') if remember_conversation else None

            if len(files) > MAX_FILES:
                return jsonify({"message": f"Przekroczono limit {MAX_FILES} plików."}), 400

            result = backend_app.generate_response(prompt, files, session_id, remember_conversation)
            return jsonify(result)

        except Exception as e:
            backend_app.log(f"Krytyczny błąd w /api/generate: {e}\n{traceback.format_exc()}", is_error=True)
            return jsonify({"message": f"Wewnętrzny błąd serwera: {e}"}), 500

    @flask_app.route('/api/prompt/<int:prompt_id>', methods=['GET'])
    def get_prompt(prompt_id):
        result = backend_app.get_predefined_prompt(prompt_id)
        return jsonify(result), 200 if result["success"] else 404

    @flask_app.route('/api/reset-session', methods=['POST'])
    def reset_session():
        try:
            session_id = request.json.get('sessionId', 'default')
            success = backend_app.reset_session(session_id)
            return jsonify({"success": success, "message": f"Sesja {session_id} zresetowana" if success else "Sesja nie istnieje"})
        except Exception as e:
            backend_app.log(f"Błąd resetowania sesji: {e}", is_error=True)
            return jsonify({"success": False, "message": f"Błąd: {e}"}), 500

    @flask_app.route('/api/check-session-availability', methods=['POST'])
    def check_session_availability():
        try:
            session_id = request.json.get('sessionId', '')
            if not session_id:
                return jsonify({"available": False, "message": "Nazwa sesji nie może być pusta"}), 400
            
            is_available = backend_app.check_session_name_availability(session_id)
            return jsonify({
                "available": is_available,
                "message": "Nazwa dostępna" if is_available else "Nazwa sesji już istnieje dla dzisiejszego dnia"
            })
        except Exception as e:
            backend_app.log(f"Błąd sprawdzania dostępności nazwy sesji: {e}", is_error=True)
            return jsonify({"available": False, "message": f"Błąd: {e}"}), 500

    @flask_app.route('/api/token-stats', methods=['GET'])
    def get_token_stats():
        try:
            stats = backend_app.get_token_statistics()
            return jsonify(stats)
        except Exception as e:
            backend_app.log(f"Błąd pobierania statystyk tokenów: {e}", is_error=True)
            return jsonify({"last_minute": 0, "last_hour": 0, "last_day": 0}), 500

    def run_flask():
        try:
            flask_app.run(host=HOST, port=PORT, debug=False)
        except Exception as e:
             backend_app.log(f"FATAL: Flask server failed: {e}", is_error=True)
             os._exit(1)

    threading.Thread(target=run_flask, daemon=True).start()

    server_ip = get_ip_address()
    print(f"Serwer uruchomiony. Dostępny pod adresem: http://{server_ip}:{PORT}")
    print(f"Domyślny model: {GEMINI_MODEL_NAME}")
    
    # Automatyczne otwieranie index.html
    try:
        webbrowser.open(f"http://{server_ip}:{PORT}")
    except Exception as e:
        print(f"Nie można otworzyć przeglądarki: {e}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")
        backend_app.cleanup_threads()