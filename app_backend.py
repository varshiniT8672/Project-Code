"""Unified Financial Assistant Backend

Combines stock/Bitcoin price fetching with intelligent web scraping.
Uses Gemini LLM for query understanding and content relevance filtering.
"""

import logging
import re
import os
import ssl
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime

import requests
import urllib3
from pydantic_settings import BaseSettings

# SSL bypass for corporate firewalls
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''


class Settings(BaseSettings):
    """Configuration settings."""
    GOOGLE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'

    @property
    def api_key(self) -> str:
        """Get API key from either GEMINI_API_KEY or GOOGLE_API_KEY."""
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging."""
    logger = logging.getLogger()
    logger.setLevel(level)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# Company name to ticker lookup
COMPANY_LOOKUP = {
    'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'alphabet': 'GOOGL',
    'amazon': 'AMZN', 'tesla': 'TSLA', 'meta': 'META', 'facebook': 'META',
    'netflix': 'NFLX', 'nvidia': 'NVDA', 'amd': 'AMD', 'intel': 'INTC',
    'jpmorgan': 'JPM', 'bank of america': 'BAC', 'wells fargo': 'WFC',
    'goldman sachs': 'GS', 'morgan stanley': 'MS', 'berkshire hathaway': 'BRK.B',
    'johnson & johnson': 'JNJ', 'procter & gamble': 'PG', 'coca cola': 'KO',
    'pepsi': 'PEP', 'walmart': 'WMT', 'disney': 'DIS', 'nike': 'NKE',
    'mcdonald': 'MCD', 'mcdonalds': 'MCD', 'visa': 'V', 'mastercard': 'MA',
    'salesforce': 'CRM', 'oracle': 'ORCL', 'cisco': 'CSCO', 'ibm': 'IBM',
    'ge': 'GE', 'general electric': 'GE', 'ford': 'F', 'general motors': 'GM',
    'gm': 'GM', 'boeing': 'BA', 'caterpillar': 'CAT', 'home depot': 'HD',
    'lowes': 'LOW', 'target': 'TGT', 'costco': 'COST', 'starbucks': 'SBUX',
    'ups': 'UPS', 'fedex': 'FDX', 'exxon': 'XOM', 'chevron': 'CVX',
    'pfizer': 'PFE', 'moderna': 'MRNA', 'abbvie': 'ABBV', 'zoom': 'ZM',
    'spotify': 'SPOT', 'uber': 'UBER', 'lyft': 'LYFT', 'airbnb': 'ABNB',
    'snapchat': 'SNAP', 'paypal': 'PYPL', 'square': 'SQ', 'robinhood': 'HOOD'
}


class FinancialAssistant:
    """Main financial assistant class."""

    def __init__(self, google_api_key: Optional[str] = None):
        """Initialize the assistant."""
        self.settings = Settings()
        if google_api_key:
            self.settings.GOOGLE_API_KEY = google_api_key
        setup_logging()

    def find_ticker_from_text(self, text: str) -> Optional[str]:
        """Extract ticker symbol from text."""
        text_lower = text.lower()

        # Check company names
        for company_name in sorted(COMPANY_LOOKUP.keys(), key=len, reverse=True):
            if company_name in text_lower:
                return COMPANY_LOOKUP[company_name]

        # Check for ticker patterns
        stock_pattern = r'\b[A-Z]{2,5}\b'
        matches = re.findall(stock_pattern, text)
        common_words = {'I', 'IS', 'IT', 'IN', 'ON', 'TO', 'OF', 'THE', 'AND', 'OR', 'BUT', 'GET', 'CAN', 'HOW', 'YOU', 'YOUR'}
        valid_tickers = [m for m in matches if m not in common_words]

        return valid_tickers[0] if valid_tickers else None

    def fetch_stock_price(self, ticker: str) -> Dict[str, Any]:
        """Fetch stock price from Yahoo Finance API."""
        logging.info(f"Fetching stock data for: {ticker}")

        try:
            # Chart API
            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
            params = {"interval": "1d", "range": "5d"}
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()

            if 'chart' not in data or 'result' not in data['chart']:
                return {"error": f"No data found for ticker {ticker}"}

            result = data['chart']['result'][0]
            meta = result.get('meta', {})

            current_price = meta.get('regularMarketPrice', 0)
            previous_close = meta.get('previousClose', current_price)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close != 0 else 0

            # Quote API for additional info
            quote_url = f"https://query2.finance.yahoo.com/v7/finance/quote"
            quote_params = {"symbols": ticker}

            try:
                quote_response = requests.get(quote_url, params=quote_params, headers=headers, timeout=10, verify=False)
                quote_response.raise_for_status()
                quote_data = quote_response.json()

                if 'quoteResponse' in quote_data and 'result' in quote_data['quoteResponse']:
                    quote_info = quote_data['quoteResponse']['result'][0]
                    company_name = quote_info.get('longName') or quote_info.get('shortName', ticker)
                    market_cap = quote_info.get('marketCap')
                    high = quote_info.get('regularMarketDayHigh', current_price)
                    low = quote_info.get('regularMarketDayLow', current_price)
                else:
                    company_name = ticker
                    market_cap = None
                    high = current_price
                    low = current_price
            except:
                company_name = ticker
                market_cap = None
                high = current_price
                low = current_price

            return {
                "symbol": ticker,
                "name": company_name,
                "current_price": round(current_price, 2),
                "previous_close": round(previous_close, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "currency": meta.get('currency', 'USD'),
                "market_cap": market_cap,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            logging.error(f"Error fetching stock data: {e}")
            return {"error": str(e)}

    def fetch_bitcoin_price(self) -> Dict[str, Any]:
        """Fetch Bitcoin price from Coinlore API."""
        logging.info("Fetching Bitcoin data")

        try:
            url = "https://api.coinlore.net/api/ticker/"
            params = {"id": "90"}  # Bitcoin ID

            response = requests.get(url, params=params, timeout=10, verify=False)
            response.raise_for_status()
            data = response.json()

            if not data or len(data) == 0:
                return {"error": "Could not fetch Bitcoin data"}

            bitcoin_info = data[0]

            return {
                "name": bitcoin_info.get("name", "Bitcoin"),
                "symbol": bitcoin_info.get("symbol", "BTC"),
                "current_price": float(bitcoin_info.get("price_usd", 0)),
                "change_24h": float(bitcoin_info.get("percent_change_24h", 0)),
                "change_1h": float(bitcoin_info.get("percent_change_1h", 0)),
                "change_7d": float(bitcoin_info.get("percent_change_7d", 0)),
                "volume_24h": float(bitcoin_info.get("volume24", 0)) if bitcoin_info.get("volume24") else None,
                "market_cap": float(bitcoin_info.get("market_cap_usd", 0)) if bitcoin_info.get("market_cap_usd") else None,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            logging.error(f"Error fetching Bitcoin data: {e}")
            return {"error": str(e)}

    def scrape_url(self, url: str, query: str) -> Dict[str, Any]:
        """Scrape a URL for relevant information using Gemini."""
        logging.info(f"Scraping URL: {url} for query: {query}")

        api_key = self.settings.api_key
        if not api_key:
            return {"error": "Google/Gemini API key not configured"}

        try:
            # Step 1: Fetch the webpage content
            logging.info(f"Fetching webpage: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            html_content = response.text

            # Step 2: Extract text from HTML using BeautifulSoup
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Get text
                text_content = soup.get_text(separator=' ', strip=True)

                # Limit to first 8000 characters to avoid token limits
                text_content = text_content[:8000]

                logging.info(f"Extracted {len(text_content)} characters from webpage")

            except ImportError:
                # Fallback: simple HTML tag removal
                import re
                text_content = re.sub('<[^<]+?>', '', html_content)
                text_content = text_content[:8000]

            # Step 3: Use Gemini to analyze the content
            logging.info(f"Analyzing content with Gemini...")

            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            analysis_prompt = f"""Analyze this webpage content and extract information about: "{query}"

Webpage URL: {url}
Content:
{text_content}

Task:
1. Find information related to "{query}"
2. If relevant information is found, summarize it in 2-3 concise bullet points
3. If NO relevant information is found, respond with exactly: "No relevant information found"

Respond in JSON format:
{{
    "relevant": true/false,
    "summary": "your summary here or 'No relevant information found'",
    "key_points": ["point 1", "point 2", "point 3"] or []
}}
"""

            response = model.generate_content(analysis_prompt)
            result_text = response.text.strip()

            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            import json
            analysis = json.loads(result_text)

            logging.info(f"Gemini analysis complete")

            # Format response
            if not analysis.get("relevant", False):
                return {
                    "relevant": False,
                    "message": f"No relevant information found about '{query}' on this page.",
                    "url": url
                }
            else:
                return {
                    "relevant": True,
                    "data": {
                        "summary": analysis.get("summary", ""),
                        "key_points": analysis.get("key_points", [])
                    },
                    "url": url,
                    "query": query
                }

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching URL: {e}")
            return {"error": f"Failed to fetch webpage: {str(e)}", "url": url}
        except Exception as e:
            logging.error(f"Error scraping URL: {e}")
            return {"error": str(e), "url": url}

    def analyze_query_with_gemini(self, query: str) -> Dict[str, Any]:
        """Use Gemini to analyze the query and determine what action to take."""
        logging.info(f"Analyzing query with Gemini: {query}")

        api_key = self.settings.api_key
        if not api_key:
            # Fallback to rule-based if no API key
            return self._fallback_query_analysis(query)

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            analysis_prompt = f"""Analyze this financial query and extract information:

Query: "{query}"

Respond in this exact JSON format:
{{
    "intent": "stock_price" OR "bitcoin_price" OR "web_scrape" OR "both" OR "unknown",
    "ticker": "TICKER_SYMBOL or null",
    "company_name": "Company name or null",
    "urls": ["url1", "url2"] or [],
    "search_query": "what to search for or null"
}}

Rules:
- If asking about stock price only: intent="stock_price", extract ticker
- If asking about Bitcoin/BTC: intent="bitcoin_price"
- If URLs are provided: intent="web_scrape" or "both", extract URLs
- If asking for both price AND scraping: intent="both"

Example 1: "What is Apple stock price?"
→ {{"intent": "stock_price", "ticker": "AAPL", "company_name": "Apple", "urls": [], "search_query": null}}

Example 2: "Get Tesla stock price and scrape https://news.com for Tesla news"
→ {{"intent": "both", "ticker": "TSLA", "company_name": "Tesla", "urls": ["https://news.com"], "search_query": "Tesla news"}}

Example 3: "Scrape https://finance.yahoo.com/news for market trends"
→ {{"intent": "web_scrape", "ticker": null, "company_name": null, "urls": ["https://finance.yahoo.com/news"], "search_query": "market trends"}}
"""

            response = model.generate_content(analysis_prompt)
            result_text = response.text.strip()

            # Extract JSON from markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            import json
            analysis = json.loads(result_text)

            logging.info(f"Gemini analysis: {analysis}")
            return analysis

        except Exception as e:
            logging.error(f"Error analyzing query with Gemini: {e}")
            return self._fallback_query_analysis(query)

    def _fallback_query_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback rule-based query analysis."""
        query_lower = query.lower()

        # Check for URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, query)

        # Check for Bitcoin
        if any(kw in query_lower for kw in ['bitcoin', 'btc', 'crypto']):
            if urls:
                return {"intent": "both", "ticker": None, "company_name": "Bitcoin", "urls": urls, "search_query": query}
            return {"intent": "bitcoin_price", "ticker": None, "company_name": "Bitcoin", "urls": [], "search_query": None}

        # Check for ticker/company
        ticker = self.find_ticker_from_text(query)

        if ticker:
            if urls:
                return {"intent": "both", "ticker": ticker, "company_name": None, "urls": urls, "search_query": query}
            return {"intent": "stock_price", "ticker": ticker, "company_name": None, "urls": [], "search_query": None}

        if urls:
            return {"intent": "web_scrape", "ticker": None, "company_name": None, "urls": urls, "search_query": query}

        return {"intent": "unknown", "ticker": None, "company_name": None, "urls": [], "search_query": query}

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query."""
        logging.info(f"Processing query: {query}")

        # Analyze query
        analysis = self.analyze_query_with_gemini(query)

        result = {
            "query": query,
            "analysis": analysis,
            "stock_data": None,
            "bitcoin_data": None,
            "scraped_data": None
        }

        intent = analysis.get("intent")

        # Execute based on intent
        if intent == "stock_price":
            ticker = analysis.get("ticker")
            if ticker:
                result["stock_data"] = self.fetch_stock_price(ticker)

        elif intent == "bitcoin_price":
            result["bitcoin_data"] = self.fetch_bitcoin_price()

        elif intent == "web_scrape":
            urls = analysis.get("urls", [])
            search_query = analysis.get("search_query", query)
            if urls:
                scraped_results = []
                for url in urls:
                    scraped_results.append(self.scrape_url(url, search_query))
                result["scraped_data"] = scraped_results

        elif intent == "both":
            # Get price data
            ticker = analysis.get("ticker")
            if ticker:
                result["stock_data"] = self.fetch_stock_price(ticker)
            elif "bitcoin" in query.lower():
                result["bitcoin_data"] = self.fetch_bitcoin_price()

            # Scrape URLs
            urls = analysis.get("urls", [])
            search_query = analysis.get("search_query", query)
            if urls:
                scraped_results = []
                for url in urls:
                    scraped_results.append(self.scrape_url(url, search_query))
                result["scraped_data"] = scraped_results

        return result


def format_stock_response(data: Dict[str, Any]) -> str:
    """Format stock data for display."""
    if "error" in data:
        return f"❌ Error: {data['error']}"

    change_symbol = "+" if data['change'] >= 0 else ""
    change_direction = "📈" if data['change'] >= 0 else "📉"

    response = f"{change_direction} **{data['name']}** ({data['symbol']})\n"
    response += f"**Current Price:** ${data['current_price']} {data['currency']}\n"
    response += f"**Change:** {change_symbol}${data['change']} ({change_symbol}{data['change_percent']:.2f}%)\n"
    response += f"**Previous Close:** ${data['previous_close']}\n"
    response += f"**Day Range:** ${data['low']} - ${data['high']}\n"

    if data.get('market_cap'):
        market_cap_b = data['market_cap'] / 1e9
        response += f"**Market Cap:** ${market_cap_b:.2f}B\n"

    response += f"\n_Updated: {data['timestamp']}_"
    return response


def format_bitcoin_response(data: Dict[str, Any]) -> str:
    """Format Bitcoin data for display."""
    if "error" in data:
        return f"❌ Error: {data['error']}"

    change_symbol = "+" if data['change_24h'] >= 0 else ""
    change_direction = "📈" if data['change_24h'] >= 0 else "📉"

    response = f"{change_direction} **{data['name']}** ({data['symbol']})\n"
    response += f"**Current Price:** ${data['current_price']:,.2f} USD\n"
    response += f"**24h Change:** {change_symbol}{data['change_24h']:.2f}%\n"

    if data.get('market_cap'):
        market_cap_b = data['market_cap'] / 1e9
        response += f"**Market Cap:** ${market_cap_b:.2f}B\n"

    if data.get('volume_24h'):
        volume_b = data['volume_24h'] / 1e9
        response += f"**24h Volume:** ${volume_b:.2f}B\n"

    response += f"\n_Updated: {data['timestamp']}_"
    return response


def format_scraped_response(data: Dict[str, Any]) -> str:
    """Format scraped data for display."""
    if "error" in data:
        return f"❌ Error scraping {data.get('url', 'URL')}: {data['error']}"

    if not data.get("relevant", True):
        return f"ℹ️ {data.get('message', 'No relevant information found')}"

    response = f"✅ **Found relevant information from:** {data.get('url', 'Unknown URL')}\n\n"

    scraped_data = data.get('data', {})
    if isinstance(scraped_data, dict):
        for key, value in scraped_data.items():
            response += f"**{key.replace('_', ' ').title()}:**\n{value}\n\n"
    else:
        response += str(scraped_data)

    return response


if __name__ == "__main__":
    # Test the assistant
    setup_logging()

    assistant = FinancialAssistant()

    print("Testing Financial Assistant Backend\n")

    # Test stock price
    print("1. Stock Price Test:")
    stock_data = assistant.fetch_stock_price("AAPL")
    print(format_stock_response(stock_data))
    print("\n" + "="*50 + "\n")

    # Test Bitcoin
    print("2. Bitcoin Price Test:")
    btc_data = assistant.fetch_bitcoin_price()
    print(format_bitcoin_response(btc_data))
    print("\n" + "="*50 + "\n")

    # Test query processing
    print("3. Query Processing Test:")
    result = assistant.process_query("What is Tesla stock price?")
    print(f"Analysis: {result['analysis']}")
    if result['stock_data']:
        print(format_stock_response(result['stock_data']))
