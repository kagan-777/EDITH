# 🎓 EcoEdith

AI-powered learning platform: upload your study material (PDF / DOCX / TXT) and
chat with it, or generate notes, summaries, quizzes, flashcards, mind maps and
study plans. Includes voice chat and AI-graded voice assignments.

Built with Streamlit, LangChain text splitting, Sentence-Transformers, OpenRouter and gTTS.
Document search uses sentence embeddings when available and falls back to local BM25 keyword search.
Chat combines relevant document excerpts with general AI knowledge and uses recent messages to
understand follow-up questions.

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
- Sessions are in-memory: refreshing the browser logs you out.
