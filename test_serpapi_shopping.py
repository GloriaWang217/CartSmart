"""Quick test: call SerpAPI Google Shopping for one product and print raw results.
Costs 1 SerpAPI call.
"""

import os
from serpapi import GoogleSearch

API_KEY = os.getenv("SERPAPI_KEY", "")

params = {
    "engine": "google_shopping",
    "q": "CeraVe Moisturizing Cream",
    "gl": "us",
    "hl": "en",
    "api_key": API_KEY,
}

print("Calling SerpAPI google_shopping...")
search = GoogleSearch(params)
results = search.get_dict()

# Check for errors
if "error" in results:
    print(f"ERROR: {results['error']}")
elif "search_metadata" in results:
    print(f"Status: {results['search_metadata'].get('status')}")

shopping = results.get("shopping_results", [])
print(f"Shopping results count: {len(shopping)}")

if shopping:
    for i, item in enumerate(shopping[:3]):
        print(f"\n--- Result {i+1} ---")
        print(f"  title: {item.get('title')}")
        print(f"  source: {item.get('source')}")
        print(f"  price: {item.get('price')}")
        print(f"  extracted_price: {item.get('extracted_price')} (type: {type(item.get('extracted_price')).__name__})")
        print(f"  old_price: {item.get('old_price')}")
        print(f"  extracted_old_price: {item.get('extracted_old_price')}")
        print(f"  link: {item.get('link', 'N/A')[:80]}")
        print(f"  rating: {item.get('rating')}")
        print(f"  reviews: {item.get('reviews')}")
        print(f"  tag: {item.get('tag')}")
        print(f"  delivery: {item.get('delivery')}")
else:
    print("\nNo shopping_results found. Full response keys:")
    print(list(results.keys()))
    # Print first 500 chars of response for debugging
    import json
    print("\nResponse preview:")
    print(json.dumps(results, indent=2)[:1000])
