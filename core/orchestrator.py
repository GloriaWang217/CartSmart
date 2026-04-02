"""Pipeline orchestration - connects the three stages."""

from concurrent.futures import ThreadPoolExecutor

from models.user_need import UserNeed
from models.product import Product
from research.community_researcher import research_community
from shopping.price_searcher import search_prices_for_candidates
from shopping.price_comparator import categorize_by_budget, rank_by_value
from analysis.review_analyzer import analyze_reviews_for_candidates
from analysis.ingredient_analyzer import analyze_ingredients_for_candidates


def run_community_research(need: UserNeed) -> tuple[list[Product], str]:
    """Stage 2: Run community research based on extracted needs.

    Returns (ranked list of candidate products, price_tier string).
    """
    return research_community(need)


def run_price_research(
    candidates: list[Product], need: UserNeed
) -> tuple[list[Product], list[Product]]:
    """Stage 3a: Search prices, categorize by budget.

    Returns (in_budget products, value_picks products).
    Both lists are ranked by value.
    """
    search_prices_for_candidates(candidates)
    in_budget, value_picks = categorize_by_budget(candidates, need)
    in_budget = rank_by_value(in_budget)
    value_picks = rank_by_value(value_picks)
    return in_budget, value_picks


def run_analysis(
    candidates: list[Product], need: UserNeed, max_products: int = 5
) -> list[Product]:
    """Stage 3b+3c: Run review analysis and ingredient analysis IN PARALLEL.

    Both analyses are independent, so we run them concurrently
    using ThreadPoolExecutor to cut wall-clock time in half.
    """
    top = candidates[:max_products]

    with ThreadPoolExecutor(max_workers=2) as executor:
        review_future = executor.submit(
            analyze_reviews_for_candidates, top, need, max_products
        )
        ingredient_future = executor.submit(
            analyze_ingredients_for_candidates, top, need, max_products
        )
        # Wait for both to complete
        review_future.result()
        ingredient_future.result()

    return candidates
