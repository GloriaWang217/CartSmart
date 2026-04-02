"""Community research - search Reddit, review articles, Sephora community via SerpAPI."""

import json
import asyncio

from anthropic import Anthropic
from serpapi import GoogleSearch

from core.prompts import PRICE_TIER_PROMPT
from models.user_need import UserNeed
from models.product import Product
from research.page_fetcher import fetch_pages_async
from research.recommendation_extractor import extract_recommendations, aggregate_recommendations
from utils.config import SERPAPI_KEY, ANTHROPIC_API_KEY

# Load subreddit config
with open("data/subreddits.json") as f:
    SUBREDDITS = json.load(f)

_anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)


def _get_price_tier(need: UserNeed) -> str:
    """Ask LLM to classify the user's budget into a price tier for this product category.

    Different product types have very different price scales, so we let
    the LLM judge rather than using hardcoded thresholds.
    Returns one of: drugstore, affordable, mid-range, premium, high-end, luxury.
    Returns empty string if no budget is specified.
    """
    if need.budget_min is None and need.budget_max is None:
        return ""

    budget_min = need.budget_min or 0
    budget_max = need.budget_max or budget_min * 2

    prompt = PRICE_TIER_PROMPT.format(
        product_type=need.product_type,
        budget_min=int(budget_min),
        budget_max=int(budget_max),
    )

    response = _anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        messages=[{"role": "user", "content": prompt}],
    )
    tier = response.content[0].text.strip().lower()

    # Validate — fall back to empty if LLM returned something unexpected
    valid_tiers = {"drugstore", "affordable", "mid-range", "premium", "high-end", "luxury"}
    if tier not in valid_tiers:
        print(f"[PriceTier] Unexpected LLM response: {tier!r}, ignoring")
        return ""

    print(f"[PriceTier] {need.product_type} ${budget_min}-${budget_max} → {tier}")
    return tier


def _build_search_queries(need: UserNeed, price_tier: str) -> list[dict]:
    """Build SerpAPI search queries based on user needs.

    Incorporates the price tier keyword so community results are biased
    toward the right price range for this product category.
    """
    product_type = need.product_type
    skin_type = need.skin_type or ""
    concerns = " ".join(need.concerns) if need.concerns else ""

    # Price tier keyword biases search results toward the right price range
    search_term = f"{price_tier} {product_type} {skin_type} {concerns}".strip()

    queries = []

    # Reddit searches - pick subreddits relevant to the product type
    for sub in SUBREDDITS:
        if sub["tier"] > 1:
            continue
        if product_type in sub["categories"] or any(c in sub["categories"] for c in need.concerns):
            queries.append({
                "q": f"best {search_term} site:reddit.com/r/{sub['name']}",
                "num": 8,
                "source_type": "reddit",
                "source_name": f"r/{sub['name']}",
            })

    # If no subreddit matched, search general Reddit
    if not any(q["source_type"] == "reddit" for q in queries):
        queries.append({
            "q": f"best {search_term} site:reddit.com",
            "num": 8,
            "source_type": "reddit",
            "source_name": "reddit",
        })

    # Professional review articles
    queries.append({
        "q": f"best {search_term} 2025 dermatologist recommended review",
        "num": 8,
        "source_type": "review_article",
        "source_name": "review_articles",
    })

    return queries


def _search_serpapi(query: dict) -> list[dict]:
    """Run a single SerpAPI Google search and return organic results."""
    params = {
        "engine": "google",
        "q": query["q"],
        "num": query["num"],
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
            "source_type": query["source_type"],
            "source_name": query["source_name"],
        })
    return pages


def research_community(need: UserNeed) -> tuple[list[Product], str]:
    """Main entry point: search communities and extract product recommendations.

    Returns (ranked list of candidate Products, price_tier string).
    The price_tier is passed through so downstream stages can use it.
    """
    # Step 0: Determine price tier via LLM
    price_tier = _get_price_tier(need)

    # Step 1: Build search queries (now budget-aware)
    queries = _build_search_queries(need, price_tier)

    # Step 2: Run all SerpAPI searches
    all_pages = []
    for q in queries:
        pages = _search_serpapi(q)
        all_pages.extend(pages)

    # Step 3: Fetch full page content for all results
    urls = [p["link"] for p in all_pages]
    page_contents = asyncio.run(fetch_pages_async(urls))

    # Attach fetched content to page metadata (fall back to snippet if fetch failed)
    for page in all_pages:
        page["content"] = page_contents.get(page["link"]) or page["snippet"]

    # Step 4: Extract recommendations from each source via LLM
    all_recommendations = extract_recommendations(all_pages, need)

    # Step 5: Aggregate and rank (now budget-aware)
    candidates = aggregate_recommendations(all_recommendations, need, price_tier)

    return candidates, price_tier
