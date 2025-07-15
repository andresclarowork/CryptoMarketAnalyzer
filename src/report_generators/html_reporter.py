import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from jinja2 import Template

from utils.logger import LoggerMixin, log_execution_time
from utils.config import get_config


class HTMLReporter(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.template = self._load_template()

    def _load_template(self) -> Template:
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, {{ primary_color }}, {{ secondary_color }});
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .summary-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .summary-card h2 {
            color: {{ primary_color }};
            margin-bottom: 20px;
            border-bottom: 2px solid {{ primary_color }};
            padding-bottom: 10px;
        }
        
        .market-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .market-table th {
            background-color: {{ table_header_bg }};
            color: #333;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        
        .market-table td {
            padding: 12px 15px;
            border-bottom: 1px solid {{ table_border_color }};
        }
        
        .market-table tr:nth-child(even) {
            background-color: {{ table_stripe_bg }};
        }
        
        .market-table tr:hover {
            background-color: #e9ecef;
        }
        
        .sentiment-score {
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 5px;
            color: white;
        }
        
        .sentiment-very-bullish { background-color: {{ success_color }}; }
        .sentiment-bullish { background-color: #28a745; }
        .sentiment-neutral-bullish { background-color: #17a2b8; }
        .sentiment-neutral { background-color: #6c757d; }
        .sentiment-neutral-bearish { background-color: #ffc107; }
        .sentiment-bearish { background-color: {{ danger_color }}; }
        
        .price-change {
            font-weight: bold;
        }
        
        .price-positive { color: {{ success_color }}; }
        .price-negative { color: {{ danger_color }}; }
        .price-neutral { color: #6c757d; }
        
        .crypto-section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .crypto-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .crypto-icon {
            width: 40px;
            height: 40px;
            background: {{ primary_color }};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            margin-right: 15px;
        }
        
        .crypto-info h3 {
            color: {{ primary_color }};
            margin-bottom: 5px;
        }
        
        .crypto-info p {
            color: #666;
            font-size: 0.9em;
        }
        
        .news-articles {
            margin-top: 20px;
        }
        
        .article {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid {{ primary_color }};
        }
        
        .article h4 {
            color: {{ primary_color }};
            margin-bottom: 8px;
        }
        
        .article h4 a {
            color: {{ primary_color }};
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        .article h4 a:hover {
            color: {{ secondary_color }};
            text-decoration: underline;
        }
        
        .article img {
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .article img[src*="broken"] {
            display: none;
        }
        
        .article-meta {
            font-size: 0.8em;
            color: #666;
            margin-bottom: 10px;
        }
        
        .article-content {
            color: #333;
            line-height: 1.5;
        }
        
        .article-sentiment {
            margin-top: 10px;
            padding: 8px 12px;
            border-radius: 5px;
            display: inline-block;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .footer {
            text-align: center;
            padding: 30px;
            color: #666;
            border-top: 1px solid #dee2e6;
            margin-top: 40px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: {{ primary_color }};
        }
        
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        
        .comparison-section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        .comparison-table th,
        .comparison-table td {
            padding: 12px;
            text-align: center;
            border: 1px solid {{ table_border_color }};
        }
        
        .comparison-table th {
            background-color: {{ table_header_bg }};
            font-weight: 600;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .market-table {
                font-size: 0.9em;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <p>Generated on {{ timestamp }}</p>
        </div>
        
        <div class="summary-card">
            <h2>Market Overview</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{{ total_cryptos }}</div>
                    <div class="stat-label">Cryptocurrencies Analyzed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ total_articles }}</div>
                    <div class="stat-label">News Articles Analyzed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ avg_sentiment_score }}</div>
                    <div class="stat-label">Average Sentiment Score</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ bullish_count }}</div>
                    <div class="stat-label">Bullish Sentiments</div>
                </div>
            </div>
            
            <table class="market-table">
                <thead>
                    <tr>
                        <th>Cryptocurrency</th>
                        <th>Price (USD)</th>
                        <th>24h Change</th>
                        <th>Volume (24h)</th>
                        <th>Sentiment Score</th>
                        <th>Sentiment Label</th>
                    </tr>
                </thead>
                <tbody>
                    {% for crypto in crypto_data %}
                    <tr>
                        <td>
                            <strong>{{ crypto.name }} ({{ crypto.ticker }})</strong>
                        </td>
                        <td>${{ "{:,.2f}".format(crypto.price_usd) }}</td>
                        <td class="price-change {% if crypto.price_change_percentage_24h > 0 %}price-positive{% elif crypto.price_change_percentage_24h < 0 %}price-negative{% else %}price-neutral{% endif %}">
                            {% if crypto.price_change_percentage_24h > 0 %}+{% endif %}{{ "{:.2f}".format(crypto.price_change_percentage_24h) }}%
                        </td>
                        <td>${{ "{:,.0f}B".format(crypto.volume_24h / 1e9) }}</td>
                        <td>
                            <span class="sentiment-score sentiment-{{ crypto.sentiment_label }}">
                                {{ "{:.1f}".format(crypto.sentiment_score) }}/10
                            </span>
                        </td>
                        <td>{{ crypto.sentiment_label.replace('_', ' ').title() }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        {% for crypto in crypto_data %}
        <div class="crypto-section">
            <div class="crypto-header">
                <div class="crypto-icon">{{ crypto.ticker[:2] }}</div>
                <div class="crypto-info">
                    <h3>{{ crypto.name }} ({{ crypto.ticker }}) - Sentiment Analysis</h3>
                    <p>Sentiment Score: {{ "{:.1f}".format(crypto.sentiment_score) }}/10 ({{ crypto.sentiment_label.replace('_', ' ').title() }})</p>
                </div>
            </div>
            
            {% if crypto.news_articles %}
            <div class="news-articles">
                <h4>Key News Headlines:</h4>
                {% for article in crypto.news_articles %}
                <div class="article">
                    <h4>
                        {% if article.url %}
                        <a href="{{ article.url }}" target="_blank" style="color: {{ primary_color }}; text-decoration: none;">{{ article.title }}</a>
                        {% else %}
                        {{ article.title }}
                        {% endif %}
                    </h4>
                    <div class="article-meta">
                        <strong>Source:</strong> {{ article.source }} | 
                        <strong>Published:</strong> {{ article.published_at.strftime('%Y-%m-%d %H:%M UTC') }}
                    </div>
                    <div class="article-content">
                        {{ article.description[:200] }}{% if article.description|length > 200 %}...{% endif %}
                    </div>
                    {% if article.sentiment_score %}
                    <div class="article-sentiment sentiment-{{ article.sentiment_label }}">
                        Sentiment: {{ "{:.1f}".format(article.sentiment_score) }}/10 ({{ article.sentiment_label.replace('_', ' ').title() }})
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% else %}
            <p>No recent news articles found for {{ crypto.name }}.</p>
            {% endif %}
        </div>
        {% endfor %}
        
        {% if sentiment_comparison %}
        <div class="comparison-section">
            <h2>Sentiment Analysis Comparison</h2>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Cryptocurrency</th>
                        <th>TextBlob Score</th>
                        <th>VADER Score</th>
                        <th>Average Score</th>
                        <th>Agreement</th>
                    </tr>
                </thead>
                <tbody>
                    {% for comparison in sentiment_comparison %}
                    <tr>
                        <td><strong>{{ comparison.crypto_name }}</strong></td>
                        <td>{{ "{:.1f}".format(comparison.textblob_score) }}/10</td>
                        <td>{{ "{:.1f}".format(comparison.vader_score) }}/10</td>
                        <td>{{ "{:.1f}".format(comparison.average_score) }}/10</td>
                        <td>{{ "✓" if comparison.agreement else "✗" }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Report generated by Crypto Market Sentiment Analyzer v{{ version }}</p>
            <p>Data sources: {{ data_sources }}</p>
        </div>
    </div>
</body>
</html>
        """
        return Template(template_content)

    @log_execution_time
    def generate_report(
        self,
        crypto_data: Dict,
        news_data: Dict,
        sentiment_data: Dict,
        output_path: Optional[str] = None,
    ) -> str:
        self.log_info("Generating HTML report...")

        template_data = self._prepare_template_data(
            crypto_data, news_data, sentiment_data
        )

        html_content = self.template.render(**template_data)

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.config.report.filename_template.format(timestamp=timestamp)
            output_dir = Path(self.config.get_output_dir())
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.log_info(f"HTML report generated: {output_path}")
        return str(output_path)

    def _prepare_template_data(
        self, crypto_data: Dict, news_data: Dict, sentiment_data: Dict
    ) -> Dict[str, Any]:
        total_cryptos = len(crypto_data)
        total_articles = sum(len(articles) for articles in news_data.values())

        sentiment_scores = []
        bullish_count = 0

        crypto_list = []
        for symbol, crypto in crypto_data.items():
            crypto_sentiment = sentiment_data.get(symbol, {})
            sentiment_score = crypto_sentiment.get("average_score", 5.0)
            sentiment_label = crypto_sentiment.get("average_label", "neutral")

            crypto_obj = dict(crypto)
            crypto_obj["sentiment_score"] = sentiment_score
            crypto_obj["sentiment_label"] = sentiment_label

            crypto_obj["news_articles"] = news_data.get(symbol, [])

            crypto_list.append(crypto_obj)

            sentiment_scores.append(sentiment_score)
            if sentiment_label in ["very_bullish", "bullish", "neutral_bullish"]:
                bullish_count += 1

        avg_sentiment_score = (
            sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 5.0
        )

        sentiment_comparison = []
        for symbol, crypto in crypto_data.items():
            crypto_sentiment = sentiment_data.get(symbol, {})
            textblob_score = crypto_sentiment.get("textblob_score", 5.0)
            vader_score = crypto_sentiment.get("vader_score", 5.0)
            average_score = crypto_sentiment.get("average_score", 5.0)

            agreement = abs(textblob_score - vader_score) <= 1.0

            sentiment_comparison.append(
                {
                    "crypto_name": crypto["name"],
                    "textblob_score": textblob_score,
                    "vader_score": vader_score,
                    "average_score": average_score,
                    "agreement": agreement,
                }
            )

        data_sources = []
        for crypto in crypto_data.values():
            if "source" in crypto:
                data_sources.append(crypto["source"])
        data_sources = list(set(data_sources))

        return {
            "title": "Crypto Market Sentiment Report",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            "version": "1.0.0",
            "total_cryptos": total_cryptos,
            "total_articles": total_articles,
            "avg_sentiment_score": round(avg_sentiment_score, 1),
            "bullish_count": bullish_count,
            "crypto_data": crypto_list,
            "sentiment_comparison": sentiment_comparison,
            "data_sources": ", ".join(data_sources),
            "primary_color": self.config.report.styling["primary_color"],
            "secondary_color": self.config.report.styling["secondary_color"],
            "success_color": self.config.report.styling["success_color"],
            "danger_color": self.config.report.styling["danger_color"],
            "warning_color": self.config.report.styling["warning_color"],
            "info_color": self.config.report.styling["info_color"],
            "table_header_bg": self.config.report.styling["table_header_bg"],
            "table_stripe_bg": self.config.report.styling["table_stripe_bg"],
            "table_border_color": self.config.report.styling["table_border_color"],
        }

    def generate_summary_report(self, analysis_results: Dict) -> str:
        crypto_data = analysis_results.get("crypto_data", {})
        news_data = analysis_results.get("news_data", {})
        sentiment_data = analysis_results.get("sentiment_data", {})

        return self.generate_report(crypto_data, news_data, sentiment_data)

    def get_report_template(self) -> str:
        return self.template.render()

    def validate_report_data(self, data: Dict) -> bool:
        required_keys = ["crypto_data", "news_data", "sentiment_data"]

        for key in required_keys:
            if key not in data:
                self.log_error(f"Missing required key in report data: {key}")
                return False

        if not data["crypto_data"]:
            self.log_error("No cryptocurrency data provided")
            return False

        return True
