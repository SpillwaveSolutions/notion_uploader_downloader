---
**PDA Tier**: 3 (Setup Guide)
**Estimated Tokens**: ~600 tokens
**Load Condition**: User explicitly asks for complete setup walkthrough
**Dependencies**: References configuration-guide.md for details
---

# First-Time Setup Guide

## Token Budget

**This Guide**: ~600 tokens
**Total with Tier 1+2**: 1,350 tokens

---

## Complete Setup Walkthrough

### Prerequisites

- Python 3.8 or higher installed
- Notion account
- pip (Python package manager)

---

## Step 1: Install Python Dependencies

```bash
# Navigate to the skill directory
cd /Users/richardhightower/.claude/skills/notion-uploader-downloader

# Install required packages
pip install -r scripts/requirements.txt
```

**Packages installed**:
- `requests` - HTTP library for Notion API calls
- `python-dotenv` - For loading .env files

---

## Step 2: Create Notion Integration

1. **Go to Notion integrations page**:
   - Visit: https://www.notion.so/my-integrations
   - Click "+ New integration"

2. **Configure integration**:
   - **Name**: "Markdown Uploader" (or your preferred name)
   - **Associated workspace**: Select your workspace
   - **Type**: Internal integration
   - Click "Submit"

3. **Copy integration token**:
   - After creation, find "Internal Integration Token"
   - Click "Show" → "Copy"
   - Save this token (you'll need it in Step 4)

---

## Step 3: Choose and Prepare Parent Page

1. **Create or choose a parent page**:
   - Open Notion
   - Create a new page called "Uploaded Articles" (or use existing page)
   - This is where uploaded markdown files will be created as child pages

2. **Get the page ID**:
   - Open the page in your browser
   - Copy the URL
   - Extract the ID from URL (long string at the end)
   - Example: `https://notion.so/Uploads-abc123def456` → ID is `abc123def456`

3. **Share page with integration**:
   - Open the page
   - Click "..." menu (top right)
   - Scroll to "Add connections"
   - Select your integration name ("Markdown Uploader")
   - Click "Confirm"

**Critical**: Without sharing, you'll get "404 object_not_found" errors.

---

## Step 4: Create .env.notion Configuration File

```bash
# In the skill directory (or your project directory)
cd /Users/richardhightower/.claude/skills/notion-uploader-downloader

# Create .env.notion file
touch .env.notion

# Edit the file (use nano, vim, or any text editor)
nano .env.notion
```

**Add this content** (replace with your actual values):

```bash
NOTION_TOKEN=ntn_paste_your_token_here
NOTION_PARENT_PAGE=paste_your_page_id_here
```

**Example**:
```bash
NOTION_TOKEN=ntn_1234567890abcdefghijklmnopqrstuvwxyz1234567890
NOTION_PARENT_PAGE=abc123def456789012345678901234
```

Save and exit.

---

## Step 5: Secure the Configuration File

⚠️ **Important**: Never commit .env.notion to git!

```bash
# Add to .gitignore
echo ".env.notion" >> .gitignore
echo ".env" >> .gitignore

# Verify it's ignored
git status  # Should not show .env.notion
```

---

## Step 6: Test the Setup

### Test 1: Create a test markdown file

```bash
cat > test-upload.md <<EOF
# Test Article

This is a test article to verify the Notion uploader works.

## Features

- Markdown to Notion conversion
- Image upload support
- Rich formatting

**Success!** If you can read this in Notion, the setup works.
EOF
```

### Test 2: Upload to Notion

```bash
python3 scripts/notion_upload.py test-upload.md
```

**Expected output**:
```
✅ Page created successfully!
   Page ID: xyz123...
   URL: https://notion.so/Test-Article-xyz123...
```

### Test 3: Open in Notion

- Click the URL from the output
- Verify the page appears in Notion
- Check it's a child of your parent page
- Verify formatting is preserved

### Test 4: Download back

```bash
python3 scripts/notion_download.py xyz123  # Use the page ID from step 2
```

**Expected**:
- Creates `./downloaded/test-article.md`
- Content matches original

---

## Step 7: Organize Your Workspace

### Create a good structure in Notion

1. **Main parent page**: "Uploaded Content" or "Articles"
2. **Sub-pages by category** (optional):
   - Blog Posts
   - Documentation
   - Notes
   - etc.

### Configure different parent pages for different projects

You can have multiple `.env.notion` files in different directories:

```
~/projects/blog/.env.notion         → NOTION_PARENT_PAGE=blog_page_id
~/projects/docs/.env.notion         → NOTION_PARENT_PAGE=docs_page_id
~/projects/notes/.env.notion        → NOTION_PARENT_PAGE=notes_page_id
```

Each project directory will use its own parent page!

---

## Common First-Time Issues

### Issue: "NOTION_TOKEN not found"

**Solutions**:
- Check .env.notion exists: `ls -la .env.notion`
- Check format: `cat .env.notion` (should show `NOTION_TOKEN=ntn_...`)
- Check no extra spaces: Should be `NOTION_TOKEN=value` not `NOTION_TOKEN = value`

### Issue: "404 object_not_found"

**Solutions**:
- Share parent page with integration (Step 3.3 above)
- Verify page ID is correct
- Check page wasn't deleted

### Issue: "Permission denied" or "Unauthorized"

**Solutions**:
- Token might be incorrect - copy again from Notion integrations page
- Token might be expired - regenerate in Notion
- Integration might not have access to workspace

### Issue: Python or pip not found

**Solutions**:
```bash
# Install Python 3 (macOS with Homebrew)
brew install python3

# Install Python 3 (Ubuntu/Debian)
sudo apt-get install python3 python3-pip

# Verify installation
python3 --version
pip3 --version
```

---

## You're All Set!

Now you can:

- ✅ Upload markdown files to Notion
- ✅ Download Notion pages to markdown
- ✅ Append content to existing pages
- ✅ Upload images automatically
- ✅ Preserve rich formatting

### Next Steps

**Learn the workflows**:
- `guides/workflows/upload-workflow.md` - Upload details
- `guides/workflows/download-workflow.md` - Download details
- `guides/workflows/update-workflow.md` - Append content

**Explore features**:
- `references/MAPPINGS.md` - All supported markdown elements
- `references/QUICK_START.md` - Command quick reference

**If you encounter errors**:
- `guides/troubleshooting/error-resolution.md` - Common errors and fixes

---

## Quick Reference Card

### Upload
```bash
python3 scripts/notion_upload.py article.md
python3 scripts/notion_upload.py article.md --parent-id PAGE_ID
```

### Download
```bash
python3 scripts/notion_download.py PAGE_ID
python3 scripts/notion_download.py "https://notion.so/Page-URL"
```

### Append/Update
```bash
python3 scripts/notion_upload.py new-content.md --page-id PAGE_ID
```

### Configuration Files
- `.env.notion` - Main configuration
- Add to `.gitignore` - CRITICAL for security

### Getting Help
- Configuration details: `guides/setup/configuration-guide.md`
- Troubleshooting: `guides/troubleshooting/error-resolution.md`
