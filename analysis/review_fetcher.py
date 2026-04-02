"""Fetch review data from shopping platforms via SerpAPI and web scraping."""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

from serpapi import GoogleSearch

from models.product import Product
from utils.config import SERPAPI_KEY

MAX_REVIEW_LENGTH = 12000


def _fetch_shopping_reviews(product_name: str) -> dict:
    """Use SerpAPI Google Shopping to get ratings and review counts.

    Returns aggregated rating info from shopping results.
    """
    params = {
        "engine": "google_shopping",
        "q": f"{product_name} reviews",
        "gl": "us",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    ratings = []
    total_reviews = 0
    for item in results.get("shopping_results", []):
        r = item.get("rating")
        rc = item.get("reviews")
        if r:
            ratings.append(float(r))
        if rc:
            total_reviews += int(rc)

    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
    return {"average_rating": avg_rating, "total_reviews": total_reviews}


def _search_review_pages(product_name: str) -> list[dict]:
    """Search Google for review pages about a product.

    Returns list of {title, link, snippet} for review articles and discussions.
    """
    params = {
        "engine": "google",
        "q": f"{product_name} review site:reddit.com OR site:makeupalley.com OR review",
        "num": 6,
        "api_key": SERPAPI_KEY,
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    pages = []
    for r in results.get("organic_results", []):
        pages.append({
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "snippet": r.get("snippet", ""),
        })
    return pages


async def _fetch_page_text(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch and extract text content from a single URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
    }
    # Use old.reddit.com for better scraping
    fetch_url = url
    if "reddit.com" in url and "old.reddit.com" not in url:
        fetch_url = url.replace("www.reddit.com", "old.reddit.com").replace("://reddit.com", "://old.reddit.com")

    try:
        async with session.get(fetch_url, headers=headers, timeout=aiohttp.ClientTimeout(total=12), allow_redirects=True) as resp:
            if resp.status != 200:
                return ""
            html = await resp.text()
    except Exception:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        tag.decompose()

    if "reddit.com" in url:
        comment_area = soup.find("div", class_="commentarea")
        if comment_area:
            texts = [md.get_text(separator=" ", strip=True) for md in comment_area.find_all("div", class_="md")]
        else:
            texts = [md.get_text(separator=" ", strip=True) for md in soup.find_all("div", class_="md")]
        return "\n".join(texts)[:MAX_REVIEW_LENGTH]

    main = soup.find("article") or soup.find("main") or soup.find("div", class_="content")
    text = (main or soup).get_text(separator="\n", strip=True)
    return text[:MAX_REVIEW_LENGTH]


async def _fetch_all_pages(urls: list[str]) -> dict[str, str]:
    """Fetch multiple review pages in parallel."""
    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_page_text(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    return {url: text for url, text in zip(urls, results)}


def fetch_reviews_for_product(product: Product) -> dict:
    """Fetch all available review data for a single product.

    Returns a dict with:
      - average_rating: float or None (from price search data if available)
      - total_reviews: int
      - review_texts: combined text from review pages (for LLM analysis)

    Note: We no longer call _fetch_shopping_reviews here — rating data
    comes from the price search stage (saved on PriceInfo). This saves
    one SerpAPI call per product.
    """
    # Use rating data from price search if available
    avg_rating = None
    total_reviews = 0
    if product.prices:
        ratings = [p.rating for p in product.prices if p.rating]
        reviews = [p.reviews_count for p in product.prices if p.reviews_count]
        if ratings:
            avg_rating = round(sum(ratings) / len(ratings), 1)
        if reviews:
            total_reviews = sum(reviews)

    # Search for and fetch review page content
    review_pages = _search_review_pages(product.name)
    urls = [p["link"] for p in review_pages if p["link"]]

    page_texts = asyncio.run(_fetch_all_pages(urls))

    # Combine all review content: snippets + full page text
    all_text_parts = []
    for page in review_pages:
        full_text = page_texts.get(page["link"], "")
        if full_text and len(full_text) > 50:
            all_text_parts.append(f"--- {page['title']} ---\n{full_text}")
        elif page["snippet"]:
            all_text_parts.append(f"--- {page['title']} ---\n{page['snippet']}")

    combined_reviews = "\n\n".join(all_text_parts)
    if len(combined_reviews) > MAX_REVIEW_LENGTH:
        combined_reviews = combined_reviews[:MAX_REVIEW_LENGTH]

    return {
        "average_rating": avg_rating,
        "total_reviews": total_reviews,
        "review_texts": combined_reviews,
    }
