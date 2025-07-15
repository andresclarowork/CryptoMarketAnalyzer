import requests
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import feedparser

from utils.logger import LoggerMixin, log_execution_time
from utils.config import get_config


@dataclass
class NewsArticle:
    title: str
    description: str
    content: str
    url: str
    source: str
    published_at: datetime
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None


class NewsDataCollector(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "CryptoMarketSentimentAnalyzer/1.0.0"}
        )

    @log_execution_time
    def collect_news(
        self, crypto_symbol: str, max_articles: Optional[int] = None
    ) -> List[NewsArticle]:
        if max_articles is None:
            max_articles = self.config.news.max_articles_per_crypto

        self.log_info(
            f"Collecting news for {crypto_symbol}, max articles: {max_articles}"
        )

        search_terms = self.config.get_search_terms(crypto_symbol)
        if not search_terms:
            self.log_warning(f"No search terms configured for {crypto_symbol}")
            return []

        # Try primary API first
        primary_api = self.config.news_api.primary
        self.log_info(f"Trying primary API: {primary_api}")
        articles = self._try_news_api(primary_api, search_terms, max_articles)

        if articles and len(articles) >= 2:
            self.log_info(
                f"Successfully collected {len(articles)} articles from {primary_api}"
            )
            return articles
        elif articles and len(articles) < 2:
            self.log_warning(
                f"Primary API returned only {len(articles)} articles, trying RSS fallback for more relevant content"
            )
        else:
            self.log_warning(f"Primary API returned no articles, trying RSS fallback")

        if "rss" in self.config.news_api.fallbacks:
            self.log_info("Trying RSS feeds for more relevant articles...")
            rss_articles = self._collect_from_rss_feeds(search_terms, max_articles)
            if rss_articles:
                self.log_info(
                    f"Successfully collected {len(rss_articles)} articles from RSS feeds"
                )
                return rss_articles
            else:
                self.log_warning("RSS feeds returned no articles")
        else:
            self.log_warning("RSS not configured as fallback")

        for fallback_api in self.config.news_api.fallbacks:
            if fallback_api == "rss":
                continue
            self.log_warning(f"Trying fallback API: {fallback_api}")
            articles = self._try_news_api(fallback_api, search_terms, max_articles)
            if articles:
                self.log_info(
                    f"Successfully collected {len(articles)} articles from fallback API: {fallback_api}"
                )
                return articles

        self.log_warning(f"No news articles found for {crypto_symbol}")
        return []

    def _try_news_api(
        self, api_name: str, search_terms: List[str], max_articles: int
    ) -> Optional[List[NewsArticle]]:
        try:
            if api_name == "newsapi":
                return self._collect_from_newsapi(search_terms, max_articles)
            elif api_name == "guardian":
                return self._collect_from_guardian(search_terms, max_articles)
            elif api_name == "rss":
                return self._collect_from_rss_feeds(search_terms, max_articles)
            else:
                self.log_error(f"Unknown news API: {api_name}")
                return None
        except Exception as e:
            self.log_error(f"Failed to collect news from {api_name}: {e}")
            return None

    def _collect_from_newsapi(
        self, search_terms: List[str], max_articles: int
    ) -> List[NewsArticle]:
        endpoint_config = self.config.get_endpoint("newsapi")
        if not endpoint_config:
            raise ValueError("NewsAPI endpoint not configured")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=48)

        articles = []
        for term in search_terms:
            url = f"{endpoint_config.base_url}{endpoint_config.search_endpoint}"
            params = {
                "q": term,
                "language": "en",
                "pageSize": min(max_articles, 100),
                "apiKey": endpoint_config.api_key,
                "from": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

            try:
                response = self._make_request(url, params)
                try:
                    data = response.json()
                except Exception as json_err:
                    self.log_error(
                        f"NewsAPI non-JSON response for term '{term}': {response.text}"
                    )
                    continue

                if response.status_code != 200:
                    self.log_error(
                        f"NewsAPI error for term '{term}': status={response.status_code}, data={data}"
                    )
                    continue

                if "articles" in data:
                    for article_data in data["articles"]:
                        if len(articles) >= max_articles:
                            break

                        content = (
                            article_data.get("content")
                            or article_data.get("description")
                            or ""
                        )
                        if (
                            not content
                            or len(content) < self.config.news.min_article_length
                        ):
                            continue

                        published_at_str = article_data.get("publishedAt", "")
                        try:
                            published_at = datetime.fromisoformat(
                                published_at_str.replace("Z", "+00:00")
                            )
                        except Exception:
                            published_at = datetime.utcnow()

                        article = NewsArticle(
                            title=article_data.get("title", ""),
                            description=article_data.get("description", ""),
                            content=content,
                            url=article_data.get("url", ""),
                            source=article_data.get("source", {}).get(
                                "name", "Unknown"
                            ),
                            published_at=published_at,
                            sentiment_score=None,
                            sentiment_label=None,
                        )
                        articles.append(article)

            except Exception as e:
                self.log_error(f"Failed to collect news for term '{term}': {e}")
                continue

        return articles[:max_articles]

    def _collect_from_guardian(
        self, search_terms: List[str], max_articles: int
    ) -> List[NewsArticle]:
        endpoint_config = self.config.get_endpoint("guardian")
        if not endpoint_config:
            raise ValueError("Guardian endpoint not configured")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=48)

        articles = []
        for term in search_terms:
            url = f"{endpoint_config.base_url}{endpoint_config.search_endpoint}"

            search_query = (
                f'"{term}" cryptocurrency'
                if term.lower()
                in ["bitcoin", "ethereum", "solana", "btc", "eth", "sol"]
                else term
            )

            params = {
                "q": search_query,
                "from-date": start_date.strftime("%Y-%m-%d"),
                "to-date": end_date.strftime("%Y-%m-%d"),
                "show-fields": "headline,trailText,bodyText",
                "page-size": 50,
                "order-by": "newest",
                "api-key": endpoint_config.api_key,
            }

            try:
                response = self._make_request(url, params)
                data = response.json()

                self.log_info(
                    f"Guardian API response status: {data.get('response', {}).get('status', 'unknown')}"
                )
                self.log_info(
                    f"Guardian API total results: {data.get('response', {}).get('total', 0)}"
                )

                if "response" in data and "results" in data["response"]:
                    self.log_info(
                        f"Guardian API returned {len(data['response']['results'])} articles for term '{term}'"
                    )
                    for article_data in data["response"]["results"]:
                        if len(articles) >= max_articles:
                            break

                        fields = article_data.get("fields", {})
                        title = fields.get("headline", "") or article_data.get(
                            "webTitle", ""
                        )
                        content = (
                            fields.get("bodyText", "")
                            or fields.get("trailText", "")
                            or title
                        )

                        self.log_info(
                            f"Article: '{title}' | Content length: {len(content)}"
                        )

                        if len(content) < self.config.news.min_article_length:
                            self.log_info(
                                f"Skipping article '{title}' - content too short ({len(content)} chars)"
                            )
                            continue

                        article = NewsArticle(
                            title=title,
                            description=fields.get("trailText", "") or title,
                            content=content,
                            url=article_data.get("webUrl", ""),
                            source="The Guardian",
                            published_at=(
                                datetime.fromisoformat(
                                    article_data.get("webPublicationDate", "").replace(
                                        "Z", "+00:00"
                                    )
                                )
                                if article_data.get("webPublicationDate")
                                else datetime.utcnow()
                            ),
                            sentiment_score=None,
                            sentiment_label=None,
                        )
                        articles.append(article)
                        self.log_info(f"Added article: '{title}'")
                else:
                    self.log_info(
                        f"No results found in Guardian API response for term '{term}'"
                    )

            except Exception as e:
                self.log_error(f"Failed to collect news for term '{term}': {e}")
                continue

        return articles[:max_articles]

    def _collect_from_rss_feeds(
        self, search_terms: List[str], max_articles: int
    ) -> List[NewsArticle]:
        """Collect news from free RSS feeds."""
        articles = []

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=48)

        rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://cryptonews.com/news/feed",
            "https://bitcoinmagazine.com/.rss/full/",
            "https://decrypt.co/feed",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://www.newsbtc.com/feed/",
            "https://cryptoslate.com/feed/",
            "https://ambcrypto.com/feed/",
        ]

        for feed_url in rss_feeds:
            if len(articles) >= max_articles:
                break

            try:
                self.log_info(f"Fetching RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                for entry in feed.entries:
                    if len(articles) >= max_articles:
                        break

                    title = entry.get("title", "").lower()
                    description = entry.get("summary", "").lower()

                    relevant = False
                    for term in search_terms:
                        term_lower = term.lower()
                        if term_lower in title:
                            relevant = True
                            break
                        elif term_lower in description:
                            relevant = True
                            break

                    if not relevant:
                        continue

                    try:
                        published_at = (
                            datetime(*entry.published_parsed[:6])
                            if hasattr(entry, "published_parsed")
                            else datetime.now()
                        )
                    except:
                        published_at = datetime.now()

                    if published_at < start_date:
                        continue

                    article = NewsArticle(
                        title=entry.get("title", ""),
                        description=entry.get("summary", ""),
                        content=entry.get("summary", ""),
                        url=entry.get("link", ""),
                        source=feed.feed.get("title", "RSS Feed"),
                        published_at=published_at,
                        sentiment_score=None,
                        sentiment_label=None,
                    )
                    articles.append(article)
                    self.log_info(
                        f"✓ RSS article found: '{article.title}' from {article.source}"
                    )

            except Exception as e:
                self.log_error(f"Failed to fetch RSS feed {feed_url}: {e}")
                continue

        self.log_info(f"RSS feeds provided {len(articles)} relevant articles")
        return articles[:max_articles]

    def _make_request(
        self, url: str, params: Optional[Dict] = None
    ) -> requests.Response:
        time.sleep(self.config.news_api.rate_limit_delay)
        try:
            response = self.session.get(
                url, params=params, timeout=self.config.news_api.timeout
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.log_error(f"News request failed: {e} | URL: {url} | Params: {params}")
            print(f"News request failed: {e} | URL: {url} | Params: {params}")
            if hasattr(e, "response") and e.response is not None:
                self.log_error(f"NewsAPI raw response: {e.response.text}")
                print(f"NewsAPI raw response: {e.response.text}")
            raise
        except Exception as e:
            self.log_error(
                f"Unexpected error in _make_request: {e} | URL: {url} | Params: {params}"
            )
            print(
                f"Unexpected error in _make_request: {e} | URL: {url} | Params: {params}"
            )
            raise

    def get_supported_apis(self) -> List[str]:
        apis = [self.config.news_api.primary] + self.config.news_api.fallbacks

        if "rss" not in apis:
            apis.append("rss")
        return apis

    def get_api_status(self) -> Dict[str, bool]:
        status = {}
        apis = self.get_supported_apis()

        for api in apis:
            try:
                # Simple test request
                if api == "newsapi":
                    url = "https://newsapi.org/v2/top-headlines"
                    params = {"country": "us", "apiKey": ""}
                elif api == "guardian":
                    url = "https://content.guardianapis.com/search"
                    params = {"api-key": ""}
                else:
                    status[api] = False
                    continue

                response = self.session.get(url, params=params, timeout=5)
                status[api] = response.status_code in [200, 401, 403]
            except Exception:
                status[api] = False

        return status

    def filter_articles_by_relevance(
        self, articles: List[NewsArticle], crypto_symbol: str
    ) -> List[NewsArticle]:
        relevant_articles = []
        search_terms = self.config.get_search_terms(crypto_symbol)

        self.log_info(
            f"Filtering {len(articles)} articles for {crypto_symbol} using terms: {search_terms}"
        )

        for article in articles:
            title_lower = article.title.lower()
            desc_lower = article.description.lower()
            content_lower = article.content.lower()

            relevant = False

            for term in search_terms:
                term_lower = term.lower()
                if term_lower in title_lower:
                    relevant = True
                    break
                elif term_lower in desc_lower or term_lower in content_lower:
                    relevant = True
                    break

            if relevant:
                relevant_articles.append(article)
                self.log_info(
                    f"✓ Relevant article for {crypto_symbol}: '{article.title}'"
                )
            else:
                self.log_info(
                    f"✗ Irrelevant article for {crypto_symbol}: '{article.title}' (no matches for {search_terms})"
                )

        self.log_info(
            f"Found {len(relevant_articles)} relevant articles out of {len(articles)} total articles for {crypto_symbol}"
        )
        return relevant_articles
