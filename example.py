#!/usr/bin/env python3
"""
Example usage of the Crypto Market Sentiment Analyzer.

This script demonstrates how to use the analyzer programmatically.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import CryptoMarketSentimentAnalyzer


def main():
    """Run the example analysis."""
    print("🚀 Crypto Market Sentiment Analyzer - Example")
    print("=" * 50)
    
    try:
        # Initialize the analyzer
        print("📋 Initializing analyzer...")
        analyzer = CryptoMarketSentimentAnalyzer(debug_mode=True)
        
        # Check system status
        print("\n🔍 Checking system status...")
        status = analyzer.check_system_status()
        
        print("System Status:")
        print(f"  Configuration loaded: {'✅' if status['config_loaded'] else '❌'}")
        
        if 'apis' in status:
            print("  API Status:")
            for api_type, apis in status['apis'].items():
                if isinstance(apis, dict):
                    for api_name, is_available in apis.items():
                        status_icon = "✅" if is_available else "❌"
                        print(f"    {api_name}: {status_icon}")
        
        if 'analyzers' in status:
            print("  Analyzer Status:")
            for analyzer_name, is_configured in status['analyzers'].items():
                status_icon = "✅" if is_configured else "❌"
                print(f"    {analyzer_name}: {status_icon}")
        
        # Run the analysis
        print("\n📊 Running analysis...")
        results = analyzer.run_analysis()
        
        if results['status'] == 'success':
            print("\n✅ Analysis completed successfully!")
            print(f"📈 Cryptocurrencies analyzed: {len(results['crypto_data'])}")
            
            # Display crypto data
            print("\n📊 Cryptocurrency Data:")
            for symbol, data in results['crypto_data'].items():
                print(f"  {data['name']} ({data['ticker']}):")
                print(f"    Price: ${data['price_usd']:,.2f}")
                print(f"    24h Change: {data['price_change_percentage_24h']:+.2f}%")
                print(f"    Volume: ${data['volume_24h']/1e9:.1f}B")
            
            # Display sentiment data
            print("\n😊 Sentiment Analysis Results:")
            for symbol, sentiment in results['sentiment_data'].items():
                crypto_name = results['crypto_data'][symbol]['name']
                print(f"  {crypto_name}:")
                print(f"    Average Score: {sentiment['average_score']:.1f}/10")
                print(f"    Label: {sentiment['average_label'].replace('_', ' ').title()}")
                print(f"    Articles Analyzed: {sentiment['articles_analyzed']}")
                print(f"    TextBlob Score: {sentiment['textblob_score']:.1f}/10")
                print(f"    VADER Score: {sentiment['vader_score']:.1f}/10")
            
            # Display news summary
            print("\n📰 News Summary:")
            for symbol, articles in results['news_data'].items():
                crypto_name = results['crypto_data'][symbol]['name']
                print(f"  {crypto_name}: {len(articles)} articles found")
            
            print(f"\n📄 Report generated: {results['report_path']}")
            print("🌐 Open the HTML file in your browser to view the full report!")
            
        else:
            print(f"\n❌ Analysis failed: {results.get('error', 'Unknown error')}")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def run_quick_demo():
    """Run a quick demo with limited data."""
    print("🚀 Crypto Market Sentiment Analyzer - Quick Demo")
    print("=" * 50)
    
    try:
        # Initialize the analyzer
        analyzer = CryptoMarketSentimentAnalyzer(debug_mode=True)
        
        # Run quick test
        print("🔍 Running quick system test...")
        success = analyzer.run_quick_test()
        
        if success:
            print("✅ Quick demo completed successfully!")
            print("🎉 The system is working correctly!")
            return True
        else:
            print("❌ Quick demo failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error in quick demo: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crypto Market Sentiment Analyzer Example")
    parser.add_argument("--quick", action="store_true", help="Run quick demo only")
    
    args = parser.parse_args()
    
    if args.quick:
        success = run_quick_demo()
    else:
        success = main()
    
    sys.exit(0 if success else 1) 