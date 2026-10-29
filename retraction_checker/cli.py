"""Command-line interface for retraction-checker."""
import argparse
import json

from .core import RetractionIndex, extract_dois, screen


def main(argv=None):
    ap = argparse.ArgumentParser(prog="retraction-checker",
                                 description="Check the DOIs in a bibliography or manuscript against the Retraction Watch dataset.")
    ap.add_argument("inputs", nargs="+", help=".bib, .tex, .txt, .ris ... files containing DOIs")
    ap.add_argument("-d", "--database", required=True,
                    help="Retraction Watch CSV (download: https://gitlab.com/crossref/retraction-watch-data)")
    ap.add_argument("--corrections", action="store_true", help="also report corrections")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    dois = []
    for path in args.inputs:
        with open(path, encoding="utf-8", errors="replace") as fh:
            dois += [d for d in extract_dois(fh.read()) if d not in dois]
    index = RetractionIndex.from_csv(args.database)
    hits = screen(dois, index, args.corrections)
    if args.json:
        print(json.dumps({"checked": len(dois), "hits": hits}, indent=2))
    else:
        print("Checked %d DOI(s) against %d records." % (len(dois), len(index)))
        for h in hits:
            n = h["notices"][0]
            print("\n[%s] %s\n    %s (%s)\n    notice: %s\n    reasons: %s" % (
                h["status"].upper(), h["doi"], n["title"][:80], n["date"],
                ("https://doi.org/" + n["notice_doi"]) if n["notice_doi"] else "-", "; ".join(n["reasons"][:4]) or "-"))
        if not hits:
            print("No retracted papers found.")
    return 1 if any(h["status"].lower() == "retraction" for h in hits) else 0
