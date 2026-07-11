import uuid

from fastapi_users import schemas
from pydantic import field_validator


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    display_name: str

    @field_validator("display_name")
    @classmethod
    def display_name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display_name cannot be blank")
        if len(value) > 32:
            raise ValueError("display_name cannot be longer than 32 characters")
        return value

    def create_update_dict(self) -> dict:
        data = super().create_update_dict()
        data.pop("display_name", None)
        return data

    def create_update_dict_superuser(self) -> dict:
        data = super().create_update_dict_superuser()
        data.pop("display_name", None)
        return data
