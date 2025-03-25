# AI-Powered Bookmark Manager

A smart bookmark management system that uses AI to help you organize and retrieve your web bookmarks with natural language queries.

## Features

-   **AI-Generated Summaries**: Automatically creates concise summaries of bookmarked websites
-   **Smart Categorization**: Uses AI to categorize bookmarks into a hierarchical structure
-   **Vector Search**: Find bookmarks using natural language queries
-   **Chat Interface**: Interact with your bookmarks through a user-friendly chat interface
-   **Persistent Storage**: Bookmarks are stored in a local vector database

## Installation

1. Clone the repository:

    ```bash
    git clone <repository-url>
    cd bookmarks
    ```

2. Set up a virtual environment:

    ```bash
    python -m venv venv

    # On Windows
    venv\Scripts\activate

    # On macOS/Linux
    source venv/bin/activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the project root with your OpenAI API key:
    ```
    OPENAI_API_KEY=your_api_key_here
    MODEL=gpt-4o  # Optional: specify which OpenAI model to use (defaults to gpt-4o-mini)
    ```

## Usage

Run the application:

```bash
python main.py
```

This will launch the chat interface in your web browser.

### Example Commands

-   **Add a bookmark**: "Please bookmark https://example.com in the Technology category"
-   **Find bookmarks**: "Show me my programming bookmarks"
-   **Search by content**: "Find bookmarks about machine learning"
-   **Delete a bookmark**: "Remove the bookmark for https://example.com"

## How It Works

The system uses:

-   **ChromaDB**: For storing and retrieving bookmarks as vector embeddings
-   **OpenAI**: For generating summaries and categories, and providing the chat interface
-   **Gradio**: For the web-based chat UI
-   **BeautifulSoup**: For extracting content from web pages

## Project Structure

-   `classes/`
    -   `bookmark.py`: Defines the Bookmark data model
    -   `bookmark_store.py`: Handles storage and retrieval of bookmarks
    -   `website.py`: Fetches and extracts content from websites
    -   `ai.py`: Provides AI capabilities for summarization and categorization
    -   `chat.py`: Implements the chat interface
-   `main.py`: Initializes and runs the application

## Requirements

-   Python 3.9+
-   OpenAI API key
-   Internet connection for fetching website content and accessing OpenAI

## License

This project is licensed under the MIT License.
