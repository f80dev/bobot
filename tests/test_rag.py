"""Tests for server/rag.py — TF-IDF RAG over the knowledge/ corpus."""

from rag import KnowledgeBase


def test_load_corpus():
    kb = KnowledgeBase("knowledge")
    # 6 thematic .md files (README.md excluded). Each yields ≥ 1 passage.
    assert len(kb.passages) >= 6, f"expected ≥6 passages, got {len(kb.passages)}"


def test_search_emdr():
    kb = KnowledgeBase("knowledge")
    results = kb.search("C'est quoi l'EMDR exactement ?", top_k=3)
    assert results, "expected at least one result for EMDR query"
    # top hit should mention EMDR in title or snippet
    top = results[0]
    haystack = (top["title"] + " " + top["snippet"]).lower()
    assert "emdr" in haystack, f"top result does not match EMDR: {top}"
    assert top["score"] > 0


def test_search_attachement():
    kb = KnowledgeBase("knowledge")
    results = kb.search("théorie de l'attachement Bowlby", top_k=3)
    assert results
    top = results[0]
    haystack = (top["source"] + " " + top["title"]).lower()
    assert "attach" in haystack, f"top source/title not related: {top}"


def test_search_polyvagale():
    kb = KnowledgeBase("knowledge")
    results = kb.search("système nerveux autonome Porges", top_k=3)
    assert results
    assert any("polyvagale" in r["source"] or "polyvagale" in r["title"].lower() for r in results)


def test_search_handles_gibberish():
    kb = KnowledgeBase("knowledge")
    results = kb.search("xyzqwerty abcdefg", top_k=3)
    # No match expected, but should not crash
    assert isinstance(results, list)


def test_search_handles_french_stopwords():
    kb = KnowledgeBase("knowledge")
    # Pure stopwords -> no tokens after _tokenize -> empty results
    results = kb.search("le la de du", top_k=3)
    assert results == []


def test_search_top_k_limit():
    kb = KnowledgeBase("knowledge")
    results = kb.search("thérapie psychique trauma blessure", top_k=2)
    assert len(results) <= 2


def test_search_returns_consistent_shape():
    kb = KnowledgeBase("knowledge")
    results = kb.search("EMDR", top_k=3)
    for r in results:
        assert set(r.keys()) == {"source", "title", "snippet", "score"}
        assert isinstance(r["score"], float)
        assert 0.0 <= r["score"] <= 1.0