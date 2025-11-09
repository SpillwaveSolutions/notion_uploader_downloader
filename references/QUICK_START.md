# Notion Uploader/Downloader - Quick Start

## Instant Usage (Just say these phrases!)

### Upload to Notion
```
"Upload articles/my_article.md to Notion"
"Publish work/final/article.md to Notion"
"Save this document to Notion"
"Upload my blog post to Notion"
```

### Download from Notion
```
"Download https://notion.so/page-url"
"Download that Notion page"
"Backup my articles from Notion"
"Export that article from Notion"
```

## Quick Commands

**Upload**:
```bash
python3 ~/.claude/skills/notion-uploader-downloader/notion_upload.py \
  article.md --parent-id 2a5d6bbdbbea8089bf5cc5afdc1cabd0
```

**Download**:
```bash
python3 ~/.claude/skills/notion-uploader-downloader/notion_download.py PAGE_ID
```

## First Time Setup

1. **Get your Notion token**:
   - Go to https://www.notion.so/my-integrations
   - Create a new integration
   - Copy the Internal Integration Token

2. **Save token**:
   ```bash
   echo "NOTION_TOKEN=ntn_your_token_here" > .env.notion
   ```

3. **Share pages with integration**:
   - Open your Notion page
   - Click "..." → "Add connections" → Select your integration

## Default Articles Page
Default parent page ID: `2a5d6bbdbbea8089bf5cc5afdc1cabd0`

## Features
- ✅ Uploads local images automatically
- ✅ Preserves all formatting (bold, italic, code, links, tables)
- ✅ Supports Mermaid diagrams
- ✅ GitHub-flavored markdown (task lists, callouts, strikethrough)
- ✅ Downloads images locally
- ✅ Bidirectional sync

## Trigger Words
Just mention: **upload**, **download**, **notion**, **markdown**, **.md file**, **article**, **document**, **publish**, **sync**, **backup**, **export**

Claude Code will automatically offer to use this skill! 🎉
