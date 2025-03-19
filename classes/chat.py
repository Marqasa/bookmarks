import gradio as gr
import json
from typing import Any, Dict, List, Optional, Union
from classes.ai import AI
from classes.website import Website
from classes.bookmark import Bookmark
from classes.bookmark_store import BookmarkStore


class Chat:
    def __init__(self, ai: AI, bookmark_store: BookmarkStore) -> None:
        """
        Initialize the Chat with AI and BookmarkStore instances.

        Args:
            ai (AI): The AI instance for chat and summarization
            bookmark_store (BookmarkStore): The bookmark storage system
        """
        self.ai: AI = ai
        self.bookmark_store: BookmarkStore = bookmark_store

    def add_bookmark(self, url: str) -> str:
        """
        Fetches and summarizes the content from the provided URL,
        then creates a bookmark and stores it in the database.

        Args:
            url (str): The website URL to fetch

        Returns:
            str: The bookmark content string and status message
        """
        try:
            # Check if the URL already exists in the database
            if self.bookmark_store.url_exists(url):
                # Retrieve existing bookmarks with this URL
                results = self.bookmark_store.search_bookmarks(
                    query="URL lookup", n_results=1
                )
                if results:
                    return f"**Bookmark already exists:**\n\n{results[0]['content']}"
                else:
                    return f"Bookmark with URL {url} exists but couldn't be retrieved."

            # Create a new bookmark
            website = Website(url)
            summary = self.ai.summarize_website(website)
            bookmark = Bookmark(url=url, title=website.title, summary=summary)

            # Generate a category for the bookmark
            existing_categories = self.bookmark_store.get_all_categories()
            category = self.ai.generate_category(
                bookmark, existing_categories=existing_categories
            )
            bookmark.category = category

            # Store the bookmark in the database
            self.bookmark_store.add_bookmark(bookmark)

            # Return the formatted bookmark content
            return f"**New bookmark created:**\n\n{bookmark.to_content_string()}"
        except Exception as e:
            return f"Error occurred: {str(e)}"

    def chat_with_ai(self, message: str, history: List[Dict[str, str]]) -> str:
        """
        Chat with the AI and process any tool calls.

        Args:
            message (str): The message from the user
            history (List[Dict[str, str]]): Chat history with role and content

        Returns:
            str: The AI's response
        """
        # Get response from AI
        chat_input = []
        for item in history:
            clean_item = {"role": item["role"], "content": item["content"]}
            chat_input.append(clean_item)

        chat_input.append({"role": "user", "content": message})

        response = self.ai.chat(chat_input)

        tool_called = False

        # Check for tool calls
        for tool_call in response.output:
            if tool_call.type != "function_call":
                continue

            tool_called = True
            name = tool_call.name
            args = json.loads(tool_call.arguments)

            result = self.call_function(name, args)
            chat_input.append(tool_call)
            chat_input.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": str(result),
                }
            )

        # If a tool was called, inform the AI
        if tool_called:
            response = self.ai.chat(chat_input)

        return response.output_text

    def call_function(self, name: str, args: Dict[str, Any]) -> Any:
        """
        Call the appropriate function based on the name and arguments.

        Args:
            name (str): The name of the function to call
            args (Dict[str, Any]): The arguments for the function

        Returns:
            Any: The result of the function call
        """
        if name == "add_bookmark":
            return self.add_bookmark(**args)

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
            fn=self.chat_with_ai,
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
        return chat_interface.launch(inbrowser=inbrowser, **kwargs)
