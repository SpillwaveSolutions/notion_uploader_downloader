---
**PDA Tier**: 3 (Workflow Guide)
**Estimated Tokens**: ~1,250 tokens
**Load Condition**: Upload Intent - User wants to send markdown to Notion
**Dependencies**: May load MAPPINGS.md, QUICK_START.md, error-resolution.md
---

# Upload Workflow Guide

## Token Budget for This Workflow

**Tier 1 (Metadata)**: 150 tokens *(already loaded)*
**Tier 2 (Orchestrator)**: 600 tokens *(already loaded)*
**Tier 3 (This Guide)**: 1,250 tokens *(loading now)*

**Conditional Loading** (if needed during execution):
- `references/MAPPINGS.md`: +515 tokens (if user asks about supported elements)
- `references/QUICK_START.md`: +320 tokens (if command syntax unclear)
- `guides/troubleshooting/error-resolution.md`: +950 tokens (if errors occur)

**Estimated Total**: 2,000-3,635 tokens
**Status**: ✅ Within budget (10,000 token limit)

---

## Workflow Overview

**Purpose**: Upload a markdown file (with images and formatting) to create a new Notion page or database entry.

**Input**: Markdown file path (.md file)
**Output**: Notion page URL and page ID
**Prerequisites**: NOTION_TOKEN configured, markdown file exists

---

## Step 1: Prerequisites Check

### 1.1 Verify Markdown File
```bash
# User must provide a markdown file path
# Verify file exists before proceeding
```

**If file doesn't exist**: Report error and ask user to verify path.

### 1.2 Check for PlantUML Diagrams (CRITICAL!)

**Search the markdown for**:
- ` ```puml ` or ` ```plantuml ` code blocks
- `![](*.puml)` image references

**If PlantUML content found**:
1. ⚠️ **STOP the upload workflow immediately**
2. Invoke PlantUML skill FIRST:
   - Path: `/Users/richardhightower/.claude/skills/plantuml`
   - Script: `python scripts/process_markdown_puml.py <file.md> --format png`
   - This creates `<filename>_with_images.md` with diagrams converted to PNG
3. **Use the transformed file** (`*_with_images.md`) for the rest of this workflow
4. **Reason**: Notion does not natively render PlantUML code blocks

**If no PlantUML**: Continue with original markdown file.

### 1.3 Verify Configuration

Check if required configuration is available:

**NOTION_TOKEN** (required):
- Discovery order: ENV var → `.env.notion` → `.env` → Parent dirs
- If not found: Route to `guides/setup/configuration-guide.md`

**NOTION_PARENT_PAGE** (optional):
- Discovery order: Same as token
- If not found AND user didn't specify --parent-id/--database-id/--page-id:
  - Script will prompt user with helpful error message
  - Route to `guides/setup/configuration-guide.md`

---

## Step 2: Determine Upload Destination

User can specify destination in three ways (mutually exclusive):

### Option A: Use Default Parent Page (Most Common)
**Command**:
```bash
python3 scripts/notion_upload.py article.md
```

**What happens**:
- Script looks for NOTION_PARENT_PAGE in environment/config
- If found: Creates page as child of that parent
- If not found: Shows configuration error with helpful instructions

**Use when**: User wants to use their configured default location.

### Option B: Specific Parent Page
**Command**:
```bash
python3 scripts/notion_upload.py article.md --parent-id PAGE_ID
```

**What happens**:
- Creates page as child of specified parent page
- Overrides NOTION_PARENT_PAGE environment variable
- Parent page must be shared with Notion integration

**Use when**: User wants to upload to a different parent than default.

### Option C: Specific Database
**Command**:
```bash
python3 scripts/notion_upload.py article.md --database-id DATABASE_ID
```

**What happens**:
- Creates entry in specified database
- Uses first H1 heading as database title property
- Database must have "title" property and be shared with integration

**Use when**: User wants to create a database entry (not a page).

---

## Step 3: Optional Cover Image

User can add a cover image to the uploaded page:

```bash
python3 scripts/notion_upload.py article.md --parent-id PAGE_ID --cover-image path/to/image.png
```

**Cover image requirements**:
- Path can be relative to markdown file or absolute
- Supported formats: PNG, JPG, GIF, etc.
- Maximum size: 20MB
- Uploaded via Notion File Upload API

---

## Step 4: Execute Upload

**Full command structure**:
```bash
python3 scripts/notion_upload.py <markdown_file> \
  [--parent-id PAGE_ID | --database-id DB_ID] \
  [--cover-image IMAGE_PATH]
```

**Example commands**:
```bash
# Use default parent from environment
python3 scripts/notion_upload.py my-article.md

# Specify parent page
python3 scripts/notion_upload.py my-article.md --parent-id abc123

# Upload to database
python3 scripts/notion_upload.py my-article.md --database-id xyz789

# With cover image
python3 scripts/notion_upload.py my-article.md --cover-image cover.png
```

---

## Step 5: Monitor Execution

**Script output shows**:
- Parsing markdown file
- Uploading images (if any): "Uploading image: image.png"
- Creating Notion page
- Final Notion URL

**Expected output**:
```
✅ Page created successfully!
   Page ID: abc123def456
   URL: https://notion.so/Page-Title-abc123def456
```

---

## Step 6: Verify Success

**Success criteria**:
1. Script returns exit code 0
2. Notion URL is displayed
3. Page ID is displayed

**Report to user**:
- ✅ Share the Notion URL so they can open the page
- ✅ Confirm the upload was successful
- ✅ Mention any images that were uploaded

---

## Error Handling

### Common Errors

**"NOTION_TOKEN not found"**:
- Route to: `guides/setup/configuration-guide.md` (+700 tokens)
- User needs to configure .env.notion file

**"No parent page specified and NOTION_PARENT_PAGE not configured"**:
- Route to: `guides/setup/configuration-guide.md` (+700 tokens)
- User needs to either set NOTION_PARENT_PAGE or use a flag

**"404 object_not_found" or "Could not find page"**:
- Route to: `guides/troubleshooting/error-resolution.md` (+950 tokens)
- Most common cause: Page not shared with Notion integration

**"Failed to upload image"**:
- Route to: `guides/troubleshooting/error-resolution.md` (+950 tokens)
- Common causes: Image path wrong, file doesn't exist, >20MB size

**Script crashes or Python error**:
- Route to: `guides/troubleshooting/error-resolution.md` (+950 tokens)
- May be missing dependencies, Python version issue, etc.

---

## When to Load Additional Resources

**User asks "What markdown elements are supported?"**:
→ Load `references/MAPPINGS.md` (+515 tokens)

**User asks "What's the command syntax?" or "Show me examples"**:
→ Load `references/QUICK_START.md` (+320 tokens)

**User asks "How does image upload work?" or other technical questions**:
→ Load `references/IMPLEMENTATION_SUMMARY.md` (+1,090 tokens)

**Any error occurs during execution**:
→ Load `guides/troubleshooting/error-resolution.md` (+950 tokens)

---

## Supported Markdown Features

**Quick Reference** (for details, load `references/MAPPINGS.md`):

**Inline Formatting**: **bold**, *italic*, `code`, [links](url), ~~strikethrough~~, <u>underline</u>

**Block Elements**:
- Headers (H1-H6)
- Bullet lists, numbered lists, task lists
- Code blocks with syntax highlighting
- Tables
- Images (local files uploaded, URLs referenced)
- Blockquotes
- GitHub-style callouts (`> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, etc.)
- Horizontal dividers
- Mermaid diagrams (preserved in code blocks)

---

## Post-Execution Token Summary

After completing this workflow, calculate and optionally report:

**Tokens used this request**:
- Tier 1: 150
- Tier 2: 600
- This guide: 1,250
- Conditionally loaded: 0-2,555 (depending on errors/questions)
- **Total**: 2,000-4,555 tokens

**Remaining budget**: 5,445-8,000 tokens

**Status**: ✅ Well within 10,000 token budget
