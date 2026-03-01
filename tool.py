from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, TypedDict
import re


class ToolResult(TypedDict, total=False):
    """
    Structured result returned by all tools.

    Keys
    ----
    ok:
        Whether the call succeeded.
    data:
        Tool-specific payload when the call succeeds.
    error_type:
        Short string describing the error class (e.g. ``ValueError``).
    error_message:
        Human-readable explanation of what went wrong.
    """

    ok: bool
    data: Dict[str, Any]
    error_type: str
    error_message: str


class Tool:
    """
    Lightweight wrapper for an AI agent tool.

    This class is intentionally simple so that it can be easily adapted to
    different agent frameworks that expect a callable with a name,
    description, and parameter schema. The wrapped function is responsible
    for implementing the actual business logic; the wrapper adds a
    consistent execution interface and basic error handling.
    """

    def __init__(self, name: str, description: str, fn: Callable[..., ToolResult]) -> None:
        """
        Create a new tool wrapper.

        Parameters
        ----------
        name:
            Short identifier used by the agent to reference this tool.
        description:
            Human-readable explanation of what the tool does and when it
            should be used.
        fn:
            The underlying callable that performs the work. It must accept
            only keyword arguments and return a ``ToolResult``.
        """
        self.name = name
        self.description = description
        self.fn = fn

    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the underlying tool function with structured error handling.

        All exceptions are caught and converted into a structured
        ``ToolResult`` so that agents do not need to implement their own
        try/except blocks when calling tools.

        Returns
        -------
        ToolResult
            A dictionary containing either a successful payload
            (``ok=True`` and ``data``) or an error description
            (``ok=False`` and ``error_type``/``error_message``).
        """
        try:
            return self.fn(**kwargs)
        except Exception as exc:  # pragma: no cover - defensive fallback
            return ToolResult(
                ok=False,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )


def _tokenize(text: str) -> List[str]:
    """
    Split text into lowercase word tokens using a simple regex.

    This avoids external NLP dependencies and keeps the tool lightweight.
    """
    return re.findall(r"[A-Za-z']+", text.lower())


_STOPWORDS = {
    # Common English stopwords (not exhaustive)
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "so",
    "because",
    "as",
    "of",
    "in",
    "on",
    "for",
    "with",
    "at",
    "by",
    "to",
    "from",
    "about",
    "into",
    "over",
    "after",
    "before",
    "between",
    "through",
    "during",
    "above",
    "below",
    "up",
    "down",
    "out",
    "off",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "than",
    "too",
    "very",
}

_POSITIVE_WORDS = {
    "growth",
    "profit",
    "profits",
    "profitable",
    "positive",
    "strong",
    "gain",
    "gains",
    "improved",
    "improvement",
    "record",
    "beat",
    "beats",
    "upgrade",
    "upgraded",
    "optimistic",
    "opportunity",
    "opportunities",
}

_NEGATIVE_WORDS = {
    "loss",
    "losses",
    "negative",
    "weak",
    "decline",
    "declined",
    "declining",
    "drop",
    "dropped",
    "miss",
    "missed",
    "downgrade",
    "downgraded",
    "risk",
    "risks",
    "uncertain",
    "uncertainty",
    "crisis",
    "slowdown",
}


def analyze_business_text(text: Any, top_n_keywords: int = 5) -> ToolResult:
    """
    Analyze short business/news text and return basic statistics and signals.

    This tool is intentionally simple and dependency-free. It is aimed at
    lightweight agent workflows that need a quick, explainable overview of a
    piece of business news, earnings commentary, or internal update.

    Parameters
    ----------
    text:
        The input text to analyze. Must be a non-empty string.
    top_n_keywords:
        Number of prominent keywords (excluding simple stopwords) to return.
        Must be a positive integer. Defaults to 5.

    Returns
    -------
    ToolResult
        On success (``ok=True``), the ``data`` field contains:

        - ``char_count``: total number of characters in the input
        - ``word_count``: number of word tokens
        - ``unique_word_count``: number of unique words
        - ``sentence_count``: rough count of sentences
        - ``avg_sentence_length``: average words per sentence
        - ``top_keywords``: list of ``{"keyword", "count"}`` dicts
        - ``sentiment``: simple heuristic sentiment summary with
          ``score`` and ``label`` (``"positive"``, ``"negative"`` or
          ``"neutral"``)

        On failure (``ok=False``), the result contains ``error_type`` and
        ``error_message`` describing what went wrong (for example invalid
        parameter types), so an agent can surface a clear explanation to the
        end user.
    """
    # Input validation
    if not isinstance(text, str):
        raise TypeError("Parameter 'text' must be a string.")

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Parameter 'text' must be a non-empty string.")

    if not isinstance(top_n_keywords, int):
        raise TypeError("Parameter 'top_n_keywords' must be an integer.")
    if top_n_keywords <= 0:
        raise ValueError("Parameter 'top_n_keywords' must be positive.")

    tokens = _tokenize(cleaned)
    word_count = len(tokens)
    unique_word_count = len(set(tokens))

    # Very rough sentence segmentation based on punctuation.
    sentence_like = [s for s in re.split(r"[.!?]+", cleaned) if s.strip()]
    sentence_count = len(sentence_like) or 1
    avg_sentence_length = word_count / sentence_count if sentence_count else 0.0

    # Keyword extraction (frequency-based, excluding simple stopwords).
    keywords = [t for t in tokens if t not in _STOPWORDS]
    freq = Counter(keywords)
    top_keywords = [
        {"keyword": word, "count": count}
        for word, count in freq.most_common(top_n_keywords)
    ]

    # Simple domain-focused sentiment: look only at a small lexicon of
    # business-relevant positive/negative words.
    positive_hits = [t for t in tokens if t in _POSITIVE_WORDS]
    negative_hits = [t for t in tokens if t in _NEGATIVE_WORDS]
    score = len(positive_hits) - len(negative_hits)
    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    else:
        label = "neutral"

    sentiment = {
        "score": score,
        "label": label,
        "positive_words": positive_hits,
        "negative_words": negative_hits,
    }

    return ToolResult(
        ok=True,
        data={
            "char_count": len(cleaned),
            "word_count": word_count,
            "unique_word_count": unique_word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_sentence_length,
            "top_keywords": top_keywords,
            "sentiment": sentiment,
        },
    )


business_text_tool = Tool(
    name="business_text_analyzer",
    description=(
        "Analyze short business or news text and return word statistics, "
        "simple keyword extraction, and a lightweight sentiment signal."
    ),
    fn=analyze_business_text,
)

