import warnings
import os
import sys

# ── CRITICAL: FORCE LOCAL CACHE ENVIRONMENT BEFORE ANY IMPORTS ────────────────
_server_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_server_dir)
LOCAL_CACHE = os.path.join(_project_root, ".cache")
os.makedirs(LOCAL_CACHE, exist_ok=True)

os.environ["LLAMA_INDEX_CACHE_DIR"]   = LOCAL_CACHE
os.environ["TRANSFORMERS_CACHE"]      = LOCAL_CACHE
os.environ["HF_HOME"]                 = LOCAL_CACHE
os.environ["SENTENCE_TRANSFORMERS_HOME"] = LOCAL_CACHE

import json
import asyncio
import logging
import importlib
from datetime import datetime

# 1. Suppress all warnings immediately to prevent protocol corruption
warnings.filterwarnings("ignore")

# 2. Add scripts to path
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
sys.path.append(SCRIPT_DIR)

try:
    from pdf_to_markdown import (
        extract_context_to_md,
        convert_pdf_to_md,
    )
    from vector_index import (
        extract_hierarchical_pdf_to_json,
        build_vector_index_from_json,
        query_vector_index,
    )
    from plan_to_pdf import generate_pdf
    from uvm_mermaid_gen import generate_mermaid
    from uvm_env_gen import generate_uvm_env
except ImportError as e:
    sys.stderr.write(f"Error importing scripts: {e}\n")
    sys.exit(1)

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

app = Server("pdf-custom-tools")

@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="extract_pdf_context_to_md",
            description="Searches for keywords in a given PDF file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {"type": "string"},
                    "keywords": {"type": "string"},
                    "output_md_path": {"type": "string"},
                    "context_words": {"type": "integer", "default": 30},
                    "exclude_header_footer": {"type": "boolean", "default": False}
                },
                "required": ["pdf_path", "keywords", "output_md_path"]
            }
        ),
        Tool(
            name="convert_pdf_to_md",
            description="Converts entire PDF to markdown using pymupdf4llm with full layout, table, and image support.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {"type": "string"},
                    "output_md_path": {"type": "string"},
                    "exclude_header_footer": {"type": "boolean", "default": False},
                    "write_images": {"type": "boolean", "default": False, "description": "Save extracted images as files to image_path."},
                    "embed_images": {"type": "boolean", "default": False, "description": "Embed images inline as base64 in the markdown."},
                    "image_format": {"type": "string", "default": "png", "description": "Image format: png, jpeg, webp."},
                    "image_path": {"type": "string", "default": "", "description": "Folder to save extracted images when write_images=true."},
                    "dpi": {"type": "integer", "default": 150, "description": "Resolution for rasterised images."},
                    "table_strategy": {"type": "string", "default": "lines_strict", "description": "Table detection: lines_strict, lines, explicit, text."},
                    "page_separators": {"type": "boolean", "default": True, "description": "Insert --- between pages."},
                    "ignore_images": {"type": "boolean", "default": False, "description": "Strip all raster images."},
                    "ignore_graphics": {"type": "boolean", "default": False, "description": "Strip all vector graphics."}
                },
                "required": ["pdf_path", "output_md_path"]
            }
        ),
        Tool(
            name="convert_plan_to_pdf",
            description="Converts YAML verification plan into a PDF report.",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {"type": "string"},
                    "output_pdf_path": {"type": "string"}
                },
                "required": ["input_path", "output_pdf_path"]
            }
        ),
        Tool(
            name="generate_uvm_mermaid",
            description="Generates a UVM Mermaid diagram.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dut_role": {"type": "string"},
                    "protocol": {"type": "string", "default": "AXI"},
                    "has_config": {"type": "boolean", "default": True},
                    "has_scoreboard": {"type": "boolean", "default": True}
                },
                "required": ["dut_role"]
            }
        ),
        Tool(
            name="generate_uvm_code",
            description="Generates UVM SystemVerilog code by merging a YAML plan with templates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "yaml_path": {"type": "string"},
                    "template_dir": {"type": "string"},
                    "output_dir": {"type": "string"}
                },
                "required": ["yaml_path", "template_dir", "output_dir"]
            }
        ),
        Tool(
            name="extract_hierarchical_pdf",
            description="Builds a LlamaIndex RAG Knowledge Graph from the PDF. Uses PyMuPDFReader to load the document into page-level nodes, maps each node to its TOC section hierarchy, and outputs a structured JSON Knowledge Graph with 'kg_metadata', 'sections' (TOC-mapped with child node IDs), and 'nodes' (page text + section context + embedding placeholder). No LLM or embedding model required.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {"type": "string"},
                    "output_json_path": {"type": "string"}
                },
                "required": ["pdf_path", "output_json_path"]
            }
        ),
        Tool(
            name="build_vector_index",
            description=(
                "Builds an offline LlamaIndex VectorStoreIndex from a Knowledge Graph JSON "
                "(produced by extract_hierarchical_pdf). Embeds all chunks with the free, offline "
                "BAAI/bge-small-en-v1.5 HuggingFace model — no API key, no internet required after "
                "first model download. Persists the index to disk for reuse. NO LLM is used."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "json_path":    {"type": "string", "description": "Absolute path to the KG JSON file."},
                    "persist_dir":  {"type": "string", "description": "Directory to persist the vector index.", "default": "./storage"}
                },
                "required": ["json_path", "persist_dir"]
            }
        ),
        Tool(
            name="query_vector_index",
            description=(
                "Queries a persisted LlamaIndex VectorStoreIndex using pure embedding-based retrieval. "
                "Returns the top-K most semantically relevant spec chunks with section title, page number, "
                "and similarity score. NO LLM is invoked — zero generative token cost. "
                "The calling LLM only reads the returned chunks, not the entire PDF."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "persist_dir": {"type": "string", "description": "Path to the persisted vector index directory."},
                    "query_str":   {"type": "string", "description": "Technical query string for semantic search."},
                    "top_k":       {"type": "integer", "default": 5, "description": "Number of top chunks to return (default: 5)."}
                },
                "required": ["query_str", "persist_dir"]
            }
        ),
        mcp.types.Tool(
            name="debug_env",
            description="Returns the current environment variables and cache settings for debugging.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool calls with absolute stdout protection."""
    if not arguments:
        raise ValueError("Missing arguments")

    # ── TECHNICAL FIX: Force environment variables before any LlamaIndex work ──
    project_root = os.path.dirname(os.path.abspath(__file__))
    local_cache = os.path.join(project_root, ".cache")
    os.environ["LLAMA_INDEX_CACHE_DIR"]   = local_cache
    os.environ["TRANSFORMERS_CACHE"]      = local_cache
    os.environ["HF_HOME"]                 = local_cache
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = local_cache
    os.makedirs(local_cache, exist_ok=True)

    try:
        import scripts.vector_index
        importlib.reload(scripts.vector_index)
    except Exception as e:
        logging.error(f"Failed to reload vector_index: {e}")

    # Redirect stdout to stderr for the duration of the tool call
    _orig_stdout = sys.stdout
    sys.stdout = sys.stderr
    
    try:
        if name == "extract_pdf_context_to_md":
            res = extract_context_to_md(arguments.get("pdf_path"), arguments.get("keywords"), arguments.get("output_md_path"), arguments.get("context_words", 30), arguments.get("exclude_header_footer", False))
            result_text = f"Success: {res}" if res else "Failed"
        if name == "debug_env":
            env_data = {
                "LLAMA_INDEX_CACHE_DIR": os.environ.get("LLAMA_INDEX_CACHE_DIR"),
                "HF_HOME": os.environ.get("HF_HOME"),
                "TRANSFORMERS_CACHE": os.environ.get("TRANSFORMERS_CACHE"),
                "SENTENCE_TRANSFORMERS_HOME": os.environ.get("SENTENCE_TRANSFORMERS_HOME"),
                "LOCAL_CACHE_PATH": LOCAL_CACHE,
                "PYTHONPATH": os.environ.get("PYTHONPATH"),
                "CWD": os.getcwd(),
            }
            return [mcp.types.TextContent(type="text", text=json.dumps(env_data, indent=2))]

        if name == "convert_pdf_to_md":
            res = convert_pdf_to_md(
                arguments.get("pdf_path"),
                arguments.get("output_md_path"),
                exclude_header_footer=arguments.get("exclude_header_footer", False),
                write_images=arguments.get("write_images", False),
                embed_images=arguments.get("embed_images", False),
                image_format=arguments.get("image_format", "png"),
                image_path=arguments.get("image_path", ""),
                dpi=arguments.get("dpi", 150),
                table_strategy=arguments.get("table_strategy", "lines_strict"),
                page_separators=arguments.get("page_separators", True),
                ignore_images=arguments.get("ignore_images", False),
                ignore_graphics=arguments.get("ignore_graphics", False),
            )
            result_text = f"Success: {res}" if res else "Failed"
        elif name == "convert_plan_to_pdf":
            res = generate_pdf(arguments.get("input_path"), arguments.get("output_pdf_path"))
            result_text = f"Success: {res}" if res else "Failed"
        elif name == "generate_uvm_mermaid":
            result_text = generate_mermaid(arguments.get("dut_role"), arguments.get("protocol", "AXI"), arguments.get("has_config", True), arguments.get("has_scoreboard", True))
        elif name == "generate_uvm_code":
            result_text = generate_uvm_env(arguments.get("yaml_path"), arguments.get("template_dir"), arguments.get("output_dir"))
        elif name == "extract_hierarchical_pdf":
            res = extract_hierarchical_pdf_to_json(arguments.get("pdf_path"), arguments.get("output_json_path"))
            result_text = f"Success: {res}" if res and "Failed" not in res else res
        elif name == "build_vector_index":
            res = build_vector_index_from_json(
                arguments.get("json_path"),
                arguments.get("persist_dir", "./storage"),
            )
            result_text = res
        elif name == "query_vector_index":
            res = query_vector_index(
                arguments.get("persist_dir", "./storage"),
                arguments.get("query_str"),
                top_k=int(arguments.get("top_k", 5)),
            )
            result_text = res
        else:
            result_text = f"Unknown tool: {name}"
    except Exception as e:
        sys.stderr.write(f"Error executing tool {name}: {e}\n")
        result_text = f"Error: {e}"
    finally:
        # ALWAYS restore stdout
        sys.stdout = _orig_stdout

    return [TextContent(type="text", text=result_text)]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
