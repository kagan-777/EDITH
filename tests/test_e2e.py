"""End-to-end pipeline tests with a fake embedder and fake LLM (works offline)."""
import hashlib
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["ECOEDITH_DATA_DIR"] = tempfile.mkdtemp()

from backend import user_db, vectorstore, retriever, rag, quiz, flashcards, mindmap, notes
from backend import teaching, history
from backend.errors import NoDocumentError
from backend.loader import full_text, load_document
from backend.splitter import split_documents


class FakeEmbeddings:
    def _encode(self, text):
        vector = [0.0] * 64
        for token in re.findall(r"\w+", text.casefold()):
            index = int(hashlib.sha256(token.encode()).hexdigest(), 16) % len(vector)
            vector[index] += 1
        return vector

    def embed_documents(self, texts):
        return [self._encode(text) for text in texts]

    def embed_query(self, text):
        return self._encode(text)


FAKE_EMB = FakeEmbeddings()


def _write_doc(name, n_paragraphs):
    p = os.path.join(tempfile.mkdtemp(), name)
    with open(p, "w") as f:
        f.write("\n\n".join(f"Topic {i}: " + ("concept detail " * 60) for i in range(n_paragraphs)))
    return p


def _index(user, path):
    docs = load_document(path)
    chunks = split_documents(docs)
    vectorstore.create_vector_store(chunks, user)
    user_db.save_user_full_text(user, full_text(docs))
    return chunks


@mock.patch("backend.vectorstore.get_embedding_model", return_value=FAKE_EMB)
class PipelineTests(unittest.TestCase):
    def test_chat_answers_from_general_knowledge_without_document(self, _):
        with mock.patch("backend.rag.ask_llm", return_value="A general answer.") as ask_llm:
            answer = rag.ask_rag("What is photosynthesis?", "nodoc_user")

        self.assertEqual(answer, "A general answer.")
        self.assertNotIn("Sources:", answer)
        self.assertIn("No relevant excerpt", ask_llm.call_args.args[0])

    def test_other_document_features_require_document(self, _):
        with self.assertRaises(NoDocumentError):
            notes.generate_notes("nodoc_user")
        with self.assertRaises(NoDocumentError):
            mindmap.generate_mindmap("nodoc_user")

    def test_reupload_replaces_instead_of_duplicating(self, _):
        a = _index("u_replace", _write_doc("a.txt", 12))
        n1 = len(retriever.get_all_chunks("u_replace"))
        self.assertEqual(n1, len(a))
        b = _index("u_replace", _write_doc("b.txt", 4))
        n2 = len(retriever.get_all_chunks("u_replace"))
        self.assertEqual(n2, len(b))                  # old document is gone
        _index("u_replace", _write_doc("b.txt", 4))   # same doc again: no duplicates
        self.assertEqual(len(retriever.get_all_chunks("u_replace")), len(b))

    def test_users_have_separate_indexes(self, _):
        _index("u_one", _write_doc("a.txt", 10))
        self.assertEqual(retriever.get_all_chunks("u_two"), [])

    def test_bm25_fallback_when_embedding_model_is_unavailable(self, _):
        with self.assertLogs("backend.vectorstore", level="ERROR"):
            with mock.patch(
                "backend.vectorstore.get_embedding_model",
                side_effect=RuntimeError("embedding model unavailable"),
            ):
                _index("u_bm25", _write_doc("topics.txt", 12))

                results = retriever.search("u_bm25", "Topic 9")

        self.assertIn("Topic 9:", results[0]["text"])
        self.assertEqual(retriever.search("u_bm25", "volcanology"), [])

    def test_greeting_does_not_retrieve_or_call_llm(self, _):
        with mock.patch("backend.rag.search") as search, mock.patch(
            "backend.rag.ask_llm"
        ) as ask_llm:
            answer = rag.ask_rag("hi!", "u_greeting")

        self.assertEqual(answer, rag.GREETING)
        search.assert_not_called()
        ask_llm.assert_not_called()

    def test_irrelevant_question_gets_general_answer_without_sources(self, _):
        _index("u_irrelevant", _write_doc("a.txt", 8))
        model = mock.Mock()
        model.embed_query.return_value = [0.0] * 64

        with mock.patch("backend.vectorstore.get_embedding_model", return_value=model):
            with mock.patch(
                "backend.rag.ask_llm", return_value="A general answer."
            ) as ask_llm:
                answer = rag.ask_rag("What is quantum mechanics?", "u_irrelevant")

        self.assertEqual(answer, "A general answer.")
        self.assertNotIn("Sources:", answer)
        self.assertIn("No relevant excerpt", ask_llm.call_args.args[0])

    def test_rag_with_sources_and_history(self, _):
        _index("u_rag", _write_doc("a.txt", 8))
        conversation = [{"role": "user", "content": "Tell me about Topic 3."}]
        with mock.patch(
            "backend.rag.ask_llm", return_value="Here is the answer."
        ) as ask_llm:
            out = rag.ask_rag(
                "What is Topic 3?",
                "u_rag",
                conversation_history=conversation,
            )
            prompt = ask_llm.call_args.args[0]
        self.assertIn("Here is the answer.", out)
        self.assertIn("Sources:", out)
        self.assertEqual(history.get_history("u_rag")[0]["question"], "What is Topic 3?")
        self.assertIn("study material with your general knowledge", prompt)
        self.assertIn("Tell me about Topic 3.", prompt)

    def test_notes_context_covers_whole_document(self, _):
        _index("u_notes", _write_doc("big.txt", 80))
        seen = {}
        def fake(prompt, **kw):
            seen["prompt"] = prompt
            return "NOTES"
        with mock.patch("backend.notes.ask_llm", side_effect=fake):
            self.assertEqual(notes.generate_notes("u_notes"), "NOTES")
        pages = [int(x) for x in __import__("re").findall(r"\[Section (\d+)\]", seen["prompt"])]
        total = max(c["page"] for c in retriever.get_all_chunks("u_notes"))
        self.assertGreater(len(set(pages)), 3)
        self.assertGreater(max(pages), total * 0.7)    # reaches the end of the document

    def test_quiz_flashcards_mindmap_generation(self, _):
        _index("u_gen", _write_doc("a.txt", 10))
        q = json.dumps([{"question": "Q?", "options": ["a", "b", "c", "d"], "answer": 1,
                         "explanation": "because", "page": 2}])
        with mock.patch("backend.quiz.ask_llm", return_value="```json\n" + q + "\n```"):
            self.assertEqual(quiz.generate_quiz("u_gen", 3)[0]["answer"], 1)
        f = json.dumps([{"front": "F", "back": "B", "page": 1}])
        with mock.patch("backend.flashcards.ask_llm", return_value="Here you go: " + f):
            self.assertEqual(flashcards.generate_flashcards("u_gen")[0]["front"], "F")
        m = json.dumps({"root": "R", "branches": [{"title": "T", "items": ["x"]}]})
        with mock.patch("backend.mindmap.ask_llm", return_value=m):
            self.assertEqual(mindmap.generate_mindmap("u_gen")["root"], "R")   # per-user file works now

    def test_teaching(self, _):
        _index("u_teach", _write_doc("a.txt", 6))
        with mock.patch("backend.teaching.ask_llm", return_value="Simple explanation"):
            out = teaching.teach_topic("Topic 2", "ELI5", "u_teach")
        self.assertIn("Simple explanation", out)

    def test_delete_document(self, _):
        _index("u_del", _write_doc("a.txt", 6))
        vectorstore.delete_document("u_del")
        self.assertEqual(retriever.get_all_chunks("u_del"), [])
        self.assertEqual(user_db.get_user_full_text("u_del"), "")


if __name__ == "__main__":
    unittest.main()
