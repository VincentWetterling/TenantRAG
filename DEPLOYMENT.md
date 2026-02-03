# 🚀 TenantRAG Production Deployment Guide

## 📋 Überblick

Dieses Dokument beschreibt, wie man TenantRAG Backend in Production deployt.

**Architektur:**
```
┌─────────────────────────────────────────┐
│     Docker Container (TenantRAG App)    │
│  FastAPI Server (Port 8000)             │
└──────────┬────────────────────────────┬─┘
           │                            │
    ┌──────▼──────┐           ┌────────▼────────┐
    │ ChromaDB     │           │ MariaDB         │
    │ (Coolify)    │           │ (Managed/Ext)   │
    └─────────────┘           └─────────────────┘
```

---

## 🐳 Docker Build & Deploy

### 1. Docker Image bauen

```bash
# Production Image bauen
docker build -f Dockerfile.prod -t tenantrag:latest .

# Mit Tag für Registry
docker build -f Dockerfile.prod -t myregistry.de/tenantrag:v1.0.0 .
```

### 2. Lokal testen (mit Docker)

```bash
# Mit docker run
docker run -p 8000:8000 \
  --env-file .env \
  --name tenantrag-test \
  tenantrag:latest

# Mit docker-compose
docker-compose -f docker-compose.prod.yml up

# Logs anschauen
docker-compose -f docker-compose.prod.yml logs -f tenantrag
```

### 3. Health Check

```bash
# Anwendung ist healthy wenn:
curl http://localhost:8000/docs
curl http://localhost:8000/health  # (Optional)
```

---

## ☁️ Deployment auf Coolify

### 1. Docker Image zu Registry pushen

```bash
# Anmelden bei Registry
docker login myregistry.de

# Image pushen
docker push myregistry.de/tenantrag:v1.0.0
```

### 2. In Coolify erstellen

**A. Service erstellen:**
1. Coolify öffnen → "Services" → "Add Service"
2. Wähle: "Docker Compose"
3. Konfiguration:
   ```yaml
   version: '3.8'
   services:
     tenantrag:
       image: myregistry.de/tenantrag:v1.0.0
       ports:
         - "8000:8000"
       env_file:
         - .env
   ```

**B. Umgebungsvariablen setzen:**
1. Services → tenantrag → "Environment"
2. Folgende Variablen setzen:
   - `CHROMA_URL`: Deine Coolify ChromaDB URL
   - `CHROMA_AUTH_TOKEN`: Token für ChromaDB
   - `DATABASE_URL`: Managed MariaDB URL
   - `IONOS_API_KEY`: IONOS API-Key
   - `WEBUI_USERNAME`: Admin-Username (optional)
   - `WEBUI_PASSWORD`: Admin-Passwort (optional)

**C. Domain/Reverse Proxy konfigurieren:**
1. Services → tenantrag → "Reverse Proxy"
2. Domain eingeben: `tenantrag.example.com`
3. Port: `8000`
4. SSL/TLS aktivieren

### 3. Starten & Monitoring

```bash
# Starten
coolify-cli start tenantrag

# Logs
coolify-cli logs tenantrag

# Neustarten
coolify-cli restart tenantrag
```

---

## 🔐 Sicherheit in Production

### 1. Umgebungsvariablen sichern

Stelle sicher, dass folgende in **Coolify Secrets** (nicht im Code) gespeichert sind:
- `IONOS_API_KEY`
- `CHROMA_AUTH_TOKEN`
- `DATABASE_URL` (besonders Passwort)
- `WEBUI_PASSWORD`

### 2. HTTPS/TLS

- Reverse Proxy (Nginx/Caddy) vor der App
- SSL Zertifikate (Let's Encrypt)
- HTTP → HTTPS Redirect

### 3. Firewall & Network

- App nur auf Private Network exponieren
- Nur HTTP(S) Ports öffnen
- ChromaDB & MariaDB nur intern erreichbar

### 4. API-Rate Limiting (optional)

In `app/main.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/upload")
@limiter.limit("10/minute")
async def upload_doc(...):
    ...
```

---

## 📊 Monitoring & Logs

### 1. Health Check Endpoint hinzufügen

In `app/main.py`:
```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
```

### 2. Prometheus Metriken (optional)

```bash
pip install prometheus-client
```

In `app/main.py`:
```python
from prometheus_client import Counter, generate_latest

request_count = Counter('tenantrag_requests_total', 'Total requests')

@app.post("/upload")
async def upload_doc(...):
    request_count.inc()
    ...
```

### 3. Logs strukturieren

Mit Structured Logging:
```python
import logging
import json

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger()

def log_event(event_type, details):
    logger.info(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "details": details
    }))
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

`.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -f Dockerfile.prod -t tenantrag:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          docker tag tenantrag:${{ github.sha }} myregistry.de/tenantrag:latest
          docker push myregistry.de/tenantrag:latest
      
      - name: Deploy to Coolify
        run: coolify-cli restart tenantrag
```

---

## 🚨 Troubleshooting

| Problem | Lösung |
|---------|--------|
| App startet nicht | `docker logs tenantrag` prüfen, `.env` Variablen checken |
| ChromaDB Verbindung fehlgeschlagen | `CHROMA_URL` und `CHROMA_AUTH_TOKEN` prüfen |
| Datenbank-Fehler | `DATABASE_URL` Format prüfen, MariaDB erreichbar? |
| Hohe CPU-Last | Chunk-Größe reduzieren, Caching erhöhen |
| OOM (Out of Memory) | Limits in `docker-compose.prod.yml` erhöhen |

---

## 📝 Checkliste für Production

- [ ] `.env` mit echten Credentials gefüllt
- [ ] HTTPS/TLS konfiguriert
- [ ] Backup-Strategie für MariaDB
- [ ] ChromaDB mit Token gesichert
- [ ] Log-Aggregation eingerichtet
- [ ] Monitoring/Alerting aktiv
- [ ] Rate Limiting implementiert
- [ ] API-Dokumentation aktualisiert
- [ ] Staging-Environment getestet
- [ ] Disaster-Recovery Plan

---

## 🎯 Performance-Optimierungen

### 1. Uvicorn Worker Prozesse

`docker-compose.prod.yml`:
```yaml
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Database Connection Pooling

In `app/db.py`:
```python
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10
)
```

### 3. ChromaDB Caching

In `app/chroma_client.py`:
```python
@lru_cache(maxsize=10)
def get_collection(name):
    return client.get_or_create_collection(name)
```

---

## 📞 Support

Bei Fragen oder Issues:
1. Logs prüfen: `docker logs tenantrag`
2. Health-Endpoint testen: `curl http://localhost:8000/health`
3. ChromaDB Verbindung testen
4. Datenbank-Verbindung testen

---

**Letzte Aktualisierung:** 3. Februar 2026
