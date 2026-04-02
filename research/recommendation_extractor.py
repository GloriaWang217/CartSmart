"""LLM-powered extraction of frequently recommended products from community content."""

import json

from openai import OpenAI

from core.prompts import RECOMMENDATION_EXTRACTION_PROMPT, AGGREGATE_RECOMMENDATIONS_PROMPT
from models.user_need import UserNeed
from models.product import Product
from utils.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def _call_llm(prompt: str) -> str:
    """Call OpenAI API with a single prompt."""
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


def extract_recommendations(pages: list[dict], need: UserNeed) -> list[dict]:
    """Extract product recommendations from fetched pages using LLM.

    Processes each page individually to avoid content truncation,
    then returns all extracted recommendations.
    """
    need_str = need.model_dump_json(exclude_none=True)
    all_recommendations = []

    for page in pages:
        content = page.get("content", page.get("snippet", ""))
        if not content or len(content) < 50:
            continue

        prompt = RECOMMENDATION_EXTRACTION_PROMPT.format(
            user_need=need_str,
            content=f"--- {page['title']} ---\n{content}",
            source_name=page["source_name"],
        )

        raw = _call_llm(prompt)
        data = _parse_llm_json(raw)
        if not data:
            continue

        for product in data.get("products", []):
            product["source_name"] = page["source_name"]
            all_recommendations.append(product)

    return all_recommendations


def aggregate_recommendations(
    all_recommendations: list[dict], need: UserNeed, price_tier: str = ""
) -> list[Product]:
    """Aggregate recommendations from all sources, rank, and return top candidates.

    price_tier is used to bias ranking toward products that match the user's budget.
    """
    if not all_recommendations:
        return []

    need_str = need.model_dump_json(exclude_none=True)
    recs_str = json.dumps(all_recommendations, indent=2)

    prompt = AGGREGATE_RECOMMENDATIONS_PROMPT.format(
        user_need=need_str,
        all_recommendations=recs_str,
        budget_min=int(need.budget_min or 0),
        budget_max=int(need.budget_max or 0),
        product_type=need.product_type,
        price_tier=price_tier or "unknown",
    )

    raw = _call_llm(prompt)
    data = _parse_llm_json(raw)
    if not data:
        return []

    candidates = []
    for c in data.get("candidates", []):
        candidates.append(Product(
            name=c.get("name", ""),
            brand=c.get("brand"),
            mentions=c.get("mentions", 0),
            sources=c.get("sources", []),
            why_recommended=c.get("why_recommended"),
        ))

    return candidates
