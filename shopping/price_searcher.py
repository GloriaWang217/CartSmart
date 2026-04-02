"""Cross-platform price search via site-specific Google searches.

Instead of Google Shopping (which mixes similar but different products),
we search each major retail platform directly using site: queries.
This ensures we find the EXACT product page on each platform.
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from serpapi import GoogleSearch

from models.product import Product, PriceInfo
from utils.config import SERPAPI_KEY


# Target retail platforms to search
TARGET_PLATFORMS = {
    "amazon.com": "Amazon",
    "sephora.com": "Sephora",
    "target.com": "Target",
    "walmart.com": "Walmart",
    "ulta.com": "Ulta",
}


def _identify_platform(url: str) -> str | None:
    """Identify which retail platform a URL belongs to."""
    lower = url.lower()
    for domain, name in TARGET_PLATFORMS.items():
        if domain in lower:
            return name
    return None


def _extract_price_from_text(text: str) -> float | None:
    """Extract a USD price from text using regex.

    Looks for patterns like $14.99, $9.00, $120. Returns the smallest
    reasonable price found (typically the product price, not shipping etc).
    """
    matches = re.findall(r'\$(\d+(?:\.\d{2})?)', text)
    if matches:
        prices = [float(m) for m in matches]
        reasonable = [p for p in prices if 3 < p < 500]
        if reasonable:
            return min(reasonable)
    return None


def _extract_size_from_text(text: str) -> str | None:
    """Extract product size/volume (e.g. '16 oz', '50 ml') from text."""
    patterns = [
        r'(\d+(?:\.\d+)?\s*(?:fl\.?\s*)?oz)',
        r'(\d+(?:\.\d+)?\s*ml)\b',
        r'(\d+(?:\.\d+)?\s*g)\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _search_product_across_platforms(
    product_name: str, brand: str | None = None
) -> tuple[list[PriceInfo], str | None]:
    """Search for a product across all target platforms in ONE SerpAPI call.

    Uses a combined site: OR query to find the product page on each
    major retailer. Also looks for the brand's official product page.

    Returns (list of PriceInfo, official_link or None).
    """
    query = product_name
    if brand and brand.lower() not in product_name.lower():
        query = f"{brand} {product_name}"

    # Build site: OR clause for all platforms + brand official
    site_parts = [f"site:{domain}" for domain in TARGET_PLATFORMS]
    if brand:
        brand_domain = brand.lower().replace(" ", "").replace("'", "")
        site_parts.append(f"site:{brand_domain}.com")

    site_clause = " OR ".join(site_parts)
    search_query = f'"{query}" ({site_clause})'

    params = {
        "engine": "google",
        "q": search_query,
        "num": 20,
        "gl": "us",
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    prices: list[PriceInfo] = []
    seen_platforms: set[str] = set()
    official_link: str | None = None

    for r in results.get("organic_results", []):
        link = r.get("link", "")
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        full_text = f"{title} {snippet}"

        # Check for brand official link
        if brand:
            bd = brand.lower().replace(" ", "").replace("'", "")
            if bd + ".com" in link.lower() and not official_link:
                official_link = link
                continue

        # Identify platform from URL
        platform = _identify_platform(link)
        if not platform or platform in seen_platforms:
            continue
        seen_platforms.add(platform)

        # Extract price from title + snippet text
        price = _extract_price_from_text(full_text)

        # Try rich snippet data if no price found in text
        rich = r.get("rich_snippet", {})
        if rich:
            top = rich.get("top", {})
            detected = top.get("detected_extensions", {})
            if not price and "price" in detected:
                price = _extract_price_from_text(str(detected["price"]))
            if not price:
                for ext in top.get("extensions", []):
                    price = _extract_price_from_text(str(ext))
                    if price:
                        break

        # Extract size from text
        size = _extract_size_from_text(full_text)

        # Extract rating from rich snippet
        rating = None
        reviews_count = None
        if rich:
            detected = rich.get("top", {}).get("detected_extensions", {})
            rating = detected.get("rating")
            reviews_count = detected.get("reviews")

        prices.append(PriceInfo(
            platform=platform,
            price=price,
            link=link,
            rating=rating,
            reviews_count=reviews_count,
            size=size,
        ))

    return prices, official_link


def search_prices_for_candidates(
    candidates: list[Product], max_products: int = 5
) -> list[Product]:
    """Search prices for candidate products in parallel.

    Each product's search runs concurrently using ThreadPoolExecutor.
    Mutates each Product in place by populating `prices` and `official_link`.
    """

    def _search_one(product: Product) -> None:
        try:
            prices, official_link = _search_product_across_platforms(
                product.name, product.brand
            )
            product.prices = prices
            product.official_link = official_link
            print(f"[PriceSearch] {product.name}: {len(prices)} platform prices")
        except Exception as e:
            print(f"[PriceSearch] {product.name}: FAILED - {e}")
            product.prices = []
            product.official_link = None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(_search_one, p) for p in candidates[:max_products]
        ]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception:
                pass

    return candidates
