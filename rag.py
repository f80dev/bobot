"""Minimal TF-IDF retrieval over the knowledge/ corpus.

Pure stdlib (re, math, os, pathlib, collections). No external deps.
Section-aware: each `## ` heading in a .md file becomes one indexed passage.

Usage:
    kb = KnowledgeBase("knowledge")
    hits = kb.search("Qu'est-ce que l'EMDR ?", top_k=3)
    # -> [{"source": "emdr.md", "title": "Qu'est-ce que l'EMDR ?",
    #      "snippet": "...", "score": 0.42}, ...]
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from pathlib import Path


_STOPWORDS_FR = frozenset(
    """
    le la les de du des un une et est que qui à a dans pour par sur ce il elle
    ils elles on je tu vous nous se sa son ses mon ma tes ta ton notre votre
    leur leurs au aux y en ne pas plus très trop peu car mais ou où donc quand
    comme si fait faire être avoir été suis es sommes êtes sont était étaient
    c'est c'était ça cela ce que quoi dont pourquoi comment qui que quel quelle
    quoi sans avec entre vers chez après avant depuis pendant lors tandis que
    parce qu' parce que alors aussi donc puis encore très peut peuvent peut
    peuvent aussi beaucoup moins plus tout toute tous toutes autre autres même
    mêmes non oui ah oh eh bien vraiment presque déjà jamais toujours souvent
    parfois rien personne aucun aucune lequel laquelle lesquels lesquelles
    """.split()
)

# Section delimiter: lines starting with `## ` (level-2 headings).
_SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)
# Token: alphanum (incl. French diacritics, apostrophes handled by delim).
_TOKEN_RE = re.compile(r"[a-zàâçëéèêïîôùûüœæ]+", re.IGNORECASE)
# Limit passage length to keep context window sane (~1200 chars ≈ 250 tokens).
_MAX_PASSAGE_CHARS = 1200


def _tokenize(text: str) -> list[str]:
    return [
        tok
        for tok in (t.lower() for t in _TOKEN_RE.findall(text))
        if tok and tok not in _STOPWORDS_FR and len(tok) > 1
    ]


def _split_passages(text: str, source: str) -> list[dict]:
    """Split a markdown file into passages by `## ` headings.

    First heading anchors the first section (everything before the first `## `
    is discarded if it is only a title). Always returns at least one passage.
    """
    matches = list(_SECTION_RE.finditer(text))
    passages: list[dict] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = m.group(1).strip()
        body = text[start:end].strip()
        body = _strip_md(body)
        if not body:
            continue
        snippet = body[: _MAX_PASSAGE_CHARS]
        passages.append(
            {"source": source, "title": title, "snippet": snippet, "text": f"## {title}\n{snippet}"}
        )
    if not passages:
        body = _strip_md(text).strip()
        if body:
            passages.append(
                {
                    "source": source,
                    "title": Path(source).stem,
                    "snippet": body[: _MAX_PASSAGE_CHARS],
                    "text": body[: _MAX_PASSAGE_CHARS],
                }
            )
    return passages


def _strip_md(body: str) -> str:
    """Light markdown cleanup — keep prose, drop syntax noise."""
    body = re.sub(r"^\s*[-*+]\s+", "", body, flags=re.MULTILINE)
    body = re.sub(r"\*\*(.+?)\*\*", r"\1", body)
    body = re.sub(r"\*(.+?)\*", r"\1", body)
    body = re.sub(r"`([^`]+?)`", r"\1", body)
    body = re.sub(r"\[(.+?)\]\([^)]+\)", r"\1", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


class KnowledgeBase:
    """Loads .md files from a directory and serves TF-IDF top-k search."""

    def __init__(self, directory: str | os.PathLike):
        self.directory = Path(directory)
        self.passages: list[dict] = []
        self._vocab: dict[str, float] = {}  # token -> idf
        self._doc_vectors: list[dict[str, float]] = []
        self._doc_norms: list[float] = []
        self._load()
        self._build_index()

    def _load(self) -> None:
        if not self.directory.exists():
            return
        for md in sorted(self.directory.glob("*.md")):
            if md.name.lower() == "readme.md":
                continue
            text = md.read_text(encoding="utf-8")
            self.passages.extend(_split_passages(text, md.name))

    def _build_index(self) -> None:
        # IDF over each passage (treating each passage as a "doc")
        df: Counter[str] = Counter()
        tokenized: list[list[str]] = []
        for p in self.passages:
            toks = _tokenize(p["text"])
            tokenized.append(toks)
            df.update(set(toks))
        n = max(1, len(self.passages))
        self._vocab = {
            tok: math.log((1 + n) / (1 + df_t)) + 1.0 for tok, df_t in df.items()
        }
        # Per-passage TF-IDF vectors + L2 norms
        self._doc_vectors: list[dict[str, float]] = []
        self._doc_norms: list[float] = []
        for toks in tokenized:
            tf = Counter(toks)
            vec: dict[str, float] = {
                tok: count * self._vocab.get(tok, 0.0) for tok, count in tf.items()
            }
            self._doc_vectors.append(vec)
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1e-9
            self._doc_norms.append(norm)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        toks = _tokenize(query)
        if not toks:
            return []
        q_tf = Counter(toks)
        q_vec = {tok: count * self._vocab.get(tok, 0.0) for tok, count in q_tf.items()}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1e-9

        scored: list[tuple[int, float]] = []
        for i, d_vec in enumerate(self._doc_vectors):
            if not d_vec:
                continue
            # dot product over shared keys
            inter = set(q_vec.keys()) & set(d_vec.keys())
            if not inter:
                continue
            dot = sum(q_vec[t] * d_vec[t] for t in inter)
            score = dot / (q_norm * self._doc_norms[i])
            if score < 0.02:  # ignore noise
                continue
            scored.append((i, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {
                "source": self.passages[i]["source"],
                "title": self.passages[i]["title"],
                "snippet": self.passages[i]["snippet"][: 280],
                "score": round(float(s), 4),
            }
            for i, s in scored[:top_k]
        ]