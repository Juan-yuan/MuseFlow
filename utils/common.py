"""Shared LLM client. Secrets come from .env via Config (same pattern as Knowledge-Graph)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_openai import ChatOpenAI

from utils.config import Config

conf = Config()

my_llm = ChatOpenAI(
    api_key=conf.require("MODEL_API_KEY"),
    base_url=conf.require("MODEL_BASE_URL"),
    model=conf.require("MODEL_NAME"),
)
