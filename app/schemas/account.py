from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr


class AccountRead(BaseModel):
    id: str = Field(validation_alias="public_id")
    display_name: str
    email: EmailStr
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AccountExists(BaseModel):
    exists: bool
