"""Shared Azure OpenAI client for use across the application."""
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from agents import OpenAIChatCompletionsModel

# Create Azure OpenAI client with Entra ID authentication
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

azure_client = AsyncAzureOpenAI(
    azure_ad_token_provider=token_provider,
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
)

# Model for use with agents - uses Chat Completions API
MODEL = OpenAIChatCompletionsModel(
    model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    openai_client=azure_client,
)
