"""
Centralized Application Configuration

Uses Pydantic Settings to provide type-safe, validated configuration.
All settings are loaded from environment variables or .env file.

USAGE:
    from .config.config import settings
    
    endpoint = settings.azure_openai_endpoint
    port = settings.server_port
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.
    
    ARCHITECTURE NOTES:
    - Required fields (no default) will fail fast at startup if missing
    - Optional fields (with default or | None) allow graceful degradation
    - validation_alias maps .env variable names to Python property names
    """
    
    # Pydantic v2 settings config
    # env_file path is relative to CWD (where uvicorn runs from = src/)
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )
    
    # =========================================================================
    # Azure OpenAI (required for app to function)
    # =========================================================================
    azure_openai_endpoint: str = Field(validation_alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(validation_alias="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment: str = Field(
        default="gpt-4o", 
        validation_alias="AZURE_OPENAI_DEPLOYMENT"
    )
    
    # Optional API key - if not set, uses DefaultAzureCredential (Entra ID)
    azure_openai_api_key: str | None = Field(
        default=None, 
        validation_alias="AZURE_OPENAI_API_KEY"
    )
    
    # =========================================================================
    # Application Insights / Telemetry (optional - app runs without it)
    # =========================================================================
    application_insights_connection_string: str | None = Field(
        default=None,
        validation_alias="APPLICATIONINSIGHTS_CONNECTION_STRING",
    )
    
    # =========================================================================
    # Application Metadata
    # =========================================================================
    app_name: str = Field(default="OpenAI Airlines Demo")
    environment: str = Field(default="dev", validation_alias="APP_ENVIRONMENT")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    
    # =========================================================================
    # Server Configuration
    # =========================================================================
    server_host: str = Field(default="0.0.0.0", validation_alias="SERVER_HOST")
    server_port: int = Field(default=8000, validation_alias="SERVER_PORT")


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached singleton of Settings.
    
    The @lru_cache ensures we only read .env once.
    Subsequent calls return the cached object.
    """
    return Settings()


# Singleton instance for easy import
settings = get_settings()


