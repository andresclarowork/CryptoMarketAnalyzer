import argparse
import sys
import traceback
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data_collectors import CryptoDataCollector, NewsDataCollector
from sentiment_analyzers import TextBlobAnalyzer, VADERAnalyzer
from report_generators import HTMLReporter
from utils.config import get_config, reload_config
from utils.logger import setup_logger, get_logger


class CryptoMarketSentimentAnalyzer:
    """Main application class for crypto market sentiment analysis."""

    def __init__(self, debug_mode: bool = False):
        """Initialize the analyzer."""
        self.config = get_config()
        self.debug_mode = debug_mode

        # Set up logging
        log_level = "DEBUG" if debug_mode else self.config.logging.level
        self.logger = setup_logger(
            name="crypto_analyzer",
            level=log_level,
            log_file=self.config.get_log_file(),
            console_output=True,
        )

        self.crypto_collector = CryptoDataCollector()
        self.news_collector = NewsDataCollector()
        self.textblob_analyzer = TextBlobAnalyzer()
        self.vader_analyzer = VADERAnalyzer()
        self.html_reporter = HTMLReporter()

        self.logger.info("Crypto Market Sentiment Analyzer initialized")

    def run_analysis(self) -> Dict[str, Any]:
        self.logger.info("Starting crypto market sentiment analysis...")

        try:
            self.logger.info("Step 1: Collecting cryptocurrency data...")
            crypto_data = self._collect_crypto_data()

            self.logger.info("Step 2: Collecting news data...")
            news_data = self._collect_news_data()

            self.logger.info("Step 3: Performing sentiment analysis...")
            sentiment_data = self._analyze_sentiment(news_data)

            self.logger.info("Step 4: Generating report...")
            report_path = self._generate_report(crypto_data, news_data, sentiment_data)

            results = {
                "crypto_data": crypto_data,
                "news_data": news_data,
                "sentiment_data": sentiment_data,
                "report_path": report_path,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
            }

            self.logger.info("Analysis completed successfully!")
            return results

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            self.logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _collect_crypto_data(self) -> Dict[str, Any]:
        """Collect cryptocurrency price and market data."""
        try:
            crypto_data = self.crypto_collector.collect_data()

            result = {}
            for symbol, data in crypto_data.items():
                result[symbol] = {
                    "symbol": data.symbol,
                    "name": data.name,
                    "ticker": data.ticker,
                    "price_usd": data.price_usd,
                    "price_change_24h": data.price_change_24h,
                    "price_change_percentage_24h": data.price_change_percentage_24h,
                    "volume_24h": data.volume_24h,
                    "market_cap": data.market_cap,
                    "last_updated": data.last_updated,
                    "source": data.source,
                }

            self.logger.info(f"Collected data for {len(result)} cryptocurrencies")
            return result

        except Exception as e:
            self.logger.error(f"Failed to collect crypto data: {e}")
            raise

    def _collect_news_data(self) -> Dict[str, List]:
        """Collect news data for each cryptocurrency."""
        try:
            news_data = {}
            crypto_symbols = self.config.get_crypto_symbols()

            for symbol in crypto_symbols:
                self.logger.info(f"Collecting news for {symbol}...")
                articles = self.news_collector.collect_news(symbol)

                # Filter articles by relevance
                relevant_articles = self.news_collector.filter_articles_by_relevance(
                    articles, symbol
                )
                news_data[symbol] = relevant_articles

                self.logger.info(
                    f"Found {len(relevant_articles)} relevant articles for {symbol}"
                )

            return news_data

        except Exception as e:
            self.logger.error(f"Failed to collect news data: {e}")
            raise

    def _analyze_sentiment(self, news_data: Dict[str, List]) -> Dict[str, Any]:
        """Perform sentiment analysis on news articles."""
        try:
            sentiment_data = {}
            crypto_symbols = self.config.get_crypto_symbols()

            for symbol in crypto_symbols:
                self.logger.info(f"Analyzing sentiment for {symbol}...")
                articles = news_data.get(symbol, [])

                if not articles:
                    self.logger.warning(
                        f"No articles found for {symbol}, using neutral sentiment"
                    )
                    sentiment_data[symbol] = {
                        "textblob_score": 5.0,
                        "vader_score": 5.0,
                        "average_score": 5.0,
                        "average_label": "neutral",
                        "articles_analyzed": 0,
                    }
                    continue

                # Analyze with TextBlob
                textblob_results = self.textblob_analyzer.analyze_articles(articles)
                textblob_sentiments = [
                    result["sentiment"] for result in textblob_results
                ]
                textblob_average = self.textblob_analyzer.get_average_sentiment(
                    textblob_sentiments
                )

                # Analyze with VADER
                vader_results = self.vader_analyzer.analyze_articles(articles)
                vader_sentiments = [result["sentiment"] for result in vader_results]
                vader_average = self.vader_analyzer.get_average_sentiment(
                    vader_sentiments
                )

                average_score = (textblob_average.score + vader_average.score) / 2

                if average_score >= 8.0:
                    average_label = "very_bullish"
                elif average_score >= 6.0:
                    average_label = "bullish"
                elif average_score >= 4.0:
                    average_label = "neutral_bullish"
                elif average_score >= 2.0:
                    average_label = "neutral"
                elif average_score >= 0.5:
                    average_label = "neutral_bearish"
                else:
                    average_label = "bearish"

                sentiment_data[symbol] = {
                    "textblob_score": textblob_average.score,
                    "vader_score": vader_average.score,
                    "average_score": average_score,
                    "average_label": average_label,
                    "articles_analyzed": len(articles),
                    "textblob_summary": self.textblob_analyzer.get_sentiment_summary(
                        textblob_sentiments
                    ),
                    "vader_summary": self.vader_analyzer.get_sentiment_summary(
                        vader_sentiments
                    ),
                }

                self.logger.info(
                    f"Sentiment analysis for {symbol}: {average_score:.1f}/10 ({average_label})"
                )

            return sentiment_data

        except Exception as e:
            self.logger.error(f"Failed to analyze sentiment: {e}")
            raise

    def _generate_report(
        self, crypto_data: Dict, news_data: Dict, sentiment_data: Dict
    ) -> str:
        try:
            report_path = self.html_reporter.generate_report(
                crypto_data, news_data, sentiment_data
            )
            self.logger.info(f"Report generated: {report_path}")
            return report_path

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            raise

    def check_system_status(self) -> Dict[str, Any]:
        status = {
            "config_loaded": True,
            "apis": {},
            "analyzers": {},
            "timestamp": datetime.now().isoformat(),
        }

        try:
            crypto_apis = self.crypto_collector.get_api_status()
            news_apis = self.news_collector.get_api_status()
            status["apis"] = {"crypto": crypto_apis, "news": news_apis}
        except Exception as e:
            self.logger.error(f"Failed to check API status: {e}")
            status["apis"] = {"error": str(e)}

        try:
            status["analyzers"] = {
                "textblob": self.textblob_analyzer.is_configured(),
                "vader": self.vader_analyzer.is_configured(),
            }
        except Exception as e:
            self.logger.error(f"Failed to check analyzer status: {e}")
            status["analyzers"] = {"error": str(e)}

        return status

    def run_quick_test(self) -> bool:
        """Run a quick test to verify all components work."""
        try:
            self.logger.info("Running quick system test...")

            if not self.config.cryptocurrencies:
                self.logger.error("No cryptocurrencies configured")
                return False

            test_symbols = [self.config.cryptocurrencies[0].symbol]
            crypto_data = self.crypto_collector.collect_data(test_symbols)
            if not crypto_data:
                self.logger.error("Failed to collect crypto data")
                return False

            # Test news collection
            news_data = self.news_collector.collect_news(
                test_symbols[0], max_articles=1
            )

            if news_data:
                textblob_result = self.textblob_analyzer.analyze_text(
                    "Bitcoin is performing well."
                )
                vader_result = self.vader_analyzer.analyze_text(
                    "Bitcoin is performing well."
                )

                if not textblob_result or not vader_result:
                    self.logger.error("Failed to perform sentiment analysis")
                    return False

            crypto_obj = crypto_data[test_symbols[0]]
            test_crypto_data = {
                test_symbols[0]: {
                    "symbol": crypto_obj.symbol,
                    "name": crypto_obj.name,
                    "ticker": crypto_obj.ticker,
                    "price_usd": crypto_obj.price_usd,
                    "price_change_24h": crypto_obj.price_change_24h,
                    "price_change_percentage_24h": crypto_obj.price_change_percentage_24h,
                    "volume_24h": crypto_obj.volume_24h,
                    "market_cap": crypto_obj.market_cap,
                    "last_updated": crypto_obj.last_updated,
                    "source": crypto_obj.source,
                }
            }
            test_news_data = {test_symbols[0]: news_data}
            test_sentiment_data = {
                test_symbols[0]: {"average_score": 5.0, "average_label": "neutral"}
            }

            report_path = self.html_reporter.generate_report(
                test_crypto_data, test_news_data, test_sentiment_data
            )

            if not Path(report_path).exists():
                self.logger.error("Failed to generate test report")
                return False

            self.logger.info("Quick test completed successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Quick test failed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Crypto Market Sentiment Analyzer")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--test", action="store_true", help="Run quick system test")
    parser.add_argument("--status", action="store_true", help="Check system status")
    parser.add_argument("--config", type=str, help="Path to configuration file")

    args = parser.parse_args()

    try:
        if args.config:
            reload_config(args.config)

        analyzer = CryptoMarketSentimentAnalyzer(debug_mode=args.debug)

        if args.test:
            success = analyzer.run_quick_test()
            sys.exit(0 if success else 1)

        if args.status:
            status = analyzer.check_system_status()
            print(json.dumps(status, indent=2))
            return

        results = analyzer.run_analysis()

        if results["status"] == "success":
            print(f"\n✅ Analysis completed successfully!")
            print(f"📊 Report generated: {results['report_path']}")
            print(f"📈 Cryptocurrencies analyzed: {len(results['crypto_data'])}")
            print(
                f"📰 News articles analyzed: {sum(len(articles) for articles in results['news_data'].values())}"
            )
        else:
            print(f"\n❌ Analysis failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
