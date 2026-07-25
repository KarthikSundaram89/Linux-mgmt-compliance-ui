"""
Base Parser
===========

Abstract base class for parsing raw collector output.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseParser(ABC):
    """
    Abstract parser that transforms raw command output
    into structured data.
    
    Each collector type has a corresponding parser that
    understands its output format.
    """
    
    @abstractmethod
    def parse(self, raw_output: str) -> Dict[str, Any]:
        """
        Parse raw command output into structured data.
        
        Args:
            raw_output: Raw string output from SSH command.
        
        Returns:
            Structured dictionary of parsed data.
        """
        ...
    
    def safe_parse(
        self, raw_output: str
    ) -> Dict[str, Any]:
        """
        Parse with error handling.
        
        Returns empty dict on parse failure instead of raising.
        """
        try:
            return self.parse(raw_output)
        except Exception:
            return {"_parse_error": True, "_raw": raw_output[:500]}
