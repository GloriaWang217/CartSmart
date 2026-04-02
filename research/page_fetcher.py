"""Fetch full page content from Reddit posts and review articles."""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

# Max content per page sent to LLM
MAX_CONTENT_LENGTH = 15000


def _make_fetch_url(url: str) -> str:
    """Convert URLs for better scraping. Reddit → old.reddit.com."""
    if "reddit.com" in url and "old.reddit.com" not in url:
        return url.replace("www.reddit.com", "old.reddit.com").replace("://reddit.com", "://old.reddit.com")
    return url


def _is_reddit(url: str) -> bool:
    return "reddit.com" in url


def _extract_reddit_comments(soup: BeautifulSoup) -> str:
    """Extract comment text from old.reddit.com HTML."""
    # Comments live in div.commentarea, each comment body is div.md inside div.comment
    comment_area = soup.find("div", class_="commentarea")
    if not comment_area:
        # Fallback: get all .md divs but skip sidebar
        all_md = soup.find_all("div", class_="md")
        texts = [md.get_text(separator=" ", strip=True) for md in all_md]
    else:
        all_md = comment_area.find_all("div", class_="md")
        texts = [md.get_text(separator=" ", strip=True) for md in all_md]

    # Also get the original post body
    post_body = soup.find("div", class_="expando")
    if post_body:
        post_md = post_body.find("div", class_="md")
        if post_md:
            texts.insert(0, post_md.get_text(separator=" ", strip=True))

    combined = "\n".join(texts)
    return combined[:MAX_CONTENT_LENGTH]


def _extract_article(soup: BeautifulSoup) -> str:
    """Extract main content from a general web page."""
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        tag.decompose()

    main = soup.find("article") or soup.find("main") or soup.find("div", class_="content")
    if main:
        text = main.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    return text[:MAX_CONTENT_LENGTH]


async def _fetch_one(session: aiohttp.ClientSession, url: str) -> tuple[str, str]:
    """Fetch a single URL and extract text content.

    Returns (original_url, text_content).
    """
    fetch_url = _make_fetch_url(url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with session.get(fetch_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as resp:
            if resp.status != 200:
                return url, ""
            html = await resp.text()
    except Exception:
        return url, ""

    soup = BeautifulSoup(html, "html.parser")

    if _is_reddit(url):
        text = _extract_reddit_comments(soup)
    else:
        text = _extract_article(soup)

    return url, text


async def fetch_pages_async(urls: list[str]) -> dict[str, str]:
    """Fetch multiple URLs in parallel.

    Returns dict of {url: text_content}.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_one(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    return {url: content for url, content in results}
