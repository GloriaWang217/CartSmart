"""Cross-platform price comparison logic."""

from models.product import Product, PriceInfo
from models.user_need import UserNeed


# Major retailers we prioritize in comparison display
PRIORITY_PLATFORMS = ["Amazon", "Target", "Walmart", "Sephora", "Ulta"]


def _normalize_platform(platform: str) -> str:
    """Normalize platform names for consistent matching.

    SerpAPI returns varied names like 'Amazon.com', 'Target.com', 'Walmart.com'.
    """
    lower = platform.lower()
    for name in PRIORITY_PLATFORMS:
        if name.lower() in lower:
            return name
    return platform


def _deduplicate_prices(prices: list[PriceInfo]) -> list[PriceInfo]:
    """Keep only the lowest price per platform."""
    best: dict[str, PriceInfo] = {}
    for p in prices:
        normalized = _normalize_platform(p.platform)
        p_copy = p.model_copy(update={"platform": normalized})
        if p_copy.price is None:
            continue
        existing = best.get(normalized)
        if existing is None or (existing.price is not None and p_copy.price < existing.price):
            best[normalized] = p_copy
    return list(best.values())


def get_best_price(product: Product) -> PriceInfo | None:
    """Return the lowest-priced option across all platforms."""
    valid = [p for p in product.prices if p.price is not None]
    if not valid:
        return None
    return min(valid, key=lambda p: p.price)


def compare_prices(product: Product) -> dict:
    """Generate a price comparison summary for a single product.

    Returns a dict with:
      - best_price: PriceInfo with the lowest price
      - platform_prices: deduplicated list sorted by price (lowest first)
      - price_range: (min, max) tuple
    """
    deduped = _deduplicate_prices(product.prices)
    sorted_prices = sorted(deduped, key=lambda p: p.price if p.price is not None else float("inf"))

    valid_prices = [p.price for p in sorted_prices if p.price is not None]

    return {
        "best_price": sorted_prices[0] if sorted_prices else None,
        "platform_prices": sorted_prices,
        "price_range": (min(valid_prices), max(valid_prices)) if valid_prices else None,
    }


def filter_by_budget(candidates: list[Product], need: UserNeed) -> list[Product]:
    """Filter candidates that have at least one price within the user's budget.

    Products with no price data are kept (benefit of the doubt).
    Checks both budget_min and budget_max.
    """
    if need.budget_min is None and need.budget_max is None:
        return candidates

    filtered = []
    for product in candidates:
        valid_prices = [p.price for p in product.prices if p.price is not None]
        if not valid_prices:
            # No price data — keep the product
            filtered.append(product)
            continue

        highest = max(valid_prices)
        lowest = min(valid_prices)

        # If the most expensive option is still below budget_min, skip
        if need.budget_min is not None and highest < need.budget_min:
            continue
        # If the cheapest option exceeds budget_max, skip
        if need.budget_max is not None and lowest > need.budget_max:
            continue

        filtered.append(product)

    return filtered


def categorize_by_budget(
    candidates: list[Product], need: UserNeed
) -> tuple[list[Product], list[Product]]:
    """Split candidates into (in_budget, value_picks).

    - in_budget: products with at least one price within budget range
    - value_picks: products BELOW budget but highly recommended (great deals)
    - products significantly ABOVE budget are filtered out
    """
    if need.budget_min is None and need.budget_max is None:
        return candidates, []

    in_budget: list[Product] = []
    value_picks: list[Product] = []

    for product in candidates:
        valid_prices = [p.price for p in product.prices if p.price is not None]
        if not valid_prices:
            # No price data — keep in main list (benefit of the doubt)
            in_budget.append(product)
            continue

        lowest = min(valid_prices)

        # Too expensive (>30% above budget_max) — drop
        if need.budget_max is not None and lowest > need.budget_max * 1.3:
            continue

        # Below budget_min — move to value picks
        if need.budget_min is not None and lowest < need.budget_min:
            value_picks.append(product)
            continue

        # Within budget range
        in_budget.append(product)

    return in_budget, value_picks


def rank_by_value(candidates: list[Product]) -> list[Product]:
    """Re-rank candidates by a value score combining community mentions and best price.

    Products with more mentions rank higher. Price is secondary.
    """
    def _score(product: Product) -> float:
        mention_score = product.mentions
        best = get_best_price(product)
        # Lower price = higher score. Use inverse; cap at 200 to avoid division issues
        price_score = 0
        if best and best.price and best.price > 0:
            price_score = 100 / best.price
        return mention_score * 2 + price_score

    return sorted(candidates, key=_score, reverse=True)
