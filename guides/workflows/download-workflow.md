---
**PDA Tier**: 3 (Workflow Guide)
**Estimated Tokens**: ~850 tokens
**Load Condition**: Download Intent - User wants to extract content from Notion
**Dependencies**: May load error-resolution.md
---

# Download Workflow Guide

## Token Budget for This Workflow

**Tier 1 (Metadata)**: 150 tokens *(already loaded)*
**Tier 2 (Orchestrator)**: 600 tokens *(already loaded)*
**Tier 3 (This Guide)**: 850 tokens *(loading now)*

**Conditional Loading** (if needed):
- `guides/troubleshooting/error-resolution.md`: +950 tokens (if errors occur)

**Estimated Total**: 1,600-2,550 tokens
**Status**: ✅ Within budget (10,000 token limit)

---

## Workflow Overview

**Purpose**: Download a Notion page (with images) to markdown format.

**Input**: Notion page ID or URL
**Output**: Markdown file with images in `./downloaded/` directory
**Prerequisites**: NOTION_TOKEN configured, valid page ID

---

## Step 1: Extract Page ID

Users can provide the page ID in multiple formats:

### Format 1: Notion URL
```
https://notion.so/Page-Title-abc123def456
https://notion.so/abc123def456
https://www.notion.so/workspace/Page-Title-abc123def456
```

**Script handles**: Extracts the 32-character hex ID from any Notion URL format.

### Format 2: Page ID (32-character hex)
```
abc123def456789...
```

### Format 3: Page ID (UUID format with hyphens)
```
abc12345-6789-0123-4567-890123456789
```

**All formats work**: The script automatically extracts and formats the ID correctly.

---

## Step 2: Determine Output Location

### Option A: Default Location (Recommended)
**Command**:
```bash
python3 scripts/notion_download.py PAGE_ID
```

**Output**:
- Creates `./downloaded/` directory if it doesn't exist
- Saves markdown file as `./downloaded/page-title.md`
- Downloads images to `./downloaded/images/`

### Option B: Custom Output Directory
**Command**:
```bash
python3 scripts/notion_download.py PAGE_ID --output custom/path
```

**Output**:
- Creates `custom/path/` directory if needed
- Saves markdown as `custom/path/page-title.md`
- Downloads images to `custom/path/images/`

---

## Step 3: Execute Download

**Command structure**:
```bash
python3 scripts/notion_download.py <PAGE_ID_OR_URL> [--output DIR]
```

**Example commands**:
```bash
# Download with default output
python3 scripts/notion_download.py abc123def456

# Download from URL
python3 scripts/notion_download.py "https://notion.so/My-Page-abc123"

# Custom output directory
python3 scripts/notion_download.py abc123def456 --output ./my-backups

# Download multiple pages (run separately)
python3 scripts/notion_download.py page1_id
python3 scripts/notion_download.py page2_id
python3 scripts/notion_download.py page3_id
```

---

## Step 4: Monitor Execution

**Script output shows**:
- Fetching page from Notion
- Downloading images (if any): "Downloading image: image_name.png"
- Converting blocks to markdown
- Saving file

**Expected output**:
```
✅ Page downloaded successfully!
   Saved to: ./downloaded/my-page-title.md
   Images: 3 images downloaded to ./downloaded/images/
```

---

## Step 5: Verify Downloaded Content

**Check that**:
1. Markdown file created at expected location
2. Images directory created (if page had images)
3. Images referenced in markdown match downloaded files
4. Formatting preserved (headers, lists, code blocks, etc.)

**Report to user**:
- ✅ File path where markdown was saved
- ✅ Number of images downloaded
- ✅ Confirm download was successful

---

## Downloaded Content Format

**Markdown file includes**:
- Page title as H1 heading
- All page content converted to markdown
- Images as `![alt](./images/filename.png)` references
- All formatting preserved: bold, italic, code, links, etc.
- Tables, lists, code blocks maintained
- Nested lists supported

**Image handling**:
- All images downloaded to `./downloaded/images/` (or `<output>/images/`)
- Filenames sanitized for filesystem compatibility
- Image URLs replaced with local relative paths
- Original image format preserved (PNG, JPG, GIF, etc.)

---

## Error Handling

### Common Errors

**"NOTION_TOKEN not found"**:
- Route to: `guides/setup/configuration-guide.md` (+700 tokens)
- User needs to configure .env.notion file

**"404 object_not_found" or "Could not find page"**:
- Route to: `guides/troubleshooting/error-resolution.md` (+950 tokens)
- Common causes:
  - Invalid page ID
  - Page not shared with Notion integration
  - Page was deleted

**"Failed to download image"**:
- Route to: `guides/troubleshooting/error-resolution.md` (+950 tokens)
- Image URLs may be expired or inaccessible
- Download continues, image reference left as-is in markdown

**"Permission denied" or file system errors**:
- Check output directory permissions
- Verify disk space available
- Ensure directory is writable

---

## Round-Trip Compatibility

**Download → Edit → Upload workflow**:

1. Download page: `python3 scripts/notion_download.py PAGE_ID`
2. Edit the markdown file locally
3. Upload back to Notion: `python3 scripts/notion_upload.py ./downloaded/page-title.md --parent-id PARENT`

**Formatting preservation**:
- Most elements survive round-trip (download → upload)
- Some Notion-specific features may not convert perfectly
- Always verify uploaded content matches expectations

---

## When to Load Additional Resources

**User asks "What elements are preserved?" or "What's supported?"**:
→ Load `references/MAPPINGS.md` (+515 tokens)

**User asks "Show me command examples"**:
→ Load `references/QUICK_START.md` (+320 tokens)

**Any error occurs during execution**:
→ Load `guides/troubleshooting/error-resolution.md` (+950 tokens)

---

## Post-Execution Token Summary

**Tokens used this request**:
- Tier 1: 150
- Tier 2: 600
- This guide: 850
- Conditionally loaded: 0-950 (if errors occur)
- **Total**: 1,600-2,550 tokens

**Remaining budget**: 7,450-8,400 tokens

**Status**: ✅ Well within 10,000 token budget
