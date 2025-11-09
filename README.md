# Notion Markdown Sync

Bidirectional synchronization between Markdown files and Notion pages with automatic image handling and rich formatting support.

## Features

✅ **Upload to Notion**
- Convert markdown files to Notion pages or database entries
- Automatic local image upload (up to 20MB per file)
- Preserve all formatting: **bold**, *italic*, `code`, ~~strikethrough~~, <u>underline</u>, [links](url)
- Support for tables, code blocks (with syntax highlighting), task lists, callouts
- GitHub-flavored markdown extensions (callouts, task lists)
- Mermaid diagram preservation

✅ **Download from Notion**
- Convert Notion pages back to markdown
- Download images to local storage
- Preserve formatting and structure
- Support for all major Notion block types

✅ **Append to Existing Pages**
- Add content to existing Notion pages or database entries
- Preserves existing content (appends at the end)
- Works with both regular pages and database entries

## Quick Start

### 1. Installation

```bash
pip install -r scripts/requirements.txt
```

### 2. Get Notion Token

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create a new integration
3. Copy the Internal Integration Token
4. Create `.env.notion` file:
   ```bash
   echo "NOTION_TOKEN=ntn_your_token_here" > .env.notion
   ```

### 3. Share Pages with Integration

- Open your Notion page
- Click "..." → "Add connections" → Select your integration
- Repeat for any pages/databases you want to access

## Usage

### Upload Markdown to Notion

**Upload to default Articles page:**
```bash
python3 scripts/notion_upload.py article.md --parent-id 2a5d6bbdbbea8089bf5cc5afdc1cabd0
```

**Upload to a database:**
```bash
python3 scripts/notion_upload.py article.md --database-id YOUR_DATABASE_ID
```

**Append to existing page:**
```bash
python3 scripts/notion_upload.py article.md --page-id EXISTING_PAGE_ID
```

### Download from Notion

**Download by page ID:**
```bash
python3 scripts/notion_download.py PAGE_ID
```

**Download to custom directory:**
```bash
python3 scripts/notion_download.py PAGE_ID --output my_articles/
```

**Download by URL:**
```bash
python3 scripts/notion_download.py https://www.notion.so/Your-Page-abc123def456...
```

## Supported Markdown Features

### Inline Formatting
- `**bold**` → Bold text
- `*italic*` → Italic text
- `` `code` `` → Inline code
- `[text](url)` → Links
- `~~strikethrough~~` → Strikethrough
- `<u>underline</u>` → Underline

### Block Elements
- `# H1` through `###### H6` → Headings (H4-H6 become bold+underlined)
- Paragraphs (multi-line paragraphs joined automatically)
- `- bullet` or `* bullet` → Bullet lists
- `1. numbered` → Numbered lists
- `- [ ] task` → Unchecked task
- `- [x] done` → Checked task
- `` ```language `` → Code blocks with syntax highlighting
- `| table | row |` → Tables
- `![alt](image.png)` → Images (local files uploaded automatically)
- `![alt](https://...)` → Images (external URLs)
- `---`, `***`, or `___` → Horizontal dividers

### Special Features
- **Blockquotes**: `> quote text`
- **GitHub Callouts**:
  - `> [!NOTE]` → ℹ️ Blue callout
  - `> [!TIP]` → 💡 Green callout
  - `> [!WARNING]` → ⚠️ Yellow callout
  - `> [!IMPORTANT]` → ❗ Red callout
  - `> [!CAUTION]` → 🛑 Red callout
- **Mermaid Diagrams**: `` ```mermaid ``
- **Language Mapping**: Automatic conversion (e.g., `js`→`javascript`, `sh`→`shell`)

## Configuration

### Token Discovery
The scripts automatically search for `NOTION_TOKEN` in:
1. Environment variable `NOTION_TOKEN`
2. `.env.notion` file in current directory
3. `.env.notion` in parent directories (walks up the tree)

Format of `.env.notion`:
```
NOTION_TOKEN=ntn_your_integration_token_here
```

### Default Settings
- **Default parent page ID**: `2a5d6bbdbbea8089bf5cc5afdc1cabd0` (Articles page)
- **Download directory**: `./downloaded/`
- **Images directory**: `./downloaded/images/`
- **Notion API version**: `2022-06-28`

## Architecture

### Scripts

- **`scripts/notion_upload.py`** - Upload markdown files to Notion
  - `MarkdownToNotionConverter`: Parses markdown into Notion blocks
  - `NotionUploader`: Handles Notion API communication and file uploads

- **`scripts/notion_download.py`** - Download Notion pages to markdown
  - `NotionToMarkdownConverter`: Converts Notion blocks to markdown
  - `NotionDownloader`: Retrieves pages and blocks from Notion API

- **`scripts/notion_utils.py`** - Shared utilities
  - Token discovery
  - Page ID extraction and formatting
  - Filename sanitization

### Image Handling

**Upload (Local Files)**:
1. Creates file upload object via POST `/v1/file_uploads`
2. Uploads binary data to the returned URL
3. References uploaded file in image block

**Download**:
1. Retrieves image URLs from Notion blocks
2. Downloads images to `./downloaded/images/`
3. Updates markdown with relative paths

## Examples

### Upload with Images

```bash
# article.md contains: ![Diagram](./images/diagram.png)
python3 scripts/notion_upload.py article.md --parent-id 2a5d6bbdbbea8089bf5cc5afdc1cabd0

# Output:
# 📄 Parsing: article.md
# 📤 Uploading image: ./images/diagram.png
# 📝 Title: My Article
# 📦 Blocks: 15
# 🚀 Uploading to Notion...
# ✅ Uploaded successfully!
#    Page ID: abc123...
#    URL: https://www.notion.so/abc123...
```

### Download Page

```bash
python3 scripts/notion_download.py abc123def456...

# Output:
# 📄 Retrieving page: abc123def456...
# 📝 Title: My Article
# 📦 Retrieving blocks...
#    Found 15 blocks
# 🔄 Converting to markdown...
# ✅ Downloaded: My Article
#    Saved: ./downloaded/my-article.md
#    Images: 3 downloaded
```

### Append Content

```bash
# Adds content to the end of an existing page
python3 scripts/notion_upload.py update.md --page-id abc123def456...

# Output:
# 📄 Parsing: update.md
# 📝 Title: Update Notes
# 📦 Blocks: 8
# 🚀 Appending content to existing page: abc123def456...
#    Appending batch 1/1...
# ✅ Content appended successfully!
#    Page ID: abc123def456...
#    URL: https://www.notion.so/abc123def456...
```

## Limitations

- **Image size**: Maximum 20MB per image (Notion File Upload API limit)
- **Code blocks**: Content truncated to 2000 characters (Notion limit)
- **Headings**: Only H1-H3 supported natively (H4-H6 become bold+underlined paragraphs)
- **Anchor links**: Stripped (Notion doesn't support internal page anchors)
- **Nested lists**: Not yet implemented
- **Math equations**: Not yet implemented
- **Toggle blocks**: Not yet implemented

## Troubleshooting

### "NOTION_TOKEN not found"
Create a `.env.notion` file with your integration token or set the `NOTION_TOKEN` environment variable.

### "404 object_not_found"
The page/database hasn't been shared with your Notion integration. Open the page in Notion and add your integration via "..." → "Add connections".

### "Failed to upload image"
- Verify the image path is correct (relative to the markdown file)
- Check the image file exists
- Ensure the image is under 20MB

### Formatting not preserved
Check that you're using proper markdown syntax. See the "Supported Markdown Features" section for the exact syntax required.

## Reference Documentation

Additional technical documentation is available in the `references/` directory:
- `references/QUICK_START.md` - Quick reference with common commands
- `references/MAPPINGS.md` - Complete markdown ↔ Notion element mappings
- `references/IMPLEMENTATION_SUMMARY.md` - Technical implementation details

## Claude Code Skill

This repository is designed as a [Claude Code](https://claude.ai/code) skill. When using Claude Code, simply say:
- "Upload article.md to Notion"
- "Download this Notion page"
- "Append content to that Notion page"

Claude Code will automatically detect the request and use this skill to perform the operation.

## License

This is a personal tool for Notion integration. Use at your own discretion.

## Contributing

This is a personal project, but suggestions and improvements are welcome. Please ensure any changes:
1. Preserve round-trip compatibility (upload then download should preserve content)
2. Update the `references/MAPPINGS.md` file with new element support
3. Follow the existing code structure and patterns
