from src.automation.chat import _filter_candidates, _score, _normalise_response


def test_filter_candidates_drops_noise_and_duplicates():
    candidates = [
        "You said: Hello",
        "Working on it…",
        "Copilot may make mistakes",
        "Final answer line",
        "Final answer line",  # duplicate
        "Extra detail",
    ]

    filtered = _filter_candidates(candidates, exclude_text="Hello")

    assert filtered == ["Final answer line", "Extra detail"]


def test_score_prefers_structured_response():
    plain = "Short reply"
    rich = "# Summary\n- Point one\n- Point two"

    assert _score(rich) > _score(plain)


def test_normalise_response_decodes_entities_and_drops_citations():
    raw = (
        "Donald Duck is great&#33;\n"
        "voice[&#95;{{{CITATION{{{&#95;1{](https://example.com).\n\n"
        "Line with trailing spaces   \n"
    )

    normalised = _normalise_response(raw)

    assert "&#" not in normalised
    assert "CITATION" not in normalised
    assert normalised.endswith("Line with trailing spaces")
