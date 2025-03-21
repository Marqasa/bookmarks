from classes.ai import AI
from classes.bookmark import Bookmark
from classes.bookmark_store import BookmarkStore
from classes.website import Website
from gradio import MessageDict
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response import Response
from openai.types.responses.response_input_param import ResponseInputParam
from typing import Any, Dict, List
import gradio as gr
import json


class Chat:
    ADD_BOOKMARK_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "add_bookmark",
        "description": "Adds a URL to the user's bookmarks",
        "parameters": {
            "type": "object",
            "required": ["url", "category_guidance"],
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to be bookmarked",
                },
                "category_guidance": {
                    "type": ["string", "null"],
                    "description": "This should be null unless the user has a specific category in mind.",
                },
            },
            "additionalProperties": False,
        },
        "strict": True,
    }
    DELETE_BOOKMARK_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "delete_bookmark",
        "description": "Deletes a URL from the user's bookmarks",
        "parameters": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to be deleted from bookmarks",
                },
            },
            "additionalProperties": False,
        },
        "strict": True,
    }
    MOVE_BOOKMARK_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "move_bookmark",
        "description": "Moves a bookmark to a different category",
        "parameters": {
            "type": "object",
            "required": ["url", "category_path"],
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the bookmark to move",
                },
                "category_path": {
                    "type": "string",
                    "description": "The new category path for the bookmark, e.g., 'Category/Subcategory'",
                },
            },
            "additionalProperties": False,
        },
        "strict": True,
    }
    SEARCH_BOOKMARKS_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "search_bookmarks",
        "description": "Searches for relevant bookmarks using input query. Returns a list of bookmarks including URL, Title, Summary, and Category.",
        "parameters": {
            "type": "object",
            "required": ["query", "max_results"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant bookmarks",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return",
                },
            },
            "additionalProperties": False,
        },
        "strict": True,
    }
    GET_CATEGORIES_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "get_categories",
        "description": "Retrieves the current hierarchical structure of all bookmark categories",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    }

    def __init__(self, ai: AI, bookmark_store: BookmarkStore) -> None:
        """
        Initialize the Chat with AI and BookmarkStore instances.

        Args:
            ai (AI): The AI instance for chat and summarization
            bookmark_store (BookmarkStore): The bookmark storage system
        """
        self.ai: AI = ai
        self.bookmark_store: BookmarkStore = bookmark_store
        self.tools: List[FunctionToolParam] = [
            self.ADD_BOOKMARK_TOOL,
            self.DELETE_BOOKMARK_TOOL,
            self.MOVE_BOOKMARK_TOOL,
            self.SEARCH_BOOKMARKS_TOOL,
            self.GET_CATEGORIES_TOOL,
        ]
        self.chat_history: ResponseInputParam = []
        self.chat_history_limit: int = 10

    def add_bookmark(self, url: str, category_guidance: str | None) -> str:
        """
        Fetches and summarizes the content from the provided URL,
        then creates a bookmark and stores it in the database.

        Args:
            url (str): The website URL to fetch

        Returns:
            str: JSON string containing status, message, and bookmark data
        """
        try:
            # Check if the URL already exists in the database
            existing_bookmark = self.bookmark_store.get_bookmark_by_url(url)
            if existing_bookmark:
                return json.dumps(
                    {
                        "status": "exists",
                        "message": "Bookmark already exists",
                        "bookmark": existing_bookmark.to_content_string(),
                    }
                )

            # Create a new bookmark
            website = Website(url)
            bookmark = Bookmark(
                url=url, title=website.title, summary=website.description
            )

            # Generate a category for the bookmark
            existing_categories = self.bookmark_store.get_all_categories()
            category = self.ai.generate_category(
                bookmark,
                existing_categories=existing_categories,
                category_guidance=category_guidance,
            )
            bookmark.category = category

            # Store the bookmark in the database
            self.bookmark_store.add_bookmark(bookmark)

            # Return the bookmark data as JSON
            return json.dumps(
                {
                    "status": "created",
                    "message": "New bookmark created",
                    "bookmark": bookmark.to_content_string(),
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error occurred: {str(e)}",
                    "bookmark": None,
                }
            )

    def delete_bookmark(self, url: str) -> str:
        """
        Deletes a bookmark from the database using the provided URL.

        Args:
            url (str): The website URL to delete
        Returns:
            str: JSON string containing status and message
        """
        try:
            # Check if the URL exists in the database
            existing_bookmark = self.bookmark_store.get_bookmark_by_url(url)
            if not existing_bookmark:
                return json.dumps(
                    {
                        "status": "not_found",
                        "message": "Bookmark not found",
                    }
                )

            # Delete the bookmark from the database
            self.bookmark_store.delete_bookmark(existing_bookmark.url)

            # Return success message
            return json.dumps(
                {
                    "status": "deleted",
                    "message": "Bookmark deleted successfully",
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error occurred: {str(e)}",
                }
            )

    def move_bookmark(self, url: str, category_path: str) -> str:
        """
        Moves a bookmark to a different category.

        Args:
            url (str): The website URL of the bookmark
            category_path (str): The new category path for the bookmark
        Returns:
            str: JSON string containing status and message
        """
        try:
            # Check if the URL exists in the database
            existing_bookmark = self.bookmark_store.get_bookmark_by_url(url)
            if not existing_bookmark:
                return json.dumps(
                    {
                        "status": "not_found",
                        "message": "Bookmark not found",
                    }
                )

            # Update the category path
            existing_bookmark.category = category_path

            # Save the updated bookmark to the database
            self.bookmark_store.add_bookmark(existing_bookmark)

            # Return success message
            return json.dumps(
                {
                    "status": "moved",
                    "message": "Bookmark moved successfully",
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error occurred: {str(e)}",
                }
            )

    def search_bookmarks(self, query: str, max_results: int) -> str:
        """
        Searches for bookmarks that match the provided query.

        Args:
            query (str): The search query
            max_results (int): The maximum number of results to return
        Returns:
            str: JSON string containing status and matching bookmarks
        """
        try:
            # Search for bookmarks in the database
            matching_bookmarks = self.bookmark_store.search_bookmarks(
                query, max_results
            )

            # Return the matching bookmarks as JSON
            return json.dumps(
                {
                    "status": "found",
                    "message": "Bookmarks found",
                    "bookmarks": [
                        bookmark.to_content_string() for bookmark in matching_bookmarks
                    ],
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error occurred: {str(e)}",
                }
            )

    def get_categories(self) -> str:
        """
        Retrieves the current hierarchical structure of all bookmark categories.

        Returns:
            str: JSON string containing status and list of categories
        """
        try:
            # Get all categories from the database
            categories = self.bookmark_store.get_category_structure()

            # Return the categories as JSON
            return json.dumps(
                {
                    "status": "found",
                    "message": "Categories found",
                    "categories": categories,
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error occurred: {str(e)}",
                }
            )

    def chat(self, message: str, history: List[MessageDict]) -> str:
        """
        Chat with the AI and process any tool calls.

        Args:
            message (str): The message from the user
            history (List[Dict[str, str]]): Chat history with role and content

        Returns:
            str: The AI's response
        """
        try:
            # Clear chat history if history is empty
            if not history:
                self.chat_history = []

            self.chat_history.append({"role": "user", "content": message})

            # Create a response with the AI
            response: Response = self.ai.client.responses.create(
                model=self.ai.model,
                input=self.chat_history,
                tools=self.tools,
            )

            tool_called = False

            # Process response output
            for item in response.output:
                self.chat_history.append(item)

                if item.type != "function_call":
                    continue

                tool_called = True
                name = item.name
                args = json.loads(item.arguments)

                result = self.call_function(name, args)
                self.chat_history.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": str(result),
                    }
                )

            # If a tool was called, inform the AI
            if tool_called:
                self.chat_history.append(
                    {
                        "role": "developer",
                        "content": "If you need to perform follow-up actions, confirm with the user first.",
                    }
                )
                # Recreate the chat input with the tool call
                response = self.ai.client.responses.create(
                    model=self.ai.model,
                    input=self.chat_history,
                    tools=self.tools,
                    tool_choice="none",
                )

            # Limit chat history
            if len(self.chat_history) > self.chat_history_limit:
                self.chat_history = self.chat_history[-self.chat_history_limit :]

            return response.output_text
        except Exception as e:
            # Log the error and return a user-friendly message
            print(f"Error in chat method: {str(e)}")
            return f"I encountered an error while processing your request. Please try again."

    def call_function(self, name: str, args: Dict[str, Any]) -> Any:
        """
        Call the appropriate function based on the name and arguments.

        Args:
            name (str): The name of the function to call
            args (Dict[str, Any]): The arguments for the function

        Returns:
            Any: The result of the function call
        """
        match name:
            case "delete_bookmark":
                return self.delete_bookmark(**args)
            case "add_bookmark":
                return self.add_bookmark(**args)
            case "move_bookmark":
                return self.move_bookmark(**args)
            case "search_bookmarks":
                return self.search_bookmarks(**args)
            case "get_categories":
                return self.get_categories()

    def create_ui(
        self,
        title: str = "Website Bookmarker",
        description: str = "Chat with AI to bookmark websites.",
    ) -> gr.ChatInterface:
        """
        Create the Gradio chat interface.

        Args:
            title (str): The title for the chat interface
            description (str): The description for the chat interface

        Returns:
            gr.ChatInterface: The Gradio chat interface
        """
        return gr.ChatInterface(
            fn=self.chat,
            type="messages",
            title=title,
            description=description,
        )

    def launch(self, inbrowser: bool = True, **kwargs: Any) -> Any:
        """
        Launch the chat interface.

        Args:
            inbrowser (bool): Whether to open in browser
            **kwargs: Additional arguments to pass to the launch method

        Returns:
            Any: The result of launching the interface
        """
        chat_interface = self.create_ui()
        return chat_interface.launch(**kwargs)
