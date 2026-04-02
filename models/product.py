"""Unified product data model."""

from pydantic import BaseModel


class PriceInfo(BaseModel):
    platform: str
    price: float | None = None
    original_price: float | None = None  # Pre-sale / strikethrough price
    link: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    deal_tag: str | None = None  # e.g. "Sale", "Best Seller", "Sponsored"
    delivery: str | None = None  # e.g. "Free delivery", "Free shipping"
    size: str | None = None  # e.g. "16 oz", "50 ml"
    unit_price: float | None = None  # price per oz/ml for comparison


class ReviewAnalysis(BaseModel):
    overall_rating: float | None = None
    total_reviews: int | None = None
    pros: list[str] = []
    cons: list[str] = []
    best_for: list[str] = []
    not_for: list[str] = []
    match_score: int | None = None  # 1-10 personalized match score
    match_reason: str | None = None
    purchase_advice: str | None = None


class Product(BaseModel):
    name: str
    brand: str | None = None
    mentions: int = 0
    sources: list[str] = []
    why_recommended: str | None = None
    prices: list[PriceInfo] = []
    official_link: str | None = None  # Brand official product page URL
    review_summary: ReviewAnalysis | None = None
    ingredient_analysis: dict | None = None
