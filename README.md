[pierwszy GIT commit (lokalnie) 13.07.2025]

# Slide Screenshot Tool

Narzędzie do automatycznego tworzenia screenshotów slajdów HTML w wysokiej jakości.

## Opis

Aplikacja składa się z:
- **Serwera Python** (Flask + Tkinter GUI) - zarządza backend i persistentną instancją Chrome
- **Web interface** - nawigacja między slajdami z wizualną kontrolą statusu zapisywania
- **Selenium screenshot engine** - tworzy precyzyjne screenshoty w rozmiarze 1536x864px

## Funkcje

- ✅ Persistent Chrome - szybkie kolejne screenshoty (~0.5s)
- ✅ Dokładny rozmiar 1536x864px (16:9)
- ✅ Wizualne statusy przycisku (ładowanie/sukces/błąd)
- ✅ Automatyczne wykrywanie ilości slajdów
- ✅ Kompaktowy interfejs z pływającymi kontrolkami

## Uruchomienie

```bash
pip install -r requirements.txt
python server.py
```

## Struktura

```
├── server.py          # Backend (Flask + Selenium)
├── index.html         # Frontend interface  
├── slides/            # Slajdy HTML + obrazy
├── number.txt         # Liczba slajdów
└── requirements.txt   # Zależności Python
```