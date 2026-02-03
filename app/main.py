from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .db import async_session
from .schemas import UploadDoc
from .embeddings import embed_text
from .chroma_client import get_collection


import os
from pathlib import Path
from pdfminer.high_level import extract_text

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = str(BASE_DIR / "web" / "static")
TEMPLATES_DIR = str(BASE_DIR / "web" / "templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/")
async def upload_form(request: Request, error: str = None, success: str = None):
    return templates.TemplateResponse("upload.html", {"request": request, "error": error, "success": success})

@app.post("/upload")
async def upload_doc(
    request: Request,
    tenant_id: str = Form(...),
    user_id: str = Form(...),
    scope: str = Form(...),
    group_id: str = Form(None),
    doc_file: UploadFile = Form(...)
):

    file_bytes = await doc_file.read()
    filename = doc_file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        # PDF-Text extrahieren
        import io
        pdf_stream = io.BytesIO(file_bytes)
        try:
            text = extract_text(pdf_stream)
        except Exception:
            url = app.url_path_for("upload_form") + "?error=PDF konnte nicht gelesen werden."
            return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)
    elif ext in [".txt", ""]:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            url = app.url_path_for("upload_form") + "?error=Die Datei ist keine gültige UTF-8-Textdatei. Bitte lade eine reine Textdatei hoch."
            return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)
    else:
        url = app.url_path_for("upload_form") + "?error=Dateiformat nicht unterstützt. Bitte lade eine PDF- oder Textdatei hoch."
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    if not text or not text.strip():
        url = app.url_path_for("upload_form") + "?error=Die Datei enthält keinen extrahierbaren Text."
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    chunks = text.split("\n\n")  # simple chunk
    collection_name = f"{tenant_id}_{scope}_{user_id}"
    col = get_collection(collection_name)
    try:
        for c in chunks:
            emb = embed_text(c)
            col.add({"embeddings":[emb],"documents":[c]})
    except Exception as e:
        url = app.url_path_for("upload_form") + f"?error=Fehler bei IONOS AI Embedding: {str(e)}"
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    url = app.url_path_for("upload_form") + f"?success={len(chunks)} Text-Chunks erfolgreich hochgeladen."
    return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

@app.get("/query")
async def query_form(request: Request):
    return templates.TemplateResponse("query.html", {"request": request})

@app.post("/query")
async def query_docs(
    tenant_id: str = Form(...),
    user_id: str = Form(...),
    question: str = Form(...)
):
    # Für Test: zeige alle docs
    return {"tenant":tenant_id,"user":user_id,"question":question}
