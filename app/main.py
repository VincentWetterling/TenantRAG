from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse

import uuid
from datetime import datetime

from .schemas import UploadDoc
from .embeddings import embed_text
from .chroma_client import get_collection


import os
from pathlib import Path
from pdfminer.high_level import extract_text

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="TenantRAG API", description="Multi-Tenant RAG System")

@app.get("/health")
async def health():
    """Health Check Endpoint"""
    return {"status": "healthy", "version": "1.0.0", "timestamp": datetime.now().isoformat()}

@app.get("/docs", include_in_schema=False)
async def docs_redirect():
    """Redirect to API documentation"""
    return {"message": "API Documentation available at /docs"}

@app.post("/upload")
async def upload_doc(
    tenant_id: str = Form(...),
    user_id: str = Form(...),
    scope: str = Form(...),
    group_id: str = Form(None),
    doc_file: UploadFile = Form(...)
):
    # Validiere Parameter
    if scope not in ["user", "group", "company"]:
        return JSONResponse(
            status_code=400,
            content={"error": f"Ungültiger scope '{scope}'. Erlaubt sind: user, group, company", "success": False}
        )
    
    # group_id ist erforderlich wenn scope=group
    if scope == "group" and not group_id:
        return JSONResponse(
            status_code=400,
            content={"error": "group_id ist erforderlich wenn scope=group", "success": False}
        )

    file_bytes = await doc_file.read()
    filename = doc_file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        # PDF-Text extrahieren
        import io
        pdf_stream = io.BytesIO(file_bytes)
        try:
            text = extract_text(pdf_stream)
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"error": f"PDF konnte nicht gelesen werden: {str(e)}", "success": False}
            )
    elif ext in [".txt", ""]:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return JSONResponse(
                status_code=400,
                content={"error": "Die Datei ist keine gültige UTF-8-Textdatei. Bitte lade eine reine Textdatei hoch.", "success": False}
            )
    else:
        return JSONResponse(
            status_code=400,
            content={"error": "Dateiformat nicht unterstützt. Bitte lade eine PDF- oder Textdatei hoch.", "success": False}
        )

    if not text or not text.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Die Datei enthält keinen extrahierbaren Text.", "success": False}
        )

    # Intelligente Chunk-Strategie: Nach Absätzen, intelligent zusammengefasst
    def create_smart_chunks(text, min_chunk_size=300, max_chunk_size=2000):
        """
        Erstelle Chunks basierend auf Absätzen mit intelligenter Zusammenfassung.
        - Splittet primär nach Absätzen (doppelte Zeilenumbrüche)
        - Kombiniert kleine Absätze bis zur Mindestgröße
        - Stoppt nicht, wenn max_chunk_size überschritten wird (respektiert Absatzgrenzen)
        """
        # Split nach doppelten Zeilenumbrüchen (Absätze)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # Wenn ein einzelner Absatz größer als max_chunk_size ist, spalte ihn
            if para_size > max_chunk_size:
                # Speichere bisherigen Chunk falls vorhanden
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk).strip()
                    if len(chunk_text) >= min_chunk_size:
                        chunks.append(chunk_text)
                    current_chunk = []
                    current_size = 0
                
                # Spalte großen Absatz in Sätze auf
                sentences = para.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|')
                sub_chunk = []
                sub_size = 0
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    sent_size = len(sentence)
                    
                    if sub_size + sent_size > max_chunk_size and sub_chunk:
                        chunks.append(' '.join(sub_chunk))
                        sub_chunk = [sentence]
                        sub_size = sent_size
                    else:
                        sub_chunk.append(sentence)
                        sub_size += sent_size + 1
                
                if sub_chunk:
                    chunks.append(' '.join(sub_chunk))
            
            # Normaler Fall: Absatz ist ok
            elif current_size + para_size > max_chunk_size and current_chunk:
                # Chunk ist voll, speichere und starte neuen
                chunk_text = '\n\n'.join(current_chunk).strip()
                if len(chunk_text) >= min_chunk_size:
                    chunks.append(chunk_text)
                current_chunk = [para]
                current_size = para_size
            else:
                # Füge Absatz zu aktuellem Chunk hinzu
                current_chunk.append(para)
                current_size += para_size + 2  # +2 für \n\n
        
        # Letzten Chunk speichern
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk).strip()
            if len(chunk_text) >= min_chunk_size:
                chunks.append(chunk_text)
            elif chunks:  # Wenn zu klein, zum letzten Chunk hinzufügen
                chunks[-1] += '\n\n' + chunk_text
            else:
                chunks.append(chunk_text)  # Oder als erstes Chunk (falls nur eins)
        
        return chunks
    
    chunks = create_smart_chunks(text, min_chunk_size=300, max_chunk_size=2000)
    collection_name = f"{tenant_id}_{scope}_{user_id}"
    col = get_collection(collection_name)
    # Bestimme Dateityp
    file_ext = os.path.splitext(filename)[1].lower() or "unknown"
    upload_date = datetime.now().isoformat()
    file_size = len(file_bytes)
    file_id = str(uuid.uuid4())  # Eindeutige ID für die gesamte Datei
    
    try:
        for c in chunks:
            emb = embed_text(c)
            chunk_id = str(uuid.uuid4())
            metadata = {
                "file_id": file_id,  # Datei-ID zur Identifikation
                "filename": filename,
                "file_type": file_ext,
                "file_size": file_size,
                "upload_date": upload_date,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "scope": scope,
                "group_id": group_id or "N/A"
            }
            col.add(
                ids=[chunk_id],
                embeddings=[emb],
                documents=[c],
                metadatas=[metadata]
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Fehler bei IONOS AI Embedding: {str(e)}", "success": False}
        )

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": f"{len(chunks)} Text-Chunks erfolgreich hochgeladen.",
            "data": {
                "file_id": file_id,
                "filename": filename,
                "file_type": file_ext,
                "file_size": file_size,
                "upload_date": upload_date,
                "chunks_count": len(chunks),
                "tenant_id": tenant_id,
                "user_id": user_id,
                "scope": scope,
                "group_id": group_id or None,
                "collection_name": f"{tenant_id}_{scope}_{user_id}"
            }
        }
    )

@app.post("/query")
async def query_docs(
    tenant_id: str = Form(...),
    user_id: str = Form(...),
    scope: str = Form(...),
    question: str = Form(...)
):
    # Validiere Parameter
    if scope not in ["user", "group", "company"]:
        return JSONResponse(
            status_code=400,
            content={"error": f"Ungültiger scope '{scope}'. Erlaubt sind: user, group, company", "success": False}
        )
    
    if not question or not question.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "question darf nicht leer sein", "success": False}
        )
    
    try:
        emb = embed_text(question)
        collection_name = f"{tenant_id}_{scope}_{user_id}"
        col = get_collection(collection_name)
        results = col.query(query_embeddings=[emb], n_results=5)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "question": question,
                "documents": results.get("documents", []),
                "metadatas": results.get("metadatas", []),
                "distances": results.get("distances", []),
                "results_count": len(results.get("documents", [[]])[0]) if results.get("documents") else 0
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Fehler bei Query: {str(e)}", "success": False}
        )
