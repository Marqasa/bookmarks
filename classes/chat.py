from classes.ai import AI
from classes.bookmark import Bookmark
from classes.bookmark_store import BookmarkStore
from classes.website import Website
from gradio import MessageDict
from openai.types.responses.function_tool_param import FunctionToolParam
from openai.types.responses.response import Response
from openai.types.responses.response_input_param import (
    ResponseInputParam,
    FunctionCallOutput,
)
from typing import Any, Dict, List
import gradio as gr
import json


class Chat:
    ADD_BOOKMARKS_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "add_bookmarks",
        "description": "Add a list of URLs to the user's bookmarks",
        "parameters": {
            "type": "object",
            "required": ["urls", "category_guidance"],
            "properties": {
                "urls": {
                    "type": "array",
                    "description": "List of URLs to be bookmarked",
                    "items": {"type": "string", "description": "A single URL"},
                },
                "category_guidance": {
                    "type": ["string", "null"],
                    "description": "This should be null unless the user has a specific category in mind",
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
    DELETE_BOOKMARKS_BY_CATEGORY_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "delete_bookmarks_by_category",
        "description": "Deletes all bookmarks in a specified category",
        "parameters": {
            "type": "object",
            "required": ["category_path"],
            "properties": {
                "category_path": {
                    "type": "string",
                    "description": "The category path to delete bookmarks from, e.g., 'Category/Subcategory'",
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
    MOVE_BOOKMARKS_BY_CATEGORY_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "move_bookmarks_by_category",
        "description": "Moves all bookmarks in a category to a new category",
        "parameters": {
            "type": "object",
            "required": ["parent_path", "new_parent_path"],
            "properties": {
                "parent_path": {
                    "type": "string",
                    "description": "The parent path of the category to be moved, e.g., 'Category/Subcategory'",
                },
                "new_parent_path": {
                    "type": "string",
                    "description": "The new parent path for the category, e.g., 'NewCategory/NewSubcategory'",
                },
            },
            "additionalProperties": False,
        },
        "strict": True,
    }
    GET_BOOKMARKS_BY_CATEGORY_TOOL: FunctionToolParam = {
        "type": "function",
        "name": "get_bookmarks_by_category",
        "description": "Returns all bookmarks in a specified category",
        "parameters": {
            "type": "object",
            "required": ["category_path"],
            "properties": {
                "category_path": {
                    "type": "string",
                    "description": "The category path to retrieve bookmarks from, e.g., 'Category/Subcategory'",
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
            self.ADD_BOOKMARKS_TOOL,
            self.DELETE_BOOKMARK_TOOL,
            self.DELETE_BOOKMARKS_BY_CATEGORY_TOOL,
            self.MOVE_BOOKMARK_TOOL,
            self.MOVE_BOOKMARKS_BY_CATEGORY_TOOL,
            self.GET_BOOKMARKS_BY_CATEGORY_TOOL,
            self.SEARCH_BOOKMARKS_TOOL,
            self.GET_CATEGORIES_TOOL,
        ]
        self.chat_history: ResponseInputParam = []
        self.chat_history_limit: int = 25

    def add_bookmarks(self, urls: List[str], category_guidance: str | None) -> str:
        """
        Adds a list of bookmarks to the database.

        Args:
            urls (List[str]): List of URLs to be added
            category_guidance (str | None): Category guidance for the bookmarks
        Returns:
            str: JSON string containing status and message
        """
        try:
            for url in urls:
                website = Website(url)
                bookmark = Bookmark(
                    url=url,
                    title=website.title,
                    summary=website.description,
                )
                existing_categories = self.bookmark_store.get_all_categories()
                category = self.ai.generate_category(
                    bookmark,
                    existing_categories=existing_categories,
                    category_guidance=category_guidance,
                )
                bookmark.category = category
                self.bookmark_store.add_bookmark(bookmark)

            # Return success message
            return json.dumps(
                {
                    "status": "added",
                    "message": "Bookmarks added successfully",
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error occurred: {str(e)}",
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

    def delete_bookmarks_by_category(self, category_path: str) -> str:
        """
        Deletes all bookmarks in a specified category.

        Args:
            category_path (str): The category path to delete bookmarks from
        Returns:
            str: JSON string containing status and message
        """
        try:
            # Get all bookmarks in the specified category
            bookmarks = self.bookmark_store.get_bookmarks_by_category_prefix(
                category_path
            )

            # Check if any bookmarks were found
            if not bookmarks:
                return json.dumps(
                    {
                        "status": "not_found",
                        "message": "No bookmarks found in the specified category",
                    }
                )

            # Delete each bookmark from the database
            for bookmark in bookmarks:
                self.bookmark_store.delete_bookmark(bookmark.url)

            # Return success message
            return json.dumps(
                {
                    "status": "deleted",
                    "message": "Bookmarks deleted successfully",
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

    def move_bookmarks_by_category(self, parent_path: str, new_parent_path: str) -> str:
        """
        Moves all bookmarks in a specified category to a new category.
        Args:
            parent_path (str): The parent path of the category to be moved
            new_parent_path (str): The new parent path for the category
        Returns:
            str: JSON string containing status and message
        """
        try:
            # Get all bookmarks in the specified category
            bookmarks = self.bookmark_store.get_bookmarks_by_category_prefix(
                parent_path
            )

            # Check if any bookmarks were found
            if not bookmarks:
                return json.dumps(
                    {
                        "status": "not_found",
                        "message": "No bookmarks found in the specified category",
                    }
                )

            # Move each bookmark to the new category
            for bookmark in bookmarks:
                bookmark.category = bookmark.category.replace(
                    parent_path, new_parent_path
                )
                self.bookmark_store.add_bookmark(bookmark)

            # Return success message
            return json.dumps(
                {
                    "status": "moved",
                    "message": "Bookmarks moved successfully",
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error occurred: {str(e)}",
                }
            )

    def get_bookmarks_by_category(self, category_path: str) -> str:
        """
        Retrieves all bookmarks in a specified category.

        Args:
            category_path (str): The category path to retrieve bookmarks from
        Returns:
            str: JSON string containing status and list of bookmarks
        """
        try:
            # Get all bookmarks in the specified category
            bookmarks = self.bookmark_store.get_bookmarks_by_category(category_path)

            # Return the bookmarks as JSON
            return json.dumps(
                {
                    "status": "found",
                    "message": "Bookmarks found",
                    "bookmarks": [bookmark.to_dict() for bookmark in bookmarks],
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
                        bookmark.to_dict() for bookmark in matching_bookmarks
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

            self.chat_history.append(
                {
                    "type": "message",
                    "role": "user",
                    "content": message,
                }
            )

            # Create a response with the AI
            response: Response = self.ai.client.responses.create(
                model=self.ai.model,
                instructions=(
                    "You are a helpful assistant that can manage bookmarks.\n\n"
                    "A bookmark is represented as:\n"
                    "Title: 'My Bookmark'\n"
                    "Category: 'Category/Subcategory'\n"
                    "URL: 'https://example.com'\n"
                    "Summary: 'This is a summary of the bookmark.'"
                ),
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
                function_call_output = FunctionCallOutput(
                    type="function_call_output",
                    call_id=item.call_id,
                    output=str(result),
                )
                self.chat_history.append(function_call_output)

            # If a tool was called, inform the AI
            if tool_called:
                self.chat_history.append(
                    {
                        "type": "message",
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

            # Limit chat history to the specified limit
            self.limit_chat_history()

            return response.output_text
        except Exception as e:
            # Log the error and return a user-friendly message
            print(f"Error in chat method: {str(e)}")
            return f"I encountered an error while processing your request. Please try again."

    def limit_chat_history(self) -> None:
        """
        Removes oldest items in the chat_history to respect the chat_history_limit.
        If a removed item is a function_call, also removes its matching function_call_output.
        """
        while len(self.chat_history) > self.chat_history_limit:
            first_item = self.chat_history.pop(0)

            # Get type and call_id, handling both object and dict structures
            first_item_type = (
                getattr(first_item, "type", None)
                if not isinstance(first_item, dict)
                else first_item.get("type")
            )
            first_item_call_id = (
                getattr(first_item, "call_id", None)
                if not isinstance(first_item, dict)
                else first_item.get("call_id")
            )

            if first_item_type == "function_call":
                for i, next_item in enumerate(self.chat_history):
                    # Get type and call_id, handling both object and dict structures
                    next_item_type = (
                        getattr(next_item, "type", None)
                        if not isinstance(next_item, dict)
                        else next_item.get("type")
                    )
                    next_item_call_id = (
                        getattr(next_item, "call_id", None)
                        if not isinstance(next_item, dict)
                        else next_item.get("call_id")
                    )

                    if (
                        next_item_type == "function_call_output"
                        and next_item_call_id == first_item_call_id
                    ):
                        self.chat_history.pop(i)
                        break

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
            case "delete_bookmarks_by_category":
                return self.delete_bookmarks_by_category(**args)
            case "add_bookmarks":
                return self.add_bookmarks(**args)
            case "move_bookmark":
                return self.move_bookmark(**args)
            case "move_bookmarks_by_category":
                return self.move_bookmarks_by_category(**args)
            case "get_bookmarks_by_category":
                return self.get_bookmarks_by_category(**args)
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
