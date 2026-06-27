import sys
import os
import argparse
import json
import argparse

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is not installed. Please install it to use this script.", file=sys.stderr)
    print("Run: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

def get_versioned_path(base_path):
    """Returns a versioned filename if the file already exists."""
    if not os.path.exists(base_path):
        return base_path
    
    directory = os.path.dirname(base_path)
    filename = os.path.basename(base_path)
    name, ext = os.path.splitext(filename)
    
    # Try name_v1, name_v2, etc.
    counter = 1
    while True:
        new_path = os.path.join(directory, f"{name}_v{counter}{ext}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def compute_global_body_size(doc):
    sizes = []
    for i in range(min(20, len(doc))):
        try:
            for b in doc[i].get_text("dict").get("blocks", []):
                if b.get("type") == 0:
                    for l in b.get("lines", []):
                        for s in l.get("spans", []):
                            txt = s.get("text", "").strip()
                            if txt: sizes.append(round(s.get("size", 10.0), 1))
        except: pass
    if sizes:
        from collections import Counter
        return Counter(sizes).most_common(1)[0][0]
    return 10.0

def extract_markdown_from_page(page, global_body_size=10.0, exclude_header_footer=False):
    md_lines = []
    
    # 1. Extract tables
    table_rects = []
    try:
        tables = page.find_tables(strategy="lines_strict")
        if tables and tables.tables:
            for table in tables.tables:
                table_rects.append(fitz.Rect(table.bbox))
                table_data = table.extract()
                if table_data:
                    for i, row in enumerate(table_data):
                        clean_row = [str(x).replace("\n", " ").strip() if x is not None else "" for x in row]
                        md_lines.append("| " + " | ".join(clean_row) + " |\n")
                        if i == 0:
                            md_lines.append("|" + "|".join(["---"] * len(row)) + "|\n")
                    md_lines.append("\n\n")
    except Exception as e:
        print(f"Warning: Table extraction error on page {page.number}: {e}", file=sys.stderr)

    # 2. Extract text blocks with heading heuristics
    try:
        blocks = page.get_text("dict")["blocks"]
        
        # Using the supplied global_body_size
        for b in blocks:
            if b.get("type", -1) == 0:
                if "bbox" not in b: continue
                b_rect = fitz.Rect(b["bbox"])
                
                # Check overlap with tables
                in_table = False
                for t_rect in table_rects:
                    if b_rect.intersects(t_rect):
                        in_table = True
                        break
                if in_table:
                    continue
                
                # Handle header/footer exclusion
                if exclude_header_footer:
                    rect = page.rect
                    if b_rect.y0 < rect.y0 + rect.height * 0.08 or b_rect.y1 > rect.y1 - rect.height * 0.08:
                        continue
                        
                block_text = ""
                is_block_heading = False
                block_heading_level = ""
                
                for l in b.get("lines", []):
                    line_text = ""
                    for s in l.get("spans", []):
                        text = s.get("text", "").replace("\n", " ").strip()
                        if not text: continue
                        
                        font_size = round(s.get("size", 10.0), 1)
                        is_bold = bool(s.get("flags", 0) & 16) or ("Bold" in s.get("font", "")) or ("Heavy" in s.get("font", ""))
                        
                        is_heading = False
                        if font_size >= global_body_size * 1.3 or font_size >= 14.0:
                            is_heading = True
                            if not block_heading_level: block_heading_level = "##"
                        elif font_size > global_body_size * 1.05 or (font_size >= 11.5 and is_bold):
                            is_heading = True
                            if not block_heading_level or len(block_heading_level) > 3: block_heading_level = "###"
                        elif is_bold and len(l.get("spans", [])) <= 3 and len(text) < 100:
                            is_heading = True
                            if not block_heading_level: block_heading_level = "####"
                        
                        if is_heading:
                            is_block_heading = True
                        
                        if is_bold and not is_heading:
                            line_text += f"**{text}** "
                        else:
                            line_text += f"{text} "
                            
                    block_text += line_text.strip() + " "
                    
                block_text = block_text.strip()
                if block_text:
                    if is_block_heading:
                        md_lines.append(f"\n{block_heading_level} {block_text}\n")
                    else:
                        md_lines.append(block_text + "\n\n")
    except Exception as e:
        print(f"Warning: Block extraction error on page {page.number}: {e}", file=sys.stderr)
        # Fallback to plain text if dictionary extraction fails entirely
        if exclude_header_footer:
            rect = page.rect
            clip_rect = fitz.Rect(rect.x0, rect.y0 + rect.height * 0.08, rect.x1, rect.y1 - rect.height * 0.08)
            md_lines.append(page.get_text("text", clip=clip_rect))
        else:
            md_lines.append(page.get_text("text"))

    return "".join(md_lines)

def extract_context_to_md(pdf_path, keywords, output_md_path, context_words=30, exclude_header_footer=False):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Failed to open PDF at {pdf_path}: {e}", file=sys.stderr)
        return False

    keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    if not keyword_list:
        print("No valid keywords provided.", file=sys.stderr)
        return False
        
    keyword_tokens = {kw: kw.split() for kw in keyword_list}
    found_contexts = []
    
    global_body_size = compute_global_body_size(doc)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        md_text = extract_markdown_from_page(page, global_body_size, exclude_header_footer)
        
        words = md_text.split()
        words_lower = [w.lower() for w in words]
        
        for i in range(len(words_lower)):
            for kw, tokens in keyword_tokens.items():
                if i + len(tokens) <= len(words_lower):
                    match = True
                    for j, tk in enumerate(tokens):
                        if tk not in words_lower[i+j]:
                            match = False
                            break
                    if match:
                        start = max(0, i - context_words)
                        end = min(len(words), i + len(tokens) + context_words)
                        context_chunk = " ".join(words[start:end])
                        
                        found_contexts.append(
                            f"### Match found on Page {page_num + 1} for keyword '{kw}'\n"
                            f"> ... {context_chunk} ...\n\n"
                        )
    
    if not found_contexts:
        print(f"No matches found for keywords: {keywords}", file=sys.stderr)
        return None

    seen = set()
    result = []
    for ctx in found_contexts:
        if ctx not in seen:
            result.append(ctx)
            seen.add(ctx)
            
    final_output_path = get_versioned_path(output_md_path)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(final_output_path)), exist_ok=True)
        with open(final_output_path, "w", encoding="utf-8") as f:
            f.write(f"# PDF Extraction Results\n\n")
            f.write(f"**Source PDF:** `{pdf_path}`\n")
            f.write(f"**Keywords Searched:** `{keywords}`\n\n")
            f.write("".join(result))
            
        print(f"Success! The extracted data has been saved to: {final_output_path}", file=sys.stderr)
        return final_output_path
    except Exception as e:
        print(f"Error writing to {final_output_path}: {e}", file=sys.stderr)
        return None

def convert_pdf_to_md(
    pdf_path,
    output_md_path,
    exclude_header_footer=False,
    write_images=False,
    embed_images=False,
    image_format="png",
    image_path="",
    dpi=150,
    table_strategy="lines_strict",
    page_separators=True,
    graphics_limit=None,
    ignore_images=False,
    ignore_graphics=False,
    force_text=True,
):
    """
    Converts a PDF to Markdown using pymupdf4llm.to_markdown() with full option support.

    Args:
        pdf_path            : path to the source PDF.
        output_md_path      : destination .md file path.
        exclude_header_footer: omit top/bottom 8% of each page (margin exclusion).
        write_images        : save extracted images as files (requires image_path).
        embed_images        : embed images inline as base64 (overrides write_images).
        image_format        : image file format — 'png', 'jpeg', 'webp', etc.
        image_path          : folder to save extracted images when write_images=True.
        dpi                 : resolution for rasterised images (default 150).
        table_strategy      : PyMuPDF table detection — 'lines_strict' (default),
                              'lines', 'explicit', or 'text'.
        page_separators     : insert '---' separators between pages in the output.
        graphics_limit      : ignore all vector graphics if count exceeds this number.
        ignore_images       : strip all raster images from output.
        ignore_graphics     : strip all vector graphics from output.
        force_text          : output text even when it sits on an image background.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Failed to open PDF at {pdf_path}: {e}", file=sys.stderr)
        return None

    final_output_path = get_versioned_path(output_md_path)
    os.makedirs(os.path.dirname(os.path.abspath(final_output_path)), exist_ok=True)

    # ── Primary path: pymupdf4llm (full-featured) ─────────────────────────────
    try:
        import pymupdf4llm

        # Build margin tuple for header/footer exclusion.
        # 'margins' = (left, top, right, bottom) in points — 0.08 * 792pt ≈ 63pt
        margins = (0, 63, 0, 63) if exclude_header_footer else 0

        # Ensure image output folder exists when saving to disk
        if write_images and image_path:
            os.makedirs(image_path, exist_ok=True)

        print(
            f"pymupdf4llm {pymupdf4llm.__version__} detected. Converting with options: "
            f"table_strategy={table_strategy}, write_images={write_images}, "
            f"embed_images={embed_images}, image_format={image_format}, dpi={dpi}",
            file=sys.stderr,
        )

        md_text = pymupdf4llm.to_markdown(
            pdf_path,
            write_images=write_images,
            embed_images=embed_images,
            ignore_images=ignore_images,
            ignore_graphics=ignore_graphics,
            image_path=image_path,
            image_format=image_format,
            dpi=dpi,
            table_strategy=table_strategy,
            page_separators=page_separators,
            graphics_limit=graphics_limit,
            force_text=force_text,
            margins=margins,
            show_progress=False,
        )

        with open(final_output_path, "w", encoding="utf-8") as f:
            f.write(md_text)

        print(f"Success! PDF converted via pymupdf4llm: {final_output_path}", file=sys.stderr)
        return final_output_path

    except ImportError:
        print("pymupdf4llm not found. Falling back to heuristic PyMuPDF conversion.", file=sys.stderr)

    # ── Fallback: heuristic extractor ─────────────────────────────────────────
    try:
        global_body_size = compute_global_body_size(doc)
        with open(final_output_path, "w", encoding="utf-8") as f:
            f.write(f"# Complete PDF Extraction\n\n")
            f.write(f"**Source PDF:** `{pdf_path}`\n\n")
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = extract_markdown_from_page(page, global_body_size, exclude_header_footer)
                f.write(f"## Page {page_num + 1}\n\n")
                f.write(text)
                f.write("\n\n---\n\n")
        print(f"Success! PDF converted via heuristic extractor: {final_output_path}", file=sys.stderr)
        return final_output_path
    except Exception as e:
        print(f"Error during PDF conversion: {e}", file=sys.stderr)
        return None

# Hierarchical PDF extraction (Stage 1) has been moved to:
# verification_mcp_server/scripts/vector_index.py
# Import via server.py using: from vector_index import extract_hierarchical_pdf_to_json



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF to Markdown Converter/Extractor")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--mode", choices=["extract", "convert"], default="extract", help="Operation mode")
    parser.add_argument("--keywords", help="Keywords for extraction (comma-separated)")
    parser.add_argument("--exclude-hf", action="store_true", help="Exclude header and footer")
    
    args = parser.parse_args()
    
    pdf_path = args.pdf_path
    if not os.path.isabs(pdf_path):
        pdf_path = os.path.abspath(pdf_path)
        
    if not os.path.exists(pdf_path):
        print(f"Error: Could not find PDF at {pdf_path}", file=sys.stderr)
        sys.exit(1)
            
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    project_dir = "d:\\Verification\\VERIFICATION_PLANNER"
    markdown_dir = os.path.join(project_dir, "markdown")
    os.makedirs(markdown_dir, exist_ok=True)

    if args.mode == "convert":
        output_filename = f"{base_name}.md"
        output_md_path = os.path.join(markdown_dir, output_filename)
        print(f"Converting entire PDF to markdown...", file=sys.stderr)
        convert_pdf_to_md(pdf_path, output_md_path, exclude_header_footer=args.exclude_hf)
    else:
        keywords = args.keywords or input("Enter keywords for extraction: ")
        safe_kw = keywords.split(",")[0].strip().replace(" ", "_").lower() or "data"
        output_filename = f"extracted_{safe_kw}_from_{base_name}.md"
        output_md_path = os.path.join(markdown_dir, output_filename)
        print(f"Extracting contexts for '{keywords}'...", file=sys.stderr)
        extract_context_to_md(pdf_path, keywords, output_md_path, exclude_header_footer=args.exclude_hf)


# Vector index build and query functionality has been moved to:
# verification_mcp_server/scripts/vector_index.py
# Import via server.py using: from vector_index import build_vector_index_from_json, query_vector_index
