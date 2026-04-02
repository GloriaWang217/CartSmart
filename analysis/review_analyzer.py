"""Deep review analysis powered by LLM."""

import json

from openai import OpenAI

from analysis.review_fetcher import fetch_reviews_for_product
from core.prompts import REVIEW_ANALYSIS_PROMPT
from models.product import Product, ReviewAnalysis
from models.user_need import UserNeed
from utils.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def _call_llm(prompt: str) -> str:
    """Call OpenAI API for review analysis."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _parse_llm_json(raw: str) -> dict | None:
    """Parse JSON from LLM response, handling markdown code fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, KeyError):
        return None


def analyze_product_reviews(product: Product, need: UserNeed) -> ReviewAnalysis | None:
    """Fetch reviews for a product and analyze them with LLM.

    Returns a ReviewAnalysis or None if analysis fails.
    """
    # Step 1: Fetch review data
    try:
        review_data = fetch_reviews_for_product(product)
    except Exception:
        return None

    review_texts = review_data.get("review_texts", "")
    if not review_texts or len(review_texts) < 30:
        # Not enough review content to analyze
        return None

    # Step 2: Build prompt and call LLM
    prompt = REVIEW_ANALYSIS_PROMPT.format(
        user_need=need.model_dump_json(exclude_none=True),
        product_name=product.name,
        average_rating=review_data.get("average_rating") or "N/A",
        total_reviews=review_data.get("total_reviews") or "N/A",
        review_texts=review_texts,
    )

    raw = _call_llm(prompt)
    data = _parse_llm_json(raw)
    if not data:
        return None

    # Step 3: Parse into ReviewAnalysis model
    return ReviewAnalysis(
        overall_rating=data.get("overall_rating"),
        total_reviews=data.get("total_reviews"),
        pros=data.get("pros", []),
        cons=data.get("cons", []),
        best_for=data.get("best_for", []),
        not_for=data.get("not_for", []),
        match_score=data.get("match_score"),
        match_reason=data.get("match_reason"),
        purchase_advice=data.get("purchase_advice"),
    )


def analyze_reviews_for_candidates(
    candidates: list[Product], need: UserNeed, max_products: int = 5
) -> list[Product]:
    """Analyze reviews for top candidate products in parallel.

    Mutates each Product in place by populating its `review_summary` field.
    Uses ThreadPoolExecutor to analyze multiple products concurrently.
    """
    from concurrent.futures import ThreadPoolExecutor

    def _analyze_one(product: Product) -> None:
        try:
            product.review_summary = analyze_product_reviews(product, need)
        except Exception:
            product.review_summary = None

    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(_analyze_one, candidates[:max_products]))

    return candidates
