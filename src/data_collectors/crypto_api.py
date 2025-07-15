import requests
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

from utils.logger import LoggerMixin, log_execution_time
from utils.config import get_config


@dataclass
class CryptoData:
    symbol: str
    name: str
    ticker: str
    price_usd: float
    price_change_24h: float
    price_change_percentage_24h: float
    volume_24h: float
    market_cap: float
    last_updated: datetime
    source: str


class CryptoDataCollector(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "CryptoMarketSentimentAnalyzer/1.0.0"}
        )

    @log_execution_time
    def collect_data(
        self, symbols: Optional[List[str]] = None
    ) -> Dict[str, CryptoData]:
        if symbols is None:
            symbols = self.config.get_crypto_symbols()

        self.log_info(f"Collecting crypto data for symbols: {symbols}")

        primary_api = self.config.crypto_api.primary
        data = self._try_api(primary_api, symbols)

        if data:
            self.log_info(f"Successfully collected data from {primary_api}")
            return data

        for fallback_api in self.config.crypto_api.fallbacks:
            self.log_warning(f"Primary API failed, trying fallback: {fallback_api}")
            data = self._try_api(fallback_api, symbols)
            if data:
                self.log_info(
                    f"Successfully collected data from fallback API: {fallback_api}"
                )
                return data

        raise Exception("All crypto APIs failed")

    def _try_api(
        self, api_name: str, symbols: List[str]
    ) -> Optional[Dict[str, CryptoData]]:
        try:
            if api_name == "coingecko":
                return self._collect_from_coingecko(symbols)
            elif api_name == "coincap":
                return self._collect_from_coincap(symbols)
            elif api_name == "cryptocompare":
                return self._collect_from_cryptocompare(symbols)
            else:
                self.log_error(f"Unknown API: {api_name}")
                return None
        except Exception as e:
            self.log_error(f"Failed to collect data from {api_name}: {e}")
            return None

    def _collect_from_coingecko(self, symbols: List[str]) -> Dict[str, CryptoData]:
        endpoint_config = self.config.get_endpoint("coingecko")
        if not endpoint_config:
            raise ValueError("CoinGecko endpoint not configured")

        # Get market data
        url = f"{endpoint_config.base_url}{endpoint_config.market_data_endpoint}"
        params = {
            "vs_currency": "usd",
            "ids": ",".join(symbols),
            "order": "market_cap_desc",
            "per_page": len(symbols),
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h",
        }

        response = self._make_request(url, params)
        data = response.json()

        result = {}
        for item in data:
            symbol = item["id"]
            crypto_config = self.config.get_crypto_by_symbol(symbol)
            if crypto_config:
                result[symbol] = CryptoData(
                    symbol=symbol,
                    name=crypto_config.name,
                    ticker=crypto_config.ticker,
                    price_usd=float(item["current_price"]),
                    price_change_24h=float(item["price_change_24h"]),
                    price_change_percentage_24h=float(
                        item["price_change_percentage_24h"]
                    ),
                    volume_24h=float(item["total_volume"]),
                    market_cap=float(item["market_cap"]),
                    last_updated=datetime.fromisoformat(
                        item["last_updated"].replace("Z", "+00:00")
                    ),
                    source="coingecko",
                )

        return result

    def _collect_from_coincap(self, symbols: List[str]) -> Dict[str, CryptoData]:
        endpoint_config = self.config.get_endpoint("coincap")
        if not endpoint_config:
            raise ValueError("CoinCap endpoint not configured")

        result = {}
        for symbol in symbols:
            url = (
                f"{endpoint_config.base_url}{endpoint_config.assets_endpoint}/{symbol}"
            )
            response = self._make_request(url)
            data = response.json()

            if "data" in data:
                item = data["data"]
                crypto_config = self.config.get_crypto_by_symbol(symbol)
                if crypto_config:
                    result[symbol] = CryptoData(
                        symbol=symbol,
                        name=crypto_config.name,
                        ticker=crypto_config.ticker,
                        price_usd=float(item["priceUsd"]),
                        price_change_24h=float(item["changePercent24Hr"]),
                        price_change_percentage_24h=float(item["changePercent24Hr"]),
                        volume_24h=float(item["volumeUsd24Hr"]),
                        market_cap=float(item["marketCapUsd"]),
                        last_updated=datetime.fromisoformat(
                            item["updated"].replace("Z", "+00:00")
                        ),
                        source="coincap",
                    )

        return result

    def _collect_from_cryptocompare(self, symbols: List[str]) -> Dict[str, CryptoData]:
        """Collect data from CryptoCompare API."""
        endpoint_config = self.config.get_endpoint("cryptocompare")
        if not endpoint_config:
            raise ValueError("CryptoCompare endpoint not configured")

        # Get price data
        url = f"{endpoint_config.base_url}{endpoint_config.price_endpoint}"
        params = {
            "fsym": symbols[0],
            "tsyms": "USD",
        }

        result = {}
        for symbol in symbols:
            params["fsym"] = symbol
            response = self._make_request(url, params)
            data = response.json()

            if "USD" in data:
                crypto_config = self.config.get_crypto_by_symbol(symbol)
                if crypto_config:
                    result[symbol] = CryptoData(
                        symbol=symbol,
                        name=crypto_config.name,
                        ticker=crypto_config.ticker,
                        price_usd=float(data["USD"]),
                        price_change_24h=0.0,
                        price_change_percentage_24h=0.0,
                        volume_24h=0.0,
                        market_cap=0.0,
                        last_updated=datetime.utcnow(),
                        source="cryptocompare",
                    )

        return result

    def _make_request(
        self, url: str, params: Optional[Dict] = None
    ) -> requests.Response:
        time.sleep(self.config.crypto_api.rate_limit_delay)

        try:
            response = self.session.get(
                url, params=params, timeout=self.config.crypto_api.timeout
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.log_error(f"Request failed: {e}")
            raise

    def get_supported_apis(self) -> List[str]:
        return [self.config.crypto_api.primary] + self.config.crypto_api.fallbacks

    def get_api_status(self) -> Dict[str, bool]:
        status = {}
        apis = self.get_supported_apis()

        for api in apis:
            try:
                # Simple test request
                if api == "coingecko":
                    url = "https://api.coingecko.com/api/v3/ping"
                elif api == "coincap":
                    url = "https://api.coincap.io/v2/assets"
                elif api == "cryptocompare":
                    url = "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD"
                else:
                    status[api] = False
                    continue

                response = self.session.get(url, timeout=5)
                status[api] = response.status_code == 200
            except Exception:
                status[api] = False

        return status
