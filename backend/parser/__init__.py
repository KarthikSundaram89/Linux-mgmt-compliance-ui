"""
Parser Module
=============

Parses raw command output from collectors into structured data.
Each parser corresponds to a collector type.
"""

from backend.parser.base import BaseParser

__all__ = ["BaseParser"]
