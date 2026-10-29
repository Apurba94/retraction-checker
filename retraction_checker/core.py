"""Index the Retraction Watch dataset (CSV) and check DOIs against it."""
import csv
import re

_DOI = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)")

# Column names used by the Retraction Watch database CSV (distributed openly via Crossref since 2023).
COLUMNS = {
    "original_doi": ("OriginalPaperDOI", "original_doi", "doi"),
    "notice_doi": ("RetractionDOI", "retraction_doi", "notice_doi"),
    "nature": ("RetractionNature", "nature", "type"),
    "date": ("RetractionDate", "date"),
    "reason": ("Reason", "reason"),
    "title": ("Title", "title"),
    "journal": ("Journal", "journal"),
}
SEVERITY = {"retraction": 3, "expression of concern": 2, "correction": 1, "reinstatement": 0}


def normalize_doi(doi):
    d = (doi or "").strip().lower()
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d.rstrip(".,;")


def extract_dois(text):
    seen, out = set(), []
    for m in _DOI.finditer(text):
        d = normalize_doi(m.group(1))
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def _col(row, name):
    for c in COLUMNS[name]:
        if c in row and row[c] is not None:
            return row[c].strip()
    return ""


class RetractionIndex:
    """DOI -> list of notices. Reasons in the RW dataset are ';'-separated and '+'-prefixed."""

    def __init__(self):
        self.by_doi = {}

    @classmethod
    def from_csv(cls, path_or_lines):
        idx = cls()
        if isinstance(path_or_lines, str):
            with open(path_or_lines, newline="", encoding="utf-8", errors="replace") as fh:
                idx.load(csv.DictReader(fh))
        else:
            idx.load(csv.DictReader(path_or_lines))
        return idx

    def load(self, rows):
        for row in rows:
            doi = normalize_doi(_col(row, "original_doi"))
            if not doi or doi in ("unavailable", "na"):
                continue
            reasons = [r.strip().lstrip("+").strip() for r in _col(row, "reason").split(";") if r.strip(" +")]
            self.by_doi.setdefault(doi, []).append({
                "nature": _col(row, "nature") or "Retraction",
                "date": _col(row, "date").split(" ")[0],
                "notice_doi": normalize_doi(_col(row, "notice_doi")),
                "reasons": reasons,
                "title": _col(row, "title"),
                "journal": _col(row, "journal"),
            })
        return self

    def __len__(self):
        return len(self.by_doi)

    def lookup(self, doi):
        return self.by_doi.get(normalize_doi(doi), [])


def status_of(notices):
    """Most severe notice nature, e.g. 'Retraction'; '' if none."""
    if not notices:
        return ""
    return max((n["nature"] for n in notices), key=lambda s: SEVERITY.get(s.lower(), 1))


def screen(dois, index, include_corrections=False):
    """Return a list of hits: dicts with doi, status and notices, most severe first."""
    hits = []
    for d in dois:
        notices = index.lookup(d)
        st = status_of(notices)
        if not st:
            continue
        if not include_corrections and SEVERITY.get(st.lower(), 1) < 2:
            continue
        hits.append({"doi": normalize_doi(d), "status": st, "notices": notices})
    return sorted(hits, key=lambda h: (-SEVERITY.get(h["status"].lower(), 1), h["doi"]))
