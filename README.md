<div align="center">

# CartSmart - AI Beauty Advisor

**Your AI-powered skincare & beauty shopping assistant**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude API](https://img.shields.io/badge/Claude_API-191919?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)

<br/>

<img src="https://img.shields.io/badge/status-active_development-brightgreen?style=flat-square" alt="Status"/>

---

*Tell me what you need, and I'll find the perfect product for you.*

</div>

## What is CartSmart?

CartSmart is an AI-driven beauty shopping assistant that helps you find the best skincare and beauty products through a 3-stage intelligent pipeline:

```
💬 Chat with AI  →  🔍 Community Research  →  🛒 Smart Recommendations
```

Instead of spending hours browsing Reddit threads, comparing prices across retailers, and decoding ingredient lists — CartSmart does it all for you in under 25 seconds.

## How It Works

### Stage 1: Conversation Diagnosis
A natural chat interface powered by Claude AI extracts your specific needs:
- Skin type & concerns
- Budget range
- Ingredient preferences / allergies
- Texture & product type preferences

### Stage 2: Community Research
Automatically searches real user discussions from:
- **Reddit** — r/SkincareAddiction, r/AsianBeauty, r/MakeupAddiction
- **Professional review sites** & dermatologist articles

Uses LLM to extract the most frequently recommended products from real user experiences.

### Stage 3: Product Research & Recommendations
For each candidate product, CartSmart runs three analyses **in parallel**:

| Analysis | What it does |
|----------|-------------|
| **Price Comparison** | Cross-platform pricing from Amazon, Sephora, Target, Walmart, Ulta |
| **Review Analysis** | AI-powered pros/cons extraction, personalized match scoring (1-10) |
| **Ingredient Analysis** | Safety grading, key actives identification, allergy/avoidance checks |

The final output is a **Top 5 ranked recommendation** with detailed cards:

<div align="center">

```
┌─────────────────────────────────────────────────┐
│  #1  CeraVe Moisturizing Cream                  │
│      Community Mentions: 47  |  Match: 9/10     │
│                                                  │
│  ✅ Why it matches: Fragrance-free, ceramide-    │
│     rich formula ideal for dry, sensitive skin   │
│                                                  │
│  ┌─────────┬────────┬─────────┬───────────────┐  │
│  │Platform │ Price  │ Deals   │    Link       │  │
│  ├─────────┼────────┼─────────┼───────────────┤  │
│  │Amazon   │$15.99  │Free Ship│  [Buy Now →]  │  │
│  │Target   │$16.49  │  -10%   │  [Buy Now →]  │  │
│  │Walmart  │$14.97  │ Best ⭐ │  [Buy Now →]  │  │
│  └─────────┴────────┴─────────┴───────────────┘  │
│                                                  │
│  Ingredient Grade: A                             │
│  Key Actives: Ceramides, Hyaluronic Acid, MVE   │
└─────────────────────────────────────────────────┘
```

</div>

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit (conversational UI with streaming) |
| **LLM** | Claude API (primary) / OpenAI API (backup) |
| **Search** | SerpAPI (Google Search + Google Shopping) |
| **Scraping** | requests + BeautifulSoup |
| **Data Models** | Pydantic |
| **Caching** | SQLite |
| **Async** | asyncio + aiohttp (parallel searches) |

## Project Structure

```
CartSmart/
├── app.py                          # Streamlit entry point & UI rendering
├── core/
│   ├── conversation.py             # Multi-turn dialog state management
│   ├── need_extractor.py           # Extract structured needs from chat
│   ├── orchestrator.py             # 3-stage pipeline orchestration
│   └── prompts.py                  # All LLM prompts (centralized)
├── research/
│   ├── community_researcher.py     # Reddit & review site research
│   ├── page_fetcher.py             # Web page content fetching
│   └── recommendation_extractor.py # LLM-based product extraction
├── shopping/
│   ├── price_searcher.py           # Google Shopping search
│   └── price_comparator.py         # Cross-platform price comparison
├── analysis/
│   ├── review_analyzer.py          # AI-driven review analysis
│   ├── review_fetcher.py           # Review data fetching
│   └── ingredient_analyzer.py      # Ingredient safety & efficacy analysis
├── models/
│   ├── user_need.py                # User need data model
│   └── product.py                  # Product, PriceInfo, ReviewAnalysis models
├── data/
│   ├── ingredients.json            # Ingredient database (top 200)
│   └── subreddits.json             # Reddit community config
└── utils/
    ├── cache.py                    # SQLite search result cache
    ├── config.py                   # Config management
    └── async_utils.py              # Async parallel utilities
```

## Getting Started

### Prerequisites
- Python 3.11+
- API keys for: [Anthropic (Claude)](https://console.anthropic.com/), [SerpAPI](https://serpapi.com/)

### Installation

```bash
# Clone the repo
git clone https://github.com/GloriaWang217/CartSmart.git
cd CartSmart

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
SERPAPI_KEY=your_serpapi_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here    # Optional, backup LLM
```

### Run

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Performance

| Stage | Target | Description |
|-------|--------|-------------|
| Community Research | < 8s | Reddit + review site search & extraction |
| Price Comparison | < 5s | Cross-platform Google Shopping lookup |
| Review + Ingredient Analysis | < 10s | Parallel AI analysis |
| **First result visible** | **< 15s** | User sees the first recommendation |
| **All results loaded** | **< 25s** | Complete Top 5 with full details |

## License

This project is for educational and personal use.

---

<div align="center">

**Built with Claude AI + Streamlit**

</div>
