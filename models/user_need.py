"""User need data model."""

from pydantic import BaseModel


class UserNeed(BaseModel):
    product_type: str
    skin_type: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    concerns: list[str] = []
    avoid_ingredients: list[str] = []
    texture_preference: str | None = None
