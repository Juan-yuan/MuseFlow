import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.path_utils import get_file_path


def _load_env() -> None:
    # Reload on every Config() so edits to .env are picked up without a full process restart
    load_dotenv(get_file_path(".env"), override=True)
    load_dotenv(get_file_path("common/.env"), override=True)


_load_env()


class Config:
    def __init__(self):
        _load_env()
        self.MODEL_API_KEY = os.getenv("MODEL_API_KEY")
        self.MODEL_BASE_URL = os.getenv("MODEL_BASE_URL")
        self.MODEL_NAME = os.getenv("MODEL_NAME")

    def require(self, key: str) -> str:
        value = getattr(self, key, None) or os.getenv(key)
        if not value:
            raise RuntimeError(f"{key} is missing. Set it in .env (see .env.example).")
        return value

    def require_json(self, key: str):
        return json.loads(self.require(key))

    def get_json(self, key: str, default=None):
        raw = getattr(self, key, None) or os.getenv(key)
        if not raw:
            return default
        return json.loads(raw)


if __name__ == "__main__":
    conf = Config()
    print("MODEL_NAME=", conf.MODEL_NAME)
    print("MODEL_BASE_URL=", conf.MODEL_BASE_URL)
    print("MODEL_API_KEY set=", bool(conf.MODEL_API_KEY))
