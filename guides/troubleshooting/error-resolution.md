---
**PDA Tier**: 3 (Troubleshooting Guide)
**Estimated Tokens**: ~950 tokens
**Load Condition**: Errors occur or user reports issues
**Dependencies**: May route to configuration-guide.md
---

# Error Resolution Guide

## Token Budget

**This Guide**: ~950 tokens
**Total with Tier 1+2**: 1,700 tokens

---

## Error Category Index

Jump to specific error:
- [Configuration Errors](#configuration-errors)
- [Permission & Access Errors](#permission--access-errors)
- [Image Upload Errors](#image-upload-errors)
- [Script Execution Errors](#script-execution-errors)
- [Notion API Errors](#notion-api-errors)

---

## Configuration Errors

### Error: "NOTION_TOKEN not found!"

**Full message**:
```
❌ NOTION_TOKEN not found!
   Create .env.notion with NOTION_TOKEN=your_token
   Or set NOTION_TOKEN environment variable
```

**Cause**: Notion integration token not configured.

**Solutions**:

1. **Create .env.notion file**:
   ```bash
   echo "NOTION_TOKEN=ntn_your_token_here" > .env.notion
   ```

2. **Or set environment variable**:
   ```bash
   export NOTION_TOKEN=ntn_your_token_here
   ```

3. **Verify file exists**:
   ```bash
   ls -la .env.notion
   cat .env.notion  # Should show NOTION_TOKEN=...
   ```

**Get your token**: https://www.notion.so/my-integrations

**Route to**: `guides/setup/configuration-guide.md` for complete setup

---

### Error: "No parent page specified and NOTION_PARENT_PAGE not configured"

**Full message**:
```
❌ No parent page specified and NOTION_PARENT_PAGE not configured

   Please either:
   1. Add NOTION_PARENT_PAGE=your_page_id to .env.notion file
   2. Set NOTION_PARENT_PAGE environment variable
   3. Use --parent-id, --database-id, or --page-id flag
```

**Cause**: No destination specified for upload and no default configured.

**Solutions**:

1. **Add to .env.notion** (recommended):
   ```bash
   echo "NOTION_PARENT_PAGE=your_page_id" >> .env.notion
   ```

2. **Or use flag every time**:
   ```bash
   python3 scripts/notion_upload.py file.md --parent-id PAGE_ID
   ```

3. **Get page ID from Notion URL**:
   - URL: `https://notion.so/My-Page-abc123def456`
   - ID: `abc123def456`

**Route to**: `guides/setup/configuration-guide.md` for details

---

## Permission & Access Errors

### Error: "404 object_not_found" or "Could not find page"

**HTTP response**:
```json
{
  "object": "error",
  "status": 404,
  "code": "object_not_found",
  "message": "Could not find page with ID: abc123..."
}
```

**Causes** (in order of likelihood):

1. **Page not shared with integration** (MOST COMMON)
2. Invalid page ID
3. Page was deleted or moved to trash
4. Integration doesn't have access to workspace

**Solutions**:

#### Solution 1: Share Page with Integration

1. Open the page in Notion
2. Click "..." menu (top right)
3. Scroll down to "Add connections"
4. Find your integration name
5. Click to add connection
6. Click "Confirm"

**This must be done for**:
- The parent page (for uploads)
- Any page you want to download
- Any database you want to create entries in

#### Solution 2: Verify Page ID

```bash
# Try accessing the page directly in browser
https://notion.so/YOUR_PAGE_ID

# If it doesn't open, ID is wrong
```

**Get correct ID**:
- Open page in Notion → Copy URL → Extract ID from end

#### Solution 3: Check Page Wasn't Deleted

- Look in Notion trash (sidebar → "Trash")
- If found, restore the page
- Then share with integration

---

### Error: "401 Unauthorized"

**HTTP response**:
```json
{
  "object": "error",
  "status": 401,
  "code": "unauthorized",
  "message": "API token is invalid."
}
```

**Causes**:

1. Token is incorrect or corrupted
2. Token was regenerated in Notion (old token invalid)
3. Integration was deleted

**Solutions**:

1. **Get fresh token**:
   - Go to https://www.notion.so/my-integrations
   - Find your integration
   - Click "Show" → "Copy" for token
   - Update .env.notion with new token

2. **Verify token format**:
   - Should start with `ntn_`
   - Very long string (80+ characters)
   - No spaces, no line breaks

3. **Check integration exists**:
   - Visit integrations page
   - Verify your integration is still there
   - If deleted, create new one

---

## Image Upload Errors

### Error: "Failed to upload image: [filename]"

**Causes**:

1. Image file doesn't exist
2. Image path is wrong (relative vs. absolute)
3. Image size exceeds 20MB limit
4. Image format not supported
5. Network/connectivity issue

**Solutions**:

#### Solution 1: Verify Image Exists

```bash
# Check if image file exists
ls -lh path/to/image.png

# Verify it's accessible
file path/to/image.png
```

#### Solution 2: Fix Image Path

**In markdown**, image paths should be:

```markdown
<!-- Relative to markdown file (RECOMMENDED) -->
![alt text](./images/photo.png)
![alt text](images/photo.png)

<!-- Absolute path (works but not portable) -->
![alt text](/full/path/to/image.png)
```

**Script resolves paths relative to markdown file location**:
- If markdown is in `/home/user/docs/article.md`
- And markdown has `![](images/pic.png)`
- Script looks for `/home/user/docs/images/pic.png`

#### Solution 3: Check Image Size

```bash
# Check file size
ls -lh image.png

# If over 20MB, resize/compress first
# Use ImageMagick, Photoshop, or online tools
```

**Notion limit**: 20MB per image file

#### Solution 4: Verify Format

**Supported formats**:
- PNG
- JPG/JPEG
- GIF
- SVG (may have rendering issues)
- WebP

**Not supported**:
- PSD
- AI
- RAW formats
- Most video formats as images

---

## Script Execution Errors

### Error: "python3: command not found"

**Cause**: Python 3 not installed or not in PATH.

**Solutions**:

```bash
# macOS (with Homebrew)
brew install python3

# Ubuntu/Debian
sudo apt-get install python3

# Verify installation
python3 --version  # Should show 3.8 or higher
```

---

### Error: "ModuleNotFoundError: No module named 'requests'"

**Cause**: Required Python packages not installed.

**Solution**:

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Or install individually
pip install requests python-dotenv
```

---

### Error: "Permission denied" when creating files

**Cause**: No write permissions for output directory.

**Solutions**:

```bash
# Check permissions
ls -ld ./downloaded

# Create directory with correct permissions
mkdir -p ./downloaded
chmod 755 ./downloaded

# Or download to a different location
python3 scripts/notion_download.py PAGE_ID --output ~/Documents/notion-downloads
```

---

## Notion API Errors

### Error: "400 validation_error"

**Example**:
```json
{
  "object": "error",
  "status": 400,
  "code": "validation_error",
  "message": "body failed validation..."
}
```

**Causes**:

1. Invalid block structure sent to Notion
2. Unsupported property type
3. Malformed request

**Solutions**:

1. **Check your markdown**:
   - Verify it's valid markdown
   - Check for weird characters
   - Try with simpler markdown first

2. **Report as bug** (if markdown seems valid):
   - This might be a parser issue
   - Save the problematic markdown
   - Test with minimal example to isolate issue

---

### Error: "429 rate_limited"

**Message**: "Rate limited. Too many requests."

**Cause**: Exceeded Notion API rate limits.

**Notion limits**:
- 3 requests per second per integration

**Solutions**:

1. **Wait a minute** then retry
2. **Don't upload too many files rapidly** in a loop
3. **Add delay between uploads**:
   ```bash
   python3 scripts/notion_upload.py file1.md
   sleep 2
   python3 scripts/notion_upload.py file2.md
   sleep 2
   python3 scripts/notion_upload.py file3.md
   ```

---

### Error: "503 service_unavailable"

**Message**: "Service temporarily unavailable"

**Cause**: Notion's servers are down or experiencing issues.

**Solutions**:

1. **Wait and retry** (5-10 minutes)
2. **Check Notion status**: https://status.notion.so/
3. **Try again later** if widespread outage

---

## Debugging Techniques

### Enable Verbose Output

Add `print()` statements in script for debugging:

```python
# Add to scripts/notion_upload.py temporarily
print(f"DEBUG: Token found: {token[:10]}...")
print(f"DEBUG: Parent page: {args.parent_id}")
print(f"DEBUG: Blocks to upload: {len(blocks)}")
```

### Check Network Connectivity

```bash
# Test connection to Notion API
curl -I https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28"

# Should return 200 OK if token valid
```

### Validate JSON Responses

If script fails, capture the API response:

```python
# Add to script
print("Response:", response.text)
print("Status:", response.status_code)
```

---

## Getting More Help

### Check Documentation

- **Configuration**: `guides/setup/configuration-guide.md`
- **First-time setup**: `guides/setup/first-time-setup.md`
- **Upload workflow**: `guides/workflows/upload-workflow.md`
- **Download workflow**: `guides/workflows/download-workflow.md`

### Common Patterns

**Most errors are**:
1. Configuration missing (token or parent page)
2. Page not shared with integration
3. Wrong path to file or image

**Quick checklist**:
- [ ] .env.notion exists and has NOTION_TOKEN
- [ ] Integration created in Notion
- [ ] Pages shared with integration
- [ ] File paths are correct
- [ ] Python dependencies installed

---

## Error Not Listed?

If you encounter an error not covered here:

1. **Read the error message carefully** - it often tells you what's wrong
2. **Check Notion status page** - might be a platform issue
3. **Test with minimal example** - isolate the problem
4. **Check the script output** - look for specific error details

**Most issues are configuration or permissions** - double-check those first!
