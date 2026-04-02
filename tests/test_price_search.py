"""Tests for price search and comparison modules."""

from models.product import Product, PriceInfo
from models.user_need import UserNeed
from shopping.price_comparator import (
    compare_prices,
    filter_by_budget,
    get_best_price,
    rank_by_value,
    _normalize_platform,
    _deduplicate_prices,
)
from shopping.price_searcher import _parse_price


# --- price_searcher tests ---

def test_parse_price_basic():
    assert _parse_price("$14.99") == 14.99

def test_parse_price_with_comma():
    assert _parse_price("$1,299.00") == 1299.00

def test_parse_price_none():
    assert _parse_price(None) is None

def test_parse_price_invalid():
    assert _parse_price("free") is None


# --- price_comparator tests ---

def test_normalize_platform():
    assert _normalize_platform("Amazon.com") == "Amazon"
    assert _normalize_platform("Target.com") == "Target"
    assert _normalize_platform("Walmart.com") == "Walmart"
    assert _normalize_platform("SomeRandomShop") == "SomeRandomShop"

def test_deduplicate_prices():
    prices = [
        PriceInfo(platform="Amazon.com", price=14.99),
        PriceInfo(platform="Amazon.com - Seller X", price=16.50),
        PriceInfo(platform="Target.com", price=15.99),
    ]
    deduped = _deduplicate_prices(prices)
    platforms = {p.platform for p in deduped}
    assert "Amazon" in platforms
    assert "Target" in platforms
    # Should keep the cheaper Amazon price
    amazon = next(p for p in deduped if p.platform == "Amazon")
    assert amazon.price == 14.99

def test_get_best_price():
    product = Product(
        name="Test Product",
        prices=[
            PriceInfo(platform="Amazon", price=14.99),
            PriceInfo(platform="Target", price=12.50),
            PriceInfo(platform="Sephora", price=19.00),
        ],
    )
    best = get_best_price(product)
    assert best is not None
    assert best.price == 12.50
    assert best.platform == "Target"

def test_get_best_price_no_prices():
    product = Product(name="Test", prices=[])
    assert get_best_price(product) is None

def test_compare_prices():
    product = Product(
        name="Test",
        prices=[
            PriceInfo(platform="Amazon.com", price=14.99),
            PriceInfo(platform="Target.com", price=12.50),
        ],
    )
    result = compare_prices(product)
    assert result["best_price"].price == 12.50
    assert result["price_range"] == (12.50, 14.99)
    assert len(result["platform_prices"]) == 2

def test_filter_by_budget():
    candidates = [
        Product(name="Cheap", prices=[PriceInfo(platform="A", price=10.0)]),
        Product(name="Mid", prices=[PriceInfo(platform="A", price=30.0)]),
        Product(name="Expensive", prices=[PriceInfo(platform="A", price=100.0)]),
        Product(name="No Price", prices=[]),
    ]
    need = UserNeed(product_type="moisturizer", budget_max=50.0)
    filtered = filter_by_budget(candidates, need)
    names = [p.name for p in filtered]
    assert "Cheap" in names
    assert "Mid" in names
    assert "Expensive" not in names
    assert "No Price" in names  # kept due to no data

def test_filter_by_budget_no_limit():
    candidates = [Product(name="Any", prices=[PriceInfo(platform="A", price=999.0)])]
    need = UserNeed(product_type="moisturizer")
    filtered = filter_by_budget(candidates, need)
    assert len(filtered) == 1

def test_rank_by_value():
    candidates = [
        Product(name="Low Mentions Cheap", mentions=2, prices=[PriceInfo(platform="A", price=5.0)]),
        Product(name="High Mentions Expensive", mentions=20, prices=[PriceInfo(platform="A", price=50.0)]),
        Product(name="High Mentions Cheap", mentions=20, prices=[PriceInfo(platform="A", price=10.0)]),
    ]
    ranked = rank_by_value(candidates)
    assert ranked[0].name == "High Mentions Cheap"
    assert ranked[1].name == "High Mentions Expensive"
