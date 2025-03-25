from classes.ai import AI
from classes.bookmark_store import BookmarkStore
from classes.chat import Chat
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("MODEL")

# Initialize the bookmark store and AI
bookmark_store = BookmarkStore()
ai = AI(api_key=api_key, model=model)

# Initialize the chat
chat = Chat(ai, bookmark_store)

if __name__ == "__main__":
    chat.launch(inbrowser=True)
