"""Deutsche Stoppwörter.

Für Vergleiche wie „Steht diese Antwort in den Quellen?“ zählen nur
inhaltstragende Wörter. „die“, „der“ und „ist“ stehen überall und würden jede
Überdeckung künstlich auf neunzig Prozent heben.
"""

from __future__ import annotations

from deutsches_ki.text.folding import fold
from deutsches_ki.text.tokens import search_tokens

__all__ = ["STOPWORDS", "content_terms", "is_stopword"]

_WORDS: frozenset[str] = frozenset(
    {
        # Artikel und Pronomen
        "der",
        "die",
        "das",
        "den",
        "dem",
        "des",
        "ein",
        "eine",
        "einer",
        "eines",
        "einem",
        "einen",
        "er",
        "sie",
        "es",
        "ihr",
        "ihre",
        "ihren",
        "sein",
        "seine",
        "seinen",
        "dieser",
        "diese",
        "dieses",
        "jene",
        "welche",
        "welcher",
        "man",
        "sich",
        "uns",
        "euch",
        "mich",
        "dich",
        "wer",
        "was",
        # Konjunktionen und Partikeln
        "und",
        "oder",
        "aber",
        "doch",
        "denn",
        "sondern",
        "sowie",
        "als",
        "wie",
        "wenn",
        "dass",
        "ob",
        "damit",
        "weil",
        "während",
        "bevor",
        "nachdem",
        "auch",
        "nicht",
        "kein",
        "keine",
        "keinen",
        "keiner",
        "nur",
        "schon",
        "noch",
        "so",
        "zu",
        "sehr",
        "mehr",
        "bereits",
        "etwa",
        # Präpositionen
        "in",
        "im",
        "an",
        "am",
        "auf",
        "aus",
        "bei",
        "beim",
        "mit",
        "nach",
        "von",
        "vom",
        "vor",
        "für",
        "über",
        "unter",
        "durch",
        "gegen",
        "ohne",
        "um",
        "bis",
        "seit",
        "zwischen",
        "innerhalb",
        "außerhalb",
        "gemäß",
        "laut",
        # Hilfs- und Modalverben
        "ist",
        "sind",
        "war",
        "waren",
        "wird",
        "werden",
        "wurde",
        "wurden",
        "hat",
        "haben",
        "hatte",
        "hatten",
        "kann",
        "können",
        "muss",
        "müssen",
        "soll",
        "sollen",
        "darf",
        "dürfen",
        "will",
        "wollen",
        "mag",
        "mögen",
        "würde",
        "würden",
        "könnte",
        "müsste",
        "sollte",
        "sei",
        "seien",
        # Sonstiges
        "ja",
        "nein",
        "hier",
        "dort",
        "dann",
        "also",
        "ebenfalls",
    }
)

# Die Wortliste steht in normaler Schreibweise da, verglichen wird aber in der
# gefalteten Form. Die Such-Token sind bereits gefaltet, und ohne diesen Schritt
# würde „gemäß“ zu „gemaess“ und nie gefunden.
STOPWORDS: frozenset[str] = frozenset(fold(word) for word in _WORDS)


def is_stopword(word: str) -> bool:
    """Prüft, ob ein Wort ein Stoppwort ist."""
    return fold(word) in STOPWORDS


def content_terms(text: str, *, expand_compounds: bool = True) -> list[str]:
    """Inhaltstragende Wörter eines Textes, gefaltet und ohne Stoppwörter."""
    return [
        token
        for token in search_tokens(text, expand_compounds=expand_compounds)
        if token not in STOPWORDS
    ]
