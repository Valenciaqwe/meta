from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str
    openai_api_key: str
    openai_base_url: str = "https://openrouter.ai/api/v1"
    openai_model: str = "google/gemma-3-27b-it:free"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
