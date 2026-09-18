"""Deutsche Textverarbeitung: Normalisierung, Segmentierung, Komposita."""

from __future__ import annotations

from deutsches_ki.text.abbreviations import ABBREVIATIONS, is_abbreviation
from deutsches_ki.text.compounds import (
    CompoundAnalysis,
    analyze_compound,
    decompound_for_search,
)
from deutsches_ki.text.dictionary import get_dictionary, is_known_word
from deutsches_ki.text.normalize import (
    NormalizeMode,
    normalize_case,
    normalize_dashes,
    normalize_ergaenzung,
    normalize_for_search,
    normalize_german,
    normalize_punctuation,
    normalize_quotes,
    normalize_ss,
    normalize_umlauts,
    normalize_unicode,
    normalize_whitespace,
)
from deutsches_ki.text.query import default_glossary, expand_query
from deutsches_ki.text.segment import split_sentences, tokenize_words
from deutsches_ki.text.tokens import search_tokens

__all__ = [
    "ABBREVIATIONS",
    "CompoundAnalysis",
    "NormalizeMode",
    "analyze_compound",
    "decompound_for_search",
    "default_glossary",
    "expand_query",
    "get_dictionary",
    "is_abbreviation",
    "is_known_word",
    "normalize_case",
    "normalize_dashes",
    "normalize_ergaenzung",
    "normalize_for_search",
    "normalize_german",
    "normalize_punctuation",
    "normalize_quotes",
    "normalize_ss",
    "normalize_umlauts",
    "normalize_unicode",
    "normalize_whitespace",
    "search_tokens",
    "split_sentences",
    "tokenize_words",
]
