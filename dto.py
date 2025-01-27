from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str = "how to create an account?"
    k: int = 2
    source: str = "FAQ"