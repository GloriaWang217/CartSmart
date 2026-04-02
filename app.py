"""AI Beauty Advisor - Streamlit entry point."""

import streamlit as st

from core.conversation import get_diagnosis_response
from core.orchestrator import run_community_research, run_price_research, run_analysis
from shopping.price_comparator import compare_prices, get_best_price


def _escape_dollars(text: str) -> str:
    """Escape $ signs so Streamlit doesn't render them as LaTeX."""
    return text.replace("$", "\\$")


CARD_CSS = """
<style>
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


def _format_review_count(count: int | None) -> str:
    if count is None:
        return "N/A"
    if count >= 1000:
        value = count / 1000
        if value == int(value):
            return f"{int(value)}k"
        return f"{value:.1f}k"
    return str(count)


def render_price_table(product):
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
        deal_cell = " ".join(deal_parts) if deal_parts else '<span class="no-deal">&mdash;</span>'

        # Size cell
        size_cell = f'<span>{p.size}</span>' if p.size else '<span style="color:#ccc">&mdash;</span>'

        # Unit price cell
        if p.unit_price is not None:
            unit_price_cell = f'<span>${p.unit_price:.2f}/oz</span>'
        else:
            unit_price_cell = '<span style="color:#ccc">&mdash;</span>'

        # Buy cell
        if p.link:
            buy_cell = f'<span class="buy-link"><a href="{p.link}" target="_blank">Buy Now &#8599;</a></span>'
        else:
            buy_cell = '<span class="no-deal">&mdash;</span>'

        rows_html += f"<tr{row_class}><td>{platform_cell}</td><td>{size_cell}</td><td>{price_cell}</td><td>{unit_price_cell}</td><td>{deal_cell}</td><td>{buy_cell}</td></tr>\n"

    # Summary
    price_range = comparison.get("price_range")
    summary = ""
    if price_range:
        summary = f'<div class="price-summary">Price range: ${price_range[0]:.2f} &mdash; ${price_range[1]:.2f} across {len(platform_prices)} platforms</div>'

    html = (
        '<table class="price-table">'
        "<thead><tr>"
        "<th>Platform</th><th>Size</th><th>Price</th><th>Unit Price</th><th>Deals &amp; Shipping</th><th>Link</th>"
        "</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table>"
        f"{summary}"
    )

    with st.expander(f"Where to Buy: {product.name}", expanded=True):
        st.markdown(html, unsafe_allow_html=True)
        if product.official_link:
            st.markdown(f"🔗 [View on official {product.brand or 'brand'} website]({product.official_link})")


def display_product_card(rank: int, product):
    """Render a single product recommendation card with price comparison."""
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

            if ia.get("potential_concerns"):
                st.markdown("**Potential Concerns:**")
                for concern in ia["potential_concerns"]:
                    severity = concern.get("severity", "low")
                    icon = {"low": "🟡", "moderate": "🟠", "high": "🔴"}.get(severity, "🟡")
                    st.markdown(f"- {icon} **{concern['name']}** ({severity}): {concern.get('concern', '')}")

            if ia.get("warnings"):
                st.warning(ia["warnings"])

    # Price comparison table
    if product.prices:
        render_price_table(product)

    st.divider()


def main():
    st.set_page_config(page_title="AI Beauty Advisor", page_icon="✨", layout="wide")
    st.markdown(CARD_CSS, unsafe_allow_html=True)
    st.title("✨ AI Beauty Advisor")
    st.caption("Your AI-powered skincare & beauty shopping assistant")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_need" not in st.session_state:
        st.session_state.user_need = None
    if "diagnosis_complete" not in st.session_state:
        st.session_state.diagnosis_complete = False
    if "candidates" not in st.session_state:
        st.session_state.candidates = None
    if "value_picks" not in st.session_state:
        st.session_state.value_picks = None
    if "price_tier" not in st.session_state:
        st.session_state.price_tier = ""
    if "research_done" not in st.session_state:
        st.session_state.research_done = False
    if "price_done" not in st.session_state:
        st.session_state.price_done = False
    if "analysis_done" not in st.session_state:
        st.session_state.analysis_done = False

    # Show greeting if no messages yet
    if not st.session_state.messages:
        greeting = (
            "Hi there! 👋 I'm your beauty advisor. "
            "Tell me what product you're looking for, and I'll help you find the best one!\n\n"
            "For example: \"I'm looking for a moisturizer for dry skin\" or \"想找一个平价防晒霜\""
        )
        st.session_state.messages.append({"role": "assistant", "content": greeting})

    # Sidebar: show extracted needs
    if st.session_state.user_need:
        with st.sidebar:
            st.subheader("📋 Your Needs")
            st.json(st.session_state.user_need.model_dump(exclude_none=True))

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(_escape_dollars(msg["content"]))

    # --- Stage 1: Diagnosis conversation ---
    if not st.session_state.diagnosis_complete:
        if user_input := st.chat_input("Tell me what you're looking for..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    api_messages = [
                        m for m in st.session_state.messages
                        if not (m["role"] == "assistant" and m == st.session_state.messages[0])
                    ]
                    display_text, user_need = get_diagnosis_response(api_messages)

                st.markdown(_escape_dollars(display_text))

            st.session_state.messages.append({"role": "assistant", "content": display_text})

            if user_need:
                st.session_state.user_need = user_need
                st.session_state.diagnosis_complete = True
                st.rerun()

    # --- Stage 2: Community research ---
    elif not st.session_state.research_done:
        status = st.status("Researching the best products for you...", expanded=True)
        with status:
            st.write("Searching Reddit communities & professional reviews...")
            candidates, price_tier = run_community_research(st.session_state.user_need)
            if price_tier:
                st.write(f"Budget tier detected: **{price_tier}** (for {st.session_state.user_need.product_type})")
            st.write(f"Found {len(candidates)} recommended products!")
            status.update(label=f"Research complete — {len(candidates)} products found!", state="complete")

        st.session_state.candidates = candidates
        st.session_state.price_tier = price_tier
        st.session_state.research_done = True
        st.rerun()

    # --- Stage 3: Price research ---
    elif not st.session_state.price_done:
        candidates = st.session_state.candidates
        if candidates:
            status = st.status("Comparing prices across Amazon, Sephora, Target, Walmart, Ulta...", expanded=True)
            with status:
                st.write(f"Searching {min(len(candidates), 5)} products across retail platforms...")
                in_budget, value_picks = run_price_research(candidates, st.session_state.user_need)
                st.write(f"Found {len(in_budget)} products in budget, {len(value_picks)} value picks!")
                status.update(label="Price comparison complete!", state="complete")
            st.session_state.candidates = in_budget
            st.session_state.value_picks = value_picks

        st.session_state.price_done = True
        st.rerun()

    # --- Stage 3b+3c: Review + Ingredient analysis (combined, parallel) ---
    elif not st.session_state.analysis_done:
        candidates = st.session_state.candidates
        if candidates:
            status = st.status("Analyzing reviews & ingredients...", expanded=True)
            with status:
                st.write(f"Running review + ingredient analysis in parallel for top {min(len(candidates), 5)} products...")
                candidates = run_analysis(candidates, st.session_state.user_need)
                st.write("Analysis complete!")
                status.update(label="Review & ingredient analysis complete!", state="complete")
            st.session_state.candidates = candidates

        st.session_state.analysis_done = True
        st.rerun()

    # --- Display results ---
    else:
        candidates = st.session_state.candidates
        value_picks = st.session_state.value_picks or []

        if candidates:
            need = st.session_state.user_need
            budget_str = ""
            if need.budget_min or need.budget_max:
                budget_str = f" (\\${int(need.budget_min or 0)}-\\${int(need.budget_max or 0)})"

            st.subheader(f"Top {len(candidates)} Recommendations{budget_str}")
            st.caption("Based on community research, review analysis, ingredient analysis & cross-platform pricing")

            for i, product in enumerate(candidates, 1):
                display_product_card(i, product)

            # Value picks section
            if value_picks:
                st.divider()
                st.subheader("Great Value Picks")
                st.caption("These products are below your budget but highly recommended by the community — worth considering!")
                for i, product in enumerate(value_picks, 1):
                    display_product_card(i, product)

        else:
            st.warning("Sorry, I couldn't find enough recommendations. Try broadening your search criteria.")

        # Reset button
        if st.button("Start a new search"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()
