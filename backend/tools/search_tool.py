from duckduckgo_search import DDGS
from typing import List, Dict

class SearchTool:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, maxResults: int = 5) -> List[Dict[str, str]]:
        try:
            results = list(self.ddgs.text(query, max_results=maxResults))
            return results
        except Exception as e:
            print(f"[SearchTool Error]: {e}")
            return [{"error": str(e)}]

    def news(self, query: str, maxResults: int = 5) -> List[Dict[str, str]]:
        try:
            results = list(self.ddgs.news(query, max_results=maxResults))
            return results
        except Exception as e:
            print(f"[SearchTool Error]: {e}")
            return [{"error": str(e)}]
