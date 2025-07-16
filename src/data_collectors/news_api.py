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

        all_articles = []

        # Collect from primary API
        primary_api = self.config.news_api.primary
        self.log_info(f"Collecting from primary API: {primary_api}")
        primary_articles = self._try_news_api(primary_api, search_terms, max_articles)
        if primary_articles:
            all_articles.extend(primary_articles)
            self.log_info(
                f"Collected {len(primary_articles)} articles from {primary_api}"
            )

        # Always collect from RSS feeds (not just as fallback)
        self.log_info("Collecting from RSS feeds...")
        rss_articles = self._collect_from_rss_feeds(search_terms, max_articles)
        if rss_articles:
            all_articles.extend(rss_articles)
            self.log_info(f"Collected {len(rss_articles)} articles from RSS feeds")

        # Collect from fallback APIs
        for fallback_api in self.config.news_api.fallbacks:
            if fallback_api == "rss":
                continue  # Already collected RSS
            self.log_info(f"Collecting from fallback API: {fallback_api}")
            fallback_articles = self._try_news_api(
                fallback_api, search_terms, max_articles
            )
            if fallback_articles:
                all_articles.extend(fallback_articles)
                self.log_info(
                    f"Collected {len(fallback_articles)} articles from {fallback_api}"
                )

        if not all_articles:
            self.log_warning(f"No news articles found for {crypto_symbol}")
            return []

        # Deduplicate articles based on URL and title similarity
        unique_articles = self._deduplicate_articles(all_articles)
        self.log_info(
            f"Deduplicated {len(all_articles)} articles to {len(unique_articles)} unique articles"
        )

        # Sort by relevance and recency
        sorted_articles = self._sort_articles_by_relevance(
            unique_articles, search_terms
        )

        # Return top articles up to max limit
        final_articles = sorted_articles[:max_articles]

        # Log collection statistics
        stats = self.get_collection_statistics(final_articles)
        self.log_info(f"Collection statistics for {crypto_symbol}:")
        self.log_info(f"  Total articles: {stats['total_articles']}")
        self.log_info(f"  Recent articles (24h): {stats['recent_articles']}")
        self.log_info(f"  Sources: {stats['sources']}")

        return final_articles

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

        end_date = datetime.utcnow().replace(tzinfo=None)
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
                            published_at = datetime.utcnow().replace(tzinfo=None)

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

        end_date = datetime.utcnow().replace(tzinfo=None)
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
                                else datetime.utcnow().replace(tzinfo=None)
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

        end_date = datetime.utcnow().replace(tzinfo=None)
        start_date = end_date - timedelta(hours=48)

        # Limit RSS collection to avoid overwhelming combined results
        rss_max_articles = min(
            max_articles, 20
        )  # Cap RSS articles when combining with other sources

        rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://cryptonews.com/news/feed",
            "https://bitcoinmagazine.com/.rss/full/",
            "https://decrypt.co/feed",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://www.newsbtc.com/feed/",
            "https://cryptoslate.com/feed/",
            "https://ambcrypto.com/feed/",
            "https://ethereumworldnews.com/feed/",
            "https://solana.com/feed.xml",
        ]

        for feed_url in rss_feeds:
            if len(articles) >= rss_max_articles:
                break

            try:
                self.log_info(f"Fetching RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                # Limit entries per feed to avoid overwhelming results
                max_entries_per_feed = 10
                entries_processed = 0

                for entry in feed.entries:
                    if (
                        len(articles) >= rss_max_articles
                        or entries_processed >= max_entries_per_feed
                    ):
                        break

                    entries_processed += 1
                    title = entry.get("title", "").lower()
                    description = entry.get("summary", "").lower()

                    relevance_score = 0
                    matched_terms = []

                    for term in search_terms:
                        term_lower = term.lower()
                        if term_lower in title:
                            relevance_score += 3
                            matched_terms.append(term)
                        elif term_lower in description:
                            relevance_score += 2
                            matched_terms.append(term)

                    if relevance_score == 0:
                        continue

                    try:
                        published_at = (
                            datetime(*entry.published_parsed[:6])
                            if hasattr(entry, "published_parsed")
                            else datetime.now()
                        )
                    except:
                        published_at = datetime.now()

                    # Ensure both datetimes are timezone-naive for comparison
                    published_at = (
                        published_at.replace(tzinfo=None)
                        if published_at.tzinfo
                        else published_at
                    )
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
                        f"✓ RSS article found (score: {relevance_score}): '{article.title}' from {article.source} - matched: {matched_terms}"
                    )

            except Exception as e:
                self.log_error(f"Failed to fetch RSS feed {feed_url}: {e}")
                continue

        self.log_info(f"RSS feeds provided {len(articles)} relevant articles")
        return articles[:rss_max_articles]

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

        # RSS is always available as a complementary source
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

            relevance_score = 0
            matched_terms = []

            # Check for exact matches in title (highest priority)
            for term in search_terms:
                term_lower = term.lower()
                if term_lower in title_lower:
                    relevance_score += 3
                    matched_terms.append(term)
                elif term_lower in desc_lower:
                    relevance_score += 2
                    matched_terms.append(term)
                elif term_lower in content_lower:
                    relevance_score += 1
                    matched_terms.append(term)

            # Consider article relevant if it has at least one match
            if relevance_score > 0:
                relevant_articles.append(article)
                self.log_info(
                    f"✓ Relevant article for {crypto_symbol} (score: {relevance_score}): '{article.title}' - matched: {matched_terms}"
                )
            else:
                self.log_info(
                    f"✗ Irrelevant article for {crypto_symbol}: '{article.title}' (no matches for {search_terms})"
                )

        self.log_info(
            f"Found {len(relevant_articles)} relevant articles out of {len(articles)} total articles for {crypto_symbol}"
        )
        return relevant_articles

    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on URL and title similarity."""
        unique_articles = []
        seen_urls = set()
        seen_titles = set()

        for article in articles:
            # Normalize URL for comparison
            normalized_url = article.url.lower().strip()
            if normalized_url in seen_urls:
                continue

            # Normalize title for comparison (remove common prefixes, lowercase)
            normalized_title = article.title.lower().strip()
            # Remove common prefixes like "Breaking:", "Update:", etc.
            for prefix in ["breaking:", "update:", "news:", "latest:", "alert:"]:
                if normalized_title.startswith(prefix):
                    normalized_title = normalized_title[len(prefix) :].strip()

            # Check for title similarity (if titles are very similar, consider them duplicates)
            is_duplicate = False
            for seen_title in seen_titles:
                if self._calculate_title_similarity(normalized_title, seen_title) > 0.8:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_articles.append(article)
                seen_urls.add(normalized_url)
                seen_titles.add(normalized_title)

        return unique_articles

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles using simple word overlap."""
        words1 = set(title1.split())
        words2 = set(title2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _sort_articles_by_relevance(
        self, articles: List[NewsArticle], search_terms: List[str]
    ) -> List[NewsArticle]:
        """Sort articles by relevance score and recency."""

        def calculate_relevance_score(article: NewsArticle) -> float:
            title_lower = article.title.lower()
            desc_lower = article.description.lower()
            content_lower = article.content.lower()

            score = 0.0

            # Check for exact matches in title (highest priority)
            for term in search_terms:
                term_lower = term.lower()
                if term_lower in title_lower:
                    score += 3.0
                elif term_lower in desc_lower:
                    score += 2.0
                elif term_lower in content_lower:
                    score += 1.0

            # Add recency bonus (newer articles get higher scores)
            # Ensure both datetimes are timezone-aware for comparison
            now = datetime.utcnow().replace(tzinfo=None)
            published_at = (
                article.published_at.replace(tzinfo=None)
                if article.published_at.tzinfo
                else article.published_at
            )

            hours_old = (now - published_at).total_seconds() / 3600
            recency_bonus = max(0, 24 - hours_old) / 24  # Bonus decreases over 24 hours
            score += recency_bonus * 0.5

            # Add source quality bonus
            quality_sources = [
                "cointelegraph",
                "cryptonews",
                "bitcoin magazine",
                "decrypt",
                "coindesk",
            ]
            source_lower = article.source.lower()
            for quality_source in quality_sources:
                if quality_source in source_lower:
                    score += 0.3
                    break

            return score

        # Sort by relevance score (descending)
        sorted_articles = sorted(articles, key=calculate_relevance_score, reverse=True)

        # Log top articles for debugging
        for i, article in enumerate(sorted_articles[:5]):
            score = calculate_relevance_score(article)
            self.log_info(
                f"Top article {i+1}: '{article.title}' (score: {score:.2f}) from {article.source}"
            )

        return sorted_articles

    def get_collection_statistics(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Get statistics about collected articles from different sources."""
        stats = {
            "total_articles": len(articles),
            "sources": {},
            "recent_articles": 0,  # Articles from last 24 hours
            "relevance_distribution": {"high": 0, "medium": 0, "low": 0},
        }

        now = datetime.utcnow().replace(tzinfo=None)
        recent_threshold = now - timedelta(hours=24)

        for article in articles:
            # Count by source
            source = article.source
            if source not in stats["sources"]:
                stats["sources"][source] = 0
            stats["sources"][source] += 1

            # Count recent articles
            # Ensure both datetimes are timezone-naive for comparison
            published_at = (
                article.published_at.replace(tzinfo=None)
                if article.published_at.tzinfo
                else article.published_at
            )
            if published_at >= recent_threshold:
                stats["recent_articles"] += 1

        # Sort sources by article count
        stats["sources"] = dict(
            sorted(stats["sources"].items(), key=lambda x: x[1], reverse=True)
        )

        return stats
