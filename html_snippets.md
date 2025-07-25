# HTML Snippets - Instrukcja implementacji

## Przegląd systemu

System HTML Snippets w aplikacji prezentacji AI umożliwia wstawianie niestandardowej zawartości HTML/CSS do **Box 1** i **Box 2** w template'ach slajdów. Mechanizm działa na zasadzie list rozwijanych "HTML" w edytorze template'u.

## Architektura systemu

### 1. Frontend (template-1.html)

#### Listy rozwijane kontrolne
```html
<!-- Dla Box 2 (wcześniej pole zielone) -->
<select id="greenSnippet" onchange="selectGreenSnippet()">
    <option value="">Brak HTML</option>
    <option value="box2a.html">Tabela 2x2</option>
    <option value="box2b.html">Lista kropkowana</option>
</select>

<!-- Dla Box 1 (wcześniej pole pomarańczowe) -->
<select id="orangeSnippet" onchange="selectOrangeSnippet()">
    <option value="">Brak HTML</option>
    <option value="box1a.html">Tabela 2x2</option>
    <option value="box1b.html">Lista kropkowana</option>
</select>
```

#### Checkboxy "usuń kontur"
```html
<!-- Checkbox dla ukrycia czerwonego konturu -->
<input type="checkbox" id="greenHideBorder" onchange="toggleGreenBorder()">
<input type="checkbox" id="orangeHideBorder" onchange="toggleOrangeBorder()">
```

#### Funkcje kontrolne
- `selectGreenSnippet()` - wybór snippet'u dla Box 2
- `selectOrangeSnippet()` - wybór snippet'u dla Box 1  
- `toggleGreenBorder()` - ukrycie/pokazanie konturu Box 2
- `toggleOrangeBorder()` - ukrycie/pokazanie konturu Box 1

**Mechanizm działania:**
1. Lista rozwijana pozwala wybrać typ snippet'u (tabela 2x2 lub lista kropkowana)
2. Podgląd na żywo w edytorze pokazuje wybraną zawartość
3. Checkbox "usuń kontur" kontroluje widoczność czerwonej ramki  
4. Stan zapisywany w presetach jako `snippetFile: "box1a.html"` itp.

### 2. Backend (server.py)

#### Funkcja parsowania snippet'ów
```python
def parse_snippet_content(snippet_html):  # linijka 344
    """Parsuje snippet HTML i wydziela CSS oraz HTML"""
    import re
    
    # Wyciągnij CSS z <style>
    css_match = re.search(r'<style>(.*?)</style>', snippet_html, re.DOTALL)
    css_content = css_match.group(1).strip() if css_match else ""
    
    # Wyciągnij HTML bez <style>
    html_content = re.sub(r'<style>.*?</style>', '', snippet_html, flags=re.DOTALL).strip()
    
    return css_content, html_content
```

#### Obsługa w generowaniu CSS
- **Box 2 (green):** sprawdza `data['green'].get('snippetFile')`
- **Box 1 (orange):** sprawdza `data['orange'].get('snippetFile')`

Dla każdego pola z wybranym snippet'em:
1. Ładuje odpowiedni plik snippet'u (`box1a.html`, `box1b.html`, `box2a.html`, `box2b.html`)
2. Parsuje CSS i HTML
3. Dodaje CSS do sekcji `<style>` slajdu
4. Konfiguruje podstawowe style pozycjonowania

#### Obsługa w generowaniu HTML
Zastępuje standardowy `<div class="box2">` przez:
```html
<div class="box2 box2-snippet">{snippet_html_content}</div>
```

### 3. Pliki snippet'ów

#### Lokalizacja i nazewnictwo
- `templates/presets/box1a.html` - tabela 2x2 dla Box 1
- `templates/presets/box1b.html` - lista kropkowana dla Box 1
- `templates/presets/box2a.html` - tabela 2x2 dla Box 2  
- `templates/presets/box2b.html` - lista kropkowana dla Box 2

#### Struktura pliku snippet'u (przykład box2a.html)
```html
<style>
.box2-snippet {
    /* Nadpisywanie domyślnych stylów Box 2 */
    background-color: transparent !important;
    background-image: none !important;
    padding: 0 !important;
    overflow: hidden;
}

.box2-snippet table {
    width: 100%;
    height: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    display: table;  /* Ważne dla stabilności screenshotów */
}

.box2-snippet td {
    display: table-cell;  /* Ważne dla stabilności screenshotów */
    width: 50%;
    height: 50%;
    border: 1px solid #333;
    text-align: center;
    vertical-align: middle;
    font-family: Arial, sans-serif;
    font-size: 14px;
    font-weight: bold;
    color: white;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}

.box2-snippet .cell-1 { background-color: #e74c3c; }
.box2-snippet .cell-2 { background-color: #3498db; }
.box2-snippet .cell-3 { background-color: #2ecc71; }
.box2-snippet .cell-4 { background-color: #f39c12; }
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

#### Struktura pliku listy kropkowanej (przykład box2b.html)
```html
<style>
.box2-snippet {
    /* Nadpisywanie domyślnych stylów Box 2 */
    background-color: transparent !important;
    background-image: none !important;
    padding: 15px !important;
    overflow: hidden;
}

.box2-snippet ul {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    justify-content: space-evenly;
    font-family: Arial, sans-serif;
}

.box2-snippet li {
    position: relative;
    padding-left: 20px;
    font-size: 14px;
    font-weight: bold;
    color: #333;
    text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
    line-height: 1.2;
}

.box2-snippet li::before {
    content: "•";
    position: absolute;
    left: 0;
    color: #e74c3c;
    font-size: 18px;
    font-weight: bold;
}

/* Kolorowe kropki dla kolejnych pozycji */
.box2-snippet li:nth-child(2)::before { color: #3498db; }
.box2-snippet li:nth-child(3)::before { color: #2ecc71; }
.box2-snippet li:nth-child(4)::before { color: #f39c12; }
.box2-snippet li:nth-child(5)::before { color: #9b59b6; }
</style>

<ul>
    <li>Pozycja 1</li>
    <li>Pozycja 2</li>
    <li>Pozycja 3</li>
    <li>Pozycja 4</li>
    <li>Pozycja 5</li>
</ul>
```

## Przepływ danych

### 1. W edytorze (podgląd na żywo)
```
Lista rozwijana zmieniona → selectFunction() → innerHTML = zawartość snippet'u + sprawdzenie border checkbox
```

### 2. W presetach (zapis/odczyt)
```javascript
// Zapis
snippetFile: document.getElementById('greenSnippet').value || null

// Odczyt z kompatybilnością wsteczną
if (preset.green.snippetFile) {
    document.getElementById('greenSnippet').value = preset.green.snippetFile;
} else if (preset.green.htmlSnippet) {
    // Stare presety z htmlSnippet: true → box2a.html
    document.getElementById('greenSnippet').value = 'box2a.html';
} else {
    document.getElementById('greenSnippet').value = '';
}
```

### 3. Podczas eksportu
```
1. Frontend wysyła dane z snippetFile: "box2a.html"
2. Backend sprawdza data['green'].get('snippetFile')
3. Ładuje snippet z templates/presets/box2a.html
4. Parsuje CSS i HTML
5. Wstrzykuje CSS do <style>
6. Zastępuje <div> zawartością snippet'u
7. Generuje standalone HTML
```

## Kluczowe właściwości techniczne

### CSS Classes
- `.box1-snippet` - dla Box 1 (wcześniej pomarańczowe)
- `.box2-snippet` - dla Box 2 (wcześniej zielone)

### HTML Elements
- `<div class="box1">` - Box 1 w CSS
- `<div class="box2">` - Box 2 w CSS

### Zarządzanie konturami
- Domyślnie: `border: 2px solid red`
- Po zaznaczeniu "usuń kontur": `border: none`
- Funkcje `toggleGreenBorder()` i `toggleOrangeBorder()` kontrolują widoczność

### Stabilność screenshotów
Explicite ustawione `display` properties:
- `table` → `display: table`
- `tr` → `display: table-row` 
- `td` → `display: table-cell`

To zapewnia poprawne renderowanie w Selenium WebDriver.

### Nadpisywanie stylów
Snippet'y używają `!important` do nadpisania domyślnych stylów pól:
- `background-color: transparent !important`
- `background-image: none !important`
- `padding: 0 !important` (dla tabel) lub `padding: 15px !important` (dla list)

## Dostępne typy snippet'ów

### Tabele 2x2 (box1a.html, box2a.html)
- **Zastosowanie:** Prezentacja danych w układzie macierzowym
- **Zawartość:** 4 komórki z kolorowymi tłami (A1, A2, B1, B2)
- **Style:** Każda komórka ma inny kolor tła i białą czcionkę

### Listy kropkowane (box1b.html, box2b.html)
- **Zastosowanie:** Wyliczenia, punkty kluczowe
- **Zawartość:** 5 pozycji z kolorowymi kropkami
- **Style:** Każda pozycja ma kropkę w innym kolorze

## Rozszerzanie systemu

### Dodawanie nowych snippet'ów
1. Utwórz nowy plik HTML w `templates/presets/` (np. `box1c.html`)
2. Zastosuj strukturę: `<style>` + HTML content
3. Użyj dedykowanej klasy CSS (`.box1-snippet` lub `.box2-snippet`)
4. Dodaj explicit display properties dla stabilności
5. Dodaj nową opcję do listy rozwijanej w HTML

### Parametryzacja snippet'ów
W przyszłości możliwe rozszerzenia:
- Zmienne w HTML: `{{title}}`, `{{color}}`
- Konfiguracja przez interfejs
- Biblioteka snippet'ów z podglądem

## Zastosowanie w workflow

1. **Edytor:** Wybierz typ HTML z listy rozwijanej → podgląd na żywo
2. **Kontrola konturu:** Zaznacz "usuń kontur" jeśli potrzeba
3. **Preset:** Zapisz układ → snippetFile zapisany w JSON
4. **Eksport:** Wygeneruj slajd → snippet HTML wstrzyknięty
5. **Screenshot:** Zrób screenshot → stabilne renderowanie zawartości

## Najważniejsze zmiany w najnowszej wersji

### Zmiany w nazewnictwie
- **Pola kolorowe** → **Box 1** i **Box 2**
- **Checkboxy** → **Listy rozwijane** z opcjami snippet'ów
- Usunięto kolorowe stylowanie z panelu kontrolnego

### Nowe funkcjonalności
- **Checkbox "usuń kontur"** - kontrola widoczności czerwonej ramki
- **Dwa typy snippet'ów** - tabela 2x2 i lista kropkowana
- **Neutralne nazewnictwo** - Box 1/Box 2 zamiast kolorów

### Ulepszenia techniczne
- **Kompatybilność wsteczna** - stare presety automatycznie konwertowane
- **Lepsze pozycjonowanie** - checkbox "usuń kontur" wyrównany do prawej
- **Stabilne renderowanie** - poprawione style dla screenshotów

## Ograniczenia i uwagi

- Obecnie obsługiwane 4 snippet'y (box1a.html, box1b.html, box2a.html, box2b.html)
- Brak walidacji poprawności HTML/CSS
- Snippet'y nie mają parametryzacji
- Sandbox zabezpieczeń nie został zaimplementowany
- Checkbox "usuń kontur" nie jest zapisywany w presetach (domyślnie zawsze wyłączony)