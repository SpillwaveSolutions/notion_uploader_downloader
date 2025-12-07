#!/usr/bin/env python3
"""
Recursive Notion page downloader.

Downloads a Notion page and all its child pages recursively,
creating a folder structure matching the Notion hierarchy.

Features:
- Two-phase processing: discovery then download
- YAML frontmatter with page metadata (notion_id, title, etc.)
- Strict file naming (lowercase, underscores, no special chars)
- Mapping file for round-trip sync
- Dry-run mode for preview
- Flat mode option (no subdirectories)

Usage:
    python notion_download_recursive.py <page_id_or_url> --output ./docs/
    python notion_download_recursive.py <page_id_or_url> --dry-run
    python notion_download_recursive.py <page_id_or_url> --flat --output ./flat_docs/
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

from notion_utils import (
    find_notion_token,
    extract_page_id,
    format_page_id,
    sanitize_filename_strict,
    ensure_directory
)


NOTION_VERSION = "2022-06-28"
DEFAULT_OUTPUT_DIR = "./downloaded"


@dataclass
class NotionPage:
    """Represents a Notion page with metadata."""
    id: str
    title: str
    parent_id: Optional[str]
    url: str
    created_time: str
    last_edited_time: str
    has_children: bool
    children: List['NotionPage'] = field(default_factory=list)
    local_path: Optional[Path] = None
    depth: int = 0


class PageHierarchy:
    """Discovers and builds page hierarchy from Notion."""

    def __init__(self, token: str, max_depth: Optional[int] = None, verbose: bool = False):
        self.token = token
        self.max_depth = max_depth
        self.verbose = verbose
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
        self.base_url = "https://api.notion.com/v1"
        self.pages: Dict[str, NotionPage] = {}
        self.total_pages = 0

    def discover_recursive(self, page_id: str, depth: int = 0, parent_id: Optional[str] = None) -> Optional[NotionPage]:
        """
        Recursively discover all child pages.

        Args:
            page_id: Page ID to start from
            depth: Current recursion depth
            parent_id: Parent page ID

        Returns:
            NotionPage with children populated
        """
        if self.max_depth is not None and depth > self.max_depth:
            return None

        page = self._fetch_page(page_id, parent_id, depth)
        if not page:
            return None

        self.total_pages += 1
        self.pages[page.id] = page

        if self.verbose:
            indent = "  " * depth
            print(f"{indent}Found: {page.title}")

        # Get child pages
        child_page_ids = self._get_child_pages(page_id)

        for child_id in child_page_ids:
            child_page = self.discover_recursive(child_id, depth + 1, page.id)
            if child_page:
                page.children.append(child_page)
                page.has_children = True

        return page

    def _fetch_page(self, page_id: str, parent_id: Optional[str], depth: int) -> Optional[NotionPage]:
        """Fetch page metadata from Notion API."""
        page_id = extract_page_id(page_id)
        formatted_id = format_page_id(page_id)

        response = requests.get(
            f"{self.base_url}/pages/{formatted_id}",
            headers=self.headers
        )

        if not response.ok:
            if self.verbose:
                print(f"Error fetching page {page_id}: {response.status_code}")
            return None

        data = response.json()

        # Extract title
        title = self._extract_title(data)

        # Build URL
        url = f"https://notion.so/{page_id.replace('-', '')}"

        return NotionPage(
            id=page_id,
            title=title,
            parent_id=parent_id,
            url=url,
            created_time=data.get('created_time', ''),
            last_edited_time=data.get('last_edited_time', ''),
            has_children=False,  # Will be updated when we find children
            depth=depth
        )

    def _extract_title(self, page_data: Dict[str, Any]) -> str:
        """Extract title from page properties."""
        properties = page_data.get('properties', {})

        # Try 'title' property
        if 'title' in properties:
            title_prop = properties['title']
            if title_prop.get('title'):
                return ''.join(t.get('plain_text', '') for t in title_prop['title'])

        # Try 'Name' property (common in databases)
        if 'Name' in properties:
            name_prop = properties['Name']
            if name_prop.get('title'):
                return ''.join(t.get('plain_text', '') for t in name_prop['title'])

        return "Untitled"

    def _get_child_pages(self, page_id: str) -> List[str]:
        """
        Get IDs of all child pages under a page.

        Child pages appear as 'child_page' block types in the blocks API.
        """
        child_page_ids = []
        formatted_id = format_page_id(page_id)

        has_more = True
        start_cursor = None

        while has_more:
            params = {"page_size": 100}
            if start_cursor:
                params['start_cursor'] = start_cursor

            response = requests.get(
                f"{self.base_url}/blocks/{formatted_id}/children",
                headers=self.headers,
                params=params
            )

            if not response.ok:
                break

            data = response.json()
            blocks = data.get('results', [])

            for block in blocks:
                if block['type'] == 'child_page':
                    child_page_ids.append(block['id'])
                # Note: child_database blocks could be handled in future

            has_more = data.get('has_more', False)
            start_cursor = data.get('next_cursor')

        return child_page_ids


class PathGenerator:
    """Generates local file paths for pages."""

    def __init__(self, output_dir: Path, flat_mode: bool = False):
        self.output_dir = output_dir
        self.flat_mode = flat_mode
        self.paths: Dict[str, Path] = {}

    def generate_paths(self, root: NotionPage, parent_path: Optional[Path] = None) -> None:
        """
        Generate local paths for all pages in hierarchy.

        In hierarchical mode:
        - Pages with children become directories with index.md
        - Leaf pages become individual .md files

        In flat mode:
        - All pages become .md files in the output directory
        """
        if parent_path is None:
            parent_path = self.output_dir

        filename = sanitize_filename_strict(root.title) + '.md'

        if self.flat_mode:
            # Flat mode: all files in output directory
            # Use depth prefix to avoid collisions
            if root.depth > 0:
                prefix = f"{root.depth:02d}_"
            else:
                prefix = ""
            root.local_path = parent_path / f"{prefix}{filename}"
        elif root.children:
            # Hierarchical mode: page with children becomes directory
            dir_path = parent_path / sanitize_filename_strict(root.title)
            root.local_path = dir_path / 'index.md'

            for child in root.children:
                self.generate_paths(child, dir_path)
        else:
            # Leaf page is just a file
            root.local_path = parent_path / filename

        self.paths[root.id] = root.local_path


class FrontmatterGenerator:
    """Generates YAML frontmatter for markdown files."""

    @staticmethod
    def generate(page: NotionPage) -> str:
        """
        Generate YAML frontmatter for a page.

        Args:
            page: NotionPage object

        Returns:
            YAML frontmatter string (without --- delimiters)
        """
        data = {
            'notion_id': page.id,
            'notion_url': page.url,
            'title': page.title,
            'parent_id': page.parent_id,
            'created_time': page.created_time,
            'last_edited_time': page.last_edited_time,
            'downloaded_at': datetime.now().isoformat(),
            'has_children': page.has_children
        }

        lines = []
        for key, value in data.items():
            if value is None:
                lines.append(f'{key}: null')
            elif isinstance(value, bool):
                lines.append(f'{key}: {str(value).lower()}')
            else:
                # Quote strings with special characters
                str_value = str(value)
                if ':' in str_value or '"' in str_value or str_value.startswith('{'):
                    # Escape internal quotes and wrap
                    escaped = str_value.replace('"', '\\"')
                    lines.append(f'{key}: "{escaped}"')
                else:
                    lines.append(f'{key}: {str_value}')

        return '\n'.join(lines) + '\n'


class NotionToMarkdownConverter:
    """Convert Notion blocks to markdown."""

    def __init__(self, output_dir: Path, page_name: str = "page"):
        self.output_dir = output_dir
        self.page_name = sanitize_filename_strict(page_name)
        self.images_dir = output_dir / "images" / self.page_name
        self.image_counter = 0

    def blocks_to_markdown(self, blocks: List[Dict[str, Any]]) -> str:
        """Convert Notion blocks to markdown."""
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
            elif block_type == 'to_do':
                lines.append(self._todo_to_md(block))
            elif block_type == 'toggle':
                lines.append(self._toggle_to_md(block))
            elif block_type == 'child_page':
                # Child pages are handled separately in recursive download
                lines.append(f"<!-- Child page: {block.get('child_page', {}).get('title', 'Unknown')} -->")
            elif block_type == 'child_database':
                lines.append(f"<!-- Child database: {block.get('child_database', {}).get('title', 'Unknown')} -->")
            else:
                lines.append(f"<!-- Unsupported block type: {block_type} -->")

            lines.append("")

        return '\n'.join(lines)

    def _extract_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract text with markdown formatting from rich text objects."""
        if not rich_text:
            return ""

        parts = []
        for text_obj in rich_text:
            text = text_obj.get('plain_text', '')
            annotations = text_obj.get('annotations', {})

            if annotations.get('bold'):
                text = f"**{text}**"
            if annotations.get('italic'):
                text = f"*{text}*"
            if annotations.get('code'):
                text = f"`{text}`"
            if annotations.get('strikethrough'):
                text = f"~~{text}~~"

            if text_obj.get('href'):
                text = f"[{text}]({text_obj['href']})"

            parts.append(text)

        return ''.join(parts)

    def _paragraph_to_md(self, block: Dict[str, Any]) -> str:
        return self._extract_text(block['paragraph'].get('rich_text', []))

    def _heading_to_md(self, block: Dict[str, Any], level: int) -> str:
        heading_key = f'heading_{level}'
        text = self._extract_text(block[heading_key].get('rich_text', []))
        return f"{'#' * level} {text}"

    def _bulleted_list_to_md(self, block: Dict[str, Any]) -> str:
        text = self._extract_text(block['bulleted_list_item'].get('rich_text', []))
        return f"- {text}"

    def _numbered_list_to_md(self, block: Dict[str, Any]) -> str:
        text = self._extract_text(block['numbered_list_item'].get('rich_text', []))
        return f"1. {text}"

    def _code_to_md(self, block: Dict[str, Any]) -> str:
        code_data = block['code']
        code = self._extract_text(code_data.get('rich_text', []))
        language = code_data.get('language', 'text')
        return f"```{language}\n{code}\n```"

    def _quote_to_md(self, block: Dict[str, Any]) -> str:
        text = self._extract_text(block['quote'].get('rich_text', []))
        return f"> {text}"

    def _callout_to_md(self, block: Dict[str, Any]) -> str:
        callout_data = block['callout']
        icon = callout_data.get('icon', {})
        icon_str = ""
        if icon.get('type') == 'emoji':
            icon_str = icon.get('emoji', '')

        text = self._extract_text(callout_data.get('rich_text', []))
        return f"> {icon_str} {text}"

    def _todo_to_md(self, block: Dict[str, Any]) -> str:
        todo_data = block['to_do']
        checked = todo_data.get('checked', False)
        text = self._extract_text(todo_data.get('rich_text', []))
        checkbox = "[x]" if checked else "[ ]"
        return f"- {checkbox} {text}"

    def _toggle_to_md(self, block: Dict[str, Any]) -> str:
        toggle_data = block['toggle']
        text = self._extract_text(toggle_data.get('rich_text', []))
        # Toggles become details/summary in markdown
        return f"<details>\n<summary>{text}</summary>\n\n<!-- Toggle content -->\n\n</details>"

    def _image_to_md(self, block: Dict[str, Any]) -> str:
        """Download image and return markdown reference."""
        image_data = block['image']
        image_type = image_data.get('type')

        url = None
        if image_type == 'external':
            url = image_data['external'].get('url')
        elif image_type == 'file':
            url = image_data['file'].get('url')

        if not url:
            return "<!-- Image URL not found -->"

        try:
            self.image_counter += 1

            # Determine extension
            ext = '.png'
            url_lower = url.lower()
            if '.jpg' in url_lower or '.jpeg' in url_lower:
                ext = '.jpg'
            elif '.gif' in url_lower:
                ext = '.gif'
            elif '.webp' in url_lower:
                ext = '.webp'
            elif '.svg' in url_lower:
                ext = '.svg'

            # Contextual filename
            filename = f"{self.page_name}_image_{self.image_counter:02d}{ext}"
            ensure_directory(self.images_dir)
            filepath = self.images_dir / filename

            # Download
            response = requests.get(url, timeout=30)
            if response.ok:
                filepath.write_bytes(response.content)
                # Calculate relative path from markdown file to image
                rel_path = f"images/{self.page_name}/{filename}"
                return f"![Image]({rel_path})"
            else:
                return f"<!-- Failed to download image: {url} -->"

        except Exception as e:
            return f"<!-- Error downloading image: {e} -->"


class RecursiveDownloader:
    """Main orchestrator for recursive Notion download."""

    def __init__(
        self,
        token: str,
        output_dir: Path,
        max_depth: Optional[int] = None,
        flat_mode: bool = False,
        include_images: bool = True,
        verbose: bool = False,
        dry_run: bool = False
    ):
        self.token = token
        self.output_dir = output_dir
        self.max_depth = max_depth
        self.flat_mode = flat_mode
        self.include_images = include_images
        self.verbose = verbose
        self.dry_run = dry_run

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }
        self.base_url = "https://api.notion.com/v1"

        self.hierarchy = PageHierarchy(token, max_depth, verbose)
        self.path_gen = PathGenerator(output_dir, flat_mode)
        self.mapping: Dict[str, Any] = {}
        self.stats = {
            'total_pages': 0,
            'total_images': 0,
            'max_depth': 0
        }

    def download_recursive(self, page_id: str) -> int:
        """
        Main entry point for recursive download.

        Args:
            page_id: Root page ID or URL

        Returns:
            Number of pages downloaded
        """
        page_id = extract_page_id(page_id)

        # Phase 1: Discover
        print("=" * 60)
        print("PHASE 1: Discovering page hierarchy")
        print("=" * 60)

        root = self.hierarchy.discover_recursive(page_id)
        if not root:
            print("Failed to fetch root page")
            return 0

        # Generate paths
        self.path_gen.generate_paths(root)

        # Calculate stats
        self._calculate_stats(root)

        print(f"\nDiscovered {self.stats['total_pages']} pages")
        print(f"Max depth: {self.stats['max_depth']}")

        if self.dry_run:
            print("\n" + "=" * 60)
            print("DRY RUN - Would create the following structure:")
            print("=" * 60)
            self._print_tree(root)
            return 0

        # Phase 2: Download
        print("\n" + "=" * 60)
        print("PHASE 2: Downloading content")
        print("=" * 60)

        # Create directories
        ensure_directory(self.output_dir)

        # Download all pages
        downloaded = self._download_page_tree(root)

        # Save mapping
        self._save_mapping(root)

        print("\n" + "=" * 60)
        print("DOWNLOAD COMPLETE")
        print("=" * 60)
        print(f"Pages downloaded: {downloaded}")
        print(f"Images downloaded: {self.stats['total_images']}")
        print(f"Output directory: {self.output_dir}")
        print(f"Mapping file: {self.output_dir / 'mapping.json'}")

        return downloaded

    def _calculate_stats(self, page: NotionPage) -> None:
        """Calculate statistics from page tree."""
        self.stats['total_pages'] += 1
        self.stats['max_depth'] = max(self.stats['max_depth'], page.depth)

        for child in page.children:
            self._calculate_stats(child)

    def _print_tree(self, page: NotionPage, indent: int = 0) -> None:
        """Print page tree structure."""
        prefix = "  " * indent
        local_path = page.local_path.relative_to(self.output_dir) if page.local_path else "???"
        print(f"{prefix}{'[D]' if page.children else '[F]'} {page.title} -> {local_path}")

        for child in page.children:
            self._print_tree(child, indent + 1)

    def _download_page_tree(self, page: NotionPage) -> int:
        """Download a page and all its children."""
        count = 0

        if self._download_single_page(page):
            count += 1

        for child in page.children:
            count += self._download_page_tree(child)

        return count

    def _download_single_page(self, page: NotionPage) -> bool:
        """Download one page with frontmatter."""
        if self.verbose:
            print(f"Downloading: {page.title}")

        # Get blocks
        blocks = self._get_blocks(page.id)

        # Convert to markdown
        converter = NotionToMarkdownConverter(self.output_dir, page.title)
        markdown = converter.blocks_to_markdown(blocks)
        self.stats['total_images'] += converter.image_counter

        # Generate frontmatter
        frontmatter = FrontmatterGenerator.generate(page)
        content = f"---\n{frontmatter}---\n\n# {page.title}\n\n{markdown}"

        # Save to file
        ensure_directory(page.local_path.parent)
        page.local_path.write_text(content, encoding='utf-8')

        # Update mapping
        rel_path = str(page.local_path.relative_to(self.output_dir))
        self.mapping[rel_path] = {
            'notion_id': page.id,
            'title': page.title,
            'parent_id': page.parent_id,
            'has_children': page.has_children,
            'child_paths': [
                str(c.local_path.relative_to(self.output_dir))
                for c in page.children
            ] if page.children else []
        }

        return True

    def _get_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """Retrieve all blocks from a page (not recursing into child pages)."""
        all_blocks = []
        formatted_id = format_page_id(page_id)
        has_more = True
        start_cursor = None

        while has_more:
            params = {"page_size": 100}
            if start_cursor:
                params['start_cursor'] = start_cursor

            response = requests.get(
                f"{self.base_url}/blocks/{formatted_id}/children",
                headers=self.headers,
                params=params
            )

            if not response.ok:
                if self.verbose:
                    print(f"Error getting blocks: {response.status_code}")
                break

            data = response.json()
            blocks = data.get('results', [])
            all_blocks.extend(blocks)

            has_more = data.get('has_more', False)
            start_cursor = data.get('next_cursor')

        return all_blocks

    def _save_mapping(self, root: NotionPage) -> None:
        """Save mapping.json file."""
        mapping_data = {
            'source': {
                'notion_id': root.id,
                'title': root.title,
                'url': root.url
            },
            'downloaded_at': datetime.now().isoformat(),
            'pages': self.mapping,
            'statistics': self.stats
        }

        mapping_path = self.output_dir / 'mapping.json'
        mapping_path.write_text(
            json.dumps(mapping_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )


def main():
    parser = argparse.ArgumentParser(
        description="Recursively download Notion pages as markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s PAGE_ID --output ./docs/
  %(prog)s PAGE_URL --dry-run
  %(prog)s PAGE_ID --flat --output ./flat_docs/
  %(prog)s PAGE_ID --max-depth 2 --verbose

File Naming:
  - All lowercase, underscores instead of spaces
  - "Design Overview" -> design_overview.md
  - "API Reference (v2)" -> api_reference_v2.md

Output Structure (default):
  output/
  ├── parent_page/
  │   ├── index.md
  │   ├── child_1.md
  │   └── child_2/
  │       ├── index.md
  │       └── grandchild.md
  ├── images/
  │   ├── parent_page/
  │   └── child_1/
  └── mapping.json
"""
    )

    parser.add_argument(
        "page_id",
        help="Notion page ID or URL to download recursively"
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum recursion depth (default: unlimited)"
    )
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Flatten hierarchy (no subdirectories)"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip downloading images"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without actually downloading"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Find token
    token = find_notion_token()
    if not token:
        print("Error: NOTION_TOKEN not found!")
        print("  Create .env.notion with NOTION_TOKEN=your_token")
        print("  Or set NOTION_TOKEN environment variable")
        sys.exit(1)

    # Create downloader
    output_dir = Path(args.output)
    downloader = RecursiveDownloader(
        token=token,
        output_dir=output_dir,
        max_depth=args.max_depth,
        flat_mode=args.flat,
        include_images=not args.no_images,
        verbose=args.verbose,
        dry_run=args.dry_run
    )

    # Run
    count = downloader.download_recursive(args.page_id)

    if args.dry_run:
        print("\nRun without --dry-run to actually download.")
    elif count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
