"""
Shared utilities for Notion article management.
"""

import os
import re
from pathlib import Path
from typing import Optional


def find_notion_token() -> Optional[str]:
    """
    Find Notion token from .env.notion file or environment variable.

    Returns:
        str: Notion token if found
        None: If token not found
    """
    # Check environment variable first
    token = os.environ.get('NOTION_TOKEN')
    if token:
        return token

    # Check .env.notion file
    env_file = Path('.env.notion')
    if env_file.exists():
        content = env_file.read_text()
        match = re.search(r'NOTION_TOKEN=(\S+)', content)
        if match:
            return match.group(1)

    # Check parent directories
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        env_file = parent / '.env.notion'
        if env_file.exists():
            content = env_file.read_text()
            match = re.search(r'NOTION_TOKEN=(\S+)', content)
            if match:
                return match.group(1)

    return None


def sanitize_filename(name: str) -> str:
    """
    Convert a string to a valid filename.

    Args:
        name: String to sanitize

    Returns:
        Valid filename string
    """
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces and special chars with hyphens
    name = re.sub(r'[\s\-_]+', '-', name)
    # Convert to lowercase
    name = name.lower()
    # Remove leading/trailing hyphens
    name = name.strip('-')
    # Limit length
    if len(name) > 200:
        name = name[:200]
    return name or 'untitled'


def extract_page_id(page_url_or_id: str) -> str:
    """
    Extract page ID from Notion URL or return ID if already in correct format.

    Args:
        page_url_or_id: Notion page URL or ID

    Returns:
        Page ID (32 char hex or UUID format)
    """
    # If it's already a valid UUID format, return it
    if re.match(r'^[a-f0-9]{32}$', page_url_or_id):
        return page_url_or_id

    if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', page_url_or_id):
        return page_url_or_id.replace('-', '')

    # Extract from URL
    # Format: https://notion.so/page-name-{32-char-id}
    match = re.search(r'([a-f0-9]{32})', page_url_or_id)
    if match:
        return match.group(1)

    # Format: https://notion.so/{UUID}
    match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', page_url_or_id)
    if match:
        return match.group(1).replace('-', '')

    # If nothing matches, assume it's already an ID
    return page_url_or_id


def format_page_id(page_id: str) -> str:
    """
    Format page ID with hyphens for Notion API.

    Args:
        page_id: 32-char hex string

    Returns:
        UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    """
    if len(page_id) == 32:
        return f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
    return page_id


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)
