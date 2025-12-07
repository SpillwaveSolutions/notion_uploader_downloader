---
**PDA Tier**: 3 (Setup Guide)
**Estimated Tokens**: ~700 tokens
**Load Condition**: Configuration Intent - User needs setup help or config errors detected
**Dependencies**: May load first-time-setup.md for complete walkthrough
---

# Configuration Guide

## Token Budget

**Tier 1**: 150 tokens *(loaded)*
**Tier 2**: 600 tokens *(loaded)*
**This Guide**: 700 tokens *(loading)*

**Total**: 1,450 tokens
**Status**: ✅ Within budget

---

## Required Configuration

This skill requires two configuration values:

1. **NOTION_TOKEN** (required) - Your Notion integration token
2. **NOTION_PARENT_PAGE** (optional but recommended) - Default parent page ID for uploads

---

## Configuration Method 1: .env.notion File (Recommended)

### Create .env.notion file

Create a file named `.env.notion` in your project directory:

```bash
# In your project root or skill directory
touch .env.notion
```

### Add configuration values

Edit `.env.notion` and add:

```bash
NOTION_TOKEN=ntn_your_integration_token_here
NOTION_PARENT_PAGE=your_default_parent_page_id
```

**Example**:
```bash
NOTION_TOKEN=ntn_1234567890abcdef1234567890abcdef123456789012345678901234
NOTION_PARENT_PAGE=abc123def456789012345678901234
```

### File discovery

The script automatically searches for `.env.notion` in:
1. Current working directory
2. Parent directories (walks up the tree)
3. Continues until found or reaches root

**This means**: You can put `.env.notion` in a parent directory and all subdirectories will find it.

---

## Configuration Method 2: Environment Variables

Set environment variables in your shell:

### Temporary (current session only)
```bash
export NOTION_TOKEN=ntn_your_token_here
export NOTION_PARENT_PAGE=your_page_id
```

### Permanent (add to .bashrc or .zshrc)
```bash
# Add these lines to ~/.bashrc or ~/.zshrc
export NOTION_TOKEN=ntn_your_token_here
export NOTION_PARENT_PAGE=your_page_id
```

Then reload shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

---

## Configuration Method 3: .env File (Alternative)

The script also checks `.env` files (in addition to `.env.notion`):

```bash
# Create .env file
touch .env

# Add configuration
NOTION_TOKEN=ntn_your_token_here
NOTION_PARENT_PAGE=your_page_id
```

**Search order**:
1. Environment variables
2. `.env.notion` (current dir)
3. `.env` (current dir)
4. `.env.notion` (parent dirs)
5. `.env` (parent dirs)

---

## Getting Your NOTION_TOKEN

### Step 1: Create Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "+ New integration"
3. Give it a name (e.g., "Markdown Uploader")
4. Select the workspace
5. Click "Submit"

### Step 2: Copy the Token

1. After creating, you'll see "Internal Integration Token"
2. Click "Show" then "Copy"
3. Token format: `ntn_1234567890abcdef...` (very long string)
4. Paste this into your `.env.notion` file as `NOTION_TOKEN=...`

### Step 3: Important Security Note

⚠️ **NEVER commit .env.notion to git!**

The token grants access to your Notion workspace. Keep it secret:

```bash
# Make sure .env.notion is in .gitignore
echo ".env.notion" >> .gitignore
echo ".env" >> .gitignore
```

---

## Getting Your NOTION_PARENT_PAGE

This is the default page where new uploads will be created as child pages.

### Step 1: Choose a Parent Page

1. Open Notion
2. Navigate to the page you want as the default parent
3. This could be:
   - A dedicated "Uploads" or "Articles" page
   - Your main workspace page
   - Any page where you want child pages created

### Step 2: Get the Page ID from URL

The Notion URL looks like:
```
https://www.notion.so/Page-Title-abc123def456789012345678901234
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                  This is the page ID
```

**Extract the ID**:
- It's the long string of letters and numbers at the end
- Can be 32 characters without dashes: `abc123def456789012345678901234`
- Or UUID format with dashes: `abc12345-6789-0123-4567-890123456789`
- Both formats work

### Step 3: Add to Configuration

```bash
NOTION_PARENT_PAGE=abc123def456789012345678901234
```

### Step 4: Share Page with Integration

**Critical**: The parent page must be shared with your integration!

1. Open the parent page in Notion
2. Click the "..." menu (top right)
3. Scroll to bottom → "Add connections"
4. Find and select your integration name
5. Click "Confirm"

**Without this step**: You'll get "404 object_not_found" errors when uploading.

---

## Is NOTION_PARENT_PAGE Required?

**Short answer**: No, but highly recommended.

**Without NOTION_PARENT_PAGE**:
- You MUST specify destination with every upload:
  - `--parent-id PAGE_ID` or
  - `--database-id DB_ID` or
  - `--page-id PAGE_ID` (for appends)
- Script will show error if you don't specify destination

**With NOTION_PARENT_PAGE**:
- Can upload without flags: `python3 scripts/notion_upload.py article.md`
- Destination defaults to your configured parent page
- Can still override with flags when needed

---

## Verifying Configuration

### Test NOTION_TOKEN

```bash
# Try downloading any page you have access to
python3 scripts/notion_download.py YOUR_PAGE_ID
```

**Success**: If it downloads, token is correct.
**Error "NOTION_TOKEN not found"**: Token not configured properly.
**Error "401 Unauthorized"**: Token is invalid.

### Test NOTION_PARENT_PAGE

```bash
# Try uploading a test file
echo "# Test" > test.md
python3 scripts/notion_upload.py test.md
```

**Success**: Page created at default parent.
**Error "No parent page specified..."**: NOTION_PARENT_PAGE not configured.
**Error "404 object_not_found"**: Parent page not shared with integration.

---

## Troubleshooting

**"NOTION_TOKEN not found"**:
- Check `.env.notion` exists in current or parent directory
- Check file format: `NOTION_TOKEN=ntn_...` (no quotes, no spaces around `=`)
- Check environment variable: `echo $NOTION_TOKEN`

**"NOTION_PARENT_PAGE not configured"**:
- Add `NOTION_PARENT_PAGE=...` to `.env.notion`
- OR use `--parent-id` flag explicitly

**"404 object_not_found"**:
- Page not shared with integration (see "Share Page" step above)
- Invalid page ID
- Page was deleted

**Script can't find .env.notion**:
- Check you're in the right directory
- Check file name is exactly `.env.notion` (with the dot)
- Try absolute path for testing: `NOTION_TOKEN=$(cat /full/path/to/.env.notion | grep NOTION_TOKEN | cut -d= -f2)`

---

## Example .env.notion File

```bash
# Notion Configuration
# Created: 2025-01-18

# Integration token (required)
# Get from: https://www.notion.so/my-integrations
NOTION_TOKEN=ntn_1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP

# Default parent page for uploads (optional but recommended)
# This is the page ID where new pages will be created as children
# Get from your Notion page URL
NOTION_PARENT_PAGE=abc123def456789012345678901234

# Notes:
# - Never commit this file to git!
# - Add to .gitignore
# - Keep token secret
# - Share parent page with integration in Notion
```

---

## Next Steps

After configuration:

1. **Test**: Try a simple upload/download
2. **Share pages**: Remember to share any page you want to access
3. **Organize**: Create a good default parent page structure
4. **Backup**: Keep a copy of your configuration (securely!)

For complete first-time setup walkthrough, load: `guides/setup/first-time-setup.md`
