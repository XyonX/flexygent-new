"""
Configuration for the Cloudflare LLM Proxy.
Reads settings from environment variables (via .env file).
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cloudflare_account_id: str = ""
    cloudflare_api_token: str = ""
    admin_api_key: str = ""
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
