from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class CardRead(BaseModel):
    id: int
    term: str
    category_id: str | None = None
    created_at: datetime
    is_favorite: bool

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_category_public_id(cls, data):
        # data — ORM Card или dict. Заменяем int category_id на public_id категории.
        if isinstance(data, dict):
            return data

        category = getattr(data, "category", None)
        payload = {
            "id": data.id,
            "term": data.term,
            "created_at": data.created_at,
            "is_favorite": data.is_favorite,
            "category_id": category.public_id if category is not None else None,
        }
        return payload


class CardListResponse(BaseModel):
    items: list[CardRead]
    total: int
    limit: int
    offset: int


class CardCreate(BaseModel):
    term: str
    category_id: str | None = None

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
    category_id: str | None = None
    is_favorite: bool | None = None

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
