"""Deutsche Stilprüfung – als Hinweis, nicht als Ersatz für Korrektorat.

Was hier passiert, ist eine maschinelle Analyse deutscher Dokumente. Sie findet
lange Sätze, gehäufte Nominalisierungen, Anglizismen, Füllwörter und
Wortwiederholungen. Sie ersetzt keine professionelle Prüfung und soll es auch
nicht: Die Regeln sind Heuristiken, die auf deutsche Texte zugeschnitten sind,
und jeder Hinweis lässt sich im Einzelfall ablehnen.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.text.segment import split_sentences, tokenize_words

__all__ = ["StyleFinding", "StyleReport", "check_style"]

_LONG_SENTENCE_WORDS = 25
_LONG_WORD_CHARS = 26
_NOMINALIZATION_THRESHOLD = 3

# Passiv in zwei Fällen, weil die Grammatik hilft:
# Nach „wurde/wurden“ kann kein Infinitiv stehen, dort genügt also ein Wort auf
# -t oder -en. Nach „wird/werden“ kann ein Infinitiv stehen („wird prüfen“ ist
# Zukunft), dort muss das Mittelwort erkennbar sein.
_PASSIVE_PAST = re.compile(
    r"\b(?:wurde|wurden|worden)\b(?:\s+\w+){0,3}\s+\w{4,}(?:t|en)\b",
    re.IGNORECASE,
)

_PASSIVE_PRESENT = re.compile(
    r"\b(?:wird|werden)\b(?:\s+\w+){0,3}\s+"
    r"(?:(?:ge|be|ver|er|ent|zer|miss)\w{2,}(?:t|en)|\w{4,}iert)\b",
    re.IGNORECASE,
)

_NOMINALIZATION = re.compile(
    r"\b\w{4,}(?:ung|ungen|heit|heiten|keit|keiten|ion|ionen|ität|itaten|nahme|gabe|weise)\b",
    re.IGNORECASE,
)

_ANGLICISMS = re.compile(
    r"\b(?:Meeting|Report|Update|Feature|Release|Workflow|Deadline|Ticket|Sprint|"
    r"Backlog|Stakeholder|Feedback|Scope|Target|Onboarding|Rollout|Task|Call|"
    r"Review|Milestone|Roadmap|Deployment|Issue|Commit|Board|Meetingraum|"
    r"Kickoff|Setup|Tooling|Bugfix)\w*\b",
    re.IGNORECASE,
)

_FILLERS = re.compile(
    r"\b(?:eigentlich|sozusagen|gewissermaßen|irgendwie|quasi|halt|eben mal|"
    r"im Grunde genommen|mehr oder weniger|so gesehen)\b",
    re.IGNORECASE,
)

_REPEATED_WORD = re.compile(r"\b(\w{3,})\s+\1\b", re.IGNORECASE)

_LONG_WORD = re.compile(r"\b[\wÄÖÜäöüß-]{" + str(_LONG_WORD_CHARS) + r",}\b")


class StyleFinding(BaseModel):
    """Ein stilistischer Hinweis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule: str
    severity: str
    message: str
    text: str
    start: int
    end: int


class StyleReport(BaseModel):
    """Ergebnis einer Stilprüfung."""

    model_config = ConfigDict(extra="forbid")

    findings: list[StyleFinding] = Field(default_factory=list)
    sentences: int = 0
    words: int = 0
    average_sentence_words: float = 0.0
    longest_sentence_words: int = 0

    @property
    def is_clean(self) -> bool:
        """Wurde nichts gefunden?"""
        return not self.findings

    def by_rule(self) -> dict[str, int]:
        """Anzahl der Hinweise je Regel."""
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.rule] = counts.get(finding.rule, 0) + 1
        return counts


def _finding(
    rule: str, severity: str, message: str, text: str, start: int, end: int
) -> StyleFinding:
    return StyleFinding(
        rule=rule,
        severity=severity,
        message=message,
        text=text,
        start=start,
        end=end,
    )


def check_style(text: str) -> StyleReport:
    """Prüft deutschen Text auf stilistische Auffälligkeiten."""
    findings: list[StyleFinding] = []
    sentences = split_sentences(text)
    all_words = tokenize_words(text)

    lengths: list[int] = []
    for sentence in sentences:
        words = sentence.text.split()
        lengths.append(len(words))
        if len(words) > _LONG_SENTENCE_WORDS:
            findings.append(
                _finding(
                    "langer_satz",
                    "warning",
                    f"Der Satz hat {len(words)} Wörter. Kürzere Sätze lesen sich besser.",
                    sentence.text,
                    sentence.start,
                    sentence.end,
                )
            )

        nominalizations = _NOMINALIZATION.findall(sentence.text)
        if len(nominalizations) >= _NOMINALIZATION_THRESHOLD:
            findings.append(
                _finding(
                    "nominalstil",
                    "hint",
                    f"{len(nominalizations)} Substantivierungen in einem Satz. "
                    "Ein Verb statt eines Substantivs hilft oft.",
                    sentence.text,
                    sentence.start,
                    sentence.end,
                )
            )

    for pattern, rule, severity, message in (
        (
            _PASSIVE_PAST,
            "passiv",
            "hint",
            "Passivkonstruktion. Wer handelt, bleibt offen.",
        ),
        (
            _PASSIVE_PRESENT,
            "passiv",
            "hint",
            "Passivkonstruktion. Wer handelt, bleibt offen.",
        ),
        (
            _ANGLICISMS,
            "anglizismus",
            "hint",
            "Englisches Wort in deutschem Text. Gewollt oder versehentlich?",
        ),
        (
            _FILLERS,
            "fuellwort",
            "hint",
            "Füllwort ohne Informationsgehalt.",
        ),
        (
            _REPEATED_WORD,
            "wortwiederholung",
            "warning",
            "Dasselbe Wort steht zweimal hintereinander.",
        ),
        (
            _LONG_WORD,
            "langes_wort",
            "hint",
            "Sehr langes Wort. Ein Kompositum lässt sich oft auflösen.",
        ),
    ):
        for match in pattern.finditer(text):
            findings.append(
                _finding(rule, severity, message, match.group(), match.start(), match.end())
            )

    findings.sort(key=lambda item: (item.start, item.end))

    return StyleReport(
        findings=findings,
        sentences=len(sentences),
        words=len(all_words),
        average_sentence_words=(sum(lengths) / len(lengths)) if lengths else 0.0,
        longest_sentence_words=max(lengths) if lengths else 0,
    )
