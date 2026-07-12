from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SettingsRead(BaseModel):
    font: str
    language: str
    theme: str

    model_config = ConfigDict(from_attributes=True)


class SettingsUpdate(BaseModel):
    font: str | None = None
    language: str | None = None
    theme: str | None = None

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "SettingsUpdate":
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self

    @field_validator("font")
    @classmethod
    def validate_font(cls, value: str | None) -> str | None:
        if value is not None and value not in ("serif", "sans-serif"):
            raise ValueError("font must be 'serif' or 'sans-serif'")
        return value

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str | None) -> str | None:
        if value is not None and value not in ("ru", "en", "auto"):
            raise ValueError("language must be 'ru', 'en', or 'auto'")
        return value

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, value: str | None) -> str | None:
        if value is not None and value not in ("dark", "light", "auto"):
            raise ValueError("theme must be 'dark', 'light', or 'auto'")
        return value
