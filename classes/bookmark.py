from dataclasses import dataclass
from .website import Website


@dataclass
class Bookmark:
    """
    Represents a web bookmark with associated metadata.

    Attributes:
        url (str): The URL of the bookmarked webpage
        title (str): The title of the bookmark
        summary (str): A brief description or summary of the webpage content
    """

    url: str
    title: str
    summary: str

    def __post_init__(self):
        """Validate bookmark attributes after initialization."""
        if not self.url:
            raise ValueError("URL cannot be empty")
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

    def to_content_string(self) -> str:
        """
        Returns a string representation of the bookmark suitable for storing in a vector database.

        Returns:
            str: Formatted string containing the bookmark's title, summary, and URL
        """
        return f"Title: {self.title}\nSummary: {self.summary}\nURL: {self.url}"
