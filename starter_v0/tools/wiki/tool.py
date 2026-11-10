from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err

SUPPORTED_LANGS = {"vi", "en"}
USER_AGENT = "ResearchAgentLab/1.0 (educational project)"


def _clamp_results(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 1
    return max(1, min(number, 5))


def wiki_summary(query: str = "", lang: str = "vi", max_results: int = 1) -> dict[str, Any]:
    """Search Wikipedia and return the intro summary of the best matching article(s)."""
    try:
        query = (query or "").strip() if isinstance(query, str) else str(query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        lang = (lang or "").strip().lower() if isinstance(lang, str) else ""
        if lang not in SUPPORTED_LANGS:
            lang = "en"
        limit = _clamp_results(max_results)

        response = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "formatversion": 2,
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": limit,
                "prop": "extracts|info",
                "exintro": 1,
                "explaintext": 1,
                "exsentences": 5,
                "inprop": "url",
                "redirects": 1,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages") or []
        pages = sorted(pages, key=lambda page: page.get("index", 0))
        items = [{
            "title": page.get("title"),
            "url": page.get("fullurl"),
            "source": domain(page.get("fullurl", "")),
            "summary": (page.get("extract") or "").strip(),
        } for page in pages[:limit]]
        return {"tool": "wiki", "query": query, "lang": lang, "items": items}
    except Exception as exc:
        return err("wiki", exc)
