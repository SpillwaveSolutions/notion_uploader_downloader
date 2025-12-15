# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Claude Code skill** that enables bidirectional synchronization between Markdown files and Notion pages. It provides Python scripts for uploading markdown (with images and rich formatting) to Notion and downloading Notion pages back to markdown format.

**Version**: 2.0.0 (PDA-compliant)
**Architecture**: Progressive Disclosure Architecture (PDA) with 3-tier structure

## Essential Commands

### Installation
```bash
pip install -r scripts/requirements.txt
```

### Configuration
```bash
# Copy example configuration
cp .env.notion.example .env.notion

# Edit and add your values
# NOTION_TOKEN=ntn_your_token
# NOTION_PARENT_PAGE=your_default_page_id
```

### Upload Operations
```bash
# Upload with default parent (from NOTION_PARENT_PAGE env var)
python3 scripts/notion_upload.py article.md

# Upload to specific parent page
python3 scripts/notion_upload.py article.md --parent-id PAGE_ID

# Upload to database
python3 scripts/notion_upload.py article.md --database-id DATABASE_ID

# Append to existing page
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
```bash
# Currently no automated tests
# Manual testing via upload/download workflows
```

## Architecture Overview - Progressive Disclosure Architecture (PDA)

This skill implements PDA with three tiers:

### Tier 1: Metadata (~150 tokens)
- **Location**: SKILL.md YAML frontmatter (lines 1-20)
- **Purpose**: Skill identity, version, allowed tools, metadata
- **Loaded**: Every skill invocation
- **Token Budget**: 150 tokens

### Tier 2: Orchestrator (~600 tokens)
- **Location**: SKILL.md body (lines 22-169)
- **Purpose**: Intent classification, decision tree, routing logic
- **Loaded**: Every skill invocation
- **Contains**:
  - 6 intent classifications (upload, download, update, config, troubleshooting, reference)
  - Resource catalog with load conditions
  - Token budget management rules
  - Error handling & fallback logic
- **Token Budget**: 600 tokens
- **Does NOT contain**: Workflows, examples, comprehensive guides

### Tier 3: Resources (~600-1,250 tokens per guide, loaded on-demand)
- **Location**: `guides/` and `references/` directories
- **Purpose**: Detailed workflow execution, setup, troubleshooting, reference
- **Loaded**: ONLY when Tier 2 routes to specific guide
- **Categories**:

#### Workflow Guides (`guides/workflows/`)
- `upload-workflow.md` (~1,250 tokens) - Complete upload orchestration
- `download-workflow.md` (~850 tokens) - Download orchestration
- `update-workflow.md` (~1,100 tokens) - Update/append orchestration

#### Setup Guides (`guides/setup/`)
- `configuration-guide.md` (~700 tokens) - Environment setup
- `first-time-setup.md` (~600 tokens) - Complete walkthrough

#### Troubleshooting (`guides/troubleshooting/`)
- `error-resolution.md` (~950 tokens) - Common errors & fixes

#### Reference Docs (`references/`)
- `QUICK_START.md` (~320 tokens) - Command examples
- `MAPPINGS.md` (~515 tokens) - Markdown ↔ Notion elements
- `IMPLEMENTATION_SUMMARY.md` (~1,090 tokens) - Technical details

### PDA Token Budget Targets

- Tier 1 + Tier 2: ~750 tokens (always loaded)
- Typical request: 1,600-2,550 tokens (1 workflow guide)
- Complex request: 3,000-4,500 tokens (workflow + references)
- Maximum budget: 10,000 tokens per request

## Core Components

### `scripts/notion_upload.py` (913 lines)
**Main upload script with two key classes**:

- `MarkdownToNotionConverter` (lines 27-551): Parses markdown into Notion block objects
  - `parse()` method (lines 38-200): Main parsing loop handling all markdown elements
  - `_parse_rich_text()` (lines 202-291): Converts inline formatting (bold, italic, code, links, strikethrough, underline)
  - Block creation methods: `_make_heading()`, `_make_paragraph()`, `_make_code_block()`, `_make_callout()`, `_parse_table()`, etc.
  - Image handling: `_make_image()` (lines 505-551) uses File Upload API for local files

- `NotionUploader` (lines 554-727): Handles Notion API communication
  - `upload_file()` (lines 566-633): Two-step file upload using File Upload API
  - `create_page()` (lines 635-708): Creates pages/database entries and adds content in 100-block batches
  - `_append_blocks()` (lines 710-727): Appends blocks to existing pages

### `scripts/notion_download.py` (399 lines)
**Download script with**:

- `NotionToMarkdownConverter` (lines 23-225): Converts Notion blocks to markdown
  - `blocks_to_markdown()` (lines 32-80): Main conversion loop
  - `_extract_text()` (lines 82-116): Converts rich text with inline formatting
  - Block conversion methods for all supported Notion block types
  - `_image_to_md()` (lines 169-218): Downloads images to `./downloaded/images/`

- `NotionDownloader` (lines 227-370): Handles Notion API retrieval
  - `get_blocks()` (lines 262-306): Recursively fetches all blocks with pagination
  - `download_page()` (lines 308-365): Orchestrates full page download

### `scripts/notion_utils.py` (165 lines)
**Shared utilities**:

- `find_notion_token()` (lines 11-42): Token discovery from `.env.notion` or environment variable
  - Search order: ENV var → `.env.notion` (current) → `.env.notion` (parents) → `.env`

- `find_notion_parent_page()` (lines 45-93): Parent page ID discovery (NEW in v2.0)
  - Same search pattern as token
  - Enables default parent without hardcoding
  - Critical fix for general-purpose skill usage

- `extract_page_id()` (lines 96-126): Extracts page ID from URLs or validates IDs
- `format_page_id()` (lines 129-141): Converts 32-char hex to UUID format for Notion API
- `sanitize_filename()` (lines 72-93): Converts page titles to valid filenames
- `ensure_directory()` (lines 144-151): Creates directories with parents

## Key Architectural Patterns

### Markdown Parsing Strategy
Sequential line-by-line parsing with lookahead for multi-line elements (tables, code blocks, paragraphs). Special handling order prevents conflicts (e.g., tables checked before headers, blockquotes before bullet lists).

### Notion API Batch Processing
All block operations use 100-block batches (Notion API limit). Tables include their `table_row` children inline within the `table` object rather than as separate blocks.

### Image Upload Flow
1. POST `/v1/file_uploads` with filename and content_type → receive upload_url and file_upload_id
2. POST multipart/form-data to upload_url with binary file
3. Reference file_upload_id in image block using `type: "file_upload"`

### Environment Variable Discovery
Searches current directory, then walks up parent directories for `.env.notion` file containing configuration.
Checks both `.env.notion` and `.env` files.
Environment variables take precedence.

## Configuration

### Required Configuration

1. **NOTION_TOKEN** (required)
   - Notion integration token
   - Get from: https://www.notion.so/my-integrations
   - Format: `ntn_` followed by long alphanumeric string

2. **NOTION_PARENT_PAGE** (optional but recommended)
   - Default parent page ID for uploads
   - Get from Notion page URL (ID at the end)
   - Can be overridden with `--parent-id`, `--database-id`, or `--page-id` flags

### Configuration File Locations (Searched in Order)

1. Environment variable `NOTION_TOKEN` or `NOTION_PARENT_PAGE`
2. `.env.notion` file in current directory
3. `.env` file in current directory
4. `.env.notion` in parent directories (walks up tree)
5. `.env` in parent directories

### Example .env.notion File

```bash
NOTION_TOKEN=ntn_your_integration_token_here
NOTION_PARENT_PAGE=your_default_parent_page_id
```

### Security

⚠️ **CRITICAL**: Never commit `.env.notion` or `.env` to git!
- Both files are in `.gitignore`
- Tokens grant access to your Notion workspace
- Use `.env.notion.example` as template

## Supported Markdown Features

**Inline**: `**bold**`, `*italic*`, `` `code` ``, `[links](url)`, `~~strikethrough~~`, `<u>underline</u>`

**Blocks**: H1-H6 (H4-H6 become bold+underlined paragraphs), paragraphs (with multi-line joining), bullet/numbered lists, task lists (`- [ ]`/`- [x]`), code blocks with syntax highlighting, tables, images (local/URL), blockquotes, GitHub-style callouts (`> [!NOTE]`), horizontal rules

**Special**: Mermaid diagrams (preserved in code blocks), language mapping (e.g., `js`→`javascript`, `sh`→`shell`)

## Important Implementation Notes

- Notion API version: `2022-06-28` (consistent across all API calls)
- H4/H5/H6 are rendered as bold+underlined paragraphs with colons (Notion only supports H1-H3 natively)
- Multi-line paragraphs: Consecutive non-empty lines are joined with spaces (markdown soft breaks)
- Callout emoji mapping: NOTE→ℹ️, TIP→💡, WARNING→⚠️, IMPORTANT→❗, CAUTION→🛑
- Image size limit: 20MB per file (File Upload API restriction)
- Code block content: Truncated to 2000 chars (Notion limit)
- Anchor links are stripped (Notion doesn't support internal page anchors)
- Default parent page NO LONGER HARDCODED (v2.0 improvement)

## File Organization

```
/
├── SKILL.md                    # Tier 1+2: Metadata + Orchestrator (PDA-compliant)
├── CLAUDE.md                   # This file: Development guidance
├── README.md                   # User-facing documentation
├── .env.notion.example         # Configuration template
├── .gitignore                  # Excludes secrets and cache
│
├── scripts/
│   ├── notion_upload.py        # Upload markdown → Notion
│   ├── notion_download.py      # Download Notion → markdown
│   ├── notion_utils.py         # Shared utilities
│   └── requirements.txt        # Python dependencies
│
├── guides/                     # Tier 3: On-demand workflow guides
│   ├── workflows/
│   │   ├── upload-workflow.md      # Upload orchestration
│   │   ├── download-workflow.md    # Download orchestration
│   │   └── update-workflow.md      # Update/append orchestration
│   ├── setup/
│   │   ├── configuration-guide.md  # Environment setup
│   │   └── first-time-setup.md     # Complete walkthrough
│   └── troubleshooting/
│       └── error-resolution.md     # Common errors & fixes
│
└── references/                 # Tier 3: Technical reference docs
    ├── QUICK_START.md              # Command quick reference
    ├── MAPPINGS.md                 # Element mapping table
    └── IMPLEMENTATION_SUMMARY.md   # Technical implementation details
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

### Maintaining PDA Compliance

**When modifying SKILL.md**:
- Keep Tier 2 (body) under 150 lines if possible
- Never embed full workflows or examples
- Only decision tree, routing logic, and resource catalog
- Move detailed content to Tier 3 guides

**When adding new workflows**:
- Create new guide in `guides/workflows/`
- Add entry to SKILL.md Resource Catalog
- Add routing logic to Intent Classification section
- Include token budget in guide header
- Keep guide focused (<300 lines)

**When adding new features**:
- Document in appropriate Tier 3 reference guide
- Update routing logic in SKILL.md
- Don't bloat Tier 2 with details

### Common Debugging Scenarios

**"404 object_not_found"**: Page/database not shared with Notion integration. User must click "..." → "Add connections" → select their integration.

**"Failed to upload image"**: Check image path is relative to markdown file location, verify file exists, ensure <20MB size.

**Formatting not preserved**: Check `_parse_rich_text()` regex patterns, verify annotations are correctly applied.

**Parse errors**: Check element detection order in `parse()` method - earlier checks take precedence.

**"No parent page specified"**: NOTION_PARENT_PAGE not configured. User needs to add to .env.notion or use --parent-id flag.

## Quality Assurance

This is a skill (documentation/orchestration), not an application with tests.

**Testing strategy**:
1. Manual testing of upload workflow
2. Manual testing of download workflow
3. Manual testing of update workflow
4. Round-trip validation (upload → download should match original)
5. Configuration error testing
6. PDA compliance verification (token budgets)

**No automated test suite** - changes are validated through manual workflow execution.
