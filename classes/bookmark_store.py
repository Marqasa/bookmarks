import chromadb
from typing import List, Dict, Any, Optional
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
        self.client = chromadb.PersistentClient("./chroma_db")
        self.collection = self.client.get_or_create_collection(collection_name)

    def get_bookmark_by_url(self, url: str) -> Optional[Bookmark]:
        """
        Retrieve a bookmark by its URL.

        Args:
            url (str): The URL to search for

        Returns:
            Optional[Bookmark]: The bookmark object if found, None otherwise
        """
        # Query the collection with the URL as metadata filter
        result = self.collection.get(where={"url": url}, limit=1)

        if result["documents"] and len(result["documents"]) > 0:
            return Bookmark.from_content_string(result["documents"][0])

        return None

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
        existing_bookmarks = self.collection.get(where={"url": bookmark.url})

        if existing_bookmarks and len(existing_bookmarks["ids"]) > 0:
            # Delete the existing bookmarks with this URL
            self.collection.delete(ids=existing_bookmarks["ids"])

        # Add the bookmark to the collection with category metadata
        self.collection.add(
            documents=[bookmark.to_content_string()],
            metadatas=[
                {
                    "url": bookmark.url,
                    "title": bookmark.title,
                    "category": bookmark.category,
                }
            ],
            ids=[bookmark_id],
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
        results = self.collection.query(query_texts=[query], n_results=n_results)

        # Format the results
        bookmarks = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                bookmarks.append(
                    {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                    }
                )

        return bookmarks

    def get_bookmarks_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all bookmarks in a specific category.
        For hierarchical categories, this will match the exact path.

        Args:
            category (str): The category path to filter by

        Returns:
            List[Dict[str, Any]]: List of bookmarks in the category
        """
        results = self.collection.get(where={"category": category})

        bookmarks = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                bookmarks.append(
                    {
                        "id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                    }
                )

        return bookmarks

    def get_bookmarks_by_category_prefix(
        self, category_prefix: str
    ) -> List[Dict[str, Any]]:
        """
        Get all bookmarks in a category and its subcategories.

        Args:
            category_prefix (str): The category prefix to filter by

        Returns:
            List[Dict[str, Any]]: List of bookmarks in the category and subcategories
        """
        # Get all bookmarks
        results = self.collection.get()

        bookmarks = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                metadata = results["metadatas"][i]
                # Check if the bookmark's category starts with the given prefix
                if metadata.get("category", "").startswith(category_prefix):
                    bookmarks.append(
                        {
                            "id": results["ids"][i],
                            "content": results["documents"][i],
                            "metadata": metadata,
                        }
                    )

        return bookmarks

    def get_category_structure(self) -> Dict[str, Any]:
        """
        Get the hierarchical category structure from all bookmarks.

        Returns:
            Dict[str, Any]: A nested dictionary representing the category hierarchy
        """
        # Get all bookmarks' metadata
        results = self.collection.get()

        # Build a category tree
        category_tree = {}

        if results["ids"]:
            for metadata in results["metadatas"]:
                category = metadata.get("category", "")
                if not category:
                    continue

                # Split the category path
                path_parts = category.split("/")

                # Build the tree
                current = category_tree
                for i, part in enumerate(path_parts):
                    if part not in current:
                        current[part] = {} if i < len(path_parts) - 1 else {}
                    current = current[part]

        return category_tree

    def get_all_categories(self) -> List[str]:
        """
        Get a flat list of all category paths used by bookmarks.

        Returns:
            List[str]: A list of all category paths
        """
        # Get all bookmarks' metadata
        results = self.collection.get()

        categories = set()
        if results["ids"]:
            for metadata in results["metadatas"]:
                category = metadata.get("category", "")
                if category:
                    categories.add(category)

                    # Also add parent categories
                    parts = category.split("/")
                    for i in range(1, len(parts)):
                        parent = "/".join(parts[:i])
                        categories.add(parent)

        return sorted(list(categories))

    def get_all_bookmarks(self) -> List[Bookmark]:
        """
        Retrieve all bookmarks from the vector database.

        Returns:
            List[Bookmark]: A list of all bookmark objects
        """
        results = self.collection.get()
        bookmarks: List[Bookmark] = []

        if results["ids"]:
            for i in range(len(results["ids"])):
                bookmark = Bookmark.from_content_string(results["documents"][i])

                if bookmark:
                    bookmarks.append(bookmark)

        return bookmarks
