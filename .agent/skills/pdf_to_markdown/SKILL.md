---
name: pdf_to_markdown
description: Extracts contextual data from PDFs or converts entire PDFs to markdown files without sending raw text back to the LLM to save tokens.
---

# PDF to Markdown Skill

This skill handles extracting information (like dates or data) from a PDF or converting complete PDFs to Markdown. Crucially, to **save tokens**, the extracted data is NEVER returned to the LLM. Instead, the MCP tool accesses the PDF and writes the findings directly to a targeted markdown file.

> [!TIP]
> For semantic search and full RAG query workflows, this skill integrates with the **`vector_index`** skill. See `.agent/skills/vector_index/SKILL.md` for the complete 3-stage pipeline (Extract → Build → Query).

## Instructions

Whenever you are tasked with using this skill to extract data or convert a PDF, you MUST collect the missing inputs from the user:

### Mode 1: Context Extraction (Keywords)
If the user wants specific keywords extracted:
1. **Ask for PDF Path**: Politely ask the user for the absolute path to the PDF file (if not provided).
2. **Ask for Keywords**: Politely ask the user for the comma-separated keywords to search for (if not provided).
3. **Determine Output Path**: If the user did not provide an output path, generate a descriptive file name based on the keywords or PDF name. **Ensure this path is placed inside the `markdown/` folder within the project directory** (e.g., `d:\Verification\VERIFICATION_PLANNER\markdown\extracted.md`). Create the folder if needed.
4. **Invoke `extract_pdf_context_to_md`**: Run this MCP tool with the collected arguments.

### Mode 2: Complete Conversion
If the user wants to convert the *entire* PDF to markdown:
1. **Ask for PDF Path**: Politely ask the user for the absolute path to the PDF file (if not provided).
2. **Determine Output Path**: If the user did not provide an output path, generate a descriptive file name based on the PDF name. **You MUST ensure the file is saved within a `markdown` subdirectory in the project folder** (e.g., `d:\Verification\VERIFICATION_PLANNER\markdown\converted_pdf.md`). Create the folder if needed.
3. **Invoke `convert_pdf_to_md`**: Run this MCP tool with the PDF path and the output path. You can provide additional options based on user requirements:

> **Engine:** `pymupdf4llm.to_markdown()` (falls back to a heuristic extractor if unavailable).
> 
> **Available options** — pass only what the user needs, all have sensible defaults:
> 
> | Parameter | Default | Description |
> |---|---|---|
> | `exclude_header_footer` | `false` | Clip top/bottom 8% margins to remove headers/footers |
> | `write_images` | `false` | Save extracted images as files (requires `image_path`) |
> | `embed_images` | `false` | Embed images inline as base64 (overrides `write_images`) |
> | `image_format` | `"png"` | Image format: `png`, `jpeg`, `webp` |
> | `image_path` | `""` | Folder to save extracted images |
> | `dpi` | `150` | Resolution for rasterised images |
> | `table_strategy` | `"lines_strict"` | Table detection: `lines_strict`, `lines`, `explicit`, `text` |
> | `page_separators` | `true` | Insert `---` separators between pages |
> | `ignore_images` | `false` | Strip all raster images from output |
> | `ignore_graphics` | `false` | Strip all vector graphics from output |
The tools will silently parse the PDF and write the output directly to the target file. If the target file already exists, it will automatically append a version suffix (e.g., `_v1.md`) to avoid overwriting previous work. The tool will return the final path used. Do NOT attempt to view or read the output file unless explicitly instructed by the user, as the goal is to save tokens.

## To add more tools to this Server
Modify `d:\Verification\VERIFICATION_PLANNER\verification_mcp_server\server.py` and `d:\Verification\VERIFICATION_PLANNER\verification_mcp_server\scripts\pdf_to_markdown.py` to extend abilities.
