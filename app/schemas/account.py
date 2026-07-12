from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AccountRead(BaseModel):
    id: int
    display_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
