# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill** that enables bidirectional synchronization between Markdown files and Notion pages. It provides Python scripts for uploading markdown (with images and rich formatting) to Notion and downloading Notion pages back to markdown format.

## Essential Commands

### Installation
```bash
pip install -r scripts/requirements.txt
```

### Upload Operations
```bash
# Upload to default Articles parent page (most common)
python3 scripts/notion_upload.py article.md --parent-id 2a5d6bbdbbea8089bf5cc5afdc1cabd0

# Upload to specific database
python3 scripts/notion_upload.py article.md --database-id DATABASE_ID

# Append to existing page (preserves existing content)
python3 scripts/notion_upload.py article.md --page-id PAGE_ID
```

### Download Operations
```bash
# Download by page ID or URL
python3 scripts/notion_download.py PAGE_ID

# Download to custom directory
python3 scripts/notion_download.py PAGE_ID --output custom/path
```

### Running Tests
There are currently no tests in this repository. When adding tests, use:
```bash
pytest tests/
```

## Architecture Overview

### Core Components

**`scripts/notion_upload.py`** - Main upload script with two key classes:
- `MarkdownToNotionConverter` (lines 27-551): Parses markdown into Notion block objects
  - `parse()` method (lines 38-200): Main parsing loop handling all markdown elements
  - `_parse_rich_text()` (lines 202-291): Converts inline formatting (bold, italic, code, links, strikethrough, underline)
  - Block creation methods: `_make_heading()`, `_make_paragraph()`, `_make_code_block()`, `_make_callout()`, `_parse_table()`, etc.
  - Image handling: `_make_image()` (lines 505-551) uses File Upload API for local files
- `NotionUploader` (lines 554-727): Handles Notion API communication
  - `upload_file()` (lines 566-633): Two-step file upload using File Upload API
  - `create_page()` (lines 635-708): Creates pages/database entries and adds content in 100-block batches
  - `_append_blocks()` (lines 710-727): Appends blocks to existing pages

**`scripts/notion_download.py`** - Download script with:
- `NotionToMarkdownConverter` (lines 23-225): Converts Notion blocks to markdown
  - `blocks_to_markdown()` (lines 32-80): Main conversion loop
  - `_extract_text()` (lines 82-116): Converts rich text with inline formatting
  - Block conversion methods for all supported Notion block types
  - `_image_to_md()` (lines 169-218): Downloads images to `./downloaded/images/`
- `NotionDownloader` (lines 227-370): Handles Notion API retrieval
  - `get_blocks()` (lines 262-306): Recursively fetches all blocks with pagination
  - `download_page()` (lines 308-365): Orchestrates full page download

**`scripts/notion_utils.py`** - Shared utilities:
- `find_notion_token()` (lines 11-42): Token discovery from `.env.notion` or environment variable
- `extract_page_id()` (lines 69-98): Extracts page ID from URLs or validates IDs
- `format_page_id()` (lines 101-113): Converts 32-char hex to UUID format for Notion API
- `sanitize_filename()` (lines 45-66): Converts page titles to valid filenames

### Key Architectural Patterns

**Markdown Parsing Strategy**: Sequential line-by-line parsing with lookahead for multi-line elements (tables, code blocks, paragraphs). Special handling order prevents conflicts (e.g., tables checked before headers, blockquotes before bullet lists).

**Notion API Batch Processing**: All block operations use 100-block batches (Notion API limit). Tables include their `table_row` children inline within the `table` object rather than as separate blocks.

**Image Upload Flow**:
1. POST `/v1/file_uploads` with filename and content_type → receive upload_url and file_upload_id
2. POST multipart/form-data to upload_url with binary file
3. Reference file_upload_id in image block using `type: "file_upload"`

**Token Discovery**: Searches current directory, then walks up parent directories for `.env.notion` file containing `NOTION_TOKEN=...`

### Supported Markdown Features

**Inline**: `**bold**`, `*italic*`, `` `code` ``, `[links](url)`, `~~strikethrough~~`, `<u>underline</u>`

**Blocks**: H1-H6 (H4-H6 become bold+underlined paragraphs), paragraphs (with multi-line joining), bullet/numbered lists, task lists (`- [ ]`/`- [x]`), code blocks with syntax highlighting, tables, images (local/URL), blockquotes, GitHub-style callouts (`> [!NOTE]`), horizontal rules

**Special**: Mermaid diagrams (preserved in code blocks), language mapping (e.g., `js`→`javascript`, `sh`→`shell`)

### Important Implementation Notes

- Default parent page ID: `2a5d6bbdbbea8089bf5cc5afdc1cabd0` (Articles page)
- Notion version: `2022-06-28` (consistent across all API calls)
- H4/H5/H6 are rendered as bold+underlined paragraphs with colons (Notion only supports H1-H3 natively)
- Multi-line paragraphs: Consecutive non-empty lines are joined with spaces (markdown soft breaks)
- Callout emoji mapping: NOTE→ℹ️, TIP→💡, WARNING→⚠️, IMPORTANT→❗, CAUTION→🛑
- Image size limit: 20MB per file (File Upload API restriction)
- Code block content: Truncated to 2000 chars (Notion limit)
- Anchor links are stripped (Notion doesn't support internal page anchors)

### Configuration

Token storage locations (checked in order):
1. `NOTION_TOKEN` environment variable
2. `.env.notion` file in current directory (format: `NOTION_TOKEN=ntn_...`)
3. `.env.notion` in any parent directory (walks up directory tree)

### File Organization

```
scripts/
  ├── notion_upload.py      # Upload markdown → Notion
  ├── notion_download.py    # Download Notion → markdown
  ├── notion_utils.py       # Shared utilities
  └── requirements.txt      # Python dependencies

references/
  ├── QUICK_START.md              # Quick reference guide
  ├── MAPPINGS.md                 # Complete element mapping table
  └── IMPLEMENTATION_SUMMARY.md   # Technical implementation details

SKILL.md                    # Skill definition for Claude Code
```

## Development Guidelines

### Adding New Markdown Elements

1. **Upload**: Add parser method in `MarkdownToNotionConverter`, add detection logic in `parse()` loop, ensure proper priority in the parsing order
2. **Download**: Add converter method in `NotionToMarkdownConverter`, add case in `blocks_to_markdown()` switch
3. **Test**: Verify round-trip (upload then download should preserve content)
4. **Document**: Update `references/MAPPINGS.md` with new element mapping

### Modifying the Parser

The parse order matters! Current sequence in `parse()` method:
1. Skip empty lines
2. Extract title (first H1)
3. Tables (must check before headers to avoid `|` being treated as text)
4. Headers (H1-H6)
5. Code blocks
6. Horizontal rules (must check before bullet lists to avoid `---` matching)
7. Blockquotes/callouts (must come before bullets to handle `> ` properly)
8. Images
9. Task lists (before bullet lists)
10. Bullet lists
11. Numbered lists
12. Regular paragraphs (catch-all with multi-line joining)

### Working with the Notion API

- Always use `format_page_id()` to convert IDs to UUID format before API calls
- Always include `Notion-Version: 2022-06-28` header
- Batch blocks in groups of 100 for append operations
- File uploads require two separate POST requests (create upload object, then send file)
- Tables must include `children` array inside the `table` object, not as separate top-level blocks

### Common Debugging Scenarios

**"404 object_not_found"**: Page/database not shared with Notion integration. User must click "..." → "Add connections" → select their integration.

**"Failed to upload image"**: Check image path is relative to markdown file location, verify file exists, ensure <20MB size.

**Formatting not preserved**: Check `_parse_rich_text()` regex patterns, verify annotations are correctly applied.

**Parse errors**: Check element detection order in `parse()` method - earlier checks take precedence.

## Default Configuration

- Default parent page ID: `2a5d6bbdbbea8089bf5cc5afdc1cabd0`
- Default download directory: `./downloaded/`
- Images directory: `./downloaded/images/` (for downloads)
- Notion API version: `2022-06-28`
- Batch size: 100 blocks per API request
