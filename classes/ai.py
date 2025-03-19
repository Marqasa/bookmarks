from classes.website import Website
from openai import OpenAI
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response import Response
from openai.types.responses.response_input_param import ResponseInputParam
from typing import Optional, Union


class AI:
    """
    A class that provides AI capabilities through the OpenAI API.

    This class handles interactions with OpenAI's models for tasks like
    website summarization and chat functionality with tool capabilities.
    """

    DEFAULT_MODEL: str = "gpt-4o-mini"
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
