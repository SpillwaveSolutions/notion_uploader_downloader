#!/usr/bin/env python3
"""
Download Notion pages and convert to markdown.

Usage:
    python notion_download.py <page_id_or_url> [--output DIR]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

from notion_utils import find_notion_token, extract_page_id, format_page_id, sanitize_filename, ensure_directory


NOTION_VERSION = "2022-06-28"
DEFAULT_OUTPUT_DIR = "./downloaded"


class NotionToMarkdownConverter:
    """Convert Notion blocks to markdown."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.images_dir = output_dir / "images"
        ensure_directory(self.images_dir)
        self.image_counter = 0

    def blocks_to_markdown(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Convert Notion blocks to markdown.

        Args:
            blocks: List of Notion block objects

        Returns:
            Markdown string
        """
        lines = []

        for block in blocks:
            block_type = block.get('type')

            if block_type == 'paragraph':
                lines.append(self._paragraph_to_md(block))
            elif block_type == 'heading_1':
                lines.append(self._heading_to_md(block, 1))
            elif block_type == 'heading_2':
                lines.append(self._heading_to_md(block, 2))
            elif block_type == 'heading_3':
                lines.append(self._heading_to_md(block, 3))
            elif block_type == 'bulleted_list_item':
                lines.append(self._bulleted_list_to_md(block))
            elif block_type == 'numbered_list_item':
                lines.append(self._numbered_list_to_md(block))
            elif block_type == 'code':
                lines.append(self._code_to_md(block))
            elif block_type == 'quote':
                lines.append(self._quote_to_md(block))
            elif block_type == 'callout':
                lines.append(self._callout_to_md(block))
            elif block_type == 'divider':
                lines.append("---")
            elif block_type == 'image':
                lines.append(self._image_to_md(block))
            elif block_type == 'table':
                lines.append(self._table_to_md(block))
            elif block_type == 'to_do':
                lines.append(self._todo_to_md(block))
            else:
                # Unsupported block type - add comment
                lines.append(f"<!-- Unsupported block type: {block_type} -->")

            # Add blank line between blocks
            lines.append("")

        return '\n'.join(lines)

    def _extract_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """
        Extract plain text from Notion rich text objects.

        Args:
            rich_text: List of rich text objects

        Returns:
            Plain text with markdown formatting
        """
        if not rich_text:
            return ""

        parts = []
        for text_obj in rich_text:
            text = text_obj.get('plain_text', '')
            annotations = text_obj.get('annotations', {})

            # Apply markdown formatting
            if annotations.get('bold'):
                text = f"**{text}**"
            if annotations.get('italic'):
                text = f"*{text}*"
            if annotations.get('code'):
                text = f"`{text}`"
            if annotations.get('strikethrough'):
                text = f"~~{text}~~"

            # Handle links
            if text_obj.get('href'):
                text = f"[{text}]({text_obj['href']})"

            parts.append(text)

        return ''.join(parts)

    def _paragraph_to_md(self, block: Dict[str, Any]) -> str:
        """Convert paragraph block to markdown."""
        return self._extract_text(block['paragraph'].get('rich_text', []))

    def _heading_to_md(self, block: Dict[str, Any], level: int) -> str:
        """Convert heading block to markdown."""
        heading_key = f'heading_{level}'
        text = self._extract_text(block[heading_key].get('rich_text', []))
        return f"{'#' * level} {text}"

    def _bulleted_list_to_md(self, block: Dict[str, Any]) -> str:
        """Convert bulleted list item to markdown."""
        text = self._extract_text(block['bulleted_list_item'].get('rich_text', []))
        return f"- {text}"

    def _numbered_list_to_md(self, block: Dict[str, Any]) -> str:
        """Convert numbered list item to markdown."""
        text = self._extract_text(block['numbered_list_item'].get('rich_text', []))
        return f"1. {text}"

    def _code_to_md(self, block: Dict[str, Any]) -> str:
        """Convert code block to markdown."""
        code_data = block['code']
        code = self._extract_text(code_data.get('rich_text', []))
        language = code_data.get('language', 'text')
        return f"```{language}\n{code}\n```"

    def _quote_to_md(self, block: Dict[str, Any]) -> str:
        """Convert quote block to markdown."""
        text = self._extract_text(block['quote'].get('rich_text', []))
        return f"> {text}"

    def _callout_to_md(self, block: Dict[str, Any]) -> str:
        """Convert callout block to markdown."""
        callout_data = block['callout']
        icon = callout_data.get('icon', {})
        icon_str = ""
        if icon.get('type') == 'emoji':
            icon_str = icon.get('emoji', '')

        text = self._extract_text(callout_data.get('rich_text', []))
        return f"> {icon_str} {text}"

    def _todo_to_md(self, block: Dict[str, Any]) -> str:
        """Convert to-do block to markdown."""
        todo_data = block['to_do']
        checked = todo_data.get('checked', False)
        text = self._extract_text(todo_data.get('rich_text', []))
        checkbox = "[x]" if checked else "[ ]"
        return f"- {checkbox} {text}"

    def _image_to_md(self, block: Dict[str, Any]) -> str:
        """
        Convert image block to markdown and download image.

        Args:
            block: Image block object

        Returns:
            Markdown image syntax
        """
        image_data = block['image']
        image_type = image_data.get('type')

        # Get image URL
        url = None
        if image_type == 'external':
            url = image_data['external'].get('url')
        elif image_type == 'file':
            url = image_data['file'].get('url')

        if not url:
            return "<!-- Image URL not found -->"

        # Download image
        try:
            self.image_counter += 1

            # Determine file extension from URL
            ext = 'png'
            if '.jpg' in url or '.jpeg' in url:
                ext = 'jpg'
            elif '.gif' in url:
                ext = 'gif'
            elif '.webp' in url:
                ext = 'webp'

            filename = f"image{self.image_counter}.{ext}"
            filepath = self.images_dir / filename

            # Download image
            response = requests.get(url, timeout=30)
            if response.ok:
                filepath.write_bytes(response.content)
                # Return relative path
                return f"![Image](images/{filename})"
            else:
                return f"<!-- Failed to download image: {url} -->"

        except Exception as e:
            return f"<!-- Error downloading image: {e} -->"

    def _table_to_md(self, block: Dict[str, Any]) -> str:
        """Convert table block to markdown."""
        # Note: Notion tables are complex and may need child blocks
        # This is a placeholder
        return "<!-- Table conversion not yet implemented -->"


class NotionDownloader:
    """Download pages from Notion."""

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
        self.base_url = "https://api.notion.com/v1"

    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve page metadata.

        Args:
            page_id: Page ID

        Returns:
            Page object or None
        """
        page_id = format_page_id(page_id)
        response = requests.get(
            f"{self.base_url}/pages/{page_id}",
            headers=self.headers
        )

        if not response.ok:
            print(f"Error retrieving page: {response.status_code}")
            print(response.text)
            return None

        return response.json()

    def get_blocks(self, block_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all child blocks recursively.

        Args:
            block_id: Block/page ID

        Returns:
            List of block objects
        """
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            params = {}
            if start_cursor:
                params['start_cursor'] = start_cursor

            response = requests.get(
                f"{self.base_url}/blocks/{format_page_id(block_id)}/children",
                headers=self.headers,
                params=params
            )

            if not response.ok:
                print(f"Error retrieving blocks: {response.status_code}")
                print(response.text)
                break

            data = response.json()
            blocks = data.get('results', [])
            all_blocks.extend(blocks)

            has_more = data.get('has_more', False)
            start_cursor = data.get('next_cursor')

            # Recursively get child blocks
            for block in blocks:
                if block.get('has_children'):
                    child_blocks = self.get_blocks(block['id'])
                    # Note: You may want to nest these blocks properly
                    all_blocks.extend(child_blocks)

        return all_blocks

    def download_page(self, page_id: str, output_dir: Path) -> Optional[Path]:
        """
        Download page and convert to markdown.

        Args:
            page_id: Page ID or URL
            output_dir: Output directory

        Returns:
            Path to downloaded markdown file
        """
        page_id = extract_page_id(page_id)

        # Get page metadata
        print(f"📄 Retrieving page: {page_id}")
        page = self.get_page(page_id)
        if not page:
            return None

        # Extract title
        title = "Untitled"
        properties = page.get('properties', {})
        if 'title' in properties:
            title_prop = properties['title']
            if title_prop.get('title'):
                title = self._extract_text(title_prop['title'])
        elif 'Name' in properties:
            name_prop = properties['Name']
            if name_prop.get('title'):
                title = self._extract_text(name_prop['title'])

        print(f"📝 Title: {title}")

        # Get blocks
        print(f"📦 Retrieving blocks...")
        blocks = self.get_blocks(page_id)
        print(f"   Found {len(blocks)} blocks")

        # Convert to markdown
        print(f"🔄 Converting to markdown...")
        converter = NotionToMarkdownConverter(output_dir)
        markdown = converter.blocks_to_markdown(blocks)

        # Add title as H1
        markdown = f"# {title}\n\n{markdown}"

        # Save to file
        filename = sanitize_filename(title) + ".md"
        filepath = output_dir / filename

        ensure_directory(output_dir)
        filepath.write_text(markdown, encoding='utf-8')

        print(f"✅ Downloaded: {title}")
        print(f"   Saved: {filepath}")
        print(f"   Images: {converter.image_counter} downloaded")

        return filepath

    def _extract_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract plain text from rich text."""
        return ''.join(obj.get('plain_text', '') for obj in rich_text)


def main():
    parser = argparse.ArgumentParser(description="Download Notion pages as markdown")
    parser.add_argument("page_id", help="Notion page ID or URL")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR,
                       help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")

    args = parser.parse_args()

    # Find Notion token
    token = find_notion_token()
    if not token:
        print("❌ NOTION_TOKEN not found!")
        print("   Create .env.notion with NOTION_TOKEN=your_token")
        print("   Or set NOTION_TOKEN environment variable")
        sys.exit(1)

    # Download page
    output_dir = Path(args.output)
    downloader = NotionDownloader(token)
    filepath = downloader.download_page(args.page_id, output_dir)

    if not filepath:
        print("❌ Download failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
