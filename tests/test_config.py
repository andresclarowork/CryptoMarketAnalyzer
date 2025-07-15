import pytest
import tempfile
import yaml
from pathlib import Path

from src.utils.config import Config, get_config


class TestConfig:
    def test_valid_config(self):
        config = get_config()
        assert config is not None
        assert hasattr(config, "cryptocurrencies")
        assert hasattr(config, "crypto_api")
        assert hasattr(config, "news_api")

    def test_get_crypto_symbols(self):
        config = get_config()
        symbols = config.get_crypto_symbols()
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert all(isinstance(symbol, str) for symbol in symbols)

    def test_get_crypto_tickers(self):
        config = get_config()
        tickers = config.get_crypto_tickers()
        assert isinstance(tickers, list)
        assert len(tickers) > 0
        assert all(isinstance(ticker, str) for ticker in tickers)

    def test_get_crypto_by_symbol(self):
        config = get_config()
        crypto = config.get_crypto_by_symbol("bitcoin")
        assert crypto is not None
        assert crypto.symbol == "bitcoin"
        assert crypto.name == "Bitcoin"
        assert crypto.ticker == "BTC"

    def test_get_endpoint(self):
        config = get_config()
        endpoint = config.get_endpoint("coingecko")
        assert endpoint is not None
        assert hasattr(endpoint, "base_url")
        assert hasattr(endpoint, "price_endpoint")

    def test_get_search_terms(self):
        config = get_config()
        terms = config.get_search_terms("bitcoin")
        assert isinstance(terms, list)
        assert len(terms) > 0
        assert all(isinstance(term, str) for term in terms)

    def test_invalid_config_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_config_path = f.name

        try:
            with pytest.raises(ValueError):
                Config(temp_config_path)
        finally:
            Path(temp_config_path).unlink(missing_ok=True)

    def test_missing_config_file(self):
        with pytest.raises(FileNotFoundError):
            Config("nonexistent_config.yaml")

    def test_validation(self):
        config = get_config()
        # Should not raise any exceptions
        assert config.cryptocurrencies is not None
        assert config.crypto_api.primary is not None
        assert config.news_api.primary is not None


class TestConfigValidation:

    def test_empty_cryptocurrencies(self):
        config_data = {
            "cryptocurrencies": [],
            "apis": {
                "crypto": {"primary": "coingecko", "fallbacks": []},
                "news": {"primary": "newsapi", "fallbacks": []},
            },
            "endpoints": {},
            "news": {"search_terms": {}},
            "sentiment": {"analyzers": ["textblob"]},
            "report": {"output_dir": "reports"},
            "logging": {"level": "INFO"},
            "error_handling": {},
            "development": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name

        try:
            with pytest.raises(ValueError, match="No cryptocurrencies configured"):
                Config(temp_config_path)
        finally:
            Path(temp_config_path).unlink(missing_ok=True)

    def test_missing_primary_api(self):
        config_data = {
            "cryptocurrencies": [
                {"symbol": "bitcoin", "name": "Bitcoin", "ticker": "BTC"}
            ],
            "apis": {
                "crypto": {"primary": "", "fallbacks": []},
                "news": {"primary": "newsapi", "fallbacks": []},
            },
            "endpoints": {},
            "news": {"search_terms": {}},
            "sentiment": {"analyzers": ["textblob"]},
            "report": {"output_dir": "reports"},
            "logging": {"level": "INFO"},
            "error_handling": {},
            "development": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name

        try:
            with pytest.raises(ValueError, match="No primary crypto API configured"):
                Config(temp_config_path)
        finally:
            Path(temp_config_path).unlink(missing_ok=True)

    def test_invalid_sentiment_analyzer(self):
        config_data = {
            "cryptocurrencies": [
                {"symbol": "bitcoin", "name": "Bitcoin", "ticker": "BTC"}
            ],
            "apis": {
                "crypto": {"primary": "coingecko", "fallbacks": []},
                "news": {"primary": "newsapi", "fallbacks": []},
            },
            "endpoints": {},
            "news": {"search_terms": {}},
            "sentiment": {"analyzers": ["invalid_analyzer"]},
            "report": {"output_dir": "reports"},
            "logging": {"level": "INFO"},
            "error_handling": {},
            "development": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid sentiment analyzer"):
                Config(temp_config_path)
        finally:
            Path(temp_config_path).unlink(missing_ok=True)
