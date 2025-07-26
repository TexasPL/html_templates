# Ważne instrukcje konfiguracji

## Wymagana konfiguracja API

Aby uruchomić AI edytor snippetów, musisz ręcznie utworzyć plik konfiguracji z kluczami API:

### Utwórz plik: `API_editor/config.json`

```json
{
    "api_key_gemini": "YOUR_GEMINI_API_KEY_HERE",
    "api_key_anthropic": "YOUR_ANTHROPIC_API_KEY_HERE"
}
```

### Gdzie uzyskać klucze API:

1. **Gemini API**: https://makersuite.google.com/app/apikey
2. **Anthropic API**: https://console.anthropic.com/

### Bezpieczeństwo

⚠️ **UWAGA**: Plik `config.json` jest dodany do `.gitignore` ze względów bezpieczeństwa.
**NIE** commituj tego pliku z prawdziwymi kluczami API do repozytorium!

### Uruchomienie

Po utworzeniu pliku konfiguracji:

```bash
python server.py
```

Aplikacja będzie dostępna pod adresem wyświetlonym w terminalu.