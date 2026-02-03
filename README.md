# 🧠 TenantRAG - Mehrinstanz-RAG System

## 📋 Projektbeschreibung

**TenantRAG** ist ein modernes Retrieval-Augmented Generation (RAG) System mit Mehrinstanz-Unterstützung (Multi-Tenancy). Es ermöglicht es Benutzern, PDF- und Textdateien hochzuladen, diese intelligent zu durchsuchen und semantische Anfragen zu beantworten.

### Kernfunktionalitäten:
- 📤 **Datei-Upload**: PDF und Textdateien hochladen und automatisch chunken
- 🔍 **Semantische Suche**: Intelligente Suche mit KI-Embeddings
- 👥 **Multi-Tenancy**: Mehrere Mandanten mit isolierten Daten
- 🎯 **Zugriffsschutz**: Benutzer-, Gruppen- und Unternehmen-Level Zugriff
- 🧾 **Metadaten**: Vollständige Verwaltung von Datei-Metadaten
- 🎛️ **Verwaltungs-Dashboard**: Übersichtliche Streamlit WebUI
- 🔐 **Token-Auth**: Sichere ChromaDB Verbindung mit Token-Authentifizierung

---

## 🏗️ Architektur

```
┌──────────────────────────────────────────────────┐
│           FastAPI Web-Server (Port 8000)         │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ Upload API   │  │ Query API    │             │
│  └──────────────┘  └──────────────┘             │
└──────────┬──────────────────────────────────────┘
           │
    ┌──────┴──────┬──────────────┐
    │             │              │
┌───▼────┐  ┌────▼────┐  ┌──────▼──────┐
│ ChromaDB│  │ MariaDB  │  │ IONOS AI    │
│ Vectors │  │ Metadata │  │ Embeddings  │
└────────┘  └─────────┘  └─────────────┘

┌────────────────────────────────────────┐
│   Streamlit Dashboard (Port 8501)      │
│  - Collections verwalten               │
│  - Suche testen                        │
│  - Dateien löschen                     │
└────────────────────────────────────────┘
```

---

## 🚀 Installation

### Voraussetzungen
- Python 3.11+
- Docker & Docker Compose (optional, für lokale Services)
- API-Schlüssel von IONOS Cloud

### Schritt 1: Repository klonen und Setup

```bash
# Repository klonen
git clone <repo-url>
cd TenantRAG

# Python-Abhängigkeiten installieren
pip install -r requirements.txt
```

### Schritt 2: Umgebungsvariablen konfigurieren

**Datei `.env` erstellen:**

```env
# IONOS AI Embeddings API
IONOS_AI_BASE_URL=https://openai.inference.de-txl.ionos.com/v1
IONOS_MODEL=BAAI/bge-m3
IONOS_API_KEY=<dein-ionos-api-key>

# ChromaDB Konfiguration
CHROMA_URL=<deine-chroma-url>
CHROMA_AUTH_PROVIDER=token
CHROMA_AUTH_TOKEN_TRANSPORT_HEADER=X-Token
CHROMA_AUTH_TOKEN=<dein-chroma-token>

# Datenbank
DATABASE_URL=mysql+asyncmy://user:pass@localhost/tenantrag

# WebUI Authentifizierung
WEBUI_USERNAME=admin
WEBUI_PASSWORD=TenantRAG_2025_SecurePass!
```

### Schritt 3: Services starten (lokal mit Docker Compose)

```bash
# MariaDB und ChromaDB starten
docker-compose up mariadb chromadb -d

# Oder alle Services starten
docker-compose up -d
```

### Schritt 4: Anwendung starten

**FastAPI Server (Port 8000):**
```bash
python run.py
```

**Streamlit Dashboard (Port 8501):**
```bash
cd ui
streamlit run chroma_dashboard.py
```

---

## 💻 API-Dokumentation

### Upload-Endpoint

**POST** `/upload` - Datei hochladen und chunken

#### cURL Beispiel

```bash
curl -X POST http://localhost:8000/upload \
  -F "tenant_id=acme_corp" \
  -F "user_id=john_doe" \
  -F "scope=company" \
  -F "group_id=sales_team" \
  -F "doc_file=@/path/to/document.pdf"
```

#### Request Parameter

| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `tenant_id` | string | Eindeutige Mandanten-ID (erforderlich) |
| `user_id` | string | Benutzer-ID (erforderlich) |
| `scope` | enum | `user` \| `group` \| `company` (erforderlich) |
| `group_id` | string | Gruppen-ID wenn scope=group (optional) |
| `doc_file` | file | PDF oder TXT Datei (erforderlich) |

#### Success Response (200)

```json
{
  "success": true,
  "message": "5 Text-Chunks erfolgreich hochgeladen.",
  "data": {
    "file_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "document.pdf",
    "file_type": ".pdf",
    "file_size": 54321,
    "upload_date": "2026-02-03T21:30:45.123456",
    "chunks_count": 5,
    "tenant_id": "acme_corp",
    "user_id": "john_doe",
    "scope": "company",
    "group_id": "sales_team",
    "collection_name": "acme_corp_company_john_doe"
  }
}
```

#### Error Response (400/500)

```json
{
  "success": false,
  "error": "PDF konnte nicht gelesen werden: [Details]"
}
```

---

### Query-Endpoint

**POST** `/query` - Semantische Suche ausführen

#### cURL Beispiel

```bash
curl -X POST http://localhost:8000/query \
  -d "tenant_id=acme_corp" \
  -d "user_id=john_doe" \
  -d "scope=company" \
  -d "question=Was sind die Hauptpunkte?"
```

#### Request Parameter

| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `tenant_id` | string | Mandanten-ID (erforderlich) |
| `user_id` | string | Benutzer-ID (erforderlich) |
| `scope` | enum | `user` \| `group` \| `company` (erforderlich) |
| `question` | string | Die Suchfrage (erforderlich) |

#### Success Response (200)

```json
{
  "success": true,
  "question": "Was sind die Hauptpunkte?",
  "documents": [
    [
      "Dies ist ein wichtiger Punkt aus dem Dokument...",
      "Ein weiterer relevanter Absatz...",
      "..."
    ]
  ],
  "metadatas": [
    [
      {
        "file_id": "550e8400-e29b-41d4-a716-446655440000",
        "filename": "document.pdf",
        "file_type": ".pdf",
        "file_size": 54321,
        "upload_date": "2026-02-03T21:30:45.123456",
        "tenant_id": "acme_corp",
        "user_id": "john_doe",
        "scope": "company",
        "group_id": "sales_team"
      },
      "..."
    ]
  ],
  "distances": [
    [0.15, 0.28, 0.42]
  ],
  "results_count": 3
}
```

#### Error Response (500)

```json
{
  "success": false,
  "error": "Fehler bei Query: [Details]"
}
```

---

### Health-Check Endpoint

**GET** `/health` - Anwendungs-Status prüfen

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-03T21:30:45.123456"
}
```
  -d "question=Was ist Projektmanagement?"
```

**Parameter:**
- `tenant_id` (string): Mandanten-ID
- `user_id` (string): Benutzer-ID
- `scope` (enum): `user` | `group` | `company`
- `question` (string): Die Suchanfrage

**Response (JSON):**
```json
{
  "documents": [
    ["Chunk 1 Text", "Chunk 2 Text", ...],
    ["Chunk 3 Text", "Chunk 4 Text", ...]
  ],
  "metadatas": [
    [
      {"filename": "doc.pdf", "upload_date": "2026-02-03", ...},
      {"filename": "doc.pdf", "upload_date": "2026-02-03", ...}
    ]
  ],
  "distances": [[0.15, 0.22, ...], [...]]
}
```

---

### ChromaDB REST API (mit Token-Auth)

```bash
# Collections auflisten
curl -H "X-Token: <token>" \
  https://chroma-url/api/v1/collections

# Daten aus Collection holen
curl -H "X-Token: <token>" \
  "https://chroma-url/api/v1/collections/{collection_name}/get"

# Semantische Suche
curl -H "X-Token: <token>" \
  -X POST "https://chroma-url/api/v1/collections/{collection_name}/query" \
  -d '{"query_embeddings":[[0.1, 0.2, ...]], "n_results": 5}'
```

---

## 🎛️ Streamlit Dashboard

**URL:** `http://localhost:8501`

**Authentifizierung:**
- Benutzername: `admin` (oder aus `.env`)
- Passwort: `TenantRAG_2025_SecurePass!` (oder aus `.env`)

**Funktionen:**

### Tab "📁 Dateien"
- Zeigt alle hochgeladenen Dateien gruppiert nach Name
- Metadaten anzeigen (Größe, Uploadatum, Type, etc.)
- Chunk-Vorschau
- Datei komplett löschen

### Tab "📄 Alle Chunks"
- Alle Chunks mit Volltext anzeigen
- Einzelne Chunks löschen
- Limit anpassen (5-100)

### Semantische Suche
- Text eingeben und suchen
- Ähnlichkeitsscore (0-100%)
- Ähnlichkeitsschwelle konfigurieren
- Ergebnisse mit Metadaten anzeigen

---

## 📁 Projektstruktur

```
TenantRAG/
├── app/
│   ├── main.py              # FastAPI Hauptanwendung
│   ├── config.py            # Konfigurationsverwaltung
│   ├── chroma_client.py     # ChromaDB Verbindung
│   ├── embeddings.py        # IONOS AI Integration
│   ├── models.py            # SQLAlchemy Datenbankmodelle
│   ├── crud.py              # Datenbankoperationen
│   ├── schemas.py           # Pydantic Schemas
│   ├── db.py                # SQLAlchemy Setup
│   └── web/
│       ├── templates/       # HTML Templates
│       │   ├── upload.html
│       │   └── query.html
│       └── static/          # CSS/JS
│           └── app.css
├── ui/
│   ├── chroma_dashboard.py  # Streamlit WebUI
│   └── README.md
├── run.py                   # Lokaler Entwicklungs-Server
├── docker-compose.yml       # Service-Orchestration
├── Dockerfile              # Container-Image
├── requirements.txt         # Python-Abhängigkeiten
├── .env                     # Umgebungsvariablen
└── README.md               # Diese Datei
```

---

## 🔒 Sicherheit

### Authentifizierung

1. **WebUI (Streamlit):** Benutzername + Passwort
2. **ChromaDB:** Token-basiert (Header: `X-Token`)
3. **IONOS API:** API-Key in `.env`

### Daten-Isolation

- Daten werden nach `tenant_id` in separaten ChromaDB Collections gespeichert
- Zusätzliche Isolation durch `user_id` und `scope`
- SQL-Abfragen gegen MariaDB sind gefiltert nach `tenant_id`

### Best Practices

- `.env` Datei **niemals** in Git committen
- API-Keys in `.gitignore`
- Token regelmäßig rotieren
- HTTPS/TLS in Production nutzen

---

## 🔧 Konfiguration

### Chunk-Größe anpassen

In `app/main.py`, Funktion `create_smart_chunks()`:

```python
chunks = create_smart_chunks(
    text, 
    min_chunk_size=300,    # Minimale Chunk-Größe
    max_chunk_size=2000    # Maximale Chunk-Größe
)
```

### Embedding-Model ändern

In `.env`:

```env
IONOS_MODEL=BAAI/bge-m3  # oder ein anderes Modell
```

### Datenbank wechseln

In `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/tenantrag
# oder
DATABASE_URL=sqlite+aiosqlite:///./tenantrag.db
```

---

## 📊 Nutzungsbeispiele

### Python Client

```python
import requests

# Datei hochladen
with open("dokument.pdf", "rb") as f:
    files = {"doc_file": f}
    data = {
        "tenant_id": "company-1",
        "user_id": "user-123",
        "scope": "company"
    }
    response = requests.post("http://localhost:8000/upload", files=files, data=data)
    print(response.status_code)

# Abfrage
query_data = {
    "tenant_id": "company-1",
    "user_id": "user-123",
    "scope": "company",
    "question": "Wie wird ein Projekt gestartet?"
}
response = requests.post("http://localhost:8000/query", data=query_data)
results = response.json()
print(results["documents"])
```

### Bash/cURL

```bash
# Datei hochladen
curl -X POST http://localhost:8000/upload \
  -F "tenant_id=company-1" \
  -F "user_id=user-123" \
  -F "scope=company" \
  -F "doc_file=@dokument.pdf"

# Suche
curl -X POST http://localhost:8000/query \
  -d "tenant_id=company-1" \
  -d "user_id=user-123" \
  -d "scope=company" \
  -d "question=Wie wird ein Projekt gestartet?" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

---

## 🐛 Häufige Probleme

| Problem | Lösung |
|---------|--------|
| ChromaDB Token nicht akzeptiert | Stelle sicher, dass `CHROMA_AUTH_TOKEN` in `.env` gesetzt ist |
| IONOS API Fehler | Prüfe `IONOS_API_KEY` und `IONOS_AI_BASE_URL` |
| Datenbank-Verbindung fehlgeschlagen | `DATABASE_URL` prüfen oder MariaDB starten (`docker-compose up mariadb`) |
| Chunks zu klein/groß | `min_chunk_size` und `max_chunk_size` in `main.py` anpassen |
| WebUI Login fehlgeschlagen | `WEBUI_USERNAME` und `WEBUI_PASSWORD` in `.env` prüfen |

---

## 📝 Lizenz

Dieses Projekt ist unter der Apache License 2.0 lizenziert.

---

## 👥 Mitwirkende

Entwickelt mit ❤️ für Multi-Tenancy RAG Systeme.

---

**Letzte Aktualisierung:** 3. Februar 2026
