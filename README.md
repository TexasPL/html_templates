# HTML Templates & Slide Screenshot Tool

Zaawansowane narzędzie do tworzenia i zarządzania szablonami slajdów HTML z funkcją automatycznego screenshota.

## Opis

System składa się z trzech głównych komponentów:
- **Template Editor** (`template-1.html`) - interaktywny edytor układów slajdów
- **Slide Viewer** (`index.html`) - przeglądarka i nawigacja między slajdami  
- **Screenshot Engine** (Python + Selenium) - tworzenie precyzyjnych screenshotów

## Główne funkcje

### 🎨 Template Editor
- ✅ Interaktywny edytor układów slajdów 1536x864px
- ✅ **Box 1** i **Box 2** - konfigurowalne pola z obrazami
- ✅ **HTML Snippets** - listy rozwijane z tabelami 2x2 i listami kropkowanymi
- ✅ **Kontrola konturów** - checkbox "usuń kontur" dla każdego pola
- ✅ Edycja tekstów (nagłówek/treść) z formatowaniem
- ✅ System presetów - zapisywanie/ładowanie układów
- ✅ **Eksport slajdów** - generowanie standalone HTML
- ✅ Pełna kontrola pozycji, rozmiarów, kolorów, fontów

### 📸 Screenshot Engine  
- ✅ Persistent Chrome - szybkie kolejne screenshoty (~0.5s)
- ✅ Dokładny rozmiar 1536x864px (16:9)
- ✅ Kompatybilność z eksportowanymi slajdami
- ✅ Stabilne renderowanie HTML snippets
- ✅ Wizualne statusy przycisku (ładowanie/sukces/błąd)

### 🖥️ Slide Viewer
- ✅ Nawigacja między slajdami standardowymi
- ✅ **Button P1** - ładowanie slajdów z template'ów
- ✅ Automatyczne wykrywanie ilości slajdów
- ✅ Kompaktowy interfejs z pływającymi kontrolkami

## Uruchomienie

```bash
pip install -r requirements.txt
python server.py
```

## Workflow

1. **Tworzenie template'ów**: Otwórz `template-1.html` → ustaw układ → wybierz HTML snippets → eksportuj 📤
2. **Testowanie**: Kliknij P1 w `index.html` → sprawdź slajd  
3. **Screenshot**: Naciśnij 📷 → zapisz wysokiej jakości PNG

## HTML Snippets

### Dostępne typy
- **Box 1 Snippets**: `box1a.html` (tabela 2x2), `box1b.html` (lista kropkowana)  
- **Box 2 Snippets**: `box2a.html` (tabela 2x2), `box2b.html` (lista kropkowana)

### Funkcjonalności
- **Lista rozwijana "HTML"** - wybór typu snippet'u dla każdego pola
- **Checkbox "usuń kontur"** - kontrola widoczności czerwonej ramki
- **Podgląd na żywo** - natychmiastowa wizualizacja w edytorze
- **Kompatybilność wsteczna** - automatyczna konwersja starych presetów

## Struktura

```
├── server.py              # Backend (Flask + Selenium + GUI)
├── index.html             # Slide Viewer - przeglądarka slajdów
├── templates/             # System template'ów
│   ├── template-1.html    # Template Editor - główny edytor  
│   ├── template-1.css     # Style editora
│   └── presets/           # Zapisane presety układów + HTML snippety
│       ├── preset-1.json  # Preset koła
│       ├── preset-2.json  # Preset prostokąty
│       ├── box1a.html     # Tabela 2x2 dla Box 1
│       ├── box1b.html     # Lista kropkowana dla Box 1
│       ├── box2a.html     # Tabela 2x2 dla Box 2
│       └── box2b.html     # Lista kropkowana dla Box 2
├── slides/                # Slajdy HTML + obrazy
│   ├── s1.html, s2.html   # Standardowe slajdy
│   ├── p1/, p2/           # Eksportowane template'y
│   │   ├── s1.html        # Standalone slajd 
│   │   └── *.jpg          # Skopiowane grafiki
│   └── *.jpg              # Obrazy dla standardowych slajdów
├── img_slides/            # Bank grafik dla template'ów
├── slide_generator.py     # Generator slajdów (API helper)
├── number.txt             # Liczba standardowych slajdów
└── requirements.txt       # Zależności Python
```

## API Endpoints

- `GET /templates/template-1.html` - Template Editor
- `POST /api/export-slide` - Eksport template'u  
- `GET /api/available-presets` - Lista presetów
- `POST /api/save-preset` - Zapisanie presetu
- `GET /slides/p{n}/{filename}` - Serwowanie plików z template'ów
- `GET /screenshot?slide={id}` - Screenshot slajdu

## Konfiguracja slajdów

### number.txt
Plik zawiera jedną liczbę określającą ilość dostępnych slajdów. Aplikacja:

1. **Przy starcie** - frontend fetch `number.txt` i ustawia `totalSlides`
2. **Automatycznie wykrywa** - które slajdy istnieją (s1.html, s2.html, etc.)
3. **Dynamicznie ładuje** - tylko istniejące pliki `slides/s{N}.html`
4. **Kontroluje nawigację** - wyłącza przyciski gdy brak kolejnych slajdów

### Dodawanie nowych slajdów
1. Utwórz `slides/s{N}.html` (gdzie N = kolejny numer)
2. Dodaj obrazy do `slides/` jeśli potrzebne
3. Zaktualizuj `number.txt` zwiększając liczbę o 1
4. Restart nie jest wymagany - frontend automatycznie wykryje zmiany