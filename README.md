# 🎓 EcoEdith

AI-powered learning platform: upload your study material (PDF / DOCX / TXT) and
chat with it, or generate notes, summaries, quizzes, flashcards, mind maps and
study plans. Includes voice chat and AI-graded voice assignments.

Built with Streamlit, LangChain text splitting, Sentence-Transformers, OpenRouter and gTTS.
Document search uses sentence embeddings when available and falls back to local BM25 keyword search.
Chat combines relevant document excerpts with general AI knowledge and uses recent messages to
understand follow-up questions.

## Vercel deployment

The `web/` Next.js app and `api/` FastAPI service provide a Vercel-ready MVP for persistent
accounts, private document uploads, and AI chat grounded in uploaded material plus general
knowledge. They run as two Vercel Services on one domain. The existing Streamlit app remains
available for local use; its local accounts and files are not migrated automatically.

1. Import this repository into Vercel and keep the repository root as the project root.
   The root `vercel.json` routes `/api/*` to FastAPI and all other paths to Next.js.
2. Connect a PostgreSQL Marketplace database and a **private** Vercel Blob store to the project.
   Connect them to every Vercel environment you plan to use. The API stores accounts, chat
   history, and extracted document chunks in PostgreSQL; original files stay in Blob.
3. Add these environment variables in Vercel Project Settings:
   - `OPENROUTER_API_KEY`: your OpenRouter key.
   - `AUTH_SECRET`: a randomly generated secret of at least 32 characters. For example,
     generate one locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
   - `POSTGRES_URL`: supplied by the connected PostgreSQL integration if it is not already set.
   - `BLOB_STORE_ID` and Vercel OIDC credentials are supplied by the connected Blob store.
     The Blob integration must also provide `BLOB_READ_WRITE_TOKEN` for browser uploads.
4. Deploy from Vercel, or push a commit to the connected Git branch. Check `/api/health`, then
   create an account, upload a PDF/DOCX/TXT file, and ask a question in the chat.

Do not commit `.env` files or paste secrets into chat. Use separate database resources for
Development, Preview, and Production. Vercel Services and container runtime availability and
limits depend on Vercel's current beta/plan terms. The Vercel MVP currently includes account
access, one current document per user, and persistent document-aware chat; it does not yet
replace the Streamlit app's notes, quizzes, flashcards, or other study tools.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your OPENROUTER_API_KEY inside
streamlit run app.py
```

**ffmpeg** must be installed for voice features (Whisper): `sudo apt install ffmpeg`,
`brew install ffmpeg`, or `winget install ffmpeg`.

## How it works

1. Register / log in (`app.py`).
2. **Upload** a document: it is split into chunks and indexed in a private JSON file.
   A new upload replaces the old one.
3. Use any feature. Chat and Teaching use similarity search (RAG); Notes, Summary,
   Plan, Quiz, Flashcards and Mind Map use chunks spread across the whole document.

## Data layout (all git-ignored)

```
data/users.json                 accounts (PBKDF2-salted password hashes)
data/user_data/<username>/      stats, history, uploaded file, document_index.json
```

If you have data from the old version (`users.json` / `user_data/` in the project root),
it is imported automatically on first run and old passwords are upgraded on next login.
After upgrading from a ChromaDB version, reprocess your uploaded document to create
the new search index.

## Tests

```bash
python -m unittest discover tests -v
```

## Notes

- Scanned (image-only) PDFs have no text layer; run OCR first.
- DOCX/TXT files have no real pages, so sources are shown as "Section N".
- The legacy Streamlit app uses in-memory sessions. The Vercel MVP uses a signed,
  HTTP-only session cookie and stores account data in PostgreSQL.
