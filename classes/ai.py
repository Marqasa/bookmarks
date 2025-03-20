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

        Uses the bookmark title and summary along with existing categories (if provided)
        to suggest the most appropriate category path. Optional category guidance can be provided
        to influence the category selection.

        Args:
            bookmark (Bookmark): The bookmark object to categorize
            existing_categories (list[str], optional): List of existing category paths to use as reference
            category_guidance (str, optional): Guidance about desired categorization

        Returns:
            str: A category path string using '/' as separator (e.g., "Tech/Programming/Python")
        """
        # Prepare the existing categories as a string if provided
        categories_context = ""
        if existing_categories and len(existing_categories) > 0:
            categories_context = (
                "Existing categories:\n" + "\n".join(existing_categories) + "\n\n"
            )

        # Add user guidance if provided
        category_guidance_text = ""
        if category_guidance:
            category_guidance_text = f"Category guidance: {category_guidance}\n\n"

        # Create the prompt with bookmark information and existing categories
        prompt = (
            f"{categories_context}"
            f"{category_guidance_text}"
            f"Generate an appropriate category for this bookmark:\n"
            f"Title: {bookmark.title}\n"
            f"URL: {bookmark.url}\n"
            f"Summary: {bookmark.summary}\n\n"
            "The category should follow a hierarchical structure and be returned as a string with '/' as the separator. "
            f"{'If it fits an existing category, use that. Otherwise, create a logical new category.' if categories_context else ''}"
            f"{'Incorporate category guidance when making a selection.' if category_guidance else ''}"
        )

        # Define the schema for structured output
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text=self.CATEGORY_SCHEMA,
        )

        # Parse the JSON response
        result = json.loads(response.output_text)

        # Extract the category from the response
        category = result["category"]

        return category
