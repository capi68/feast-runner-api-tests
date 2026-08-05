"""Configuration management for the test framework.

Provides environment-aware settings loaded from config.json.
Follows singleton pattern — import `config` from this module.
"""


import os
import json
from pathlib import Path


class Config:
    """Environment configuration for the test framework."""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "local").lower()
        self._data = self._load_config()

    def _load_config(self) -> dict:
        config_path = Path(__file__).parent / "config.json"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                full = json.load(f)
                return full.get("environments", {}).get(self.environment, {})
        return {}

    @property
    def base_url(self) -> str:
        return self._data.get("base_url", "http://localhost:3010")

    @property
    def admin_restaurant_email(self) -> str:
        return self._data.get("admin_restaurant_email", "admin@feastrunner.com")

    @property
    def admin_restaurant_password(self) -> str:
        return self._data.get("admin_restaurant_password", "Restaurant123!")

    @property
    def admin_customer_email(self) -> str:
        return self._data.get("admin_customer_email", "customer@feastrunner.com")

    @property
    def admin_customer_password(self) -> str:
        return self._data.get("admin_customer_password", "Customer123!")

    @property
    def admin_courier_email(self) -> str:
        return self._data.get("admin_courier_email", "courier@feastrunner.com")

    @property
    def admin_courier_password(self) -> str:
        return self._data.get("admin_courier_password", "Courier123!")


config = Config()
