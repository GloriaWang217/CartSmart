"""Ingredient analysis - safety, efficacy, and personalized assessment."""

import json

from serpapi import GoogleSearch
from openai import OpenAI

from core.prompts import INGREDIENT_ANALYSIS_PROMPT
from models.product import Product
from models.user_need import UserNeed
from utils.config import SERPAPI_KEY, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# Load ingredient database
with open("data/ingredients.json") as f:
    INGREDIENT_DB: list[dict] = json.load(f)

# Build lookup: lowercase name/alias -> ingredient entry
_INGREDIENT_LOOKUP: dict[str, dict] = {}
for entry in INGREDIENT_DB:
    _INGREDIENT_LOOKUP[entry["name"].lower()] = entry
    for alias in entry.get("aliases", []):
        _INGREDIENT_LOOKUP[alias.lower()] = entry


def _call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _parse_llm_json(raw: str) -> dict | None:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, KeyError):
        return None


def lookup_ingredient(name: str) -> dict | None:
    """Look up an ingredient in our local database by name or alias."""
    return _INGREDIENT_LOOKUP.get(name.lower())


def match_ingredients_from_db(ingredient_list: list[str]) -> list[dict]:
    """Match a product's ingredient list against our database.

    Returns list of matched entries with the original ingredient name.
    """
    matches = []
    for ing in ingredient_list:
        entry = lookup_ingredient(ing.strip())
        if entry:
            matches.append({"input_name": ing.strip(), **entry})
    return matches


def search_product_ingredients(product_name: str) -> str:
    """Search Google for a product's ingredient list.

    Returns the ingredient list as a string, or empty string if not found.
    """
    params = {
        "engine": "google",
        "q": f"{product_name} full ingredient list INCI",
        "num": 3,
        "api_key": SERPAPI_KEY,
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    # Try to extract ingredients from snippets
    for r in results.get("organic_results", []):
        snippet = r.get("snippet", "")
        # Ingredient lists typically have lots of commas and chemical names
        if snippet.count(",") >= 5:
            return snippet

    return ""


def analyze_ingredients(product: Product, need: UserNeed) -> dict | None:
    """Analyze a product's ingredients with personalized assessment.

    1. Search for the product's ingredient list online
    2. Match against our local ingredient database
    3. Use LLM for comprehensive analysis personalized to user's needs

    Returns parsed ingredient analysis dict or None.
    """
    # Step 1: Find ingredient list
    ingredient_text = search_product_ingredients(product.name)

    # Step 2: Try to match against our DB
    ingredient_names = [i.strip() for i in ingredient_text.split(",") if i.strip()] if ingredient_text else []
    db_matches = match_ingredients_from_db(ingredient_names)

    db_matches_str = json.dumps(db_matches, indent=2) if db_matches else "No matches found in local database."

    # Step 3: LLM analysis
    prompt = INGREDIENT_ANALYSIS_PROMPT.format(
        user_need=need.model_dump_json(exclude_none=True),
        product_name=product.name,
        ingredient_list=ingredient_text or "Not available — please analyze based on your knowledge of this product.",
        ingredient_db_matches=db_matches_str,
    )

    raw = _call_llm(prompt)
    return _parse_llm_json(raw)


def analyze_ingredients_for_candidates(
    candidates: list[Product], need: UserNeed, max_products: int = 5
) -> list[Product]:
    """Analyze ingredients for top candidate products in parallel.

    Uses ThreadPoolExecutor to analyze multiple products concurrently.
    """
    from concurrent.futures import ThreadPoolExecutor

    def _analyze_one(product: Product) -> None:
        try:
            product.ingredient_analysis = analyze_ingredients(product, need)
        except Exception:
            product.ingredient_analysis = None

    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(_analyze_one, candidates[:max_products]))

    return candidates
