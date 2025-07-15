from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from textblob import TextBlob
import re

from utils.logger import LoggerMixin, log_execution_time
from utils.config import get_config


@dataclass
class SentimentResult:
    score: float
    label: str
    confidence: float
    subjectivity: float
    polarity: float
    analyzer: str


class TextBlobAnalyzer(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.analyzer_name = "textblob"

    @log_execution_time
    def analyze_text(self, text: str) -> SentimentResult:
        if not text or len(text.strip()) == 0:
            return SentimentResult(
                score=0.0,
                label="neutral",
                confidence=0.0,
                subjectivity=0.0,
                polarity=0.0,
                analyzer=self.analyzer_name,
            )

        cleaned_text = self._preprocess_text(text)

        blob = TextBlob(cleaned_text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # Normalize score to 0-10 scale
        normalized_score = self._normalize_score(polarity)

        # Determine label
        label = self._get_sentiment_label(normalized_score)

        # Calculate confidence based on subjectivity
        confidence = min(abs(polarity) + subjectivity, 1.0)

        return SentimentResult(
            score=normalized_score,
            label=label,
            confidence=confidence,
            subjectivity=subjectivity,
            polarity=polarity,
            analyzer=self.analyzer_name,
        )

    @log_execution_time
    def analyze_multiple_texts(self, texts: List[str]) -> List[SentimentResult]:
        results = []
        for text in texts:
            result = self.analyze_text(text)
            results.append(result)
        return results

    @log_execution_time
    def analyze_articles(self, articles: List) -> List[Dict]:
        results = []

        for article in articles:
            text_to_analyze = f"{article.title} {article.description} {article.content}"

            sentiment_result = self.analyze_text(text_to_analyze)

            result = {
                "article": article,
                "sentiment": sentiment_result,
                "analyzed_text": (
                    text_to_analyze[:200] + "..."
                    if len(text_to_analyze) > 200
                    else text_to_analyze
                ),
            }
            results.append(result)

        return results

    def _preprocess_text(self, text: str) -> str:
        text = text.lower()

        # Remove URLs
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )

        # Remove special characters but keep spaces
        text = re.sub(r"[^\w\s]", " ", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _normalize_score(self, polarity: float) -> float:
        # Convert from -1 to 1 range to 0 to 10 range
        normalized = (polarity + 1) * 5
        return max(0.0, min(10.0, normalized))

    def _get_sentiment_label(self, score: float) -> str:
        if score >= 8.0:
            return "very_bullish"
        elif score >= 6.0:
            return "bullish"
        elif score >= 4.0:
            return "neutral_bullish"
        elif score >= 2.0:
            return "neutral"
        elif score >= 0.5:
            return "neutral_bearish"
        else:
            return "bearish"

    def get_average_sentiment(self, results: List[SentimentResult]) -> SentimentResult:
        if not results:
            return SentimentResult(
                score=5.0,
                label="neutral",
                confidence=0.0,
                subjectivity=0.0,
                polarity=0.0,
                analyzer=self.analyzer_name,
            )

        avg_score = sum(r.score for r in results) / len(results)
        avg_confidence = sum(r.confidence for r in results) / len(results)
        avg_subjectivity = sum(r.subjectivity for r in results) / len(results)
        avg_polarity = sum(r.polarity for r in results) / len(results)

        # Get most common label
        labels = [r.label for r in results]
        most_common_label = max(set(labels), key=labels.count)

        return SentimentResult(
            score=avg_score,
            label=most_common_label,
            confidence=avg_confidence,
            subjectivity=avg_subjectivity,
            polarity=avg_polarity,
            analyzer=self.analyzer_name,
        )

    def get_sentiment_summary(self, results: List[SentimentResult]) -> Dict:
        if not results:
            return {
                "total_articles": 0,
                "average_score": 5.0,
                "sentiment_distribution": {},
                "confidence_avg": 0.0,
                "subjectivity_avg": 0.0,
            }

        scores = [r.score for r in results]
        confidences = [r.confidence for r in results]
        subjectivities = [r.subjectivity for r in results]
        labels = [r.label for r in results]

        sentiment_distribution = {}
        for label in labels:
            sentiment_distribution[label] = sentiment_distribution.get(label, 0) + 1

        return {
            "total_articles": len(results),
            "average_score": sum(scores) / len(scores),
            "sentiment_distribution": sentiment_distribution,
            "confidence_avg": sum(confidences) / len(confidences),
            "subjectivity_avg": sum(subjectivities) / len(subjectivities),
            "min_score": min(scores),
            "max_score": max(scores),
        }

    def is_configured(self) -> bool:
        """Check if TextBlob analyzer is properly configured."""
        try:
            # Test with a simple text
            test_text = "This is a test."
            blob = TextBlob(test_text)
            _ = blob.sentiment
            return True
        except Exception as e:
            self.log_error(f"TextBlob analyzer not properly configured: {e}")
            return False
