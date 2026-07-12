from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class CardRead(BaseModel):
    id: int
    term: str
    category_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CardListResponse(BaseModel):
    items: list[CardRead]
    total: int
    limit: int
    offset: int


class CardCreate(BaseModel):
    term: str
    category_id: int | None = None

    @field_validator("term")
    @classmethod
    def term_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("term cannot be blank")
        if len(value) > 255:
            raise ValueError("term cannot be longer than 255 characters")
        return value


class CardUpdate(BaseModel):
    term: str | None = None
    category_id: int | None = None

    @model_validator(mode="after")
    def reject_explicit_null_term(self) -> "CardUpdate":
        if "term" in self.model_fields_set and self.term is None:
            raise ValueError("term cannot be null")
        return self

    @field_validator("term")
    @classmethod
    def term_not_blank(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("term cannot be blank")
            if len(value) > 255:
                raise ValueError("term cannot be longer than 255 characters")
        return value
