"""
Manual Service - Gerenciamento de manuais de procedimentos.

Este módulo fornece acesso aos manuais de procedimentos da empresa.
"""

import json
import os
from typing import List, Dict, Optional


class ManualService:
    """
    Service for managing procedure manuals.
    """
    
    def __init__(self, manuals_file: str = 'data/manuals/manuals.json'):
        """
        Initialize manual service.
        
        Args:
            manuals_file: Path to manuals JSON file
        """
        self.manuals_file = manuals_file
        self._ensure_manuals_file()
    
    def _ensure_manuals_file(self) -> None:
        """Ensure manuals directory and file exist."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.manuals_file), exist_ok=True)
        
        # Create file with empty structure if it doesn't exist
        if not os.path.exists(self.manuals_file):
            with open(self.manuals_file, 'w', encoding='utf-8') as f:
                json.dump({'manuals': []}, f, ensure_ascii=False, indent=2)
    
    def get_all_manuals(self) -> List[Dict]:
        """
        Get all manuals.
        
        Returns:
            List of all manuals
        """
        try:
            with open(self.manuals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('manuals', [])
        except Exception as e:
            print(f"Erro ao carregar manuais: {e}")
            return []
    
    def get_manual_by_id(self, manual_id: str) -> Optional[Dict]:
        """
        Get a specific manual by ID.
        
        Args:
            manual_id: Manual identifier
            
        Returns:
            Manual data or None if not found
        """
        manuals = self.get_all_manuals()
        for manual in manuals:
            if manual.get('id') == manual_id:
                return manual
        return None
    
    def get_manuals_summary(self) -> List[Dict]:
        """
        Get summary of all manuals (without detailed steps).
        
        Returns:
            List of manual summaries
        """
        manuals = self.get_all_manuals()
        summaries = []
        
        for manual in manuals:
            summaries.append({
                'id': manual.get('id'),
                'title': manual.get('title'),
                'icon': manual.get('icon'),
                'color': manual.get('color', 'primary'),
                'description': manual.get('description'),
                'sections_count': len(manual.get('sections', []))
            })
        
        return summaries
    
    def search_manuals(self, query: str) -> List[Dict]:
        """
        Search manuals by title or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching manuals
        """
        manuals = self.get_all_manuals()
        query_lower = query.lower()
        
        results = []
        for manual in manuals:
            title = manual.get('title', '').lower()
            description = manual.get('description', '').lower()
            
            if query_lower in title or query_lower in description:
                results.append(manual)
        
        return results
    
    def add_manual(self, manual_data: Dict) -> bool:
        """
        Add a new manual.
        
        Args:
            manual_data: Manual data dictionary
            
        Returns:
            True if successful
        """
        try:
            with open(self.manuals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if ID already exists
            existing_ids = [m.get('id') for m in data.get('manuals', [])]
            if manual_data.get('id') in existing_ids:
                raise ValueError(f"Manual com ID '{manual_data.get('id')}' já existe")
            
            data['manuals'].append(manual_data)
            
            with open(self.manuals_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Erro ao adicionar manual: {e}")
            return False
    
    def update_manual(self, manual_id: str, manual_data: Dict) -> bool:
        """
        Update an existing manual.
        
        Args:
            manual_id: Manual ID to update
            manual_data: New manual data
            
        Returns:
            True if successful
        """
        try:
            with open(self.manuals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find and update manual
            updated = False
            for i, manual in enumerate(data.get('manuals', [])):
                if manual.get('id') == manual_id:
                    data['manuals'][i] = manual_data
                    updated = True
                    break
            
            if not updated:
                raise ValueError(f"Manual com ID '{manual_id}' não encontrado")
            
            with open(self.manuals_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Erro ao atualizar manual: {e}")
            return False
    
    def delete_manual(self, manual_id: str) -> bool:
        """
        Delete a manual.
        
        Args:
            manual_id: Manual ID to delete
            
        Returns:
            True if successful
        """
        try:
            with open(self.manuals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Filter out the manual
            original_count = len(data.get('manuals', []))
            data['manuals'] = [m for m in data.get('manuals', []) if m.get('id') != manual_id]
            
            if len(data['manuals']) == original_count:
                raise ValueError(f"Manual com ID '{manual_id}' não encontrado")
            
            with open(self.manuals_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Erro ao deletar manual: {e}")
            return False