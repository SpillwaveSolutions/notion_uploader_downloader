#!/usr/bin/env python3
"""
Upload markdown articles to Notion databases.

Usage:
    python notion_upload.py <markdown_file> [--database-id ID]
"""

import argparse
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import requests

from notion_utils import find_notion_token, find_notion_parent_page, format_page_id


# Notion API version
NOTION_VERSION = "2022-06-28"

# Default parent page (discovered from environment)
DEFAULT_PARENT_PAGE = find_notion_parent_page()


class MarkdownToNotionConverter:
    """Convert markdown content to Notion blocks."""

    def __init__(self, markdown_file: Path, uploader: 'NotionUploader'):
        self.markdown_file = markdown_file
        self.base_dir = markdown_file.parent
        self.content = markdown_file.read_text(encoding='utf-8')
        self.title = ""
        self.blocks = []
        self.uploader = uploader

    def parse(self) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse markdown content into Notion blocks.

        Returns:
            Tuple of (title, blocks)
        """
        lines = self.content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Extract title from first H1
            if not self.title and line.startswith('# '):
                self.title = line[2:].strip()
                i += 1
                continue

            # Tables (must check before headers)
            if line.strip().startswith('|'):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i])
                    i += 1
                if table_lines:
                    self.blocks.append(self._parse_table(table_lines))
                continue

            # Headers (H1-H6)
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line.lstrip('#').strip()

                # H4, H5, H6 → Bold underlined text with colon (Notion only supports H1-H3)
                if level >= 4:
                    self.blocks.append(self._make_h4_special(text))
                else:
                    self.blocks.append(self._make_heading(text, level))
                i += 1
                continue

            # Code blocks
            if line.startswith('```'):
                code_lines = []
                language = line[3:].strip() or 'plain text'
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                code = '\n'.join(code_lines)
                self.blocks.append(self._make_code_block(code, language))
                i += 1
                continue

            # Horizontal rules (page breaks) - must check before bullet lists
            if line.strip() in ['---', '***', '___']:
                self.blocks.append(self._make_divider())
                i += 1
                continue

            # Blockquotes / Callouts (must come before bullet lists)
            if line.strip().startswith('> '):
                quote_lines = []
                callout_type = None

                # Check for GitHub-style callout: > [!TYPE]
                first_line = line.strip()[2:].strip()
                callout_match = re.match(r'^\[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION|INFO)\]', first_line, re.IGNORECASE)

                if callout_match:
                    callout_type = callout_match.group(1).upper()
                    # Remove the [!TYPE] marker from first line
                    first_line = first_line[len(callout_match.group(0)):].strip()
                    if first_line:
                        quote_lines.append(first_line)
                    i += 1
                else:
                    quote_lines.append(first_line)
                    i += 1

                # Collect remaining lines
                while i < len(lines) and lines[i].strip().startswith('> '):
                    quote_lines.append(lines[i].strip()[2:])  # Remove "> "
                    i += 1

                if quote_lines:
                    quote_text = ' '.join(quote_lines)
                    self.blocks.append(self._make_callout(quote_text, callout_type))
                continue

            # Images
            if line.strip().startswith('!['):
                match = re.match(r'!\[(.*?)\]\((.*?)\)', line.strip())
                if match:
                    alt_text = match.group(1)
                    image_path = match.group(2)
                    image_block = self._make_image(image_path, alt_text)
                    if image_block:
                        self.blocks.append(image_block)
                    i += 1
                    continue

            # Task lists (must check before bullet lists)
            if line.strip().startswith('- [ ]') or line.strip().startswith('- [x]'):
                checked = line.strip().startswith('- [x]')
                text = line.strip()[6:].strip()  # Remove "- [ ] " or "- [x] "
                self.blocks.append(self._make_todo(text, checked))
                i += 1
                continue

            # Bullet lists
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                text = line.strip()[2:]
                self.blocks.append(self._make_bulleted_list_item(text))
                i += 1
                continue

            # Numbered lists
            if re.match(r'^\d+\.\s', line.strip()):
                text = re.sub(r'^\d+\.\s', '', line.strip())
                self.blocks.append(self._make_numbered_list_item(text))
                i += 1
                continue

            # Regular paragraph (collect consecutive non-empty lines)
            if line.strip():
                para_lines = [line.strip()]
                i += 1
                # Collect consecutive non-empty lines that aren't special blocks
                while i < len(lines):
                    next_line = lines[i].strip()
                    # Stop if we hit empty line or start of special block
                    if (not next_line or
                        next_line.startswith('#') or
                        next_line.startswith('```') or
                        next_line.startswith('![') or
                        next_line.startswith('- ') or
                        next_line.startswith('* ') or
                        next_line.startswith('> ') or
                        next_line.startswith('|') or
                        re.match(r'^\d+\.\s', next_line)):
                        break
                    para_lines.append(next_line)
                    i += 1

                # Join lines with space (markdown soft breaks)
                paragraph_text = ' '.join(para_lines)
                self.blocks.append(self._make_paragraph(paragraph_text))
                continue

            i += 1

        # Use filename as title if no H1 found
        if not self.title:
            self.title = self.markdown_file.stem.replace('_', ' ').replace('-', ' ').title()

        return self.title, self.blocks

    def _parse_rich_text(self, text: str, bold: bool = False,
                        underline: bool = False) -> List[Dict[str, Any]]:
        """
        Parse markdown formatting in text to Notion rich text.

        Handles: **bold**, *italic*, ~~strikethrough~~, <u>underline</u>, `code`, [links](url)

        Args:
            text: Text with markdown formatting
            bold: Force bold formatting
            underline: Force underline formatting

        Returns:
            List of rich text objects
        """
        if not text:
            return []

        rich_text_segments = []

        # Pattern to match markdown formatting
        # Matches: **bold**, *italic*, ~~strikethrough~~, <u>underline</u>, `code`, [text](url)
        pattern = r'(\*\*.*?\*\*|~~.*?~~|<u>.*?</u>|\*.*?\*|`.*?`|\[.*?\]\(.*?\))'

        parts = re.split(pattern, text)

        for part in parts:
            if not part:
                continue

            annotations = {}
            if bold:
                annotations['bold'] = True
            if underline:
                annotations['underline'] = True

            content = part
            href = None

            # Bold: **text**
            if part.startswith('**') and part.endswith('**'):
                content = part[2:-2]
                annotations['bold'] = True

            # Strikethrough: ~~text~~
            elif part.startswith('~~') and part.endswith('~~'):
                content = part[2:-2]
                annotations['strikethrough'] = True

            # Underline: <u>text</u>
            elif part.startswith('<u>') and part.endswith('</u>'):
                content = part[3:-4]
                annotations['underline'] = True

            # Italic: *text*
            elif part.startswith('*') and part.endswith('*') and not part.startswith('**'):
                content = part[1:-1]
                annotations['italic'] = True

            # Code: `text`
            elif part.startswith('`') and part.endswith('`'):
                content = part[1:-1]
                annotations['code'] = True

            # Link: [text](url)
            elif part.startswith('[') and '](' in part:
                match = re.match(r'\[(.*?)\]\((.*?)\)', part)
                if match:
                    content = match.group(1)
                    url = match.group(2)
                    # Skip anchor links (Notion doesn't support them)
                    if not url.startswith('#'):
                        href = url
                    # else: treat as plain text with bold to indicate it was a link

            # Create rich text object
            rich_text_obj = {
                "type": "text",
                "text": {"content": content}
            }

            if href:
                rich_text_obj["text"]["link"] = {"url": href}

            if annotations:
                rich_text_obj["annotations"] = annotations

            rich_text_segments.append(rich_text_obj)

        return rich_text_segments if rich_text_segments else [{"type": "text", "text": {"content": text}}]

    def _make_h4_special(self, text: str) -> Dict[str, Any]:
        """
        Create H4 as bold underlined text with colon.

        Example: #### Important Note → **Important Note:**
        """
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"{text}:"},
                    "annotations": {
                        "bold": True,
                        "underline": True
                    }
                }]
            }
        }

    def _make_heading(self, text: str, level: int) -> Dict[str, Any]:
        """Create a heading block (H1-H3 supported by Notion)."""
        # Notion only supports heading_1, heading_2, heading_3
        if level > 3:
            level = 3

        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self._parse_rich_text(text)
            }
        }

    def _make_paragraph(self, text: str) -> Dict[str, Any]:
        """Create a paragraph block."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": self._parse_rich_text(text)
            }
        }

    def _make_bulleted_list_item(self, text: str) -> Dict[str, Any]:
        """Create a bulleted list item block."""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self._parse_rich_text(text)
            }
        }

    def _make_numbered_list_item(self, text: str) -> Dict[str, Any]:
        """Create a numbered list item block."""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": self._parse_rich_text(text)
            }
        }

    def _make_callout(self, text: str, callout_type: Optional[str] = None) -> Dict[str, Any]:
        """Create a callout block with appropriate emoji based on type."""
        # Map callout types to emoji and colors
        callout_config = {
            "NOTE": {"emoji": "ℹ️", "color": "blue_background"},
            "INFO": {"emoji": "ℹ️", "color": "blue_background"},
            "TIP": {"emoji": "💡", "color": "green_background"},
            "WARNING": {"emoji": "⚠️", "color": "yellow_background"},
            "IMPORTANT": {"emoji": "❗", "color": "red_background"},
            "CAUTION": {"emoji": "🛑", "color": "red_background"},
        }

        # Default for regular blockquotes
        config = callout_config.get(callout_type, {"emoji": "💡", "color": "gray_background"})

        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": self._parse_rich_text(text),
                "icon": {"type": "emoji", "emoji": config["emoji"]},
                "color": config["color"]
            }
        }

    def _make_todo(self, text: str, checked: bool = False) -> Dict[str, Any]:
        """Create a to-do (checkbox) block."""
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": self._parse_rich_text(text),
                "checked": checked
            }
        }

    def _make_divider(self) -> Dict[str, Any]:
        """Create a horizontal rule (divider) block."""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }

    def _make_code_block(self, code: str, language: str) -> Dict[str, Any]:
        """Create a code block."""
        # Map to Notion supported languages
        language = language.lower()

        # Language mappings
        language_map = {
            'mmd': 'mermaid',
            'ini': 'plain text',
            'conf': 'plain text',
            'config': 'plain text',
            'env': 'plain text',
            'sh': 'shell',
            'zsh': 'shell',
            'fish': 'shell',
            'ps1': 'powershell',
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'rb': 'ruby',
            'rs': 'rust',
            'yml': 'yaml',
        }

        language = language_map.get(language, language)

        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": code[:2000]}  # Notion limit
                }],
                "language": language
            }
        }

    def _parse_table(self, table_lines: List[str]) -> Dict[str, Any]:
        """
        Parse markdown table into Notion table block.

        Args:
            table_lines: List of table rows (markdown format)

        Returns:
            Notion table block with table_row children
        """
        # Parse table rows
        rows = []
        has_header = False

        for i, line in enumerate(table_lines):
            # Skip separator line (e.g., |---|---|)
            if re.match(r'^\s*\|[\s\-:|]+\|\s*$', line):
                has_header = True
                continue

            # Parse cells
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            rows.append(cells)

        if not rows:
            return self._make_paragraph("<!-- Empty table -->")

        # Determine table width
        table_width = len(rows[0])

        # Create table_row children
        table_row_children = []
        for row in rows:
            # Pad or trim to match table_width
            while len(row) < table_width:
                row.append("")
            row = row[:table_width]

            # Convert each cell to rich text array
            cells = [
                [{"type": "text", "text": {"content": cell}}]
                for cell in row
            ]

            table_row_children.append({
                "object": "block",
                "type": "table_row",
                "table_row": {
                    "cells": cells
                }
            })

        # Return table block with children INSIDE the table object
        return {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": table_width,
                "has_column_header": has_header,
                "has_row_header": False,
                "children": table_row_children
            }
        }

    def _make_image(self, image_path: str, alt_text: str) -> Optional[Dict[str, Any]]:
        """
        Create an image block.

        For URLs: use external reference
        For local images: upload using File Upload API
        """
        # Check if URL
        if image_path.startswith('http://') or image_path.startswith('https://'):
            return {
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {"url": image_path},
                    "caption": [{"type": "text", "text": {"content": alt_text}}] if alt_text else []
                }
            }

        # Local file - upload it
        # Resolve relative path from markdown file location
        if not os.path.isabs(image_path):
            image_full_path = self.markdown_file.parent / image_path
        else:
            image_full_path = Path(image_path)

        if not image_full_path.exists():
            print(f"   ⚠️  Image not found: {image_path}")
            return None

        print(f"   📤 Uploading image: {image_path}")
        file_upload_id = self.uploader.upload_file(image_full_path)

        if not file_upload_id:
            print(f"   ❌ Failed to upload: {image_path}")
            return None

        # Use file_upload type with the ID
        return {
            "object": "block",
            "type": "image",
            "image": {
                "type": "file_upload",
                "file_upload": {"id": file_upload_id},
                "caption": [{"type": "text", "text": {"content": alt_text}}] if alt_text else []
            }
        }


class NotionUploader:
    """Upload articles to Notion."""

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
        self.base_url = "https://api.notion.com/v1"

    def upload_file(self, file_path: Path) -> Optional[str]:
        """
        Upload a local file to Notion storage using the File Upload API.

        Args:
            file_path: Path to local file

        Returns:
            File upload ID or None on failure
        """
        filename = file_path.name

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            # Default MIME types for common image formats
            ext = file_path.suffix.lower()
            mime_types_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.svg': 'image/svg+xml'
            }
            mime_type = mime_types_map.get(ext, 'application/octet-stream')

        try:
            # Step 1: Create a file upload object
            create_res = requests.post(
                f"{self.base_url}/file_uploads",
                headers=self.headers,
                json={"filename": filename, "content_type": mime_type}
            )

            if not create_res.ok:
                print(f"   ❌ Failed to create file upload: {create_res.status_code}")
                print(f"   Response: {create_res.text}")
                return None

            file_upload = create_res.json()
            file_upload_id = file_upload["id"]
            upload_url = file_upload["upload_url"]

            # Step 2: Send the file contents (multipart/form-data)
            headers_form = {
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": NOTION_VERSION,
            }

            with open(file_path, "rb") as f:
                send_res = requests.post(
                    upload_url,
                    headers=headers_form,
                    files={"file": (filename, f, mime_type)}
                )

                if not send_res.ok:
                    print(f"   ❌ Failed to upload file: {send_res.status_code}")
                    print(f"   Response: {send_res.text}")
                    return None

            # Return the file_upload ID (not URL) for use in blocks
            return file_upload_id

        except Exception as e:
            print(f"   ❌ Upload error: {e}")
            return None

    def create_page(self, title: str, blocks: List[Dict[str, Any]],
                   parent_id: Optional[str] = None, database_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a page in Notion (either under a parent page or in a database).

        Args:
            title: Page title
            blocks: Content blocks
            parent_id: Parent page ID (for child pages)
            database_id: Database ID (for database entries)

        Returns:
            Response from Notion API
        """
        if not parent_id and not database_id:
            print("❌ Error: Must provide either parent_id or database_id")
            return None

        # Determine parent type
        if parent_id:
            # Create as child page under parent
            parent_id = format_page_id(parent_id)
            page_data = {
                "parent": {"page_id": parent_id},
                "properties": {
                    "title": {
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": title}
                            }
                        ]
                    }
                }
            }
        else:
            # Create as database entry
            database_id = format_page_id(database_id)
            page_data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "title": {
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": title}
                            }
                        ]
                    }
                }
            }

        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json=page_data
        )

        if not response.ok:
            print(f"❌ Error creating page: {response.status_code}")
            print(response.text)
            return None

        page = response.json()
        page_id = page['id']

        # Add blocks in batches (Notion API limit: 100 blocks per request)
        # Tables with children can be included in the batch
        batch_size = 100
        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i + batch_size]
            self._append_blocks(page_id, batch)

        return page

    def set_page_cover(self, page_id: str, cover_file_path: Path) -> bool:
        """
        Set the cover image for a Notion page using a local file.

        Args:
            page_id: Page ID to update
            cover_file_path: Path to local cover image file

        Returns:
            True if successful, False otherwise
        """
        # Upload the cover image file
        print(f"   📤 Uploading cover image: {cover_file_path.name}")
        file_upload_id = self.upload_file(cover_file_path)

        if not file_upload_id:
            print(f"   ❌ Failed to upload cover image")
            return False

        # Update page with cover property
        page_id = format_page_id(page_id)
        response = requests.patch(
            f"{self.base_url}/pages/{page_id}",
            headers=self.headers,
            json={
                "cover": {
                    "type": "file_upload",
                    "file_upload": {"id": file_upload_id}
                }
            }
        )

        if not response.ok:
            print(f"   ❌ Failed to set cover image: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        print(f"   ✅ Cover image set successfully")
        return True

    def _append_blocks(self, page_id: str, blocks: List[Dict[str, Any]]) -> None:
        """
        Append blocks to a page.

        Args:
            page_id: Page ID
            blocks: Blocks to append
        """
        response = requests.patch(
            f"{self.base_url}/blocks/{page_id}/children",
            headers=self.headers,
            json={"children": blocks}
        )

        if not response.ok:
            print(f"❌ Error appending blocks: {response.status_code}")
            print(response.text)


def main():
    parser = argparse.ArgumentParser(
        description="Upload or update markdown articles in Notion",
        epilog="""Examples:
  Create new page (use env default):  python notion_upload.py article.md
  Create new page (specific parent):  python notion_upload.py article.md --parent-id PAGE_ID
  Create DB entry:                    python notion_upload.py article.md --database-id DATABASE_ID
  Update existing page:               python notion_upload.py article.md --page-id PAGE_ID

Configuration:
  Set NOTION_PARENT_PAGE in .env.notion or environment variable for default parent page"""
    )
    parser.add_argument("markdown_file", help="Path to markdown file")

    parent_group = parser.add_mutually_exclusive_group()
    parent_group.add_argument("--parent-id",
                             help="Parent page ID (creates child page under this page)")
    parent_group.add_argument("--database-id",
                             help="Database ID (creates entry in database)")
    parent_group.add_argument("--page-id",
                             help="Page ID (appends content to existing page/database entry)")

    parser.add_argument("--cover-image",
                       help="Path to cover image file (relative to markdown file or absolute path)")

    args = parser.parse_args()

    # Default to parent page from environment if none specified
    if not args.parent_id and not args.database_id and not args.page_id:
        if DEFAULT_PARENT_PAGE:
            args.parent_id = DEFAULT_PARENT_PAGE
        else:
            print("❌ No parent page specified and NOTION_PARENT_PAGE not configured")
            print()
            print("   Please either:")
            print("   1. Add NOTION_PARENT_PAGE=your_page_id to .env.notion file")
            print("   2. Set NOTION_PARENT_PAGE environment variable")
            print("   3. Use --parent-id, --database-id, or --page-id flag")
            print()
            print("   Example .env.notion:")
            print("   NOTION_TOKEN=ntn_your_token_here")
            print("   NOTION_PARENT_PAGE=your_default_parent_page_id")
            sys.exit(1)

    # Find Notion token
    token = find_notion_token()
    if not token:
        print("❌ NOTION_TOKEN not found!")
        print("   Create .env.notion with NOTION_TOKEN=your_token")
        print("   Or set NOTION_TOKEN environment variable")
        sys.exit(1)

    # Verify file exists
    markdown_file = Path(args.markdown_file)
    if not markdown_file.exists():
        print(f"❌ File not found: {markdown_file}")
        sys.exit(1)

    # Create uploader
    uploader = NotionUploader(token)

    # Parse markdown
    print(f"📄 Parsing: {markdown_file.name}")
    converter = MarkdownToNotionConverter(markdown_file, uploader)
    title, blocks = converter.parse()

    print(f"📝 Title: {title}")
    print(f"📦 Blocks: {len(blocks)}")

    # Upload or update in Notion
    if args.page_id:
        # Append to existing page
        print(f"🚀 Appending content to existing page: {args.page_id}...")

        # Append blocks in batches of 100 (Notion API limit)
        batch_size = 100
        total_batches = (len(blocks) - 1) // batch_size + 1

        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i+batch_size]
            batch_num = i // batch_size + 1
            print(f"   Appending batch {batch_num}/{total_batches}...")
            uploader._append_blocks(args.page_id, batch)

        # Set cover image if provided
        if args.cover_image:
            cover_path = Path(args.cover_image)
            # Handle relative paths (relative to markdown file)
            if not cover_path.is_absolute():
                cover_path = markdown_file.parent / cover_path

            if cover_path.exists():
                print(f"🎨 Setting cover image...")
                uploader.set_page_cover(args.page_id, cover_path)
            else:
                print(f"⚠️  Cover image not found: {cover_path}")

        # Format page URL
        page_id_clean = args.page_id.replace('-', '')
        page_url = f"https://www.notion.so/{page_id_clean}"

        print(f"✅ Content appended successfully!")
        print(f"   Page ID: {args.page_id}")
        print(f"   URL: {page_url}")

    elif args.parent_id:
        # Create new child page
        print(f"🚀 Uploading to Notion (parent page: {args.parent_id})...")
        page = uploader.create_page(title, blocks, parent_id=args.parent_id)

        if page:
            # Set cover image if provided
            if args.cover_image:
                cover_path = Path(args.cover_image)
                # Handle relative paths (relative to markdown file)
                if not cover_path.is_absolute():
                    cover_path = markdown_file.parent / cover_path

                if cover_path.exists():
                    print(f"🎨 Setting cover image...")
                    uploader.set_page_cover(page['id'], cover_path)
                else:
                    print(f"⚠️  Cover image not found: {cover_path}")

            page_url = page.get('url', 'N/A')
            print(f"✅ Uploaded successfully!")
            print(f"   Page ID: {page['id']}")
            print(f"   URL: {page_url}")
        else:
            print("❌ Upload failed")
            sys.exit(1)

    else:
        # Create new database entry
        print(f"🚀 Uploading to Notion (database: {args.database_id})...")
        page = uploader.create_page(title, blocks, database_id=args.database_id)

        if page:
            # Set cover image if provided
            if args.cover_image:
                cover_path = Path(args.cover_image)
                # Handle relative paths (relative to markdown file)
                if not cover_path.is_absolute():
                    cover_path = markdown_file.parent / cover_path

                if cover_path.exists():
                    print(f"🎨 Setting cover image...")
                    uploader.set_page_cover(page['id'], cover_path)
                else:
                    print(f"⚠️  Cover image not found: {cover_path}")

            page_url = page.get('url', 'N/A')
            print(f"✅ Uploaded successfully!")
            print(f"   Page ID: {page['id']}")
            print(f"   URL: {page_url}")
        else:
            print("❌ Upload failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
