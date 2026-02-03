# 🧪 TenantRAG API Test Guide

## 🎯 Zugriffskontrolle verstehen

**Hierarchie der Daten-Isolierung:**

```
Unternehmen (tenant_id)
  └── Mitarbeiter (user_id)
      ├── Persönliche Dokumente (scope=user)
      └── Team-Dokumente (scope=group + group_id)
  └── Unternehmens-Dokumente (scope=company)
```

| Scope | Zugriff | group_id | Beispiel |
|-------|--------|----------|----------|
| `user` | Nur dieser Mitarbeiter | ❌ Nicht nötig | Persönliche Notizen |
| `group` | Diese Gruppe | ✅ **Erforderlich** | Sales-Team Dokumente |
| `company` | Ganzes Unternehmen | ❌ Nicht nötig | Handbuch |

---

## Upload Endpoint

### Einfaches Beispiel mit cURL

```bash
curl -X POST http://localhost:8000/upload \
  -F "tenant_id=acme_corp" \
  -F "user_id=john_doe" \
  -F "scope=company" \
  -F "group_id=sales_team" \
  -F "doc_file=@/path/to/your/document.pdf"
```

### Response Beispiel (Success)

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

**Wichtige Felder:**
- `file_id`: Eindeutige Datei-ID für später Referenzierung
- `collection_name`: Name der ChromaDB Collection (für weitere Queries)
- `chunks_count`: Anzahl der erstellten Chunks

### Response Beispiel (Error)

```json
{
  "success": false,
  "error": "PDF konnte nicht gelesen werden: [Fehlerdetails]"
}
```

---

## Query Endpoint

### Einfaches Beispiel mit cURL

```bash
curl -X POST http://localhost:8000/query \
  -d "tenant_id=acme_corp" \
  -d "user_id=john_doe" \
  -d "scope=company" \
  -d "question=Was sind die Hauptpunkte des Dokumentes?"
```

### Response Beispiel (Success)

```json
{
  "success": true,
  "question": "Was sind die Hauptpunkte des Dokumentes?",
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
    [0.15, 0.28, 0.42, ...]
  ],
  "results_count": 5
}
```

**Wichtige Felder:**
- `file_id`: Datei-ID zum Nachverfolgung der Quelle
- `distances`: Ähnlichkeitswerte (0=perfekt, 1=keine Übereinstimmung)

---

## Automatisierte Tests ausführen

```bash
# Mache das Script ausführbar
chmod +x test_api.sh

# Führe Tests aus (Server muss laufen!)
./test_api.sh
```

---

## Integration in andere Systeme

### Wichtige Felder für Integration

Nach einem erfolgreichen Upload bekommst du:
- ✅ `chunk_ids`: Array von eindeutigen IDs für alle hochgeladenen Chunks
- ✅ `collection_name`: Name der ChromaDB Collection (Format: `{tenant}_{scope}_{user}`)
- ✅ `chunks_count`: Anzahl der erstellten Chunks
- ✅ `upload_date`: ISO-Timestamp des Uploads

Beispiel Integration:

```python
import requests

# Datei hochladen
response = requests.post('http://localhost:8000/upload', data={
    'tenant_id': 'my_company',
    'user_id': 'user_123',
    'scope': 'company',
    'group_id': 'team_abc'
}, files={'doc_file': open('document.pdf', 'rb')})

if response.json()['success']:
    data = response.json()['data']
    print(f"✅ Datei hochgeladen!")
    print(f"   Collection: {data['collection_name']}")
    print(f"   Chunks: {data['chunks_count']}")
    print(f"   IDs: {data['chunk_ids']}")
```

---

## Wichtige Sicherheitshinweise

- 🔒 Die `tenant_id` wird für Multi-Tenancy genutzt - immer korrekt setzen!
- 🔐 `user_id` wird für Zugriffskontrolle verwendet
- 📊 `scope` kann sein: `user`, `group`, oder `company` (bestimmt Sichtbarkeit)

---

## Debugging

### Health Check

```bash
curl http://localhost:8000/health | jq .
```

### API Dokumentation

```bash
# Swagger UI (interaktiv)
open http://localhost:8000/docs

# ReDoc
open http://localhost:8000/redoc
```

### Logs anschauen

```bash
# Terminal-Output beobachten während Server läuft
tail -f logs/app.log  # Falls vorhanden
```

---

## Rate Limiting

Aktuell gibt es kein Rate Limiting. Für Production empfohlen:
- Max 10 Uploads pro Minute
- Max 100 Queries pro Minute
- Max 50MB Dateigröße

Siehe [DEPLOYMENT.md](../DEPLOYMENT.md) für Implementierung.
