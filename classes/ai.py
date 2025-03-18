from openai import OpenAI
from classes.website import Website


class AI:
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, api_key=str, model=None):
        self.client = OpenAI(api_key=api_key)
        self.model = model or self.DEFAULT_MODEL

    def summarize_website(self, website: Website):
        """
        Summarize the content of a website using OpenAI, creating a concise summary
        suitable for a bookmark.

        Args:
            website (Website): A Website object with content to summarize

        Returns:
            str: A concise summary of the website content suitable for a bookmark
        """
        website_content = website.get_page_contents()

        prompt = (
            "Create a concise summary (1-2 sentences) of the following website content "
            "that would be perfect for a bookmark description. "
            "The summary should clearly convey what the page contains and why someone "
            "might find it valuable, without being too lengthy.\n\n"
            f"{website_content}"
        )

        response = self.client.responses.create(model=self.model, input=prompt)

        return response.output_text.strip()
