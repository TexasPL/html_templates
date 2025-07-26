# HTML Snippets - Presets

## Opis systemu

Katalog zawiera predefiniowane snippety HTML używane w template-1.html:

- **box1a.html**, **box1b.html** - snippety dla Box 1 (pomarańczowy)
- **box2a.html**, **box2b.html** - snippety dla Box 2 (zielony) 
- **preset-*.json** - zapisane konfiguracje template

## Format snippetów

Każdy snippet musi zawierać:

```html
<style>
.box1-snippet {
    /* style dla Box 1 */
}
.box2-snippet {
    /* style dla Box 2 */
}
</style>

<div class="box1-snippet">
    <!-- zawartość HTML -->
</div>
```

## Reguły AI editora

### Klasy CSS
- **Box 1 (pomarańczowy)**: używa klasy `.box1-snippet`
- **Box 2 (zielony)**: używa klasy `.box2-snippet`
- Klasy są automatycznie aplikowane przez JavaScript

### Filtrowanie Gemini API
System automatycznie usuwa z odpowiedzi AI:
- Znaczniki markdown: ````html` i ````
- Dodatkowe komentarze po kodzie
- Niepotrzebne elementy: `<!DOCTYPE>`, `<html>`, `<head>`, `<body>`

### Domyślne zachowanie
- Centrowanie w poziomie i pionie
- Responsywność
- Brak zewnętrznych bibliotek
- Kod musi być self-contained

## Ładowanie snippetów

Snippety są ładowane dynamicznie przez:
- `/api/snippet/<filename>` - endpoint serwera
- `selectOrangeSnippet()` / `selectGreenSnippet()` - funkcje JS
- Automatyczne odświeżanie po edycji AI (bez reload strony)