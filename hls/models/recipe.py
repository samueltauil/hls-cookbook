"""Recipe document models."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from importlib import import_module
from typing import Any, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hls.models.units import Quantity


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _new_ulid(prefix: str) -> str:
    try:
        ulid_module = import_module("python_ulid")
    except ModuleNotFoundError:
        ulid_module = import_module("ulid")
    ulid_class = cast(type[Any], ulid_module.ULID)
    return f"{prefix}_{ulid_class()}"


def _new_recipe_id() -> str:
    return _new_ulid("rcp")


class RecipeStatus(StrEnum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"


class Contributor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    display_name: str = ""


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cuisine: str = ""
    course: str = "main"
    dietary_tags: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    difficulty: str = "easy"
    occasion: list[str] = Field(default_factory=list)


class Yield(BaseModel):
    model_config = ConfigDict(extra="forbid")

    servings: int = Field(gt=0)
    notes: str = ""


class Times(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prep_min: int = Field(default=0, ge=0)
    cook_min: int = Field(default=0, ge=0)
    rest_min: int = Field(default=0, ge=0)
    total_min: int = Field(default=0, ge=0)


class Source(BaseModel):
    """Attribution for adapted or inspired-by recipes."""

    model_config = ConfigDict(extra="forbid")

    attribution: str = ""
    url: str = ""


class NutritionFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calories_kcal: Decimal | None = None
    protein_g: Decimal | None = None
    fat_g: Decimal | None = None
    carbs_g: Decimal | None = None

    @field_validator("calories_kcal", "protein_g", "fat_g", "carbs_g")
    @classmethod
    def _validate_non_negative(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("nutrition values must be non-negative")
        return value


class IngredientQuantity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: Quantity | None = None
    us: Quantity | None = None
    as_entered: str

    @field_validator("as_entered")
    @classmethod
    def _validate_as_entered(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("as_entered must not be empty")
        return normalized


class Ingredient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    quantity: IngredientQuantity
    notes: str = ""
    section: str = "main"

    @field_validator("name", "section")
    @classmethod
    def _validate_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be empty")
        return normalized


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order: int = Field(gt=0)
    text: str

    @field_validator("text")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("step text must not be empty")
        return normalized


class Photo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    blob_url: str
    caption: str = ""
    is_hero: bool = False


class ReviewNote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor: str
    action: str
    comment: str = ""
    timestamp: datetime = Field(default_factory=_utc_now)


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submitted_at: datetime | None = None
    reviewer_id: str | None = None
    review_notes: list[ReviewNote] = Field(default_factory=list)


class BookMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    included_in_editions: list[str] = Field(default_factory=list)


class Recipe(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(default_factory=_new_recipe_id)
    status: RecipeStatus
    title: str
    slug: str
    summary: str = ""
    contributor: Contributor = Field(default_factory=Contributor)
    classification: Classification
    recipe_yield: Yield = Field(alias="yield")
    times: Times
    ingredients: list[Ingredient] = Field(default_factory=list)
    steps: list[Step] = Field(default_factory=list)
    photos: list[Photo] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    tips: str = ""
    storage: str = ""
    pairings: str = ""
    source: Source | None = None
    locale: str = "en"
    nutrition_per_serving: NutritionFacts | None = None
    locales: dict[str, dict[str, Any]] = Field(default_factory=dict)
    review: Review = Field(default_factory=Review)
    book: BookMetadata = Field(default_factory=BookMetadata)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    etag: str | None = Field(default=None, alias="_etag")

    @field_validator("title", "slug")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be empty")
        return normalized

    @model_validator(mode="after")
    def _assert_valid_status(self) -> Self:
        if not isinstance(self.status, RecipeStatus):
            raise ValueError("status must be a RecipeStatus")
        return self
