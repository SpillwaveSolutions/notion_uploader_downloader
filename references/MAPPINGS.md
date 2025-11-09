# Notion Upload/Download Markdown Mappings

## Currently Supported ✅

### Inline Formatting
| Markdown | Notion | Status |
|----------|--------|--------|
| `**bold**` | `annotations.bold` | ✅ UPLOAD ✅ DOWNLOAD |
| `*italic*` | `annotations.italic` | ✅ UPLOAD ✅ DOWNLOAD |
| `` `code` `` | `annotations.code` | ✅ UPLOAD ✅ DOWNLOAD |
| `[text](url)` | `text.link.url` | ✅ UPLOAD ✅ DOWNLOAD |
| `~~strike~~` | `annotations.strikethrough` | ✅ UPLOAD ⚠️ DOWNLOAD (needs testing) |
| `<u>underline</u>` | `annotations.underline` | ✅ UPLOAD ⚠️ DOWNLOAD (needs testing) |

### Block-Level Elements
| Markdown | Notion Block | Status |
|----------|--------------|--------|
| `# H1` | `heading_1` | ✅ UPLOAD ✅ DOWNLOAD |
| `## H2` | `heading_2` | ✅ UPLOAD ✅ DOWNLOAD |
| `### H3` | `heading_3` | ✅ UPLOAD ✅ DOWNLOAD |
| `#### H4` | Bold+underlined paragraph | ✅ UPLOAD ✅ DOWNLOAD |
| `##### H5` | Bold+underlined paragraph | ✅ UPLOAD ✅ DOWNLOAD |
| `###### H6` | Bold+underlined paragraph | ✅ UPLOAD ✅ DOWNLOAD |
| Paragraph | `paragraph` | ✅ UPLOAD ✅ DOWNLOAD |
| Multi-line paragraph | `paragraph` (joined) | ✅ UPLOAD ✅ DOWNLOAD |
| `- bullet` | `bulleted_list_item` | ✅ UPLOAD ✅ DOWNLOAD |
| `1. numbered` | `numbered_list_item` | ✅ UPLOAD ✅ DOWNLOAD |
| `- [ ] todo` | `to_do` (unchecked) | ✅ UPLOAD ⚠️ DOWNLOAD (needs testing) |
| `- [x] done` | `to_do` (checked) | ✅ UPLOAD ⚠️ DOWNLOAD (needs testing) |
| `> quote` | `callout` (basic) | ✅ UPLOAD ✅ DOWNLOAD |
| `> [!NOTE]` etc. | `callout` (typed) | ✅ UPLOAD ⚠️ DOWNLOAD (lossy - emoji preserved) |
| ` ```code``` ` | `code` | ✅ UPLOAD ✅ DOWNLOAD |
| `---` | `divider` | ✅ UPLOAD ✅ DOWNLOAD |
| `![alt](url)` | `image` (external) | ✅ UPLOAD ✅ DOWNLOAD |
| `![alt](local.png)` | `image` (uploaded) | ✅ UPLOAD ⚠️ DOWNLOAD (needs implementation) |
| Table | `table` + `table_row` | ✅ UPLOAD ✅ DOWNLOAD |
| `<details>` | `toggle` | ❌ NOT IMPLEMENTED |

### Special Features
| Feature | Status |
|---------|--------|
| Mermaid diagrams | ✅ UPLOAD ✅ DOWNLOAD |
| Language mapping | ✅ UPLOAD ✅ DOWNLOAD |
| Image upload (File Upload API) | ✅ UPLOAD |
| Image download | ❌ DOWNLOAD |
| Nested lists | ❌ NOT IMPLEMENTED |
| Math equations | ❌ NOT IMPLEMENTED |

## ✅ Recently Implemented (2025-11-08)

1. **Strikethrough** - `~~text~~` → `annotations.strikethrough` ✅
2. **Underline** - `<u>text</u>` → `annotations.underline` ✅
3. **Task lists** - `- [ ]` / `- [x]` → `to_do` block with `checked` property ✅
4. **Callout types** - GitHub-style `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, etc. ✅
   - NOTE/INFO → ℹ️ blue background
   - TIP → 💡 green background
   - WARNING → ⚠️ yellow background
   - IMPORTANT → ❗ red background
   - CAUTION → 🛑 red background
5. **H5/H6 handling** - Now properly mapped like H4 (bold + underlined) ✅
6. **Multi-line paragraphs** - Consecutive lines properly joined ✅
7. **Image uploads** - Local files via File Upload API ✅

## Missing Features to Add

### High Priority
1. **Toggle blocks** - `<details>` / `<summary>` → `toggle` block
2. **Nested lists** - Indented list items → `children` property
3. **Download improvements** - Reverse all new upload features:
   - Strikethrough → `~~text~~`
   - Underline → `<u>text</u>` (or just skip, Notion doesn't roundtrip HTML)
   - Task lists → `- [ ]` / `- [x]`
   - Typed callouts → `> [!TYPE]` (detect emoji and reverse map)
   - Downloaded images to `./downloaded/images/`

### Medium Priority
4. **Math equations** - `$...$` inline, `$$...$$` block → `equation`
5. **Autolink detection** - Auto-convert bare URLs to links
6. **Color/highlighting** - Custom annotations (limited Notion support)
7. **Embed blocks** - YouTube, Twitter, etc. → `embed` blocks

## Implementation Notes

### For Strikethrough
- Add to `_parse_rich_text()` pattern: `r'(~~.*?~~)'`
- Set `annotations['strikethrough'] = True`

### For Task Lists
- Detect `- [ ]` or `- [x]` in parse loop
- Create `to_do` block with `checked` property

### For Callout Types
- Parse `> [!TYPE]` pattern
- Map TYPE to emoji:
  - NOTE → 💡 or ℹ️
  - TIP → 💡 or ✅
  - WARNING → ⚠️
  - IMPORTANT → ❗
  - CAUTION → 🛑

### For Toggle
- Detect `<details>` / `<summary>` tags
- Create `toggle` block with summary in rich_text, content in children
