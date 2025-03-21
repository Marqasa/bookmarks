import chromadb
from chromadb import QueryResult, GetResult
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
        result = self.collection.get(where={"url": url}, limit=1)

        if result["documents"] and len(result["documents"]) > 0:
            return Bookmark.from_content_string(result["documents"][0])

        return None

    def delete_bookmark(self, url: str) -> None:
        """
        Delete a bookmark by its URL.

        Args:
            url (str): The URL of the bookmark to delete
        """
        result = self.collection.get(where={"url": url})

        if result["ids"] and len(result["ids"]) > 0:
            self.collection.delete(ids=result["ids"])

    def add_bookmark(self, bookmark: Bookmark) -> None:
        """
        Add a bookmark to the vector database.
        If the bookmark with the same URL already exists, it will be replaced.

        Args:
            bookmark (Bookmark): The bookmark to add
        """
        bookmark_id = f"bookmark_{abs(hash(bookmark.url))}"
        existing_bookmarks = self.collection.get(where={"url": bookmark.url})

        if existing_bookmarks and len(existing_bookmarks["ids"]) > 0:
            self.collection.delete(ids=existing_bookmarks["ids"])

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

    def search_bookmarks(self, query: str, max_results: int) -> List[Bookmark]:
        """
        Search for bookmarks similar to the query.

        Args:
            query (str): The search query
            max_results (int): Maximum number of results to return

        Returns:
            List[Bookmark]: List of Bookmark objects matching the query
        """
        results = self.collection.query(query_texts=[query], n_results=max_results)

        return self._get_bookmarks_from_result(results)

    def get_bookmarks_by_category(self, category: str) -> List[Bookmark]:
        """
        Get all bookmarks in a specific category.
        For hierarchical categories, this will match the exact path.

        Args:
            category (str): The category path to filter by

        Returns:
            List[Bookmark]: List of bookmarks in the category
        """
        results = self.collection.get(where={"category": category})

        return self._get_bookmarks_from_result(results)

    def get_bookmarks_by_category_prefix(self, category_prefix: str) -> List[Bookmark]:
        """
        Get all bookmarks in a category and its subcategories.

        Args:
            category_prefix (str): The category prefix to filter by

        Returns:
            List[Bookmark]: List of bookmarks in the category and subcategories
        """
        results = self.collection.get()
        bookmarks: List[Bookmark] = []

        for i in range(len(results["ids"])):
            metadata = results["metadatas"][i]

            if not metadata.get("category", "").startswith(category_prefix):
                continue

            bookmark = Bookmark.from_content_string(results["documents"][i])

            if bookmark:
                bookmarks.append(bookmark)

        return bookmarks

    def get_category_structure(self) -> Dict[str, Any]:
        """
        Get the hierarchical category structure from all bookmarks.

        Returns:
            Dict[str, Any]: A nested dictionary representing the category hierarchy
        """
        results = self.collection.get()
        category_tree: Dict[str, Any] = {}

        for metadata in results["metadatas"]:
            category = metadata.get("category", "")

            if not category:
                continue

            path_parts = category.split("/")
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
        results = self.collection.get()
        categories = set()

        for metadata in results["metadatas"]:
            category = metadata.get("category", "")

            if not category:
                continue

            path_parts = category.split("/")
            for i in range(len(path_parts)):
                categories.add("/".join(path_parts[: i + 1]))

        return sorted(list(categories))

    def get_all_bookmarks(self) -> List[Bookmark]:
        """
        Retrieve all bookmarks from the vector database.

        Returns:
            List[Bookmark]: A list of all bookmark objects
        """
        results = self.collection.get()

        return self._get_bookmarks_from_result(results)

    def _get_bookmarks_from_result(
        self, result: GetResult | QueryResult
    ) -> List[Bookmark]:
        """
        Helper method to convert ChromaDB query results into Bookmark objects.

        This method handles both GetResult and QueryResult types from ChromaDB and
        properly processes document structures that might be nested (like in QueryResult).

        Args:
            result (Union[GetResult, QueryResult]): The result from a vector database
                                                   query or get operation

        Returns:
            List[Bookmark]: A list of Bookmark objects parsed from the result documents
        """
        bookmarks: List[Bookmark] = []
        documents = result["documents"]

        if documents and isinstance(documents[0], list):
            documents = [doc for sublist in documents for doc in sublist]

        for document in documents:
            bookmark = Bookmark.from_content_string(document)

            if bookmark:
                bookmarks.append(bookmark)

        return bookmarks
