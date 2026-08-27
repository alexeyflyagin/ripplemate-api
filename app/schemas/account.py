from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AccountRead(BaseModel):
    id: str = Field(validation_alias="public_id")
    display_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
