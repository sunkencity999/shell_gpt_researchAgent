import requests
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

def search_web_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """DuckDuckGo search using the official Instant Answer API (no API key required)."""
    # Clean the query of markdown formatting
    clean_query = query.replace('**', '').replace('*', '').replace('""', '"').strip()
    
    url = "https://api.duckduckgo.com/"
    params = {"q": clean_query, "format": "json", "no_redirect": 1, "no_html": 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        # Parse 'RelatedTopics' from the API format
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
                first_url = topic.get("FirstURL", "")
                if first_url and first_url.startswith(("http://", "https://")):
                    results.append({
                        "title": topic.get("Text", "Untitled"),
                        "href": first_url,
                        "snippet": topic.get("Text", "")
                    })
                if len(results) >= max_results:
                    break
            # Sometimes there are nested topics
            if isinstance(topic, dict) and "Topics" in topic:
                for subtopic in topic["Topics"]:
                    if "Text" in subtopic and "FirstURL" in subtopic:
                        first_url = subtopic.get("FirstURL", "")
                        if first_url and first_url.startswith(("http://", "https://")):
                            results.append({
                                "title": subtopic.get("Text", "Untitled"),
                                "href": first_url,
                                "snippet": subtopic.get("Text", "")
                            })
                        if len(results) >= max_results:
                            break
        return results
    except Exception as e:
        print(f"[DuckDuckGo search error: {e}]")
        return []

def search_web_brave(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Brave Search public API fallback (no API key required, limited results)."""
    # Clean the query of markdown formatting
    clean_query = query.replace('**', '').replace('*', '').replace('""', '"').strip()
    
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json"}
    params = {"q": clean_query, "count": max_results}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for r in data.get("web", {}).get("results", [])[:max_results]:
            result_url = r.get("url", "")
            if result_url and result_url.startswith(("http://", "https://")):
                results.append({
                    "title": r.get("title", "Untitled"),
                    "href": result_url,
                    "snippet": r.get("description", r.get("title", ""))
                })
        return results
    except Exception as e:
        print(f"[Brave search error: {e}]")
        return []

import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyBOXi2PiDl9P3TMsjLXMOqtjWAJg0j8U-c")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")  # User must set this

def search_web_google_cse(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Google Custom Search API (requires API key and CSE ID). Attempts pagination to get up to max_results."""
    if not GOOGLE_CSE_ID:
        print("[WARNING] Google CSE ID not set in config or env.")
        return []
    
    # Clean the query of markdown formatting and excessive quotes
    clean_query = query.replace('**', '').replace('*', '')
    # Remove nested quotes that can confuse search APIs
    clean_query = clean_query.replace('""', '"').strip()
    
    url = "https://www.googleapis.com/customsearch/v1"
    results = []
    start = 1
    while len(results) < max_results:
        num = min(10, max_results - len(results))  # CSE max per request is 10
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": clean_query,
            "num": num,
            "start": start
        }
        print(f"[Google CSE] Query: {clean_query} | Params: {params}")
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            print(f"[Google CSE] Returned {len(items)} items for query: '{clean_query}' (start={start}, num={num})")
            for item in items:
                # Only add results with valid URLs
                link = item.get("link", "")
                if link and link.startswith(("http://", "https://")):
                    results.append({
                        "title": item.get("title", "Untitled"),
                        "href": link,
                        "snippet": item.get("snippet", "")
                    })
            if not items or len(results) >= max_results:
                break
            start += len(items)
        except Exception as e:
            print(f"[WARNING] Google CSE error: {e}")
            break
    if not results:
        print("[WARNING] Google CSE returned no results.")
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
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    print('[ERROR] BeautifulSoup (bs4) is not installed. Install with `pip install beautifulsoup4`.')

async def fetch_url_text(url: str, snippet: str = "") -> str:
    """
    Extract article text using newspaper3k, fallback to Playwright, then BeautifulSoup, then snippet.
    If extracted text is <500 chars, try to follow the first likely article/content link and extract from there.
    Print a preview and length of extracted text for debugging.
    """
    # Validate URL before processing
    if not url or not url.strip():
        print(f"[URL validation failed: empty URL, using snippet]")
        return snippet or "No content available."
    
    if not url.startswith(("http://", "https://")):
        print(f"[URL validation failed: invalid scheme for '{url}', using snippet]")
        return snippet or "No content available."
    
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
        from playwright.async_api import async_playwright

        async def run_playwright():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=15000)
                content = await page.content()
                await browser.close()
                return content

        html = await run_playwright()

        if BeautifulSoup is None:
            print('[ERROR] BeautifulSoup (bs4) is not installed. Skipping HTML parsing.')
        else:
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
        if BeautifulSoup is None:
            print('[ERROR] BeautifulSoup (bs4) is not installed. Skipping HTML parsing.')
        else:
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
        if BeautifulSoup is None:
            print('[ERROR] BeautifulSoup (bs4) is not installed. Skipping HTML parsing.')
        else:
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
    if BeautifulSoup is None:
        return '[Error fetching {}: BeautifulSoup (bs4) is not installed. Install with `pip install beautifulsoup4`. All extraction methods failed.]'.format(url)
    return f"[Error fetching {url}: all extraction methods failed.]"
