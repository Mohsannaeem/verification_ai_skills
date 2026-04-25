import warnings
import sys
import os
import json
import asyncio

# 1. Suppress all warnings immediately to prevent protocol corruption
warnings.filterwarnings("ignore")

# 2. Add scripts to path
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
sys.path.append(SCRIPT_DIR)

try:
    from pdf_to_markdown import extract_context_to_md, convert_pdf_to_md
    from plan_to_pdf import generate_pdf
    from model_stats import calculate_stats
    from uvm_mermaid_gen import generate_mermaid
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
            description="Converts entire PDF to markdown.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {"type": "string"},
                    "output_md_path": {"type": "string"},
                    "exclude_header_footer": {"type": "boolean", "default": False}
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
            name="calculate_llm_stats",
            description="Calculates token counts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "file_path": {"type": "string"},
                    "model": {"type": "string", "default": "gpt-4"}
                }
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
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool calls with absolute stdout protection."""
    if not arguments:
        raise ValueError("Missing arguments")

    # Redirect stdout to stderr for the duration of the tool call
    _orig_stdout = sys.stdout
    sys.stdout = sys.stderr
    
    try:
        if name == "extract_pdf_context_to_md":
            res = extract_context_to_md(arguments.get("pdf_path"), arguments.get("keywords"), arguments.get("output_md_path"), arguments.get("context_words", 30), arguments.get("exclude_header_footer", False))
            result_text = f"Success: {res}" if res else "Failed"
        elif name == "convert_pdf_to_md":
            res = convert_pdf_to_md(arguments.get("pdf_path"), arguments.get("output_md_path"), arguments.get("exclude_header_footer", False))
            result_text = f"Success: {res}" if res else "Failed"
        elif name == "convert_plan_to_pdf":
            res = generate_pdf(arguments.get("input_path"), arguments.get("output_pdf_path"))
            result_text = f"Success: {res}" if res else "Failed"
        elif name == "calculate_llm_stats":
            stats = calculate_stats(arguments.get("text"), arguments.get("file_path"), arguments.get("model", "gpt-4"))
            result_text = json.dumps(stats)
        elif name == "generate_uvm_mermaid":
            result_text = generate_mermaid(arguments.get("dut_role"), arguments.get("protocol", "AXI"), arguments.get("has_config", True), arguments.get("has_scoreboard", True))
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
