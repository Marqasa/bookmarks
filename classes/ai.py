from classes.bookmark import Bookmark
from classes.website import Website
from openai import OpenAI
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response import Response
from openai.types.responses.response_input_param import ResponseInputParam
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from typing import List, Optional, Union
import json


class AI:
    """
    A class that provides AI capabilities through the OpenAI API.

    This class handles interactions with OpenAI's models for tasks like
    website summarization and chat functionality with tool capabilities.
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
                        "type": "array",
                        "description": "An array representing the hierarchical category path for the bookmark",
                        "items": {
                            "type": "string",
                            "description": "A string representing a part of the category path",
                        },
                    },
                },
                "required": ["category"],
                "additionalProperties": False,
            },
            "strict": True,
        }
    }
    ADD_BOOKMARK_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "add_bookmark",
        "description": "Adds a URL to the user's bookmarks",
        "parameters": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to be bookmarked",
                }
            },
            "additionalProperties": False,
        },
        "strict": True,
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

        prompt: str = (
            "Create a concise summary (1-2 sentences) of the following website content "
            "that would be perfect for a bookmark description. "
            "The summary should clearly convey what the page contains and why someone "
            "might find it valuable, without being too lengthy.\n\n"
            f"{website_content}"
        )

        response: Response = self.client.responses.create(
            model=self.model, input=prompt
        )

        return response.output_text.strip()

    def chat(self, input: Union[str, ResponseInputParam]) -> Response:
        """
        Send a chat message to the AI and receive a response.

        This method allows for interactive conversations with the AI model
        and includes the add_bookmark tool for bookmarking functionality.

        Args:
            input (Union[str, ResponseInputParam]): The user input message or a
                                                   ResponseInputParam object

        Returns:
            Response: The AI's response object containing the generated content
                     and any tool calls
        """
        response: Response = self.client.responses.create(
            model=self.model,
            input=input,
            tools=[self.ADD_BOOKMARK_TOOL],
        )

        return response

    def generate_category(
        self,
        bookmark: Bookmark,
        existing_categories: List[str] = [],
        user_guidance: Optional[str] = None,
    ) -> str:
        """
        Generate an appropriate category for a bookmark using AI.

        Uses the bookmark title and summary along with existing categories (if provided)
        to suggest the most appropriate category path. Optional user guidance can be provided
        to influence the category selection.

        Args:
            bookmark (Bookmark): The bookmark object to categorize
            existing_categories (list[str], optional): List of existing category paths to use as reference
            user_guidance (str, optional): User's guidance about desired categorization

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
        user_guidance_text = ""
        if user_guidance:
            user_guidance_text = f"User guidance: {user_guidance}\n\n"

        # Create the prompt with bookmark information and existing categories
        prompt = (
            f"{categories_context}"
            f"{user_guidance_text}"
            f"Generate an appropriate category for this bookmark:\n"
            f"Title: {bookmark.title}\n"
            f"URL: {bookmark.url}\n"
            f"Summary: {bookmark.summary}\n\n"
            "The category should follow a hierarchical structure and be returned as an array of strings. "
            "If it fits an existing category, use that. Otherwise, create a logical new category. "
            f"{'Incorporate user guidance into the category selection.' if user_guidance else ''}"
        )

        # Define the schema for structured output
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text=self.CATEGORY_SCHEMA,
        )

        # Parse the structured output and return just the category
        result = json.loads(response.output_text)

        # Convert the category array to a string path using '/' as separator
        category_path = "/".join(result["category"])

        return category_path
