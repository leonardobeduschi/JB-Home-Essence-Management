"""
ID generation utilities.

This module provides functions to generate unique IDs for clients and sales.
"""

import pandas as pd
import re
from typing import Optional


class IDGenerator:
    """Utility class for generating unique IDs."""
    
    @staticmethod
    def generate_client_id(existing_ids: list) -> str:
        """
        Generate unique client ID in format CLI001, CLI002, etc.
        
        Args:
            existing_ids: List of existing client IDs
            
        Returns:
            New unique client ID
        """
        if not existing_ids:
            return "CLI001"
        
        # Extract numeric parts from existing IDs
        numbers = []
        for id_str in existing_ids:
            # Match pattern like CLI001, CLI002, etc.
            match = re.search(r'CLI(\d+)', str(id_str).upper())
            if match:
                numbers.append(int(match.group(1)))
        
        # Get next number
        if numbers:
            next_num = max(numbers) + 1
        else:
            next_num = 1
        
        # Format with leading zeros (3 digits)
        return f"CLI{next_num:03d}"
    
    @staticmethod
    def generate_sale_id(existing_ids: list) -> str:
        """
        Generate unique sale ID in format VND001, VND002, etc.
        
        Args:
            existing_ids: List of existing sale IDs
            
        Returns:
            New unique sale ID
        """
        if not existing_ids:
            return "VND001"
        
        # Extract numeric parts from existing IDs
        numbers = []
        for id_str in existing_ids:
            # Match pattern like VND001, VND002, etc.
            match = re.search(r'VND(\d+)', str(id_str).upper())
            if match:
                numbers.append(int(match.group(1)))
        
        # Get next number
        if numbers:
            next_num = max(numbers) + 1
        else:
            next_num = 1
        
        # Format with leading zeros (3 digits)
        return f"VND{next_num:03d}"
    
    @staticmethod
    def is_valid_client_id(id_str: str) -> bool:
        """
        Validate client ID format.
        
        Args:
            id_str: ID string to validate
            
        Returns:
            True if format is valid (CLI followed by digits)
        """
        if not id_str:
            return False
        
        pattern = r'^CLI\d+$'
        return bool(re.match(pattern, id_str.upper()))
    
    @staticmethod
    def is_valid_sale_id(id_str: str) -> bool:
        """
        Validate sale ID format.
        
        Args:
            id_str: ID string to validate
            
        Returns:
            True if format is valid (VND followed by digits)
        """
        if not id_str:
            return False
        
        pattern = r'^VND\d+$'
        return bool(re.match(pattern, id_str.upper()))