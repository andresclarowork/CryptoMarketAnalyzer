import os
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv():
        pass


@dataclass
class CryptoConfig:
    symbol: str
    name: str
    ticker: str


@dataclass
class APIConfig:
    primary: str
    fallbacks: List[str]
    rate_limit_delay: float
    timeout: int
    max_retries: int


@dataclass
class EndpointConfig:
    base_url: str
    price_endpoint: Optional[str] = None
    market_data_endpoint: Optional[str] = None
    search_endpoint: Optional[str] = None
    assets_endpoint: Optional[str] = None
    api_key: Optional[str] = None


@dataclass
class NewsConfig:
    search_terms: Dict[str, List[str]]
    time_period: str
    max_articles_per_crypto: int
    min_article_length: int


@dataclass
class SentimentConfig:
    analyzers: List[str]
    confidence_threshold: float
    normalize_scores: bool
    vader: Dict[str, Any]
    textblob: Dict[str, Any]


@dataclass
class ReportConfig:
    output_dir: str
    filename_template: str
    include_timestamp: bool
    auto_open: bool
    styling: Dict[str, str]


@dataclass
class LoggingConfig:
    level: str
    format: str
    file: str
    max_file_size: str
    backup_count: int


@dataclass
class ErrorHandlingConfig:
    max_consecutive_failures: int
    exponential_backoff: bool
    backoff_factor: float
    max_backoff_time: int


@dataclass
class DevelopmentConfig:
    debug_mode: bool
    verbose_output: bool
    save_raw_data: bool
    data_dir: str


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        # Load environment variables from .env file
        try:
            # Try to load .env file with explicit encoding
            env_path = Path(".env")
            if env_path.exists():
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")
            # Continue without .env file
        self._load_config()
        self._validate_config()

    def _load_config(self) -> None:
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                config_data = yaml.safe_load(file)

            self.cryptocurrencies = [
                CryptoConfig(**crypto)
                for crypto in config_data.get("cryptocurrencies", [])
            ]

            apis_config = config_data.get("apis", {})
            self.crypto_api = APIConfig(**apis_config.get("crypto", {}))
            self.news_api = APIConfig(**apis_config.get("news", {}))

            endpoints_config = config_data.get("endpoints", {})
            self.endpoints = {
                name: EndpointConfig(**endpoint_config)
                for name, endpoint_config in endpoints_config.items()
            }

            self.news = NewsConfig(**config_data.get("news", {}))

            self.sentiment = SentimentConfig(**config_data.get("sentiment", {}))

            self.report = ReportConfig(**config_data.get("report", {}))

            self.logging = LoggingConfig(**config_data.get("logging", {}))

            self.error_handling = ErrorHandlingConfig(
                **config_data.get("error_handling", {})
            )

            self.development = DevelopmentConfig(**config_data.get("development", {}))

            # Replace API keys with environment variables
            self._replace_api_keys_with_env_vars()

        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")

    def _replace_api_keys_with_env_vars(self) -> None:
        """Replace API keys in endpoints with environment variables."""
        # Replace NewsAPI key
        if "newsapi" in self.endpoints:
            env_api_key = os.getenv("NEWSAPI_API_KEY")
            if env_api_key:
                self.endpoints["newsapi"].api_key = env_api_key
            else:
                print("Warning: NEWSAPI_API_KEY environment variable not found")
                print("Please set NEWSAPI_API_KEY in your .env file")

        # Replace Guardian API key
        if "guardian" in self.endpoints:
            env_api_key = os.getenv("GUARDIAN_API_KEY")
            if env_api_key:
                self.endpoints["guardian"].api_key = env_api_key
            else:
                print("Warning: GUARDIAN_API_KEY environment variable not found")
                print("Please set GUARDIAN_API_KEY in your .env file")

    def _validate_config(self) -> None:
        if not self.cryptocurrencies:
            raise ValueError("No cryptocurrencies configured")

        if not self.crypto_api.primary:
            raise ValueError("No primary crypto API configured")

        if not self.news_api.primary:
            raise ValueError("No primary news API configured")

        valid_analyzers = ["textblob", "vader"]
        for analyzer in self.sentiment.analyzers:
            if analyzer not in valid_analyzers:
                raise ValueError(f"Invalid sentiment analyzer: {analyzer}")

    def get_crypto_symbols(self) -> List[str]:
        return [crypto.symbol for crypto in self.cryptocurrencies]

    def get_crypto_tickers(self) -> List[str]:
        return [crypto.ticker for crypto in self.cryptocurrencies]

    def get_crypto_by_symbol(self, symbol: str) -> Optional[CryptoConfig]:
        for crypto in self.cryptocurrencies:
            if crypto.symbol.lower() == symbol.lower():
                return crypto
        return None

    def get_endpoint(self, name: str) -> Optional[EndpointConfig]:
        return self.endpoints.get(name)

    def get_search_terms(self, crypto_symbol: str) -> List[str]:
        return self.news.search_terms.get(crypto_symbol, [])

    def is_debug_mode(self) -> bool:
        return self.development.debug_mode

    def get_output_dir(self) -> str:
        return self.report.output_dir

    def get_log_file(self) -> str:
        return self.logging.file


_config: Optional[Config] = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    global _config
    _config = Config()
    return _config
