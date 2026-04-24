"""Fallback data service for local content"""

from typing import Dict
from app.data.fallback_content import FALLBACK_DATA


class FallbackService:
    """Service for providing bundled fallback data"""
    
    def __init__(self):
        """Initialize fallback service"""
        self._data = FALLBACK_DATA
    
    def get_fallback_data(self) -> Dict[str, Dict]:
        """
        Get complete fallback dataset for all categories.

        Returns a deep copy so callers cannot mutate internal state.

        Returns:
            Dict[str, Dict]: Complete fallback data mapping categories to responses
        """
        import copy
        return copy.deepcopy(self._data)
    
    def get_category_data(self, category: str) -> Dict:
        """
        Get fallback data for a specific category
        
        Args:
            category: Intent category name
            
        Returns:
            Dict: Response data for the category, or FAQ data if category not found
        """
        return self._data.get(category, self._data.get("faq", {}))
    
    def has_category(self, category: str) -> bool:
        """
        Check if category exists in fallback data
        
        Args:
            category: Intent category name
            
        Returns:
            bool: True if category exists
        """
        return category in self._data
    
    def get_categories(self) -> list:
        """
        Get list of all available categories
        
        Returns:
            list: List of category names
        """
        return list(self._data.keys())
