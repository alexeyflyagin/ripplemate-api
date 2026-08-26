from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SettingsRead(BaseModel):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingsUpdate(BaseModel):
    ...
