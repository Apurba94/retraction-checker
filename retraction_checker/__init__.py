"""Screen bibliographies for retracted or corrected papers."""
from .core import RetractionIndex, extract_dois, normalize_doi, screen

__version__ = "0.1.0"
__all__ = ["RetractionIndex", "extract_dois", "normalize_doi", "screen"]
