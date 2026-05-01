from pydantic_settings import BaseSettings , SettingsConfigDict


class Settings (BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8")

    openrouter_api_key:str
    openrouter_base_url:str="https://openrouter.ai/api/v1"
    default_model:str="nvidia/nemotron-3-super-120b-a12b:free"


settings = Settings()