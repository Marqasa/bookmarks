from classes.bookmark import Bookmark
from classes.website import Website
from openai import OpenAI
from openai.types.responses.response import Response
from openai.types.responses.response_input_param import ResponseInputParam
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from typing import List, Optional
import json


class AI:
    """
    A class that provides AI capabilities through the OpenAI API.

    This class handles interactions with OpenAI's models for tasks like
    website summarization and category generation.
    """

    DEFAULT_MODEL: str = "gpt-4o-mini"
    CATEGORY_SCHEMA: ResponseTextConfigParam = {
        "format": {
            "type": "json_schema",
            "name": "category",
            "description": "A JSON schema defining the category path for the bookmark",
            "schema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "A category path string using '/' as separator (e.g., 'Category/Subcategory')",
                    },
                },
                "required": ["category"],
                "additionalProperties": False,
            },
            "strict": True,
        }
    }

    def __init__(self, api_key: str, model: Optional[str] = None) -> None:
        """
        Initialize the AI client.

        Args:
            api_key (str): The OpenAI API key for authentication
            model (str, optional): The model to use for AI operations.
                                  Defaults to DEFAULT_MODEL if not specified.
        """
        self.client: OpenAI = OpenAI(api_key=api_key)
        self.model: str = model or self.DEFAULT_MODEL

    def summarize_website(self, website: Website) -> str:
        """
        Summarize the content of a website using OpenAI.

        Creates a concise summary (1-2 sentences) suitable for a bookmark description
        based on the website's content.

        Args:
            website (Website): A Website object with content to summarize

        Returns:
            str: A concise summary of the website content
        """
        website_content: str = website.get_page_contents()

        prompt: ResponseInputParam = [
            {
                "role": "developer",
                "content": "You are an expert summarizer. You will be provided with a website's title, url, and content. Your task is to summarize the content in a concise manner. If you do not have enough information, provide the best summary possible based on the given data.",
            },
            {
                "role": "user",
                "content": f"{website_content}",
            },
        ]

        response: Response = self.client.responses.create(
            model=self.model, input=prompt
        )

        return response.output_text.strip()

    def generate_category(
        self,
        bookmark: Bookmark,
        existing_categories: List[str] = [],
        category_guidance: Optional[str] = None,
    ) -> str:
        """
        Generate an appropriate category for a bookmark using AI.

        Args:
            bookmark (Bookmark): The bookmark object to categorize
            existing_categories (list[str], optional): List of existing category paths to use as reference
            category_guidance (str, optional): Guidance about desired categorization

        Returns:
            str: A category path string using '/' as separator (e.g., "Category/Subcategory")
        """
        # Build developer instructions
        developer_content = (
            "You are a bookmark categorization expert. Generate an appropriate category "
            "for a bookmark based on its title, URL, and summary. The category should follow "
            "a hierarchical structure using '/' as the separator (e.g., 'Category/Subcategory')."
        )

        if existing_categories:
            developer_content += " Try to use existing categories when appropriate."

        if category_guidance:
            developer_content += (
                " Consider the provided category guidance in your selection."
            )

        # Build user content with bookmark details
        user_content = f"Bookmark to categorize:\nTitle: {bookmark.title}\nURL: {bookmark.url}\nSummary: {bookmark.summary}\n\n"

        if existing_categories:
            user_content = (
                f"Existing categories:\n{'\n'.join(existing_categories)}\n\n"
                + user_content
            )

        if category_guidance:
            user_content = f"Category guidance:\n{category_guidance}\n\n" + user_content

        # Create the prompt
        prompt: ResponseInputParam = [
            {"role": "developer", "content": developer_content},
            {"role": "user", "content": user_content},
        ]

        # Make API call
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text=self.CATEGORY_SCHEMA,
        )

        # Parse and return the category
        result = json.loads(response.output_text)
        return result["category"]
