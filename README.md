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

You can run the analyzer using either of these methods:

**Method 1: Using the main entry point**

```bash
python run_analyzer.py
```

**Method 2: Using the module directly**

```bash
python src/main.py
```

### 5. View Results

Open `reports/crypto_sentiment_report_{timestamp}.html` in your web browser to view the generated report.

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
├── logs/                       # Application logs
├── data/                       # Raw data storage
├── tests/                      # Unit tests
├── requirements.txt            # Python dependencies
├── config.yaml                # Configuration file
├── run_analyzer.py            # Main entry point script
├── run_tests.py               # Test runner script
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

The application uses environment variables for sensitive configuration:

- **`NEWSAPI_API_KEY`**: Your NewsAPI key for news data collection
- **`GUARDIAN_API_KEY`**: Your Guardian API key for news data collection

### Configuration File

Edit `config.yaml` to customize:

- Target cryptocurrencies
- News search parameters
- API endpoints and fallbacks
- Sentiment analysis settings
- Report styling and output options
- Logging configuration
- Error handling parameters

## 📊 Example Output

The application generates HTML reports with:

- Current prices and 24h changes
- Volume data
- Sentiment scores for each cryptocurrency
- Key news headlines with sentiment analysis
- Market overview summary

## 🧪 Testing

Run the test suite using either method:

**Method 1: Using the test runner script**

```bash
python run_tests.py
```

**Method 2: Using pytest directly**

```bash
python -m pytest tests/
```

**Method 3: Run specific test file**

```bash
python -m pytest tests/test_config.py
```

## 📈 Supported Cryptocurrencies

- Bitcoin (BTC)
- Ethereum (ETH)
- Solana (SOL)

## 🔗 API Sources

### Price Data

- **CoinGecko API** (primary) - Free tier with rate limits
- **CoinCap API** (fallback) - Free tier available
- **CryptoCompare API** (fallback) - Free tier available

### News Data

- **NewsAPI** (primary) - Free tier: 1,000 requests/day
- **Guardian API** (fallback) - Free tier: 5,000 requests/day
- **RSS Feeds** (fallback) - Free crypto news feeds

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

- Free API tiers have rate limits (NewsAPI: 1,000/day, Guardian: 5,000/day)
- News sentiment analysis accuracy depends on article quality
- Offline sentiment analysis may not match commercial LLM accuracy
- Historical data analysis not included in current version
- RSS feeds may have limited or no content for some cryptocurrencies

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
4. **Environment Variables**: Make sure your `.env` file exists and contains valid API keys
5. **UTF-8 Encoding**: Ensure all configuration files are saved in UTF-8 encoding

### Debug Mode

Run with debug logging by editing `config.yaml`:

```yaml
development:
  debug_mode: true
  verbose_output: true
```

Or run the application and check the logs in the `logs/` directory.

### Log Files

Check the application logs for detailed error information:

```bash
tail -f logs/crypto_analyzer.log
```

## 📞 Support

For issues or questions, please check the troubleshooting section above or create an issue in the repository.
