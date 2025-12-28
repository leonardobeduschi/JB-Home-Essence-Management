"""
Base repository for CSV operations.

This module provides an abstract base class for all repository implementations,
ensuring consistent CSV handling, atomic writes, and error management.
"""

import os
import pandas as pd
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import tempfile
import shutil


class BaseRepository(ABC):
    """
    Abstract base class for CSV-based data repositories.
    
    Provides common CSV operations with atomic writes and error handling.
    All concrete repositories should inherit from this class.
    """
    
    def __init__(self, filepath: str, schema: List[str]):
        """
        Initialize the repository.
        
        Args:
            filepath: Path to the CSV file
            schema: List of column names for the CSV
        """
        self.filepath = filepath
        self.schema = schema
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """
        Create the CSV file with headers if it doesn't exist.
        
        Creates parent directories if needed and initializes an empty
        CSV with the correct schema.
        """
        if not os.path.exists(self.filepath):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            
            # Create empty DataFrame with schema and save
            df = pd.DataFrame(columns=self.schema)
            df.to_csv(self.filepath, index=False, encoding='utf-8')
            print(f"✓ Created new file: {self.filepath}")
    
    def _read_csv(self) -> pd.DataFrame:
        """
        Safely read the CSV file.
        
        Returns:
            DataFrame with CSV contents
            
        Raises:
            Exception: If file cannot be read
        """
        try:
            # Read all columns as string initially to preserve data
            df = pd.read_csv(self.filepath, dtype=str, encoding='utf-8')
            
            # Replace NaN with empty string for easier handling
            df = df.fillna('')
            
            return df
        except Exception as e:
            raise Exception(f"Error reading {self.filepath}: {str(e)}")
    
    def _write_csv(self, df: pd.DataFrame) -> None:
        """
        Safely write DataFrame to CSV using atomic write.
        
        Uses a temporary file and rename operation to ensure atomicity.
        This prevents data corruption if the write is interrupted.
        
        Args:
            df: DataFrame to write
            
        Raises:
            Exception: If write operation fails
        """
        try:
            # Validate schema
            if not all(col in df.columns for col in self.schema):
                raise ValueError(f"DataFrame missing required columns. Expected: {self.schema}")
            
            # Ensure columns are in correct order
            df = df[self.schema]
            
            # Create temporary file in the same directory
            temp_dir = os.path.dirname(self.filepath)
            with tempfile.NamedTemporaryFile(
                mode='w',
                delete=False,
                dir=temp_dir,
                suffix='.tmp',
                encoding='utf-8'
            ) as tmp_file:
                temp_path = tmp_file.name
                df.to_csv(tmp_file, index=False, encoding='utf-8')
            
            # Atomic rename (replaces old file)
            shutil.move(temp_path, self.filepath)
            
        except Exception as e:
            # Clean up temp file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            raise Exception(f"Error writing to {self.filepath}: {str(e)}")
    
    def get_all(self) -> pd.DataFrame:
        """
        Retrieve all records from the CSV.
        
        Returns:
            DataFrame with all records
        """
        return self._read_csv()
    
    def count(self) -> int:
        """
        Count total number of records.
        
        Returns:
            Number of records in the CSV
        """
        df = self._read_csv()
        return len(df)
    
    def backup(self) -> str:
        """
        Create a backup of the current CSV file.
        
        Returns:
            Path to the backup file
        """
        if not os.path.exists(self.filepath):
            return None
        
        backup_path = f"{self.filepath}.backup"
        shutil.copy2(self.filepath, backup_path)
        return backup_path
    
    @abstractmethod
    def save(self, data: Dict) -> bool:
        """
        Save a record to the CSV.
        
        Must be implemented by concrete repository classes.
        
        Args:
            data: Dictionary with record data
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def exists(self, **kwargs) -> bool:
        """
        Check if a record exists based on given criteria.
        
        Must be implemented by concrete repository classes.
        
        Args:
            **kwargs: Search criteria
            
        Returns:
            True if record exists
        """
        pass