---
description: Sync documentation from source websites to local markdown files for agent context.
allowed-tools: Task, WebFetch, Write, Edit, Bash(ls*), Bash(mkdir*), Bash(find*), Bash(rm*), Read, Glob, mcp__firecrawl-mcp__firecrawl_scrape
---

# Sync AI Docs

Sync documentation from source websites to local markdown files for agent context.

## Variables

DELETE_OLD_AI_DOCS_AFTER_HOURS: 24

## Workflow

1. **Read and Parse ai_docs/README.md**
   - Read the file and identify sections marked with `## section_name` headers
   - For each section, collect all URLs listed under it (lines starting with `- http`)
   - Build a mapping of `{section: [urls]}`

2. **Check Existing Files**
   For each section and its URLs:
   - Use Glob to find existing files: `ai_docs/<section>/*.md`
   - For each existing file, check its modification time using `ls -la`
   - If file was modified within the last `DELETE_OLD_AI_DOCS_AFTER_HOURS` hours:
     - Skip this URL - note it was skipped
   - If file is older:
     - Delete it using `rm` - note it was deleted

3. **Create Section Directories**
   For each section that has URLs to process:
   ```bash
   mkdir -p ai_docs/<section>
   ```

4. **Scrape Documentation in Parallel**
   For each URL that was not skipped, use the Task tool in parallel with the docs-scraper agent:

   <scrape_loop_prompt>
   Use @agent-docs-scraper agent - pass it the section and url in this format: `<section>: <url>`
   </scrape_loop_prompt>

5. **Report Results**
   After all Tasks are complete, respond in the Report Format below.

## Report Format

```
AI Docs Report
==============

Sections Processed:
- <section_name>: X files

Results:
--------
<section_name>/
  - <SUCCESS or FAILURE>: <url> -> <filename>.md
  - <SKIPPED>: <url> (recent)
  ...

<section_name>/
  - <SUCCESS or FAILURE>: <url> -> <filename>.md
  ...

Summary:
- Total URLs: X
- Successful: Y
- Skipped: Z
- Failed: W
```
