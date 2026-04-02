"""Dialog state management for multi-turn need diagnosis."""

from openai import OpenAI

from core.prompts import DIAGNOSIS_SYSTEM_PROMPT
from core.need_extractor import parse_needs_from_response, strip_needs_json
from models.user_need import UserNeed
from utils.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def get_diagnosis_response(messages: list[dict]) -> tuple[str, UserNeed | None]:
    """Send conversation to OpenAI and get a diagnosis response.

    Args:
        messages: List of {"role": "user"/"assistant", "content": "..."} dicts.

    Returns:
        (display_text, user_need) — display_text is the response to show the user.
        user_need is non-None when the LLM has gathered enough info.
    """
    api_messages = [{"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT}] + messages

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        messages=api_messages,
    )

    raw_text = response.choices[0].message.content
    user_need = parse_needs_from_response(raw_text)
    display_text = strip_needs_json(raw_text)

    return display_text, user_need
