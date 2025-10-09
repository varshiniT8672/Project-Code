"""Financial Assistant - Streamlit UI

A comprehensive financial assistant with stock prices, Bitcoin tracking, and web scraping.
"""

import streamlit as st
from financial_assistant_backend import (
    FinancialAssistant,
    format_stock_response,
    format_bitcoin_response,
    format_scraped_response
)

# Page configuration
st.set_page_config(
    page_title="Financial Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 2rem;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'assistant' not in st.session_state:
    st.session_state.assistant = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


def initialize_assistant(api_key: str = None):
    """Initialize the financial assistant."""
    try:
        st.session_state.assistant = FinancialAssistant(google_api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Failed to initialize assistant: {e}")
        return False


# Sidebar for configuration
with st.sidebar:
    st.title("⚙️ Configuration")

    api_key = st.text_input(
        "Google API Key (Gemini)",
        type="password",
        help="Required for web scraping and smart query analysis"
    )

    if st.button("💾 Save API Key"):
        if api_key:
            initialize_assistant(api_key)
            st.success("✅ API Key saved!")
        else:
            st.warning("⚠️ Please enter an API key")

    st.divider()

    st.subheader("ℹ️ About")
    st.markdown("""
    **Financial Assistant** combines:
    - 📊 Real-time stock prices
    - ₿ Bitcoin tracking
    - 🔍 Intelligent web scraping
    - 🤖 AI-powered query understanding

    **No API keys needed for prices!**
    Only required for web scraping.
    """)

    st.divider()

    st.subheader("📚 Examples")
    st.code("AAPL price", language="text")
    st.code("Bitcoin value", language="text")
    st.code("Scrape https://news.com for Tesla news", language="text")


# Main content
st.markdown('<div class="main-header">💰 Financial Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Stock Prices • Bitcoin • Web Scraping • AI-Powered</div>', unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["📊 Quick Prices", "🔍 Web Scraper", "🤖 Smart Assistant"])


# TAB 1: Quick Prices
with tab1:
    st.header("📊 Quick Price Lookup")
    st.markdown("Get instant stock and Bitcoin prices without any API key!")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Stock Price")
        ticker = st.text_input(
            "Enter Stock Ticker",
            placeholder="e.g., AAPL, TSLA, GOOGL",
            key="stock_ticker"
        )

        if st.button("Get Stock Price", key="fetch_stock"):
            if ticker:
                with st.spinner(f"Fetching {ticker} price..."):
                    if st.session_state.assistant is None:
                        initialize_assistant()

                    stock_data = st.session_state.assistant.fetch_stock_price(ticker.upper())
                    st.markdown(format_stock_response(stock_data))
            else:
                st.warning("Please enter a stock ticker")

    with col2:
        st.subheader("₿ Bitcoin Price")
        st.markdown("Get the latest Bitcoin price from Coinlore")

        if st.button("Get Bitcoin Price", key="fetch_btc"):
            with st.spinner("Fetching Bitcoin price..."):
                if st.session_state.assistant is None:
                    initialize_assistant()

                btc_data = st.session_state.assistant.fetch_bitcoin_price()
                st.markdown(format_bitcoin_response(btc_data))

    st.divider()

    # Popular stocks quick access
    st.subheader("🔥 Popular Stocks")
    popular_stocks = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "AMD"]

    cols = st.columns(4)
    for idx, stock in enumerate(popular_stocks):
        with cols[idx % 4]:
            if st.button(stock, key=f"quick_{stock}"):
                with st.spinner(f"Fetching {stock}..."):
                    if st.session_state.assistant is None:
                        initialize_assistant()

                    stock_data = st.session_state.assistant.fetch_stock_price(stock)
                    st.markdown(format_stock_response(stock_data))


# TAB 2: Web Scraper
with tab2:
    st.header("🔍 Intelligent Web Scraper")
    st.markdown("Scrape websites for specific financial information using AI")

    if not api_key and st.session_state.assistant is None:
        st.warning("⚠️ Please configure your Google API Key in the sidebar to use web scraping")

    url_input = st.text_input(
        "Website URL",
        placeholder="https://example.com/financial-news",
        key="scrape_url"
    )

    query_input = st.text_area(
        "What are you looking for?",
        placeholder="e.g., Tesla earnings report, Apple product launch, Market trends",
        key="scrape_query",
        height=100
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("🚀 Scrape Website", key="scrape_btn", use_container_width=True):
            if not url_input or not query_input:
                st.error("Please provide both URL and search query")
            elif st.session_state.assistant is None:
                st.error("Please configure your API key first")
            else:
                with st.spinner(f"Scraping {url_input}..."):
                    scraped_data = st.session_state.assistant.scrape_url(url_input, query_input)

                    st.divider()
                    st.subheader("📄 Scraping Results")
                    st.markdown(format_scraped_response(scraped_data))

    with col2:
        if st.button("🗑️ Clear", key="clear_scraper"):
            st.rerun()

    st.divider()

    # Examples
    with st.expander("💡 See Examples"):
        st.markdown("""
        **Example 1: Company News**
        - URL: `https://finance.yahoo.com/quote/TSLA`
        - Query: `Tesla latest news and stock performance`

        **Example 2: Market Analysis**
        - URL: `https://www.investing.com/analysis/stock-market-analysis`
        - Query: `Current market trends and predictions`

        **Example 3: Earnings Report**
        - URL: `https://www.apple.com/newsroom/`
        - Query: `Apple quarterly earnings and revenue`
        """)


# TAB 3: Smart Assistant (Chat Mode)
with tab3:
    st.header("🤖 Smart Assistant")
    st.markdown("Ask questions naturally - AI will understand and fetch the right data!")

    # Chat interface
    st.subheader("💬 Chat")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Ask me anything about stocks, Bitcoin, or financial news...")

    if user_input:
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if st.session_state.assistant is None:
                    initialize_assistant(api_key)

                result = st.session_state.assistant.process_query(user_input)

                response_parts = []

                # Format response based on what was found
                intent = result['analysis'].get('intent', 'unknown')

                if intent == 'unknown':
                    response_parts.append("I'm not sure what you're asking for. Please try:")
                    response_parts.append("- 'AAPL stock price'")
                    response_parts.append("- 'Bitcoin value'")
                    response_parts.append("- 'Scrape [URL] for [query]'")

                # Stock data
                if result.get('stock_data'):
                    response_parts.append(format_stock_response(result['stock_data']))

                # Bitcoin data
                if result.get('bitcoin_data'):
                    response_parts.append(format_bitcoin_response(result['bitcoin_data']))

                # Scraped data
                if result.get('scraped_data'):
                    for scraped in result['scraped_data']:
                        response_parts.append(format_scraped_response(scraped))

                response = "\n\n---\n\n".join(response_parts) if response_parts else "I couldn't find any relevant information."

                st.markdown(response)

                # Add assistant response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

    st.divider()

    # Smart assistant examples
    with st.expander("💡 Example Queries"):
        st.markdown("""
        **Price Queries:**
        - "What is the Apple stock price?"
        - "Show me Tesla's current value"
        - "Bitcoin price today"

        **Combined Queries:**
        - "Get AAPL stock price and scrape https://apple.com/newsroom for latest news"
        - "Tesla stock and news from https://www.teslarati.com"

        **Web Scraping:**
        - "Scrape https://finance.yahoo.com for market trends"
        - "Get information from https://bloomberg.com about inflation"
        """)


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Financial Assistant</strong> v1.0</p>
    <p>Stock data from Yahoo Finance • Bitcoin data from Coinlore • Powered by Google Gemini</p>
    <p><em>⚠️ For informational purposes only. Not financial advice.</em></p>
</div>
""", unsafe_allow_html=True)
