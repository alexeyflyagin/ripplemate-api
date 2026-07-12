from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class CategoryRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name cannot be blank")
        if len(value) > 24:
            raise ValueError("name cannot be longer than 24 characters")
        return value


class CategoryUpdate(BaseModel):
    name: str | None = None

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "CategoryUpdate":
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("name cannot be blank")
            if len(value) > 24:
                raise ValueError("name cannot be longer than 24 characters")
        return value
