"""
Database Writers

Purpose: Write validated V2 data to Supabase tables

Writers:
- SupabaseWriter: Writes to golf_courses + golf_course_contacts (mirrors Agent 8 pattern)

Created: 2025-10-31
"""

from .supabase_writer import SupabaseWriter

__all__ = ["SupabaseWriter"]
