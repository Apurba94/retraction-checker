# retraction-checker

**Make sure you are not citing retracted science: screen every DOI in a `.bib`, manuscript or
reference list against the Retraction Watch database, offline.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Retracted papers keep being cited for years after retraction, often because authors simply
do not know. Citing them weakens a manuscript and can propagate fabricated results into reviews
and meta-analyses. Since 2023 the Retraction Watch database is openly available through Crossref,
so every author can check a bibliography in seconds before submission.

## Features

- Extracts DOIs from any text file (`.bib`, `.tex`, `.ris`, `.txt`, `.md`)
- Indexes the Retraction Watch CSV (column names auto-detected); groups multiple notices per paper
- Severity ranking: retraction > expression of concern > correction; corrections optional
- Shows notice DOI, date and reasons (e.g. *Fabrication of Data*)
- Exit code 1 if a retracted paper is cited (use as a pre-submission or CI gate); JSON output

## Usage

1. Download the dataset CSV from https://gitlab.com/crossref/retraction-watch-data
2. Run:

```bash
pip install .
retraction-checker refs.bib -d retraction_watch.csv
retraction-checker manuscript.tex refs.bib -d retraction_watch.csv --corrections --json
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA. The Retraction Watch data has its own terms of use.
