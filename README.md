# Instagram Manager App

Eine Flask-Anwendung zur Verwaltung von Instagram-Posts mit automatischer Planung und KI-gestützter Inhaltsgenerierung.

## Features

- Automatische Post-Planung
- KI-gestützte Bildgenerierung
- Hashtag-Vorschläge
- Statistiken und Analytics
- Benutzerauthentifizierung

## Deployment auf Render.com

1. Erstellen Sie ein Konto auf [Render.com](https://render.com)
2. Verbinden Sie Ihr GitHub-Repository
3. Klicken Sie auf "New Web Service"
4. Wählen Sie Ihr Repository aus
5. Konfigurieren Sie die folgenden Umgebungsvariablen:
   - `FLASK_ENV`: production
   - `SECRET_KEY`: [Ihr sicherer Schlüssel]
   - `DATABASE_URL`: [Ihre Datenbank-URL]
   - `HUGGINGFACE_API_KEY`: [Ihr Hugging Face API-Schlüssel]

Die Anwendung wird automatisch auf Render.com bereitgestellt und ist unter der zugewiesenen Domain erreichbar.

## Lokale Entwicklung

1. Klonen Sie das Repository:
```bash
git clone https://github.com/[username]/instaapp.git
cd instaapp
```

2. Erstellen Sie eine virtuelle Umgebung:
```bash
python -m venv .venv
source .venv/bin/activate  # Für Linux/Mac
.venv\Scripts\activate     # Für Windows
```

3. Installieren Sie die Abhängigkeiten:
```bash
pip install -r requirements.txt
```

4. Starten Sie die Anwendung:
```bash
python instaapp.py
```

Die Anwendung ist dann unter `http://localhost:5000` erreichbar.
