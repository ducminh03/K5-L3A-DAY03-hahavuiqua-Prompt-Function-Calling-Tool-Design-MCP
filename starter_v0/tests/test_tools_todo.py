"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    result = TOOL_FUNCTIONS['clarify'](question="Which option?", response_type="choice", options=["A","B"])

    assert result["options"] == ["A", "B"]
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    result = TOOL_FUNCTIONS['format'](items=[{"section" : "A"}, {"section" : "B"}, {"section" : "A"}], template="sections", headline="Test Headline")
    assert result["markdown"].count("## A") and result["markdown"].count("## B")


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    result = TOOL_FUNCTIONS['format'](template="thread", items=[{"summary": "x"} for _ in range(2)])
    assert result["markdown"].startswith("1/") or result["markdown"].startswith("2/")  


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    result = TOOL_FUNCTIONS['format'](items=None)
    assert result["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    pytest.skip(TODO)


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    pytest.skip(TODO)


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    pytest.skip(TODO)


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    pytest.skip(TODO)


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    pytest.skip(TODO)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    pytest.skip(TODO)


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = TOOL_FUNCTIONS['policy'](query="")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    result = TOOL_FUNCTIONS['policy'](query="anything", policy_area="data_privacy")
    assert all(r["policy_area"] == "data_privacy" for r in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    result = TOOL_FUNCTIONS['policy'](query="injection probe", policy_area="source_citation", top_k=10)
    probe = next(item for item in result["results"] if item["section"] == "Injection probe")
    assert any(line.startswith("Assistant:") for line in probe["untrusted_text"])
    assert not any("Assistant:" in fact for fact in probe["facts"])


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

# ---------------- wiki (team tool) ----------------

wiki_tool = TOOL_FUNCTIONS["wiki"]

WIKI_PAYLOAD = {"query": {"pages": [
    {"pageid": 2, "index": 2, "title": "GPT-4", "fullurl": "https://vi.wikipedia.org/wiki/GPT-4",
     "extract": "GPT-4 là mô hình thứ tư. "},
    {"pageid": 1, "index": 1, "title": "Transformer (học máy)",
     "fullurl": "https://vi.wikipedia.org/wiki/Transformer_(h%E1%BB%8Dc_m%C3%A1y)",
     "extract": "Transformer là một kiến trúc học sâu."},
]}}


def test_wiki_sends_search_request_and_maps_best_match(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_PAYLOAD))

    result = wiki_tool(query="Transformer", lang="vi", max_results=2)

    assert len(calls) == 1
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://vi.wikipedia.org/w/api.php"
    assert calls[0]["params"]["gsrsearch"] == "Transformer"
    assert calls[0]["params"]["gsrlimit"] == 2
    assert calls[0]["params"]["generator"] == "search"
    assert "User-Agent" in calls[0]["headers"]
    # pages are re-ordered by search rank ("index"), not API order
    assert [item["title"] for item in result["items"]] == ["Transformer (học máy)", "GPT-4"]
    assert result["items"][0] == {
        "title": "Transformer (học máy)",
        "url": "https://vi.wikipedia.org/wiki/Transformer_(h%E1%BB%8Dc_m%C3%A1y)",
        "source": "vi.wikipedia.org",
        "summary": "Transformer là một kiến trúc học sâu.",
    }
    assert result["items"][1]["summary"] == "GPT-4 là mô hình thứ tư."  # stripped


def test_wiki_empty_query_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_PAYLOAD))

    for bad in ("", "   ", None):
        result = wiki_tool(query=bad)
        assert result["tool"] == "wiki"
        assert result["error"] == "ValueError"
    assert calls == []


def test_wiki_normalizes_bad_lang_and_max_results_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_PAYLOAD))

    wiki_tool(query="OpenAI", lang="fr", max_results="3")   # out-of-enum lang, numeric string
    wiki_tool(query="OpenAI", lang="EN", max_results=0)     # upper-case lang, zero
    wiki_tool(query="OpenAI", lang=None, max_results="abc")  # None lang, garbage
    wiki_tool(query="OpenAI", max_results=99)               # above cap

    assert calls[0]["url"] == "https://en.wikipedia.org/w/api.php"
    assert calls[0]["params"]["gsrlimit"] == 3
    assert calls[1]["url"] == "https://en.wikipedia.org/w/api.php"
    assert calls[1]["params"]["gsrlimit"] == 1
    assert calls[2]["url"] == "https://en.wikipedia.org/w/api.php"
    assert calls[2]["params"]["gsrlimit"] == 1
    assert calls[3]["url"] == "https://vi.wikipedia.org/w/api.php"
    assert calls[3]["params"]["gsrlimit"] == 5


def test_wiki_no_match_returns_empty_items(fake_http) -> None:
    fake_http(FakeResponse({"batchcomplete": True}))  # API omits "query" when nothing matches

    result = wiki_tool(query="asdkjhqwe")

    assert result["items"] == []
    assert "error" not in result


def test_wiki_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))
    result = wiki_tool(query="OpenAI")
    assert result == {"tool": "wiki", "error": "HTTPError", "message": "HTTP 429"}


def test_wiki_timeout_returns_error_dict(fake_http) -> None:
    import requests
    fake_http(requests.Timeout("read timed out"))
    result = wiki_tool(query="OpenAI")
    assert result["error"] == "Timeout"
