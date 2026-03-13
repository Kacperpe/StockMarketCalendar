import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "mt5_server" / "static" / "index.html"
APP_JS = ROOT / "mt5_server" / "static" / "app.js"
UI_FILES = (INDEX_HTML, APP_JS)


class UiSpellingTests(unittest.TestCase):
    def test_ui_files_are_utf8_and_without_mojibake(self):
        mojibake_markers = (
            "Ã",
            "Ä",
            "Å",
            "â€",
            "â€”",
            "â€¦",
            "Â",
            "\ufffd",
        )

        for path in UI_FILES:
            text = path.read_text(encoding="utf-8")
            bad_control_chars = [ch for ch in text if 127 <= ord(ch) <= 159]
            self.assertFalse(
                bad_control_chars,
                f"Found control characters in {path}: {sorted(set(bad_control_chars))}",
            )
            for marker in mojibake_markers:
                self.assertNotIn(marker, text, f"Found mojibake marker '{marker}' in {path}")

    def test_required_polish_words_exist_in_ui(self):
        text = (INDEX_HTML.read_text(encoding="utf-8") + "\n" + APP_JS.read_text(encoding="utf-8")).lower()
        required_words = {
            "połączyć",
            "hasło",
            "widoczność",
            "ładowanie",
            "następny",
            "dziś",
            "dostępna",
            "zakończona",
            "odświeżam",
            "powiodła",
            "błąd",
            "łączenia",
            "wyświetlić",
            "miesięczny",
            "bieżąca",
        }
        missing = sorted(word for word in required_words if word not in text)
        self.assertEqual([], missing, f"Missing required Polish words: {missing}")

    def test_common_wrong_forms_are_not_present(self):
        text = (INDEX_HTML.read_text(encoding="utf-8") + "\n" + APP_JS.read_text(encoding="utf-8")).lower()
        # Typical non-Polish/ASCII forms that should not appear in UI labels.
        disallowed_wrong_forms = {
            "polacz",
            "haslo",
            "widocznosc",
            "ladowanie",
            "dostepna",
            "zakonczona",
            "odswiezam",
            "powiodla",
            "blad",
            "laczenia",
            "wyswietlic",
            "miesieczny",
            "biezaca",
        }
        found = sorted(form for form in disallowed_wrong_forms if re.search(rf"\b{re.escape(form)}\b", text))
        self.assertEqual([], found, f"Found disallowed wrong forms: {found}")


if __name__ == "__main__":
    unittest.main()
