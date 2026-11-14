import os
from datetime import datetime

import streamlit as st

from backend import user_db
from backend.loader import SUPPORTED, full_text, load_document
from backend.session import require_login, reset_generated_content, run_ai
from backend.splitter import split_documents
from backend.vectorstore import create_vector_store, delete_document

st.set_page_config(page_title="Upload Materials", page_icon="📄", layout="wide")
user = require_login()

MAX_MB = 25

st.title("📄 Upload Learning Materials")
st.write("Upload one study file. A new upload **replaces** your previous document.")


def process(uploaded):
    name = os.path.basename(uploaded.name)              # never trust the client path
    if os.path.splitext(name)[1].lower() not in SUPPORTED:
        raise ValueError("Unsupported file type. Use PDF, DOCX or TXT.")
    if uploaded.size > MAX_MB * 1024 * 1024:
        raise ValueError(f"File is too large (max {MAX_MB} MB).")

    uploads = user_db.get_user_uploads_dir(user)
    for old in uploads.iterdir():                       # keep only the current file
        old.unlink()
    path = uploads / name
    path.write_bytes(uploaded.getbuffer())

    documents = load_document(str(path))
    chunks = split_documents(documents)
    if not chunks:
        raise ValueError("The document produced no text chunks.")
    create_vector_store(chunks, user)                   # replaces the old index
    user_db.save_user_full_text(user, full_text(documents))
    user_db.save_doc_meta(user, {
        "name": name,
        "chunks": len(chunks),
        "characters": sum(len(c.page_content) for c in chunks),
        "uploaded_at": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
    })
    reset_generated_content()                           # old notes/quiz belong to the old file
    return chunks


uploaded = st.file_uploader("Choose a file", type=[e.strip(".") for e in SUPPORTED])

if uploaded is not None and st.button("⚙️ Process Document", type="primary"):
    chunks = run_ai("Reading, splitting and indexing your document...", process, uploaded)
    if chunks:
        st.success(f"✅ {uploaded.name} processed - {len(chunks)} chunks stored.")
        st.session_state["upload_preview"] = [
            (c.metadata.get("unit", "Page"), c.metadata.get("page", "?"), c.page_content)
            for c in chunks[:5]
        ]

st.divider()
meta = user_db.get_doc_meta(user)
if meta:
    st.subheader("📚 Current document")
    c1, c2, c3 = st.columns(3)
    c1.metric("File", meta["name"])
    c2.metric("Chunks", meta["chunks"])
    c3.metric("Uploaded", meta["uploaded_at"])

    preview = st.session_state.get("upload_preview")
    if preview:
        with st.expander("Preview first chunks"):
            for unit, page, text in preview:
                st.caption(f"{unit} {page}")
                st.write(text)

    if st.button("🗑 Delete this document"):
        delete_document(user)
        reset_generated_content()
        st.session_state.pop("upload_preview", None)
        st.rerun()
else:
    st.info("No document uploaded yet.")
