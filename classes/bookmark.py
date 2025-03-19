from dataclasses import dataclass
from typing import Optional


@dataclass
class Bookmark:
    """
    Represents a web bookmark with associated metadata.

    Attributes:
        url (str): The URL of the bookmarked webpage
        title (str): The title of the bookmark
        summary (str): A brief description or summary of the webpage content
        category (str): Category path using '/' as separator (e.g., "Tech/Programming/Python")
    """

    url: str
    title: str
    summary: str
    category: str = ""  # Default to empty string (uncategorized)

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
            str: Formatted string containing the bookmark's title, category, URL, and summary
        """
        return f"Title: {self.title}\n\nCategory: {self.category}\n\nURL: {self.url}\n\nSummary: {self.summary}"

    @classmethod
    def from_content_string(cls, content: str) -> Optional["Bookmark"]:
        """
        Creates a Bookmark instance from a content string.

        Args:
            content (str): The content string containing the bookmark's title, category, URL, and summary

        Returns:
            Optional[Bookmark]: A new Bookmark instance or None if parsing fails
        """
        try:
            lines = content.split("\n\n")
            if len(lines) < 4:
                return None
            title = lines[0].replace("Title: ", "")
            category = lines[1].replace("Category: ", "")
            url = lines[2].replace("URL: ", "")
            summary = lines[3].replace("Summary: ", "")
            return cls(url=url, title=title, summary=summary, category=category)
        except Exception:
            return None
