"""Test script for price comparison display — uses mock data, no API calls."""

import streamlit as st

from models.product import Product, PriceInfo, ReviewAnalysis
from shopping.price_comparator import compare_prices, get_best_price


CARD_CSS = """
<style>
/* Product card */
.product-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 4px;
}
.product-rank {
    font-size: 28px;
    font-weight: 800;
    color: #6C63FF;
    min-width: 40px;
}
.product-name {
    font-size: 24px;
    font-weight: 700;
    color: #1a1a2e;
}
.product-brand {
    font-size: 14px;
    color: #888;
    margin-left: 8px;
}

/* Price table */
.price-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin: 8px 0;
    font-size: 14px;
}
.price-table thead th {
    background: #f0eeff;
    color: #4a4a6a;
    font-weight: 600;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 2px solid #d8d5f0;
}
.price-table thead th:first-child {
    border-radius: 8px 0 0 0;
}
.price-table thead th:last-child {
    border-radius: 0 8px 0 0;
}
.price-table tbody tr {
    transition: background 0.15s;
}
.price-table tbody tr:hover {
    background: #f8f7ff;
}
.price-table tbody tr.best-row {
    background: #f0fff4;
}
.price-table tbody td {
    padding: 12px 14px;
    border-bottom: 1px solid #eee;
    vertical-align: middle;
}
.platform-name {
    font-weight: 600;
    color: #1a1a2e;
    font-size: 15px;
}
.platform-rating {
    color: #999;
    font-size: 12px;
    margin-top: 2px;
}
.current-price {
    font-weight: 700;
    font-size: 18px;
    color: #1a1a2e;
}
.best-price-tag {
    font-weight: 700;
    font-size: 18px;
    color: #0d9e3f;
}
.original-price {
    text-decoration: line-through;
    color: #aaa;
    font-size: 13px;
    margin-left: 6px;
}
.discount-badge {
    display: inline-block;
    background: #ff4757;
    color: white;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 6px;
}
.deal-tag {
    display: inline-block;
    background: #6C63FF;
    color: white;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    margin-right: 6px;
}
.delivery-tag {
    display: inline-block;
    background: #e8f5e9;
    color: #2e7d32;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    margin-right: 6px;
}
.save-tag {
    color: #0d9e3f;
    font-weight: 600;
    font-size: 12px;
}
.no-deal {
    color: #ccc;
    font-size: 12px;
}
.buy-link a {
    display: inline-block;
    background: #6C63FF;
    color: white !important;
    text-decoration: none !important;
    padding: 6px 16px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    transition: background 0.15s;
}
.buy-link a:hover {
    background: #5a52d5;
}
.price-summary {
    text-align: right;
    color: #888;
    font-size: 13px;
    padding: 8px 14px 4px;
}
</style>
"""


def build_mock_products() -> list[Product]:
    """Create mock products with realistic price data for display testing."""
    return [
        Product(
            name="CeraVe Moisturizing Cream",
            brand="CeraVe",
            mentions=12,
            sources=["r/SkincareAddiction x5", "r/AsianBeauty x4", "review_articles x3"],
            why_recommended="Most recommended moisturizer for dry skin. Ceramide-based formula repairs skin barrier.",
            prices=[
                PriceInfo(
                    platform="Amazon.com",
                    price=14.99,
                    original_price=19.99,
                    link="https://www.amazon.com/dp/example1",
                    rating=4.7,
                    reviews_count=89432,
                    deal_tag="Best Seller",
                    delivery="Free delivery",
                ),
                PriceInfo(
                    platform="Target.com",
                    price=15.49,
                    link="https://www.target.com/p/example1",
                    rating=4.6,
                    reviews_count=3210,
                    delivery="Free shipping on orders $35+",
                ),
                PriceInfo(
                    platform="Walmart.com",
                    price=13.97,
                    original_price=16.99,
                    link="https://www.walmart.com/ip/example1",
                    rating=4.5,
                    reviews_count=12540,
                    deal_tag="Rollback",
                    delivery="Free shipping",
                ),
                PriceInfo(
                    platform="Sephora.com",
                    price=18.00,
                    link="https://www.sephora.com/product/example1",
                    rating=4.4,
                    reviews_count=1823,
                ),
                PriceInfo(
                    platform="Ulta.com",
                    price=15.99,
                    original_price=18.50,
                    link="https://www.ulta.com/p/example1",
                    rating=4.6,
                    reviews_count=2456,
                    deal_tag="Sale",
                ),
            ],
            review_summary=ReviewAnalysis(
                overall_rating=4.6,
                total_reviews=1517283,
                pros=["Long-lasting hydration", "Non-greasy finish", "Gentle for sensitive skin"],
                cons=["Packaging can leak", "Slightly heavy in summer"],
                best_for=["Dry skin", "Sensitive skin"],
                not_for=["Very oily skin"],
                match_score=9,
                match_reason="Excellent match for dry skin needs.",
                purchase_advice="Great price point on multiple platforms.",
            ),
            ingredient_analysis={
                "overall_grade": "A",
                "highlights": "Contains glycerin and ceramide NP for hydration and barrier repair.",
                "grade_reason": "Solid ceramide-based formula.",
                "key_actives": [
                    {"name": "Glycerin", "function": "Humectant", "benefit_for_user": "Deeply hydrates dry skin"},
                    {"name": "Ceramide NP", "function": "Barrier repair", "benefit_for_user": "Gold standard for barrier repair"},
                ],
                "avoid_ingredient_check": [
                    {"ingredient": "Alcohol Denat", "found": False, "note": "Not found - meets your requirement"},
                ],
            },
        ),
        Product(
            name="La Roche-Posay Toleriane Double Repair Moisturizer",
            brand="La Roche-Posay",
            mentions=8,
            sources=["r/SkincareAddiction x3", "review_articles x5"],
            why_recommended="Dermatologist recommended. Prebiotic formula with ceramide-3 and niacinamide.",
            prices=[
                PriceInfo(
                    platform="Amazon.com",
                    price=21.99,
                    link="https://www.amazon.com/dp/example2",
                    rating=4.6,
                    reviews_count=45200,
                    delivery="Free delivery",
                ),
                PriceInfo(
                    platform="Target.com",
                    price=22.49,
                    link="https://www.target.com/p/example2",
                    rating=4.5,
                    reviews_count=1890,
                ),
                PriceInfo(
                    platform="Ulta.com",
                    price=19.99,
                    original_price=23.99,
                    link="https://www.ulta.com/p/example2",
                    rating=4.7,
                    reviews_count=3100,
                    deal_tag="Weekly Sale",
                    delivery="Free shipping",
                ),
            ],
            review_summary=ReviewAnalysis(
                overall_rating=4.5,
                total_reviews=52000,
                pros=["Lightweight texture", "Contains niacinamide"],
                cons=["Higher price point"],
                best_for=["Sensitive skin", "Combination skin"],
                not_for=["Those seeking heavy moisture"],
                match_score=8,
                match_reason="Great lightweight option with barrier repair benefits.",
            ),
        ),
    ]


def _format_review_count(count: int | None) -> str:
    if count is None:
        return "N/A"
    if count >= 1000:
        return f"{count / 1000:.1f}k"
    return str(count)


def render_price_table(product: Product):
    """Render a styled HTML price comparison table."""
    comparison = compare_prices(product)
    platform_prices = comparison["platform_prices"]
    if not platform_prices:
        return

    best_price_val = None
    best = comparison.get("best_price")
    if best and best.price is not None:
        best_price_val = best.price

    rows_html = ""
    for p in platform_prices:
        is_best = (p.price is not None and best_price_val is not None and p.price == best_price_val)
        row_class = ' class="best-row"' if is_best else ""

        # Platform cell
        rating_str = ""
        if p.rating:
            stars = "&#9733;" * int(p.rating) + "&#9734;" * (5 - int(p.rating))
            rating_str = f'<div class="platform-rating">{stars} {p.rating}/5 ({_format_review_count(p.reviews_count)})</div>'
        platform_cell = f'<span class="platform-name">{p.platform}</span>{rating_str}'

        # Price cell
        if p.price is not None:
            price_class = "best-price-tag" if is_best else "current-price"
            price_cell = f'<span class="{price_class}">${p.price:.2f}</span>'
            if p.original_price and p.original_price > p.price:
                discount_pct = round((1 - p.price / p.original_price) * 100)
                price_cell += f'<span class="original-price">${p.original_price:.2f}</span>'
                price_cell += f'<span class="discount-badge">-{discount_pct}%</span>'
        else:
            price_cell = '<span style="color:#ccc">N/A</span>'

        # Deals cell
        deal_parts = []
        if p.deal_tag:
            deal_parts.append(f'<span class="deal-tag">{p.deal_tag}</span>')
        if p.delivery:
            deal_parts.append(f'<span class="delivery-tag">{p.delivery}</span>')
        if p.original_price and p.price and p.original_price > p.price:
            save_amt = p.original_price - p.price
            deal_parts.append(f'<span class="save-tag">Save ${save_amt:.2f}</span>')
        deal_cell = " ".join(deal_parts) if deal_parts else '<span class="no-deal">—</span>'

        # Buy cell
        if p.link:
            buy_cell = f'<span class="buy-link"><a href="{p.link}" target="_blank">Buy Now &#8599;</a></span>'
        else:
            buy_cell = '<span class="no-deal">—</span>'

        rows_html += f"<tr{row_class}><td>{platform_cell}</td><td>{price_cell}</td><td>{deal_cell}</td><td>{buy_cell}</td></tr>\n"

    # Summary row
    price_range = comparison.get("price_range")
    summary = ""
    if price_range:
        summary = f'<div class="price-summary">Price range: ${price_range[0]:.2f} — ${price_range[1]:.2f} across {len(platform_prices)} platforms</div>'

    html = (
        '<table class="price-table">'
        "<thead><tr>"
        "<th>Platform</th><th>Price</th><th>Deals &amp; Shipping</th><th>Link</th>"
        "</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table>"
        f"{summary}"
    )

    with st.expander(f"Where to Buy: {product.name}", expanded=True):
        st.markdown(html, unsafe_allow_html=True)


def display_product_card(rank: int, product: Product):
    """Render a single product recommendation card."""
    # Header
    st.markdown(
        f'<div class="product-header">'
        f'<span class="product-rank">#{rank}</span>'
        f'<span class="product-name">{product.name}</span>'
        f'<span class="product-brand">{product.brand or ""}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Metrics row
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Community Mentions", product.mentions)
    with col_b:
        if product.review_summary and product.review_summary.match_score is not None:
            st.metric("Match Score", f"{product.review_summary.match_score}/10")
    with col_c:
        best = get_best_price(product)
        if best and best.price is not None:
            st.metric("Best Price", f"${best.price:.2f}", delta=best.platform, delta_color="off")

    if product.sources:
        st.caption("Sources: " + " | ".join(product.sources))

    if product.why_recommended:
        st.info(product.why_recommended)

    # Review analysis
    if product.review_summary:
        rs = product.review_summary
        if rs.match_reason:
            st.markdown(f"> **Why it matches you:** {rs.match_reason}")

        with st.expander("View Review Analysis"):
            if rs.overall_rating:
                st.markdown(f"**Overall Rating:** {rs.overall_rating}/5 ({_format_review_count(rs.total_reviews)} reviews)")

            if rs.pros or rs.cons:
                col_pro, col_con = st.columns(2)
                with col_pro:
                    if rs.pros:
                        st.markdown("**Pros**")
                        for pro in rs.pros:
                            st.markdown(f"- :green[+] {pro}")
                with col_con:
                    if rs.cons:
                        st.markdown("**Cons**")
                        for con in rs.cons:
                            st.markdown(f"- :orange[-] {con}")

            if rs.best_for or rs.not_for:
                col_bf, col_nf = st.columns(2)
                with col_bf:
                    if rs.best_for:
                        st.markdown("**Best for:** " + ", ".join(rs.best_for))
                with col_nf:
                    if rs.not_for:
                        st.markdown("**Not for:** " + ", ".join(rs.not_for))

            if rs.purchase_advice:
                st.success(rs.purchase_advice)

    # Ingredient analysis
    if product.ingredient_analysis:
        ia = product.ingredient_analysis
        grade = ia.get("overall_grade", "N/A")
        grade_colors = {"A": "green", "B": "blue", "C": "orange", "D": "red", "F": "red"}
        color = grade_colors.get(grade, "gray")

        st.markdown(f"**Ingredient Grade:** :{color}[**{grade}**] — {ia.get('highlights', '')}")

        with st.expander("View Ingredient Analysis"):
            if ia.get("grade_reason"):
                st.markdown(f"**Assessment:** {ia['grade_reason']}")

            if ia.get("key_actives"):
                st.markdown("**Key Active Ingredients:**")
                for active in ia["key_actives"]:
                    st.markdown(f"- **{active['name']}** — {active.get('function', '')}  \n  _{active.get('benefit_for_user', '')}_")

            if ia.get("avoid_ingredient_check"):
                st.markdown("**Ingredient Avoidance Check:**")
                for check in ia["avoid_ingredient_check"]:
                    icon = ":green[PASS]" if not check.get("found") else ":red[FOUND]"
                    st.markdown(f"- {icon} **{check['ingredient']}**: {check.get('note', '')}")

    # Price comparison table
    if product.prices:
        render_price_table(product)

    st.divider()


def main():
    st.set_page_config(page_title="Price Display Test", page_icon="🧪", layout="wide")
    st.markdown(CARD_CSS, unsafe_allow_html=True)

    st.title("🧪 Price Comparison Display Test")
    st.caption("Using mock data — no API calls")

    products = build_mock_products()

    st.subheader(f"Top {len(products)} Recommendations")
    for i, product in enumerate(products, 1):
        display_product_card(i, product)


if __name__ == "__main__":
    main()
