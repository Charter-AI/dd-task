"""Configuration settings for Ascentra."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"

    LLM_TEMPERATURE: float = 0.0
    LLM_TIMEOUT_S: float = 60.0

    @property
    def is_configured(self) -> bool:
        return bool(
            self.AZURE_OPENAI_ENDPOINT
            and self.AZURE_OPENAI_API_KEY
            and self.AZURE_OPENAI_DEPLOYMENT
        )


settings = Settings()


