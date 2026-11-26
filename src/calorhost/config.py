import logging
import os
from enum import Enum


class LogLevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG


class Config:
    """
    Base configuration class for the application, used to store env variables
    """

    @property
    def log_level(self) -> LogLevel:
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        return LogLevel[log_level]

    @property
    def search_api_url(self) -> str:
        return os.environ.get("SEARCH_API_URL", "https://search.openfoodfacts.org/search")

    @property
    def user_agent(self) -> str:
        return os.environ.get("USER_AGENT", "CalorHost/0.1.0")

    @property
    def country(self) -> str:
        return os.environ.get("COUNTRY", "australia")
