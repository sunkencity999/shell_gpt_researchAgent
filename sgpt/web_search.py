import requests
from typing import List, Dict

def search_web_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """DuckDuckGo search using the official Instant Answer API (no API key required)."""
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        # Parse 'RelatedTopics' from the API format
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
                results.append({
                    "title": topic.get("Text"),
                    "href": topic.get("FirstURL"),
                    "snippet": topic.get("Text")
                })
                if len(results) >= max_results:
                    break
            # Sometimes there are nested topics
            if isinstance(topic, dict) and "Topics" in topic:
                for subtopic in topic["Topics"]:
                    if "Text" in subtopic and "FirstURL" in subtopic:
                        results.append({
                            "title": subtopic.get("Text"),
                            "href": subtopic.get("FirstURL"),
                            "snippet": subtopic.get("Text")
                        })
                        if len(results) >= max_results:
                            break
        return results
    except Exception as e:
        return [{"title": "[Error]", "href": "", "snippet": str(e)}]

def search_web_brave(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Brave Search public API fallback (no API key required, limited results)."""
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json"}
    params = {"q": query, "count": max_results}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for r in data.get("web", {}).get("results", [])[:max_results]:
            results.append({
                "title": r.get("title"),
                "href": r.get("url"),
                "snippet": r.get("description", r.get("title"))
            })
        return results
    except Exception as e:
        return [{"title": "[Error]", "href": "", "snippet": str(e)}]

import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyBOXi2PiDl9P3TMsjLXMOqtjWAJg0j8U-c")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")  # User must set this

def search_web_google_cse(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Google Custom Search API (requires API key and CSE ID). Attempts pagination to get up to max_results."""
    if not GOOGLE_CSE_ID:
        print("[WARNING] Google CSE ID not set in config or env.")
        return [{"title": "[Error]", "href": "", "snippet": "Google CSE ID not set in config or env."}]
    url = "https://www.googleapis.com/customsearch/v1"
    results = []
    start = 1
    while len(results) < max_results:
        num = min(10, max_results - len(results))  # CSE max per request is 10
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "num": num,
            "start": start
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            for item in items:
                results.append({
                    "title": item.get("title"),
                    "href": item.get("link"),
                    "snippet": item.get("snippet")
                })
            if not items or len(results) >= max_results:
                break
            start += len(items)
        except Exception as e:
            print(f"[WARNING] Google CSE error: {e}")
            break
    if not results:
        print("[WARNING] Google CSE returned no results.")
        return [{"title": "[No results]", "href": "", "snippet": "No relevant results found."}]
    if len(results) < max_results:
        print(f"[WARNING] Google CSE returned only {len(results)} results (requested {max_results}).")
    return results[:max_results]

def search_web_with_fallback(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Try Google CSE (with pagination), then DuckDuckGo, then Brave Search if no results or not enough results."""
    results = search_web_google_cse(query, max_results)
    if results and results[0]["title"] not in ("[Error]", "[No results]") and len(results) >= max_results:
        return results
    print(f"[WARNING] Google CSE could not return {max_results} results. Falling back to DuckDuckGo.")
    results = search_web_duckduckgo(query, max_results)
    if results and results[0]["title"] not in ("[Error]", "[No results]") and len(results) >= max_results:
        return results
    print(f"[WARNING] DuckDuckGo could not return {max_results} results. Falling back to Brave Search.")
    results = search_web_brave(query, max_results)
    if results and results[0]["title"] not in ("[Error]", "[No results]"):
        return results
    print(f"[WARNING] No provider could return {max_results} results. Returning whatever was found.")
    return results


from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def fetch_url_text(url: str, snippet: str = "") -> str:
    """
    Extract article text using newspaper3k, fallback to Playwright, then BeautifulSoup, then snippet.
    If extracted text is <500 chars, try to follow the first likely article/content link and extract from there.
    Print a preview and length of extracted text for debugging.
    """
    def debug_preview(text, stage, target_url):
        print(f"[{stage} extraction for {target_url}: length={len(text)} | preview='{text[:300].replace(chr(10),' ')}']")

    # 1. Try newspaper3k
    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        text = article.text
        if text:
            debug_preview(text, "newspaper3k", url)
            if len(text) >= 500:
                return text[:8000]
    except Exception as e:
        print(f"[newspaper3k failed for {url}: {e}]")

    # 2. Try Playwright
    html = None
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            html = page.content()
            browser.close()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for s in soup(["script", "style"]):
            s.extract()
        text = soup.get_text(separator=" ", strip=True)
        if text:
            debug_preview(text, "Playwright", url)
            if len(text) >= 500:
                return text[:8000]
    except Exception as e:
        print(f"[Playwright fetch failed for {url}: {e}]")

    # 3. Try requests+BeautifulSoup
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for s in soup(["script", "style"]):
            s.extract()
        text = soup.get_text(separator=" ", strip=True)
        if text:
            debug_preview(text, "Requests+BS4", url)
            if len(text) >= 500:
                return text[:8000]
    except Exception as e:
        print(f"[Requests+BS4 fetch failed for {url}: {e}")

    # 4. If text is short, try to follow first likely article/content link
    candidate_html = html
    if not candidate_html:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            candidate_html = resp.text
        except Exception:
            candidate_html = None
    if candidate_html:
        soup = BeautifulSoup(candidate_html, "html.parser")
        domain = urlparse(url).netloc
        for a in soup.find_all("a", href=True):
            href = a["href"]
            abs_url = urljoin(url, href)
            # Only follow links to same domain, and likely articles
            if urlparse(abs_url).netloc == domain and any(x in href.lower() for x in ["article", "news", "story", "202", "item", "detail"]):
                print(f"[Following likely article link: {abs_url} from {url}]")
                # Try to extract from this linked page (newspaper3k, Playwright, BS4, snippet fallback)
                return fetch_url_text(abs_url, snippet)

    # 5. Final fallback: use the snippet if provided
    if snippet:
        print(f"[Using search snippet fallback for {url}]")
        return snippet
    return f"[Error fetching {url}: all extraction methods failed.]"
