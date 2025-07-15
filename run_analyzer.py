#!/usr/bin/env python3
"""
Entry point for the Crypto Market Sentiment Analyzer.
This script can be run directly without import issues.
"""

import sys
import json
import traceback
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import CryptoMarketSentimentAnalyzer, main


if __name__ == "__main__":
    main() 