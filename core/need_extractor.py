"""Extract structured user needs from conversation."""

import json
import re

from models.user_need import UserNeed


def parse_needs_from_response(response_text: str) -> UserNeed | None:
    """Try to extract UserNeed from the LLM response containing <needs_json> tags."""
    match = re.search(r"<needs_json>\s*(\{.*?\})\s*</needs_json>", response_text, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group(1))
        return UserNeed(
            product_type=data.get("product_type", ""),
            skin_type=data.get("skin_type"),
            budget_min=data.get("budget_min"),
            budget_max=data.get("budget_max"),
            concerns=data.get("concerns", []),
            avoid_ingredients=data.get("avoid_ingredients", []),
            texture_preference=data.get("texture_preference"),
        )
    except (json.JSONDecodeError, ValueError):
        return None


def strip_needs_json(response_text: str) -> str:
    """Remove the <needs_json> block from the response so the user doesn't see it."""
    return re.sub(r"\s*<needs_json>.*?</needs_json>\s*", "", response_text, flags=re.DOTALL).strip()
