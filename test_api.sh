#!/bin/bash

# TenantRAG API Test Script
# ========================
# Testet Upload und Query Endpoints

set -e

BASE_URL="http://localhost:8000"

echo "🧪 TenantRAG API Test Suite"
echo "============================"
echo ""

# Test 1: Health Check
echo "1️⃣  Health Check..."
curl -s "$BASE_URL/health" | jq . || echo "❌ Health Check fehlgeschlagen"
echo ""

# Test 2: Upload eine Test-Textdatei
echo "2️⃣  Datei hochladen..."
echo "Dies ist ein Test-Dokument. Es enthält wichtige Informationen über TenantRAG. 

TenantRAG ist ein Multi-Tenant RAG System. Es ermöglicht Benutzern, Dokumente hochzuladen und Fragen dazu zu stellen. 

Das System nutzt ChromaDB für Vektoren und IONOS AI für Embeddings." > /tmp/test_doc.txt

UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/upload" \
  -F "tenant_id=tenant123" \
  -F "user_id=user456" \
  -F "scope=company" \
  -F "group_id=group789" \
  -F "doc_file=@/tmp/test_doc.txt")

echo "$UPLOAD_RESPONSE" | jq .

# Extrahiere wichtige Infos
FILENAME=$(echo "$UPLOAD_RESPONSE" | jq -r '.data.filename')
FILE_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.data.file_id')
CHUNKS=$(echo "$UPLOAD_RESPONSE" | jq -r '.data.chunks_count')
UPLOAD_DATE=$(echo "$UPLOAD_RESPONSE" | jq -r '.data.upload_date')

echo "✅ Upload Summary:"
echo "   - Datei-ID: $FILE_ID"
echo "   - Dateiname: $FILENAME"
echo "   - Chunks: $CHUNKS"
echo "   - Hochladen: $UPLOAD_DATE"
echo ""

# Test 3: Query
echo "3️⃣  Frage stellen..."
QUERY_RESPONSE=$(curl -s -X POST "$BASE_URL/query" \
  -d "tenant_id=tenant123" \
  -d "user_id=user456" \
  -d "scope=company" \
  -d "question=Was ist TenantRAG?")

echo "$QUERY_RESPONSE" | jq .
echo ""

# Test 4: Query Response analysieren
RESULTS_COUNT=$(echo "$QUERY_RESPONSE" | jq -r '.results_count')
echo "✅ Query Summary:"
echo "   - Frage: Was ist TenantRAG?"
echo "   - Ergebnisse: $RESULTS_COUNT gefunden"
echo ""

# Cleanup
rm /tmp/test_doc.txt

echo "✅ Tests abgeschlossen!"
