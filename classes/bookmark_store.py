import chromadb
from typing import List, Dict, Any
from .bookmark import Bookmark


class BookmarkStore:
    """
    A class for storing and retrieving bookmarks from a vector database.
    
    This class uses ChromaDB as the underlying vector database to store
    bookmarks and efficiently query them.
    """
    
    def __init__(self, collection_name: str = "bookmarks"):
        """
        Initialize the BookmarkStore with a ChromaDB collection.
        
        Args:
            collection_name (str): The name of the collection in ChromaDB
        """
        self.client = chromadb.PersistentClient('./chroma_db')
        self.collection = self.client.get_or_create_collection(collection_name)
    
    def url_exists(self, url: str) -> bool:
        """
        Check if a URL already exists in the database.
        
        Args:
            url (str): The URL to check
            
        Returns:
            bool: True if the URL exists, False otherwise
        """
        # Query the collection with the URL as metadata filter
        results = self.collection.query(
            query_texts=["URL lookup"],
            where={"url": url},
            n_results=1
        )
        
        # If we got any results, the URL exists
        return bool(results["ids"] and len(results["ids"][0]) > 0)
    
    def add_bookmark(self, bookmark: Bookmark) -> None:
        """
        Add a bookmark to the vector database.
        If the bookmark with the same URL already exists, it will be replaced.
        
        Args:
            bookmark (Bookmark): The bookmark to add
        """
        # Generate a unique ID based on the URL
        bookmark_id = f"bookmark_{abs(hash(bookmark.url))}"
        
        # Check if the bookmark already exists
        existing_bookmarks = self.collection.get(
            where={"url": bookmark.url}
        )
        
        if existing_bookmarks and len(existing_bookmarks["ids"]) > 0:
            # Delete the existing bookmarks with this URL
            self.collection.delete(
                ids=existing_bookmarks["ids"]
            )
        
        # Add the bookmark to the collection
        self.collection.add(
            documents=[bookmark.to_content_string()],
            metadatas=[{"url": bookmark.url, "title": bookmark.title}],
            ids=[bookmark_id]
        )
    
    def search_bookmarks(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for bookmarks similar to the query.
        
        Args:
            query (str): The search query
            n_results (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching bookmarks with their metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format the results
        bookmarks = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                bookmarks.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                })
            
        return bookmarks