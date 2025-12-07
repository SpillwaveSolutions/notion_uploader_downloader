---
**PDA Tier**: 3 (Workflow Guide)
**Estimated Tokens**: ~1,100 tokens
**Load Condition**: Update/Append Intent - User wants to add content to existing Notion page
**Dependencies**: May load QUICK_START.md, error-resolution.md
---

# Update/Append Workflow Guide

## Token Budget for This Workflow

**Tier 1 (Metadata)**: 150 tokens *(already loaded)*
**Tier 2 (Orchestrator)**: 600 tokens *(already loaded)*
**Tier 3 (This Guide)**: 1,100 tokens *(loading now)*

**Conditional Loading** (if needed):
- `references/QUICK_START.md`: +320 tokens (if command syntax unclear)
- `guides/troubleshooting/error-resolution.md`: +950 tokens (if errors occur)

**Estimated Total**: 1,850-3,120 tokens
**Status**: ✅ Within budget (10,000 token limit)

---

## Workflow Overview

**Purpose**: Append markdown content to an existing Notion page or database entry.

**Input**: Markdown file + existing page ID
**Output**: Updated Notion page with appended content
**Prerequisites**: NOTION_TOKEN configured, valid page ID, page is shared with integration

**Key Difference from Upload**: Uses `--page-id` flag and **appends** content (does not replace existing content).

---

## Step 1: Prerequisites Check

### 1.1 Verify Markdown File
```bash
# User must provide a markdown file with new content to append
```

**If file doesn't exist**: Report error and ask user to verify path.

### 1.2 Check for PlantUML Diagrams (CRITICAL!)

**Same as upload workflow** - search markdown for:
- ` ```puml ` or ` ```plantuml ` code blocks
- `![](*.puml)` image references

**If PlantUML content found**:
1. ⚠️ **STOP and invoke PlantUML skill FIRST**
2. Path: `/Users/richardhightower/.claude/skills/plantuml`
3. Script: `python scripts/process_markdown_puml.py <file.md> --format png`
4. **Use transformed file** (`*_with_images.md`) for append operation
5. **Reason**: Notion doesn't natively render PlantUML

### 1.3 Get Target Page ID

User must provide the page ID of the existing page:
- Can be Notion URL: `https://notion.so/Page-Title-abc123def456`
- Can be page ID: `abc123def456`
- Can be UUID format: `abc12345-6789-0123-4567-890123456789`

**Verify page access**:
- Page must be shared with the Notion integration
- Otherwise will get "404 object_not_found" error

---

## Step 2: Execute Update/Append

**Command structure**:
```bash
python3 scripts/notion_upload.py <markdown_file> --page-id <PAGE_ID> [--cover-image IMAGE]
```

**Example commands**:
```bash
# Append content to existing page
python3 scripts/notion_upload.py new-content.md --page-id abc123def456

# Append to page via URL
python3 scripts/notion_upload.py update.md --page-id "https://notion.so/My-Page-abc123"

# Append with cover image update
python3 scripts/notion_upload.py content.md --page-id abc123 --cover-image new-cover.png
```

**What happens**:
1. Script fetches the existing page to verify access
2. Parses the new markdown file
3. **Appends blocks to the END** of the existing page
4. Does NOT modify or remove existing content
5. Does NOT change the page title (keeps original)
6. Images in new content are uploaded and added

---

## Step 3: Understand Append Behavior

### Content is Added to the End

**Original page content**:
```
# Original Title
Original paragraph 1
Original paragraph 2
```

**Append this content** (from `update.md`):
```
## New Section
New paragraph 1
New paragraph 2
```

**Result**:
```
# Original Title
Original paragraph 1
Original paragraph 2
## New Section
New paragraph 1
New paragraph 2
```

### Title Handling

**Important**: The H1 heading in the appended markdown is NOT used as the page title.

- If your markdown has `# New Title`, it becomes a H1 **block** in the page content
- The page title in Notion remains the original title
- To change page title, you must do it manually in Notion

### Cover Image Handling

**With `--cover-image` flag**:
- Updates/replaces the page's cover image
- Use this if you want to change the cover when appending content

**Without flag**:
- Keeps existing cover image
- Most common for simple content appends

---

## Step 4: Works with Database Entries Too

**Appending to database entries**:

```bash
# Append content to a database entry (row)
python3 scripts/notion_upload.py additional-info.md --page-id DATABASE_ENTRY_ID
```

**Same behavior**:
- Appends content blocks to the database entry's page
- Does NOT modify database properties (title, tags, dates, etc.)
- Only adds content blocks

**To modify database properties**: Must use Notion UI or API directly (not supported by this script).

---

## Step 5: Monitor Execution

**Script output**:
```
✅ Content appended successfully!
   Page ID: abc123def456
   URL: https://notion.so/Page-Title-abc123def456
```

**Verify**:
- Open the Notion URL
- Scroll to the end of the page
- Confirm new content is there
- Existing content unchanged

---

## Use Cases for Update/Append

### 1. Daily Journal Entry
```bash
# Append today's entry to ongoing journal page
python3 scripts/notion_upload.py 2025-01-18-entry.md --page-id journal-page-id
```

### 2. Meeting Notes Accumulation
```bash
# Add new meeting notes to existing meeting log
python3 scripts/notion_upload.py meeting-2025-01-18.md --page-id meetings-page-id
```

### 3. Documentation Updates
```bash
# Append new section to existing documentation
python3 scripts/notion_upload.py new-api-section.md --page-id api-docs-id
```

### 4. Database Entry Details
```bash
# Add more details to a project database entry
python3 scripts/notion_upload.py project-update.md --page-id project-entry-id
```

---

## Error Handling

### Common Errors

**"404 object_not_found" or "Could not find page"**:
- Route to: `guides/troubleshooting/error-resolution.md` (+950 tokens)
- **Most common cause**: Page not shared with Notion integration
- **Solution**: Open page → "..." menu → "Add connections" → Select integration

**"NOTION_TOKEN not found"**:
- Route to: `guides/setup/configuration-guide.md` (+700 tokens)
- User needs to configure .env.notion file

**"Failed to upload image"**:
- Route to: `guides/troubleshooting/error-resolution.md` (+950 tokens)
- Check image paths, file existence, size limits (<20MB)

**"Page is archived" or similar**:
- Page may be in trash or archived
- Restore page in Notion first, then retry

---

## When to Load Additional Resources

**User asks "What's the difference between upload and update?"**:
→ Load `references/QUICK_START.md` (+320 tokens) for command comparison

**User asks "What happens to the existing content?"**:
→ Explain: Existing content is preserved, new content appended to end

**Any error occurs during execution**:
→ Load `guides/troubleshooting/error-resolution.md` (+950 tokens)

---

## Important Notes

### This is Append-Only

**Cannot**:
- ❌ Replace existing content
- ❌ Insert content in the middle
- ❌ Delete existing blocks
- ❌ Modify page title (via script)
- ❌ Update database properties

**Can**:
- ✅ Add new content to the end
- ✅ Upload images with new content
- ✅ Update cover image (via --cover-image flag)
- ✅ Add all supported markdown elements

### For Other Operations

**To replace content**: Delete page and create new one with upload workflow

**To edit content**: Use Notion UI directly or download → edit → delete old → upload new

**To modify database properties**: Use Notion UI or Notion API directly

---

## Post-Execution Token Summary

**Tokens used this request**:
- Tier 1: 150
- Tier 2: 600
- This guide: 1,100
- Conditionally loaded: 0-1,270 (depending on questions/errors)
- **Total**: 1,850-3,120 tokens

**Remaining budget**: 6,880-8,150 tokens

**Status**: ✅ Well within 10,000 token budget
