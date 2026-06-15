"""Measurement models."""

from __future__ import annotations

from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class Quantity(BaseModel):
    """Canonical quantity persisted with a recipe ingredient."""

    model_config = ConfigDict(extra="forbid")

    value: Decimal | None
    unit: str

    @field_validator("unit")
    @classmethod
    def _normalize_unit(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("unit must not be empty")
        return normalized

    @model_validator(mode="after")
    def _validate_to_taste(self) -> Self:
        if self.value is None and self.unit != "to_taste":
            raise ValueError("unit must be to_taste when value is None")
        return self
