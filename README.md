[pierwszy GIT commit (lokalnie) 13.07.2025]

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
- ✅ Dwa konfigurowalne pola (zielone/pomarańczowe) z obrazami
- ✅ Edycja tekstów (nagłówek/treść) z formatowaniem
- ✅ System presetów - zapisywanie/ładowanie układów
- ✅ **Eksport slajdów** - generowanie standalone HTML
- ✅ **HTML Snippety** - niestandardowe HTML w polach (prototyp)
- ✅ Pełna kontrola pozycji, rozmiarów, kolorów, fontów

### 📸 Screenshot Engine  
- ✅ Persistent Chrome - szybkie kolejne screenshoty (~0.5s)
- ✅ Dokładny rozmiar 1536x864px (16:9)
- ✅ Kompatybilność z eksportowanymi slajdami
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

## Konfiguracja slajdów

### number.txt
Plik zawiera jedną liczbę określającą ilość dostępnych slajdów. Aplikacja:

1. **Przy starcie** - frontend fetch `number.txt` i ustawia `totalSlides`
2. **Automatycznie wykrywa** - które slajdy istnieją (s1.html, s2.html, etc.)
3. **Dynamicznie ładuje** - tylko istniejące pliki `slides/s{N}.html`
4. **Kontroluje nawigację** - wyłącza przyciski gdy brak kolejnych slajdów

**Przykład:** `number.txt` zawiera `3` → aplikacja oczekuje s1.html, s2.html, s3.html

### Dodawanie nowych slajdów
1. Utwórz `slides/s{N}.html` (gdzie N = kolejny numer)
2. Dodaj obrazy do `slides/` jeśli potrzebne
3. Zaktualizuj `number.txt` zwiększając liczbę o 1
4. Restart nie jest wymagany - frontend automatycznie wykryje zmiany

## Workflow

1. **Tworzenie template'ów**: Otwórz `template-1.html` → ustaw układ → eksportuj 📤
2. **Testowanie**: Kliknij P1 w `index.html` → sprawdź slajd  
3. **Screenshot**: Naciśnij 📷 → zapisz wysokiej jakości PNG

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
│       ├── box1.html      # HTML snippet - tabela 2x2 (pole pomarańczowe)
│       └── box2.html      # HTML snippet - tabela 2x2 (pole zielone)  
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

---

# 🧩 HTML Snippety (Prototyp)

## Opis funkcji

System HTML Snippetów umożliwia wstawianie niestandardowego HTML/CSS do pól kolorowych (pomarańczowego i zielonego) bez komplikowania głównego interfejsu. Zamiast dodawać dziesiątki nowych opcji, wykorzystujemy elastyczne pliki HTML z własnymi stylami.

## Jak działa

### 1. **W edytorze (template-1.html)**
- **Checkbox "Dodaj HTML"** przy pomarańczowym i zielonym polu
- **Podgląd na żywo** - tabela 2x2 zastępuje standardowe pola
- **Zachowuje właściwości** pola (pozycja, rozmiar, kształt)
- **Zapis w presetach** - stan checkbox zapisany w JSON

### 2. **Podczas eksportu**
- **Backend parsing** snippet HTML → wydzielenie CSS i HTML
- **Wstrzykiwanie CSS** inline do wygenerowanego slajdu  
- **Zamiana zawartości** pól kolorowych na HTML ze snippetu
- **Standalone HTML** - pełna funkcjonalność bez zewnętrznych zależności

## Format snippetu

### Dostępne snippety
- **`box1.html`** - snippet dla pola pomarańczowego (klasa `.orange-box-snippet`)
- **`box2.html`** - snippet dla pola zielonego (klasa `.green-box-snippet`)

### Struktura pliku snippetu (przykład `templates/presets/box1.html`)

```html
<style>
.orange-box-snippet {
    /* Nadpisywanie domyślnych stylów pomarańczowego pola */
    background-color: transparent !important;
    background-image: none !important;
    padding: 0 !important;
    overflow: hidden;
}

.orange-box-snippet table {
    width: 100%;
    height: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}

.orange-box-snippet td {
    width: 50%;
    height: 50%;
    border: 1px solid #333;
    text-align: center;
    vertical-align: middle;
    font-family: Arial, sans-serif;
    font-size: 14px;
    font-weight: bold;
    color: white;
}

.orange-box-snippet .cell-1 { background-color: #e74c3c; }
.orange-box-snippet .cell-2 { background-color: #3498db; }
.orange-box-snippet .cell-3 { background-color: #2ecc71; }
.orange-box-snippet .cell-4 { background-color: #f39c12; }
</style>

<table>
    <tr>
        <td class="cell-1">A1</td>
        <td class="cell-2">A2</td>
    </tr>
    <tr>
        <td class="cell-3">B1</td>
        <td class="cell-4">B2</td>
    </tr>
</table>
```

### Wymagania techniczne

1. **CSS w tagu `<style>`** - automatycznie wydzielany przez parser
2. **Dedykowane klasy** - `.orange-box-snippet` lub `.green-box-snippet`
3. **Względne jednostki** (`%`, `em`) - dostosowanie do rozmiaru pola
4. **Style inline dopuszczalne** - dla prostych przypadków
5. **Explicit table display** - `display: table/table-row/table-cell` dla stabilności w screenshotach

### Mechanizm wstrzykiwania

```javascript
// Frontend - podgląd w edytorze (przykład dla zielonego pola)
function toggleGreenHtmlSnippet() {
    if (isHtmlSnippet) {
        greenBox.innerHTML = `<table>...</table>`;  // Podgląd
        greenBox.style.backgroundColor = 'transparent';
    } else {
        greenBox.innerHTML = '';  // Przywróć standardowy
        greenBox.style.backgroundColor = '#81c784';
    }
}
```

```python
# Backend - generowanie HTML (obsługa obu pól)
def generate_slide_html(data, slide_dir):
    # Obsługa zielonego pola
    if data['green'].get('htmlSnippet'):
        snippet_css, snippet_html = parse_snippet_content('box2.html')
        styles += snippet_css
        html_body += f'<div class="green-box green-box-snippet">{snippet_html}</div>'
    
    # Obsługa pomarańczowego pola
    if data['orange'].get('htmlSnippet'):
        snippet_css, snippet_html = parse_snippet_content('box1.html')
        styles += snippet_css
        html_body += f'<div class="orange-box orange-box-snippet">{snippet_html}</div>'
```

## Potencjalne kierunki usprawnień

### 🎯 **Krótkoterminowe (1-2 tygodnie)**
- ✅ **Snippet dla zielonego pola** - rozszerzenie na oba pola (UKOŃCZONE)
- **Biblioteka snippetów** - więcej gotowych szablonów (wykresy, diagramy, listy)
- **Edytor snippetów** - prosty interfejs do tworzenia bez kodowania
- **Podgląd snippetów** - miniaturki w selektorze

### 🚀 **Średnioterminowe (1-2 miesiące)**  
- **Parametryzowane snippety** - zmienne w HTML (`{{title}}`, `{{color}}`)
- **Integracja z danymi** - ładowanie danych z JSON/CSV do snippetów
- **Interaktywne elementy** - przyciski, formularze w snippetach
- **Responsive snippety** - automatyczne skalowanie zawartości

### 🌟 **Długoterminowe (3+ miesiące)**
- **Visual snippet builder** - drag&drop konstruktor elementów
- **Snippet store** - współdzielona biblioteka między projektami  
- **Animowane snippety** - CSS animations, transitions
- **Walidacja snippetów** - sprawdzanie poprawności przed użyciem
- **Snippet versioning** - historia zmian i rollback

### 🔧 **Techniczne**
- ✅ **Screenshot stability** - poprawki CSS dla stabilnego renderowania w Selenium (UKOŃCZONE)
- **Sandbox snippetów** - izolacja potencjalnie niebezpiecznego kodu
- **Performance optimization** - cache parsowania dla dużych snippetów
- **Error handling** - lepsze komunikaty błędów parsowania
- **Unit testing** - automatyczne testy dla parsera snippetów

## 🛠️ **Zmiany techniczne w tej sesji**

### Frontend
- Dodano checkbox "Dodaj HTML" dla pola zielonego
- Implementacja funkcji `toggleGreenHtmlSnippet()` 
- Rozszerzenie systemu presetów o `green.htmlSnippet`
- Aktualizacja eksportu o dane zielonego snippetu

### Backend
- Obsługa `green.htmlSnippet` w CSS generation
- Obsługa `green.htmlSnippet` w HTML generation
- Poprawa stabilności screenshotów dla tabel snippet

### Snippety
- Utworzenie `box2.html` dla pola zielonego
- Dodanie explicit CSS display properties dla stabilności
- Optimalizacja dla renderowania w Selenium