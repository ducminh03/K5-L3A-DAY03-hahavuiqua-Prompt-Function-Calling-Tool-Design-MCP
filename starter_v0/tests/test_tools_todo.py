"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import time
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
    assert result["markdown"].count("## A") == 1
    assert result["markdown"].count("## B") == 1


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    result = TOOL_FUNCTIONS["format"](template="thread", items=[{"summary": "x"} for _ in range(2)])
    assert result["markdown"].startswith("1/")
    assert "\n\n2/" in result["markdown"]


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    result1 = TOOL_FUNCTIONS["format"](items=None)
    assert result1["item_count"] == 0
    result2 = TOOL_FUNCTIONS["format"](items=[])
    assert result2["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_bot_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Bản tin AI", confirmed=True)
    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "fake_bot_token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "123456789"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Bản tin AI", confirmed=True)
    assert len(calls) == 0
    assert result["error"] == "RuntimeError"
    assert "Missing TELEGRAM_BOT_TOKEN" in result["message"]


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    monkeypatch.setenv("TAVILY_API_KEY", "fake_tavily_key")
    calls = fake_http(FakeResponse({"results": []}))
    result = TOOL_FUNCTIONS["lookup"](query="AI news", timeframe=None)
    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]
    assert result["query"] == "AI news"


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake_firecrawl_key")
    calls = fake_http(
        FakeResponse({
            "data": {
                "markdown": "Nội dung bài viết",
                "metadata": {"title": "Tiêu đề bài viết", "sourceURL": "https://example.com/article"},
            }
        })
    )
    result = TOOL_FUNCTIONS["fetch"](url="https://example.com/article")
    assert len(calls) == 1
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["title"] == "Tiêu đề bài viết"
    assert item["url"] == "https://example.com/article"
    assert item["source"] == "example.com"
    assert item["summary"] == "Nội dung bài viết"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fake_firecrawl_key")
    long_markdown = "a" * 5000
    fake_http(
        FakeResponse({
            "data": {
                "markdown": long_markdown,
                "metadata": {"title": "Bài viết dài", "sourceURL": "https://example.com/long"},
            }
        })
    )
    result = TOOL_FUNCTIONS["fetch"](url="https://example.com/long")
    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    monkeypatch.setenv("RAPIDAPI_KEY", "fake_rapidapi_key")
    raw_tweets = [{"text": "no id"}] + [
        {"tweet_id": f"id_{i}", "screen_name": "sama", "text": f"Tweet text {i}"}
        for i in range(6)
    ]
    fake_http(FakeResponse({"timeline": raw_tweets}))
    result = TOOL_FUNCTIONS["timeline"](screenname="sama", limit=3)
    assert len(result["items"]) == 3
    for i, item in enumerate(result["items"]):
        assert item["url"] == f"https://x.com/sama/status/id_{i}"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    monkeypatch.setenv("RAPIDAPI_KEY", "fake_rapidapi_key")
    calls = fake_http(FakeResponse({"tweets": []}))
    result = TOOL_FUNCTIONS["social_search"](query="DeepSeek", search_type="Top")
    assert len(calls) == 1
    assert calls[0]["params"]["query"] == "DeepSeek"
    assert calls[0]["params"]["search_type"] == "Top"
    assert result["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = TOOL_FUNCTIONS['policy'](query="")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    result = TOOL_FUNCTIONS["policy"](query="data", policy_area="data_privacy")
    assert len(result["results"]) > 0
    assert all(r["policy_area"] == "data_privacy" for r in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    result = TOOL_FUNCTIONS["policy"](query="injection", policy_area="source_citation")
    hit = result["results"][0]
    assert any("ignore the citation policy" in line for line in hit["untrusted_text"])
    assert "ignore the citation policy" not in hit["facts"]


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

ARXIV_XML_MOCK = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <title>Sample Paper Title</title>
    <summary>Sample abstract text</summary>
    <published>2024-01-01T00:00:00Z</published>
  </entry>
</feed>"""

def test_my_new_tool_happy_path(monkeypatch, fake_http) -> None:
    monkeypatch.setattr(time, "sleep", lambda x: None)
    fake_http(FakeResponse(text=ARXIV_XML_MOCK))
    result = TOOL_FUNCTIONS["papers"](query="LLM reasoning", max_results=1)
    assert len(result["items"]) == 1
    assert result["items"][0]["title"] == "Sample Paper Title"
    assert result["items"][0]["arxiv_id"] == "2401.12345v1"


def test_my_new_tool_bad_input_from_model(monkeypatch, fake_http) -> None:
    monkeypatch.setattr(time, "sleep", lambda x: None)
    fake_http(FakeResponse(text=ARXIV_XML_MOCK))
    result = TOOL_FUNCTIONS["papers"](query="", max_results=-5)
    assert "items" in result
    assert isinstance(result["items"], list)


def test_my_new_tool_failure_returns_error_dict(monkeypatch, fake_http) -> None:
    monkeypatch.setattr(time, "sleep", lambda x: None)
    fake_http(FakeResponse(status_code=500))
    result = TOOL_FUNCTIONS["papers"](query="crash")
    assert "error" in result
    assert result["error"] == "HTTPError"
