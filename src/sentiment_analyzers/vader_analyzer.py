from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

from utils.logger import LoggerMixin, log_execution_time
from utils.config import get_config


@dataclass
class VADERSentimentResult:
    score: float
    label: str
    confidence: float
    compound: float
    positive: float
    negative: float
    neutral: float
    analyzer: str


class VADERAnalyzer(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.analyzer_name = "vader"
        self.analyzer = SentimentIntensityAnalyzer()

        vader_config = self.config.sentiment.vader
        if vader_config.get("use_compound", True):
            self.use_compound = True
        else:
            self.use_compound = False

        if vader_config.get("adjust_for_length", True):
            self.adjust_for_length = True
        else:
            self.adjust_for_length = False

    @log_execution_time
    def analyze_text(self, text: str) -> VADERSentimentResult:
        if not text or len(text.strip()) == 0:
            return VADERSentimentResult(
                score=5.0,
                label="neutral",
                confidence=0.0,
                compound=0.0,
                positive=0.0,
                negative=0.0,
                neutral=1.0,
                analyzer=self.analyzer_name,
            )

        cleaned_text = self._preprocess_text(text)

        sentiment_scores = self.analyzer.polarity_scores(cleaned_text)

        positive = sentiment_scores["pos"]
        negative = sentiment_scores["neg"]
        neutral = sentiment_scores["neu"]
        compound = sentiment_scores["compound"]

        # Normalize score to 0-10 scale
        normalized_score = self._normalize_score(compound)

        # Determine label
        label = self._get_sentiment_label(normalized_score)

        # Calculate confidence based on compound score and neutrality
        confidence = abs(compound) * (1 - neutral)

        return VADERSentimentResult(
            score=normalized_score,
            label=label,
            confidence=confidence,
            compound=compound,
            positive=positive,
            negative=negative,
            neutral=neutral,
            analyzer=self.analyzer_name,
        )

    @log_execution_time
    def analyze_multiple_texts(self, texts: List[str]) -> List[VADERSentimentResult]:
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

        # Remove special characters but keep punctuation (important for VADER)
        text = re.sub(r"[^\w\s\.\!\?\,\;\:\-\(\)]", " ", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _normalize_score(self, compound: float) -> float:
        # Convert from -1 to 1 range to 0 to 10 range
        normalized = (compound + 1) * 5
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

    def get_average_sentiment(
        self, results: List[VADERSentimentResult]
    ) -> VADERSentimentResult:
        if not results:
            return VADERSentimentResult(
                score=5.0,
                label="neutral",
                confidence=0.0,
                compound=0.0,
                positive=0.0,
                negative=0.0,
                neutral=1.0,
                analyzer=self.analyzer_name,
            )

        avg_score = sum(r.score for r in results) / len(results)
        avg_confidence = sum(r.confidence for r in results) / len(results)
        avg_compound = sum(r.compound for r in results) / len(results)
        avg_positive = sum(r.positive for r in results) / len(results)
        avg_negative = sum(r.negative for r in results) / len(results)
        avg_neutral = sum(r.neutral for r in results) / len(results)

        labels = [r.label for r in results]
        most_common_label = max(set(labels), key=labels.count)

        return VADERSentimentResult(
            score=avg_score,
            label=most_common_label,
            confidence=avg_confidence,
            compound=avg_compound,
            positive=avg_positive,
            negative=avg_negative,
            neutral=avg_neutral,
            analyzer=self.analyzer_name,
        )

    def get_sentiment_summary(self, results: List[VADERSentimentResult]) -> Dict:
        if not results:
            return {
                "total_articles": 0,
                "average_score": 5.0,
                "sentiment_distribution": {},
                "confidence_avg": 0.0,
                "compound_avg": 0.0,
                "positive_avg": 0.0,
                "negative_avg": 0.0,
                "neutral_avg": 1.0,
            }

        scores = [r.score for r in results]
        confidences = [r.confidence for r in results]
        compounds = [r.compound for r in results]
        positives = [r.positive for r in results]
        negatives = [r.negative for r in results]
        neutrals = [r.neutral for r in results]
        labels = [r.label for r in results]

        sentiment_distribution = {}
        for label in labels:
            sentiment_distribution[label] = sentiment_distribution.get(label, 0) + 1

        return {
            "total_articles": len(results),
            "average_score": sum(scores) / len(scores),
            "sentiment_distribution": sentiment_distribution,
            "confidence_avg": sum(confidences) / len(confidences),
            "compound_avg": sum(compounds) / len(compounds),
            "positive_avg": sum(positives) / len(positives),
            "negative_avg": sum(negatives) / len(negatives),
            "neutral_avg": sum(neutrals) / len(neutrals),
            "min_score": min(scores),
            "max_score": max(scores),
        }

    def compare_with_textblob(self, text: str, textblob_result) -> Dict:
        vader_result = self.analyze_text(text)

        return {
            "text": text,
            "vader_score": vader_result.score,
            "vader_label": vader_result.label,
            "textblob_score": textblob_result.score,
            "textblob_label": textblob_result.label,
            "score_difference": abs(vader_result.score - textblob_result.score),
            "label_agreement": vader_result.label == textblob_result.label,
        }

    def is_configured(self) -> bool:
        """Check if VADER analyzer is properly configured."""
        try:
            # Test with a simple text
            test_text = "This is a test."
            sentiment_scores = self.analyzer.polarity_scores(test_text)
            required_keys = ["pos", "neg", "neu", "compound"]
            return all(key in sentiment_scores for key in required_keys)
        except Exception as e:
            self.log_error(f"VADER analyzer not properly configured: {e}")
            return False

    def get_lexicon_info(self) -> Dict:
        try:
            lexicon = self.analyzer.lexicon
            return {
                "total_words": len(lexicon),
                "positive_words": len(
                    [word for word, score in lexicon.items() if score > 0]
                ),
                "negative_words": len(
                    [word for word, score in lexicon.items() if score < 0]
                ),
                "neutral_words": len(
                    [word for word, score in lexicon.items() if score == 0]
                ),
            }
        except Exception as e:
            self.log_error(f"Could not get lexicon info: {e}")
            return {}
