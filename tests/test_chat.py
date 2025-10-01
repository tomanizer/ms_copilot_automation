from src.automation.chat import _filter_candidates, _normalise_response, _score


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
        "Copilot said  Donald Duck is great&#33;\n"
        "voice[&#95;{{{CITATION{{{&#95;1{](https://example.com).\n\n"
        "Line with trailing spaces   \n"
        "--- ## Heading without newline\n"
        "Content\n"
        "Summary: item overview - First bullet - Second bullet - 1. Ordered\n"
        "Edit in a page"
    )

    normalised = _normalise_response(raw)

    assert "&#" not in normalised
    assert "CITATION" not in normalised
    assert normalised.splitlines()[0].startswith("Donald Duck is great")
    assert normalised.endswith("- 1. Ordered")
    assert "---" in normalised
    assert "## Heading without newline" in normalised
    assert "\n- First bullet" in normalised
    assert "\n- Second bullet" in normalised
