---
name: notion-uploader-downloader
description: This skill should be used when the user wants to upload markdown files (articles, documents, reports, blog posts) to Notion, update existing Notion pages/database entries, or download Notion pages to markdown. Trigger keywords include upload, download, update, append, notion, markdown, .md files, article, document, report, publish, sync, backup, export, import, save, retrieve. Use this skill when the user specifies a .md file path, provides a Notion URL or page ID, or mentions uploading/updating/downloading content to/from Notion.
---

# Notion Article Uploader, Updater & Downloader

## Purpose

This skill provides bidirectional sync between Markdown and Notion with automatic image handling, rich formatting support, and GitHub-flavored markdown extensions. It enables uploading local markdown files (with images) to Notion, appending content to existing Notion pages or database entries, and downloading Notion pages (with images) back to markdown format.

## When to Use This Skill

Use this skill when the user:
- Mentions uploading, updating, or downloading with Notion
- Mentions uploading or downloading markdown files, articles, documents, or reports
- Wants to append content to an existing Notion page or database entry
- Specifies a file path ending in .md
- Provides a Notion URL or page ID
- Says phrases like "upload to Notion", "update Notion page", "append to database entry", "publish article", "save to Notion", "download from Notion", "backup Notion pages", "export to markdown"

## Example User Phrases

- "Upload this article to Notion"
- "Update this Notion page with new content"
- "Append article.md to page ID xxx"
- "Add content to this database entry"
- "Download this Notion page"
- "Publish article.md to Notion"
- "Save work/final/article.md to Notion"
- "Download https://notion.so/..."
- "Backup my Notion pages"
- "Export that article from Notion"

## How to Use This Skill

### Upload Workflow

When the user wants to upload a markdown file to Notion:

1. **Locate the markdown file** - Use the file path provided by the user
2. **Determine upload destination**:
   - If user specifies a parent page ID, use `--parent-id`
   - If user specifies a database ID, use `--database-id`
   - Default: Use parent ID `2a5d6bbdbbea8089bf5cc5afdc1cabd0` (Articles page)
3. **Execute upload script**:
   ```bash
   python3 scripts/notion_upload.py <file.md> --parent-id <PAGE_ID>
   ```
4. **Report results** - Share the Notion URL and page ID with the user

### Download Workflow

When the user wants to download from Notion:

1. **Extract page ID** - From Notion URL or use the provided page ID
2. **Determine output location** - Default is `./downloaded/`, or use `--output` flag if user specifies
3. **Execute download script**:
   ```bash
   python3 scripts/notion_download.py <PAGE_ID>
   ```
4. **Report results** - Inform user of the saved file path and number of images downloaded

### Update Workflow

When the user wants to update or append content to an existing Notion page or database entry:

1. **Locate the markdown file** - Use the file path provided by the user
2. **Get the page ID** - From the user or extract from Notion URL
3. **Execute upload script with --page-id**:
   ```bash
   python3 scripts/notion_upload.py <file.md> --page-id <PAGE_ID>
   ```
4. **Report results** - Confirm the content was appended and share the Notion URL

**Important Notes:**
- The `--page-id` flag appends content to an existing page (does not replace or modify existing content)
- Works with both regular pages and database entries
- Content is added at the end of the existing page
- All images and formatting are preserved
- The page must be shared with the Notion integration

### Configuration

The scripts automatically discover the Notion token from:
1. `.env.notion` file in the project root (format: `NOTION_TOKEN=ntn_...`)
2. `NOTION_TOKEN` environment variable

If the token is not found, prompt the user to:
- Create a `.env.notion` file with their Notion integration token
- Or set the `NOTION_TOKEN` environment variable

### Supported Features

**Upload (Markdown → Notion)**:
- Headers H1-H6 (H1-H3 as native headings, H4-H6 as bold+underlined paragraphs)
- Inline formatting: **bold**, *italic*, `code`, ~~strikethrough~~, <u>underline</u>, [links](url)
- Lists: bullet, numbered, task lists (`- [ ]`, `- [x]`)
- Code blocks with language syntax highlighting (including Mermaid diagrams)
- Tables with inline formatting
- Blockquotes and GitHub-style callouts (`> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, `> [!IMPORTANT]`, `> [!CAUTION]`)
- Horizontal dividers (`---`, `***`, `___`)
- Images: Local files uploaded via File Upload API, external URLs referenced
- Multi-line paragraph joining

**Download (Notion → Markdown)**:
- All block types converted to markdown
- Images downloaded to `./downloaded/images/`
- All formatting preserved (bold, italic, code, strikethrough, underline)
- Tables, lists, code blocks, Mermaid diagrams preserved
- Nested lists supported

### Script Locations

All Python scripts are in the `scripts/` directory:
- `scripts/notion_upload.py` - Upload markdown to Notion
- `scripts/notion_download.py` - Download Notion pages to markdown
- `scripts/notion_utils.py` - Shared utilities (token discovery, formatting)
- `scripts/requirements.txt` - Python dependencies (requests, python-dotenv)

### Reference Documentation

Additional technical documentation is available in `references/`:
- `references/QUICK_START.md` - Quick reference with common commands
- `references/MAPPINGS.md` - Complete markdown ↔ Notion element mappings
- `references/IMPLEMENTATION_SUMMARY.md` - Technical implementation details

To access reference documentation when needed, read the appropriate file from the `references/` directory.

### Common Commands

**Upload to parent page**:
```bash
python3 scripts/notion_upload.py article.md --parent-id 2a5d6bbdbbea8089bf5cc5afdc1cabd0
```

**Upload to database**:
```bash
python3 scripts/notion_upload.py article.md --database-id DATABASE_ID
```

**Update existing page (append content)**:
```bash
python3 scripts/notion_upload.py article.md --page-id PAGE_ID
```

**Download by page ID**:
```bash
python3 scripts/notion_download.py PAGE_ID
```

**Download to custom directory**:
```bash
python3 scripts/notion_download.py PAGE_ID --output custom/path
```

### Error Handling

**"NOTION_TOKEN not found"**:
- Prompt user to create `.env.notion` with `NOTION_TOKEN=ntn_...`
- Or set environment variable: `export NOTION_TOKEN=ntn_...`

**"Failed to upload image"**:
- Verify image paths are relative to markdown file
- Check image files exist
- File size limit: 20MB per image

**"404 object_not_found"**:
- Ensure the Notion page is shared with the integration
- Verify the page ID is correct

**Script execution errors**:
- Check Python dependencies are installed: `pip install -r scripts/requirements.txt`
- Verify Python 3 is available

### Image Upload Process (Technical)

The upload script uses Notion's File Upload API:
1. Create upload object via POST `/v1/file_uploads` with filename and content_type
2. Send binary data via POST multipart/form-data to the returned upload_url
3. Reference uploaded file in image block using `type: "file_upload"` with the returned ID

This enables uploading local images (up to 20MB) directly from the filesystem to Notion.

### Best Practices

- Always use the default Articles parent page ID (`2a5d6bbdbbea8089bf5cc5afdc1cabd0`) unless user specifies otherwise
- Report upload results with the Notion URL so users can access the page immediately
- For downloads, create the output directory automatically if it doesn't exist
- Handle relative image paths in markdown files correctly (relative to the markdown file location)
- Preserve all formatting during round-trip (upload then download should match original)
