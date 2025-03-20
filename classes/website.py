from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from urllib.parse import urlparse
import requests


class Website:
    """Class for fetching and extracting content from websites."""

    DEFAULT_TIMEOUT = 10
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

    def __init__(self, url, timeout=None, user_agent=None):
        """
        Initialize a Website object.

        Args:
            url (str): The URL to fetch content from
            timeout (int, optional): Request timeout in seconds
            user_agent (str, optional): Custom User-Agent string

        Raises:
            RequestException: If the request fails or returns a non-200 status code
        """
        self.url = url
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT

        try:
            self.body = self._fetch_content()
            soup = BeautifulSoup(self.body, "html.parser")
            self.title = self._extract_title(soup)
            self.text = self._extract_text(soup)
        except RequestException as e:
            self.body = None
            self.title = f"Error: {str(e)}"
            self.text = ""

    def _fetch_content(self):
        """
        Fetch the content from the base URL.

        Returns:
            bytes: The response content

        Raises:
            RequestException: If the request fails or returns a non-200 status code
        """
        base_url = self._get_base_url(self.url)
        response = requests.get(
            base_url, headers={"User-Agent": self.user_agent}, timeout=self.timeout
        )
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        return response.content

    def _get_base_url(self, url):
        """
        Extract the base URL from the given URL.

        Args:
            url (str): The URL to extract the base from

        Returns:
            str: The base URL
        """

        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    def _extract_title(self, soup):
        """Extract the page title from the soup object."""
        return soup.title.string if soup.title else "No title found"

    def _extract_text(self, soup):
        """Extract the main text content from the soup object."""
        if not soup.body:
            return ""

        # Remove non-content elements
        for tag in soup.body(["script", "style", "img", "input", "meta", "noscript"]):
            tag.decompose()

        return soup.body.get_text(separator="\n", strip=True)

    def get_page_contents(self):
        """
        Get the title and main text content of the webpage.

        Returns:
            str: A formatted string containing the webpage title and main text content
        """
        return f"Title:\n{self.title}\n\nURL:\n{self.url}\n\nContents:\n{self.text}"
