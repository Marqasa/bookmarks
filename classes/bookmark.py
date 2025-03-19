from dataclasses import dataclass


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
