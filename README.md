# Crypto Market Sentiment Analyzer

A comprehensive Python application that combines real-time cryptocurrency price data with sentiment analysis to provide market insights. This tool fetches current prices, recent news, and analyzes sentiment using offline libraries to generate detailed market reports.

## 🎯 Features

- **Real-time Crypto Data**: Fetches current prices, 24h changes, and volume for Bitcoin, Ethereum, and Solana
- **News Integration**: Collects recent news articles related to each cryptocurrency
- **Sentiment Analysis**: Analyzes news sentiment using multiple offline libraries (TextBlob, VADER)
- **HTML Reports**: Generates professional HTML reports combining price data and sentiment analysis
- **Error Handling**: Robust error handling for API failures and rate limits
- **Offline Capability**: Works entirely offline for sentiment analysis

## 📋 Requirements

- Python 3.13+
- Internet connection for API data fetching
- API keys for news services (free tiers available)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd CryptoMarketSentimentAnalyzer
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file and add your API keys:

```bash
# API Keys for Crypto Market Sentiment Analyzer
NEWSAPI_API_KEY=your_newsapi_key_here
GUARDIAN_API_KEY=your_guardian_api_key_here
```

**Note**: You'll need to obtain API keys from:

- [NewsAPI](https://newsapi.org/) (free tier available)
- [Guardian API](https://open-platform.theguardian.com/) (free tier available)

### 4. Run the Analyzer

```bash
python src/main.py
```

### 5. View Results

Open `reports/crypto_sentiment_report.html` in your web browser to view the generated report.

## 📁 Project Structure

```
CryptoMarketSentimentAnalyzer/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main application entry point
│   ├── data_collectors/
│   │   ├── __init__.py
│   │   ├── crypto_api.py       # Cryptocurrency price data collection
│   │   └── news_api.py         # News data collection
│   ├── sentiment_analyzers/
│   │   ├── __init__.py
│   │   ├── textblob_analyzer.py # TextBlob sentiment analysis
│   │   └── vader_analyzer.py   # VADER sentiment analysis
│   ├── report_generators/
│   │   ├── __init__.py
│   │   └── html_reporter.py    # HTML report generation
│   └── utils/
│       ├── __init__.py
│       ├── config.py           # Configuration management
│       └── logger.py           # Logging utilities
├── reports/                    # Generated reports directory
├── tests/                      # Unit tests
├── requirements.txt            # Python dependencies
├── config.yaml                # Configuration file
└── README.md                  # This file
```

## 🔧 Configuration

Edit `config.yaml` to customize:

- Target cryptocurrencies
- News search parameters
- API endpoints
- Report settings

## 📊 Example Output

The application generates HTML reports with:

- Current prices and 24h changes
- Volume data
- Sentiment scores for each cryptocurrency
- Key news headlines with sentiment analysis
- Market overview summary

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/
```

## 📈 Supported Cryptocurrencies

- Bitcoin (BTC)
- Ethereum (ETH)
- Solana (SOL)

## 🔗 API Sources

### Price Data

- CoinGecko API (primary)
- CoinCap API (fallback)
- CryptoCompare API (fallback)

### News Data

- NewsAPI (primary)
- Guardian API (fallback)

## 🛠️ Technical Details

### Sentiment Analysis Libraries

- **TextBlob**: Simple, built-in sentiment analysis
- **VADER**: Optimized for social media and news content
- **Comparison**: Multiple approaches for accuracy validation

### Error Handling

- API rate limiting
- Network connectivity issues
- Data validation
- Graceful degradation

## 📝 Development History

This project was developed using the following approach:

1. **Data Collection Layer**: Implemented modular API collectors with fallback mechanisms
2. **Sentiment Analysis Layer**: Created multiple analyzer implementations for comparison
3. **Report Generation**: Built HTML report generator with professional styling
4. **Error Handling**: Implemented comprehensive error handling and logging
5. **Testing**: Added unit tests for all major components

## ⚠️ Known Limitations

- Free API tiers have rate limits
- News sentiment analysis accuracy depends on article quality
- Offline sentiment analysis may not match commercial LLM accuracy
- Historical data analysis not included in current version

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **API Rate Limits**: The application automatically handles rate limits with exponential backoff
2. **Network Issues**: Check your internet connection and firewall settings
3. **Missing Dependencies**: Ensure all requirements are installed with `pip install -r requirements.txt`

### Debug Mode

Run with debug logging:

```bash
python src/main.py --debug
```

## 📞 Support

For issues or questions, please check the troubleshooting section above or create an issue in the repository.
