from venv import logger
from tavily import TavilyClient
from os import getenv


class TavilyService:
    def __init__(self):
        self.api_key = getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, max_results: int):
        try:
            return self._search(query, max_results=max_results)
        except Exception as e:
            logger.error(f"Error occurred while searching: {e}")
            raise

    def _search(self, query: str, max_results: int):
        try:
            return self.client.search(query)
        except Exception as e:
            logger.error(f"Error occurred while searching: {e}")
            raise
