---
**PDA Tier**: 3 (Workflow Guide)
**Estimated Tokens**: ~1,100 tokens
**Load Condition**: Recursive Download Intent - User wants to download a page AND all child pages
**Dependencies**: May load error-resolution.md
---

# Recursive Download Workflow Guide

## Token Budget for This Workflow

**Tier 1 (Metadata)**: 150 tokens *(already loaded)*
**Tier 2 (Orchestrator)**: 600 tokens *(already loaded)*
**Tier 3 (This Guide)**: 1,100 tokens *(loading now)*

**Conditional Loading** (if needed):
- `guides/troubleshooting/error-resolution.md`: +950 tokens (if errors occur)

**Estimated Total**: 1,850-2,800 tokens
**Status**: ✅ Within budget (10,000 token limit)

---

## Workflow Overview

**Purpose**: Download a Notion page and ALL its child pages recursively, creating a folder structure matching the Notion hierarchy.

**Key Features**:
- Two-phase processing (discovery → download)
- YAML frontmatter with metadata (notion_id, title, timestamps)
- Strict file naming (lowercase, underscores, no special chars)
- mapping.json for future round-trip uploads
- Dry-run mode for preview
- Flat mode option

**Input**: Notion page ID or URL
**Output**: Folder structure with markdown files, images, and mapping.json

---

## Step 1: Extract Page ID

Same as single-page download - accepts:
- Notion URL: `https://notion.so/Page-Title-abc123def456`
- Page ID (32-char hex): `abc123def456789...`
- UUID format: `abc12345-6789-0123-4567-890123456789`

---

## Step 2: Choose Mode and Options

### Basic Recursive Download
```bash
python3 scripts/notion_download_recursive.py PAGE_ID --output ./docs/
```

### Dry Run (Preview Structure)
```bash
python3 scripts/notion_download_recursive.py PAGE_ID --dry-run
```

### Flat Mode (No Subdirectories)
```bash
python3 scripts/notion_download_recursive.py PAGE_ID --flat --output ./flat_docs/
```

### Limited Depth
```bash
python3 scripts/notion_download_recursive.py PAGE_ID --max-depth 2 --output ./docs/
```

### Verbose Output
```bash
python3 scripts/notion_download_recursive.py PAGE_ID --verbose --output ./docs/
```

---

## Step 3: Understand Output Structure

### Hierarchical Mode (Default)

```
output/
├── parent_page/
│   ├── index.md              # Parent page content
│   ├── child_page_1.md       # Leaf child (no children)
│   └── child_page_2/         # Child with grandchildren
│       ├── index.md
│       └── grandchild.md
├── images/
│   ├── parent_page/
│   │   └── parent_page_image_01.png
│   └── child_page_1/
│       └── child_page_1_image_01.png
└── mapping.json              # Page ID mappings for uploads
```

### Flat Mode

```
output/
├── parent_page.md
├── 01_child_page_1.md        # Depth-prefixed
├── 01_child_page_2.md
├── 02_grandchild.md
├── images/
│   └── (organized by page name)
└── mapping.json
```

---

## Step 4: File Naming Convention

All files use strict naming:

| Notion Title | Local Filename |
|-------------|----------------|
| "Design Overview" | `design_overview.md` |
| "API Reference (v2)" | `api_reference_v2.md` |
| "Chapter 1: Introduction" | `chapter_1_introduction.md` |
| "My Page!!!" | `my_page.md` |

**Rules Applied**:
- Lowercase all characters
- Replace spaces/hyphens with underscores
- Remove special characters
- Collapse multiple underscores
- Trim leading/trailing underscores

---

## Step 5: YAML Frontmatter

Each downloaded markdown file includes frontmatter:

```yaml
---
notion_id: 2c2d6bbd-bbea-8156-aefd-ed7fdd75c086
notion_url: https://notion.so/2c2d6bbdbbea8156aefded7fdd75c086
title: Design Overview
parent_id: 1a2b3c4d-5e6f-7890-abcd-ef1234567890
created_time: 2025-01-15T10:30:00.000Z
last_edited_time: 2025-12-06T14:22:00.000Z
downloaded_at: 2025-12-06T22:30:00
has_children: true
---

# Design Overview

Content starts here...
```

**Use Cases for Frontmatter**:
- Re-upload to same Notion pages (update vs create)
- Track which local files map to which Notion pages
- Detect if content changed since last download
- Build link references between pages

---

## Step 6: Mapping File (mapping.json)

The mapping file enables round-trip sync:

```json
{
  "source": {
    "notion_id": "parent-page-id",
    "title": "Documentation Root",
    "url": "https://notion.so/..."
  },
  "downloaded_at": "2025-12-06T22:30:00",
  "pages": {
    "parent_page/index.md": {
      "notion_id": "2c2d6bbd-...",
      "title": "Parent Page",
      "parent_id": null,
      "has_children": true,
      "child_paths": ["parent_page/child_1.md"]
    }
  },
  "statistics": {
    "total_pages": 15,
    "total_images": 23,
    "max_depth": 3
  }
}
```

---

## Step 7: Round-Trip Sync Workflow

### Download → Edit → Upload

```bash
# 1. Download entire documentation tree
python3 scripts/notion_download_recursive.py PAGE_ID --output ./docs/

# 2. Edit markdown files locally
# (Uses any text editor or IDE)

# 3. Upload back with preserved mappings
python3 scripts/notion_upload.py ./docs/ --recursive --mapping-file ./docs/mapping.json
```

**Benefits**:
- Updates existing pages instead of creating duplicates
- Preserves page hierarchy and relationships
- Maintains internal link references

---

## Error Handling

### Common Errors

**"NOTION_TOKEN not found"**:
- Route to: `guides/setup/configuration-guide.md`

**"404 object_not_found"**:
- Page not shared with integration
- Page ID is invalid or deleted
- Route to: `guides/troubleshooting/error-resolution.md`

**"Max depth exceeded"**:
- Reduce --max-depth value
- Very deep hierarchies may hit API limits

**"Rate limiting" (HTTP 429)**:
- Script handles automatically with backoff
- Large hierarchies may take longer

---

## CLI Reference

```
usage: notion_download_recursive.py [-h] [--output DIR] [--max-depth N]
                                    [--flat] [--no-images] [--dry-run]
                                    [--verbose]
                                    page_id

Arguments:
  page_id               Notion page ID or URL to download recursively

Options:
  --output, -o DIR      Output directory (default: ./downloaded/)
  --max-depth N         Maximum recursion depth (default: unlimited)
  --flat                Flatten hierarchy (no subdirectories)
  --no-images           Skip downloading images
  --dry-run             Show structure without downloading
  --verbose, -v         Detailed progress output
```

---

## When to Load Additional Resources

**User asks about element support**:
→ Load `references/MAPPINGS.md` (+515 tokens)

**Any error occurs**:
→ Load `guides/troubleshooting/error-resolution.md` (+950 tokens)

**User asks about initial setup**:
→ Load `guides/setup/configuration-guide.md` (+700 tokens)

---

## Post-Execution Token Summary

**Tokens used this request**:
- Tier 1: 150
- Tier 2: 600
- This guide: 1,100
- Conditionally loaded: 0-950 (if errors)
- **Total**: 1,850-2,800 tokens

**Status**: ✅ Well within 10,000 token budget
