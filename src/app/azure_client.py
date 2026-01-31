"""Shared Azure OpenAI client for use across the application."""
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from agents import OpenAIChatCompletionsModel

from .config import settings

# Create Azure OpenAI client with Entra ID authentication
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

azure_client = AsyncAzureOpenAI(
    azure_ad_token_provider=token_provider,
    api_version=settings.azure_openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint,
)

# Model for use with agents - uses Chat Completions API
MODEL = OpenAIChatCompletionsModel(
    model=settings.azure_openai_deployment,
    openai_client=azure_client,
)
