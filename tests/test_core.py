import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from retraction_checker.cli import main
from retraction_checker.core import RetractionIndex, extract_dois, screen, status_of

CSV = """Record ID,Title,Journal,RetractionDate,RetractionDOI,OriginalPaperDOI,RetractionNature,Reason
1,Fake results paper,J Fake,1/5/2020 0:00,10.1000/notice1,10.1000/BAD1,Retraction,+Fabrication of Data;+Investigation by Journal;
2,Fixed figure paper,J Ok,3/1/2021 0:00,10.1000/notice2,10.1000/fix2,Correction,+Error in Figure;
3,Worrying paper,J Hmm,4/1/2022 0:00,10.1000/notice3,10.1000/eoc3,Expression of concern,+Concerns about Data;
4,Same paper later retracted,J Hmm,6/1/2023 0:00,10.1000/notice4,10.1000/eoc3,Retraction,+Results Not Reproducible;
5,No doi,J X,1/1/2000 0:00,,unavailable,Retraction,
"""


def index():
    return RetractionIndex.from_csv(io.StringIO(CSV))


class IndexTests(unittest.TestCase):
    def test_load_skips_missing_dois_and_groups(self):
        idx = index()
        self.assertEqual(len(idx), 3)
        self.assertEqual(len(idx.lookup("https://doi.org/10.1000/EOC3")), 2)

    def test_reason_parsing(self):
        n = index().lookup("10.1000/bad1")[0]
        self.assertEqual(n["reasons"], ["Fabrication of Data", "Investigation by Journal"])
        self.assertEqual(n["date"], "1/5/2020")

    def test_status_takes_most_severe(self):
        self.assertEqual(status_of(index().lookup("10.1000/eoc3")), "Retraction")
        self.assertEqual(status_of([]), "")


class ScreenTests(unittest.TestCase):
    def test_screen_filters_corrections_by_default(self):
        dois = ["10.1000/fix2", "10.1000/bad1", "10.1000/clean"]
        self.assertEqual([h["doi"] for h in screen(dois, index())], ["10.1000/bad1"])
        self.assertEqual(len(screen(dois, index(), include_corrections=True)), 2)

    def test_extract_dois_from_bib(self):
        text = "@article{a, doi={10.1000/BAD1}}\n@article{b, url={https://doi.org/10.1000/clean.}}"
        self.assertEqual(extract_dois(text), ["10.1000/bad1", "10.1000/clean"])

    def test_cli_exit_code_and_output(self):
        with tempfile.TemporaryDirectory() as d:
            db, bib = os.path.join(d, "rw.csv"), os.path.join(d, "refs.bib")
            with open(db, "w", encoding="utf-8") as fh:
                fh.write(CSV)
            with open(bib, "w", encoding="utf-8") as fh:
                fh.write("doi = {10.1000/bad1}, doi={10.1000/ok}")
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(main([bib, "-d", db]), 1)
            self.assertIn("[RETRACTION] 10.1000/bad1", buf.getvalue())
            with open(bib, "w", encoding="utf-8") as fh:
                fh.write("doi = {10.1000/ok}")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main([bib, "-d", db]), 0)


if __name__ == "__main__":
    unittest.main()
