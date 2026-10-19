class FoodService:
    """Service for interacting with data source to search for foods"""

    def search(self, name: str) -> list[str]:
        """Search open food facts api for a list of foods like 'name'"""
        return [name]
