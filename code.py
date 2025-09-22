nest_asyncio.apply()

class Settings(BaseSettings):
    google_api_key: str

    class Config:
        env_file = '.env'
    try:
        return Settings()
    except ValueError as e:
        logging.error(f"Configuration error: {e}. Ensure GOOGLE_API_KEY is set in your environment or .env file.")
        raise

def setup_logging(level: int = logging.INFO) -> None:
    logging.info(f"Executing node: scraper for URL: {url} with keyword: '{keyword}'")

    settings: Settings = config["configurable"]["settings"]
    api_key = settings.google_api_key

    if not api_key:
        logging.error(f"Google API key missing for scraping {url}.")
        return {
            "extracted_info": None,
            "extracted_from_url": url, 
            "is_information_found": False
        }
    graph_config = {
        "llm": {
            "api_key": api_key,
            "model": "gemini-2.5-pro",
            "temperature": 0.1,
        },
        "verbose": True,

