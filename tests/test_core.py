import os
import sys
import tempfile
import time
import unittest
import zipfile
import hashlib
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TMP = tempfile.mkdtemp()
os.environ["ECOEDITH_DATA_DIR"] = _TMP          # tests never touch real data

from backend import auth, user_db                                   # noqa: E402
from backend.context import select_spread, sources_line            # noqa: E402
from backend.evaluate_assignment import parse_score                 # noqa: E402
from backend.flashcards import clean_flashcards                     # noqa: E402
from backend.jsonutil import extract_json                           # noqa: E402
from backend.loader import load_document                            # noqa: E402
from backend import loader as loader_mod                            # noqa: E402
from backend.mindmap import clean_mindmap, sample_text              # noqa: E402
from backend.quiz import clean_questions                            # noqa: E402
from backend.voice import clean_for_speech                          # noqa: E402
from backend import stats as stats_mod                              # noqa: E402


class AuthTests(unittest.TestCase):
    def test_register_login(self):
        self.assertTrue(auth.register_user("alice_1", "password1", "a@x.com")[0])
        self.assertTrue(auth.login_user("  ALICE_1 ", "password1")[0])   # trims + case-insensitive
        self.assertFalse(auth.login_user("alice_1", "wrongpass")[0])

    def test_path_traversal_rejected(self):
        for bad in ["../../evil", "a/b", "..", "x y z", "ab", "a" * 31, ""]:
            self.assertFalse(auth.register_user(bad, "password1", "b@x.com")[0], bad)
        with self.assertRaises(ValueError):
            user_db.user_dir("../../evil")

    def test_password_is_salted(self):
        h1, h2 = auth.hash_password("same-password"), auth.hash_password("same-password")
        self.assertNotEqual(h1, h2)
        self.assertTrue(auth.verify_password("same-password", h1))
        self.assertFalse(auth.verify_password("other", h1))

    def test_legacy_sha256_upgraded_on_login(self):
        users = auth.load_users()
        users["olduser"] = {"password": hashlib.sha256(b"oldpass1").hexdigest(),
                            "email": "o@x.com", "created_at": "", "last_login": None}
        auth.save_users(users)
        self.assertTrue(auth.login_user("olduser", "oldpass1")[0])
        self.assertTrue(auth.load_users()["olduser"]["password"].startswith("pbkdf2_sha256$"))

    def test_validation_and_duplicates(self):
        self.assertFalse(auth.register_user("bob_ok", "short", "b@x.com")[0])
        self.assertFalse(auth.register_user("bob_ok", "password1", "not-an-email")[0])
        self.assertTrue(auth.register_user("bob_ok", "password1", "bob@x.com")[0])
        self.assertFalse(auth.register_user("bob_ok", "password1", "other@x.com")[0])
        self.assertFalse(auth.register_user("bob_two", "password1", "BOB@x.com")[0])

    def test_lockout(self):
        auth.register_user("carol_1", "password1", "c@x.com")
        for _ in range(auth.MAX_FAILED_ATTEMPTS):
            auth.login_user("carol_1", "bad-password")
        ok, msg = auth.login_user("carol_1", "password1")
        self.assertFalse(ok)
        self.assertIn("Too many", msg)

    def test_change_password(self):
        auth.register_user("dave_1", "password1", "d@x.com")
        self.assertFalse(auth.change_password("dave_1", "wrong", "newpassword")[0])
        self.assertTrue(auth.change_password("dave_1", "password1", "newpassword")[0])
        self.assertTrue(auth.login_user("dave_1", "newpassword")[0])


class StorageTests(unittest.TestCase):
    def test_user_theme_defaults_and_persists_per_user(self):
        self.assertEqual(user_db.get_user_theme("theme_one"), "amethyst")
        user_db.save_user_theme("theme_one", "ocean")
        self.assertEqual(user_db.get_user_theme("theme_one"), "ocean")
        self.assertEqual(user_db.get_user_theme("theme_two"), "amethyst")

    def test_user_theme_rejects_unknown_palette(self):
        with self.assertRaises(ValueError):
            user_db.save_user_theme("theme_user", "unknown")

    def test_stats_defaults_and_merge(self):
        s = user_db.get_user_stats("erin_1")
        self.assertEqual(s["questions"], 0)
        user_db.atomic_write_json(user_db.user_dir("erin_1") / "stats.json", {"questions": 3})
        s = user_db.get_user_stats("erin_1")          # old file missing keys -> no KeyError
        self.assertEqual((s["questions"], s["best_score"]), (3, 0))

    def test_stats_functions(self):
        stats_mod.add_question("fred_1")
        stats_mod.add_quiz(66.7, "fred_1")
        stats_mod.add_quiz(40, "fred_1")
        stats_mod.add_voice_assignment(7.5, "fred_1")
        s = stats_mod.get_stats("fred_1")
        self.assertEqual((s["questions"], s["quizzes"], s["best_score"]), (1, 2, 67))
        self.assertEqual((s["voice_assignments"], s["voice_total_score"]), (1, 7.5))

    def test_history_cap(self):
        for i in range(user_db.MAX_HISTORY + 20):
            user_db.add_to_history("gina_1", f"q{i}", "a")
        self.assertEqual(len(user_db.get_user_history("gina_1")), user_db.MAX_HISTORY)

    def test_users_isolated(self):
        user_db.save_user_full_text("hank_1", "secret")
        self.assertEqual(user_db.get_user_full_text("ivy_1"), "")


class LoaderTests(unittest.TestCase):
    def test_txt_sections_and_pages(self):
        p = os.path.join(_TMP, "n.txt")
        with open(p, "w") as f:
            f.write("\n\n".join(f"Paragraph {i} " + "word " * 120 for i in range(20)))
        docs = load_document(p)
        self.assertGreater(len(docs), 1)
        self.assertEqual([d.metadata["page"] for d in docs], list(range(1, len(docs) + 1)))
        self.assertEqual(docs[0].metadata["unit"], "Section")

    def test_empty_file_rejected(self):
        p = os.path.join(_TMP, "empty.txt")
        open(p, "w").close()
        with self.assertRaises(ValueError):
            load_document(p)

    def test_unsupported_type(self):
        with self.assertRaises(ValueError):
            load_document(os.path.join(_TMP, "x.exe"))

    def test_docx_with_table(self):
        import docx
        p = os.path.join(_TMP, "real.docx")
        d = docx.Document()
        d.add_paragraph("Hello docx world")
        t = d.add_table(rows=1, cols=2)
        t.rows[0].cells[0].text = "Term"
        t.rows[0].cells[1].text = "Definition"
        d.save(p)
        text = load_document(p)[0].page_content
        self.assertIn("Hello docx world", text)
        self.assertIn("Term | Definition", text)      # tables were ignored before

    def test_corrupt_docx_gives_friendly_error(self):
        p = os.path.join(_TMP, "bad.docx")
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("junk.txt", "x")
        with self.assertRaises(ValueError):
            load_document(p)

    @mock.patch("pypdf.PdfReader")
    def test_pdf_pages_load_without_langchain_community(self, pdf_reader):
        pdf_reader.return_value.pages = [
            mock.Mock(extract_text=lambda: "First page"),
            mock.Mock(extract_text=lambda: " "),
            mock.Mock(extract_text=lambda: "Third page"),
        ]
        docs = loader_mod._load_pdf("sample.pdf", "sample.pdf")

        self.assertEqual([doc.page_content for doc in docs], ["First page", "Third page"])
        self.assertEqual([doc.metadata["page"] for doc in docs], [1, 3])


class ContextTests(unittest.TestCase):
    def chunks(self, n):
        return [{"text": "x" * 1000, "page": i + 1, "unit": "Page"} for i in range(n)]

    def test_small_doc_returned_whole(self):
        self.assertEqual(len(select_spread(self.chunks(5), 12000)), 5)

    def test_large_doc_spread_over_whole_document(self):
        picked = select_spread(self.chunks(100), 10000)
        pages = [c["page"] for c in picked]
        self.assertLessEqual(len(picked), 10)
        self.assertLess(pages[0], 15)
        self.assertGreater(pages[-1], 85)          # reaches the END, old code never did

    def test_offset_changes_selection(self):
        a = [c["page"] for c in select_spread(self.chunks(100), 10000, 0.0)]
        b = [c["page"] for c in select_spread(self.chunks(100), 10000, 0.5)]
        self.assertNotEqual(a, b)

    def test_sources_line(self):
        self.assertEqual(sources_line([{"page": 3, "unit": "Page"}, {"page": 1, "unit": "Page"}]),
                         "Pages 1, 3")


class ParsingTests(unittest.TestCase):
    def test_extract_json_variants(self):
        self.assertEqual(extract_json('```json\n[{"a": 1}]\n```', list), [{"a": 1}])
        self.assertEqual(extract_json('Sure! Here: {"root": "x"} hope it helps', dict), {"root": "x"})
        with self.assertRaises(ValueError):
            extract_json("no json here")

    def test_quiz_validation(self):
        raw = [
            {"question": "ok", "options": ["a", "b", "c", "d"], "answer": 2, "page": 3},
            {"question": "letter", "options": ["a", "b", "c", "d"], "answer": "B"},
            {"question": "text", "options": ["a", "b", "c", "d"], "answer": "d"},
            {"question": "bad idx", "options": ["a", "b", "c", "d"], "answer": 9},
            {"question": "few", "options": ["a"], "answer": 0},
            {"question": "dups", "options": ["a", "a"], "answer": 0},
            "garbage",
        ]
        qs = clean_questions(raw)
        self.assertEqual([q["answer"] for q in qs], [2, 1, 3])
        self.assertEqual(qs[0]["page"], 3)

    def test_flashcards_validation(self):
        cards = clean_flashcards([{"front": "q", "back": "a", "page": 2}, {"front": "", "back": "x"}, 5])
        self.assertEqual(len(cards), 1)

    def test_score_parsing(self):
        self.assertEqual(parse_score("Score: 8/10"), 8)
        self.assertEqual(parse_score("**Score:** 7.5/10"), 7.5)       # old regex returned 0
        self.assertEqual(parse_score("Score: 15/10"), 10)
        self.assertIsNone(parse_score("no score at all"))

    def test_mindmap(self):
        m = clean_mindmap({"root": "R", "branches": [{"title": "B", "items": ["a", "a", "b"]}] * 7})
        self.assertEqual(len(m["branches"]), 5)
        with self.assertRaises(ValueError):
            clean_mindmap({"root": "R", "branches": []})
        text = "".join(chr(65 + i % 26) for i in range(50000))
        self.assertLessEqual(len(sample_text(text)), 12100)

    def test_speech_cleaning(self):
        out = clean_for_speech("## Title\n**Bold** text 🎓\n\n---\n📄 **Sources:** Pages 1, 2")
        self.assertNotIn("Sources", out)
        self.assertNotIn("*", out)
        self.assertNotIn("🎓", out)


if __name__ == "__main__":
    unittest.main()
