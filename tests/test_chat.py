from src.automation.chat import _filter_candidates, _score


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
