"""Ingredient master document models."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NutritionPer100g(BaseModel):
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


class IngredientMaster(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_name: str
    display_name: str
    aliases: list[str] = Field(default_factory=list)
    nutrition_per_100g: NutritionPer100g | None
    density_g_per_ml: Decimal | None = None

    @field_validator("canonical_name")
    @classmethod
    def _normalize_canonical_name(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("canonical_name must not be empty")
        return normalized

    @field_validator("display_name")
    @classmethod
    def _normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("display_name must not be empty")
        return normalized

    @field_validator("aliases")
    @classmethod
    def _normalize_aliases(cls, value: list[str]) -> list[str]:
        return [alias.strip().lower() for alias in value if alias.strip()]

    @field_validator("density_g_per_ml")
    @classmethod
    def _validate_density(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("density_g_per_ml must be positive")
        return value
