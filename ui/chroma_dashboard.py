"""
ChromaDB Dashboard - Streamlit WebUI
====================================
Interaktive Weboberfläche zur Verwaltung von ChromaDB Collections.

Features:
- Dokumente hochladen (Upload Tab)
- Semantische Suche (Query Tab)
- Collections verwalten und erkunden (Explorer Tab)
- Dateien und Chunks löschen
- Metadaten anzeigen
- Token-basierte Authentifizierung für ChromaDB

Starten mit: streamlit run chroma_dashboard.py
Erreichbar unter: http://localhost:8501
"""

import os
import sys
import json
import requests
import chromadb
import streamlit as st
from dotenv import load_dotenv

# Lade .env
load_dotenv()

# Füge parent directory zu sys.path hinzu, um app Module zu importieren
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.embeddings import embed_text

# ==================== AUTHENTIFIZIERUNG ====================

def check_password():
    """
    Prüft Benutzername und Passwort gegen .env Werte.
    
    Returns:
        bool: True wenn authentifiziert, False sonst
    """
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if not st.session_state.password_correct:
        st.warning("🔒 Diese Anwendung ist geschützt. Bitte authentifizieren Sie sich.")
        
        with st.form("login_form"):
            username = st.text_input("👤 Benutzername", key="username_input")
            password = st.text_input("🔑 Passwort", type="password", key="password_input")
            submitted = st.form_submit_button("Anmelden")
            
            if submitted:
                expected_username = os.getenv("WEBUI_USERNAME", "admin")
                expected_password = os.getenv("WEBUI_PASSWORD", "password")
                
                if username == expected_username and password == expected_password:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("❌ Benutzername oder Passwort falsch")
        
        return False
    
    return True

# Konfiguriere Seite
st.set_page_config(page_title="ChromaDB Dashboard", layout="wide")

# Authentifizierung prüfen
if not check_password():
    st.stop()

# Logout Button
st.sidebar.button("🚪 Abmelden", on_click=lambda: st.session_state.update(password_correct=False))


# Verbinde zu ChromaDB
@st.cache_resource
def get_chroma_client():
    """
    Erstellt eine gecachte Verbindung zu ChromaDB mit Token-Authentifizierung.
    
    Returns:
        chromadb.HttpClient: Der ChromaDB Client
    """
    chroma_url = os.getenv("CHROMA_URL", "http://localhost:8001")
    chroma_token = os.getenv("CHROMA_AUTH_TOKEN", "")
    chroma_header = os.getenv("CHROMA_AUTH_TOKEN_TRANSPORT_HEADER", "X-Token")
    
    headers = {}
    if chroma_token:
        headers[chroma_header] = chroma_token
    
    if headers:
        return chromadb.HttpClient(host=chroma_url, headers=headers)
    else:
        return chromadb.HttpClient(host=chroma_url)

client = get_chroma_client()

# Sidebar
st.sidebar.title("ChromaDB Explorer")
st.sidebar.write(f"**Host:** {os.getenv('CHROMA_URL', 'http://localhost:8001')}")

# Hauptinhalt
st.title("🔍 ChromaDB Dashboard")

# Haupt-Tabs
main_tab1, main_tab2, main_tab3 = st.tabs(["📤 Upload", "🔎 Query", "📊 Explorer"])

# ==================== TAB 1: UPLOAD ====================
with main_tab1:
    st.subheader("📤 Dokument hochladen")
    
    upload_col1, upload_col2 = st.columns(2)
    with upload_col1:
        tenant_id = st.text_input("Tenant ID", key="upload_tenant_id")
        user_id = st.text_input("User ID", key="upload_user_id")
        scope = st.selectbox("Scope", ["user", "group", "company"], key="upload_scope")
    with upload_col2:
        group_id = st.text_input("Group ID (optional)", key="upload_group_id")
    
    uploaded_file = st.file_uploader("Datei wählen (PDF/TXT)", type=["pdf", "txt"], key="doc_file")
    
    if st.button("📤 Hochladen", key="upload_button"):
        if not tenant_id or not user_id or not uploaded_file:
            st.error("❌ Bitte Tenant ID, User ID und Datei angeben")
        else:
            try:
                # Vorbereite Datei für Upload
                files = {'doc_file': uploaded_file}
                data = {
                    'tenant_id': tenant_id,
                    'user_id': user_id,
                    'scope': scope,
                    'group_id': group_id or ''
                }
                
                # Sende zu Backend
                response = requests.post('http://localhost:8000/upload', files=files, data=data)
                
                if response.status_code == 200:
                    st.success("✅ Datei erfolgreich hochgeladen!")
                    st.json(response.json())
                else:
                    st.error(f"❌ Fehler: {response.text}")
            except Exception as e:
                st.error(f"❌ Upload-Fehler: {e}")

# ==================== TAB 2: QUERY ====================
with main_tab2:
    st.subheader("🔎 Dokumenten durchsuchen")
    
    query_col1, query_col2 = st.columns(2)
    with query_col1:
        q_tenant_id = st.text_input("Tenant ID", key="query_tenant_id")
        q_user_id = st.text_input("User ID", key="query_user_id")
        q_scope = st.selectbox("Scope", ["user", "group", "company"], key="query_scope")
    with query_col2:
        q_group_id = st.text_input("Group ID (optional)", key="query_group_id")
    
    question = st.text_area("Deine Frage:", key="question_input")
    
    if st.button("🔍 Suchen", key="query_button"):
        if not q_tenant_id or not q_user_id or not question:
            st.error("❌ Bitte Tenant ID, User ID und Frage angeben")
        else:
            try:
                data = {
                    'tenant_id': q_tenant_id,
                    'user_id': q_user_id,
                    'scope': q_scope,
                    'group_id': q_group_id or '',
                    'question': question
                }
                
                response = requests.post('http://localhost:8000/query', json=data)
                
                if response.status_code == 200:
                    results = response.json()
                    st.success(f"✅ {len(results.get('documents', []))} Ergebnisse gefunden:")
                    
                    for i, doc in enumerate(results.get('documents', [])[:5]):
                        with st.expander(f"📌 Ergebnis {i+1}"):
                            st.write(doc)
                else:
                    st.error(f"❌ Fehler: {response.text}")
            except Exception as e:
                st.error(f"❌ Query-Fehler: {e}")

# ==================== TAB 3: EXPLORER ====================
with main_tab3:
    st.subheader("📊 ChromaDB Explorer")
    
    # Collections abrufen
    try:
        collections = client.list_collections()
        st.write(f"**Verfügbare Collections:** {len(collections)}")
        
        if collections:
            # Dropdown für Collection-Auswahl
            col_names = [c.name for c in collections]
            selected_col = st.selectbox("Wähle eine Collection:", col_names)
            
            # Hole Selected Collection
            col = client.get_collection(selected_col)
            
            # Statistiken
            st.subheader(f"📊 Collection: {selected_col}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Dokumente", col.count())
            with col2:
                st.metric("IDs", len(col.get(limit=1)['ids']) if col.count() > 0 else 0)
            
            # Tabs für verschiedene Ansichten
            exp_tab1, exp_tab2 = st.tabs(["📁 Dateien", "📄 Alle Chunks"])
            
            with exp_tab1:
                st.subheader("Hochgeladene Dateien")
                data = col.get(limit=col.count())
                
                # Gruppiere nach Dateiname
                files_dict = {}
                for doc_id, document, metadata in zip(data['ids'], data['documents'], data['metadatas'] or [None]*len(data['ids'])):
                    if metadata:
                        filename = metadata.get('filename', 'Unknown')
                        if filename not in files_dict:
                            files_dict[filename] = []
                        files_dict[filename].append((doc_id, document, metadata))
                    else:
                        if 'Unknown' not in files_dict:
                            files_dict['Unknown'] = []
                        files_dict['Unknown'].append((doc_id, document, metadata))
                
                if files_dict:
                    for filename, chunks_list in files_dict.items():
                        with st.expander(f"📄 {filename} ({len(chunks_list)} Chunks)"):
                            if chunks_list[0][2]:  # Falls Metadaten vorhanden
                                meta = chunks_list[0][2]
                                st.write("**📋 Datei-Informationen:**")
                                info_col1, info_col2 = st.columns(2)
                                with info_col1:
                                    st.write(f"- **Dateiname:** {meta.get('filename', 'N/A')}")
                                    st.write(f"- **Typ:** {meta.get('file_type', 'N/A')}")
                                    st.write(f"- **Größe:** {meta.get('file_size', 'N/A')} Bytes")
                                with info_col2:
                                    st.write(f"- **Hochgeladen:** {meta.get('upload_date', 'N/A')[:10]}")
                                    st.write(f"- **User:** {meta.get('user_id', 'N/A')}")
                                    st.write(f"- **Scope:** {meta.get('scope', 'N/A')}")
                                st.divider()
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Chunks", len(chunks_list))
                                with col2:
                                    st.metric("Größe (Bytes)", meta.get('file_size', 'N/A'))
                                with col3:
                                    st.metric("Scope", meta.get('scope', 'N/A'))
                                with col4:
                                    if st.button(f"🗑️ Löschen", key=f"delete_{filename}"):
                                        # Lösche alle Chunks dieser Datei
                                        delete_ids = [chunk[0] for chunk in chunks_list]
                                        try:
                                            col.delete(ids=delete_ids)
                                            st.success("✅ Datei gelöscht!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Fehler: {e}")
                            
                            st.write("**Chunk-Vorschau:**")
                            for i, (chunk_id, chunk_text, _) in enumerate(chunks_list[:3]):
                                st.write(f"Chunk {i+1}: `{chunk_text[:150]}...`")
                            if len(chunks_list) > 3:
                                st.caption(f"... und {len(chunks_list) - 3} weitere Chunks")
                else:
                    st.info("Keine Dateien mit Metadaten gefunden.")
            
            with exp_tab2:
                st.subheader("Alle Chunks")
                limit = st.slider("Wieviele Chunks anzeigen?", 5, 100, 20)
                data = col.get(limit=limit)
                
                st.write(f"Zeige {len(data['documents'])} von {col.count()} Chunks:")
                
                for i, (doc_id, document) in enumerate(zip(data['ids'], data['documents'])):
                    with st.expander(f"📋 {i+1}. {document[:80]}..."):
                        col_left, col_right = st.columns([4, 1])
                        with col_left:
                            st.write(f"**ID:** `{doc_id}`")
                            st.write(f"**Dokument-Inhalt:**")
                            st.code(document, language="text")
                        with col_right:
                            if st.button("🗑️", key=f"delete_chunk_{doc_id}", help="Diesen Chunk löschen"):
                                try:
                                    col.delete(ids=[doc_id])
                                    st.success("✅ Chunk gelöscht!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fehler: {e}")
            
            # Suche-Funktion
            st.subheader("🔎 Semantic Search")
            col_search1, col_search2 = st.columns([3, 1])
            
            with col_search1:
                search_query = st.text_input("Gib einen Suchbegriff ein:")
            with col_search2:
                min_similarity = st.slider("Min. Ähnlichkeit", 0, 100, 0) / 100
            
            if search_query:
                st.info(f"Suche nach: '{search_query}'")
                
                try:
                    # Embedd die Suchanfrage
                    query_emb = embed_text(search_query)
                    
                    # Suche in ChromaDB
                    results = col.query(query_embeddings=[query_emb], n_results=10)
                    
                    if results['documents'] and results['documents'][0]:
                        # Filtere nach Ähnlichkeitsschwelle
                        filtered = []
                        for doc, dist, meta in zip(results['documents'][0], results['distances'][0], results['metadatas'][0]):
                            similarity = 1 - dist
                            if similarity >= min_similarity:
                                filtered.append((doc, similarity, meta))
                        
                        if filtered:
                            st.success(f"✅ {len(filtered)} von {len(results['documents'][0])} Ergebnissen relevante gefunden:")
                            
                            for i, (doc, similarity, meta) in enumerate(filtered):
                                similarity_pct = similarity * 100
                                
                                with st.expander(f"📌 Ergebnis {i+1} ({similarity_pct:.1f}% Match)"):
                                    # Metadaten anzeigen (falls vorhanden)
                                    if meta:
                                        st.write("**📄 Datei-Informationen:**")
                                        st.write(f"- **Datei:** {meta.get('filename', 'N/A')}")
                                        st.write(f"- **Type:** {meta.get('file_type', 'N/A')}")
                                        st.write(f"- **Hochgeladen:** {meta.get('upload_date', 'N/A')[:10]}")
                                        st.write(f"- **User:** {meta.get('user_id', 'N/A')}")
                                        st.write(f"- **Scope:** {meta.get('scope', 'N/A')}")
                                    
                                    # Hauptinhalt mit größerer Vorschau
                                    st.write(f"**Ähnlichkeits-Score:** {similarity_pct:.1f}%")
                                    st.write(f"**Dokument-Inhalt:**")
                                    st.code(doc, language="text")
                        else:
                            st.warning(f"Keine Ergebnisse mit mindestens {min_similarity*100:.0f}% Ähnlichkeit gefunden.")
                    else:
                        st.warning("Keine ähnlichen Dokumente gefunden.")
                        
                except Exception as e:
                    st.error(f"Fehler bei der Suche: {e}")
                    st.write(f"Debug: {str(e)}")
        else:
            st.warning("Keine Collections gefunden. Lade zuerst Dokumente hoch.")
            
    except Exception as e:
        st.error(f"Fehler beim Verbinden zu ChromaDB: {e}")
        st.write("Stelle sicher, dass ChromaDB läuft und die CHROMA_URL korrekt ist.")

# Footer
st.divider()
st.caption("ChromaDB Dashboard v2.0 | TenantRAG")
