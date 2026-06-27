"""
vector_index.py
===============
Offline LlamaIndex Vector Index pipeline for PDF specification RAG.

Two public functions (called by server.py MCP tools):
  - extract_hierarchical_pdf_to_json(pdf_path, json_path)
  - build_vector_index_from_json(json_path, persist_dir)
  - query_vector_index(persist_dir, query_str, top_k=5)

Three CLI entry points (run directly, zero MCP/LLM tokens):
  python vector_index.py extract --pdf spec.pdf --output kg.json
  python vector_index.py build --json kg.json --persist db/
  python vector_index.py query --persist db/ --query "TVALID handshake"

Design principle:
  - NO paid LLM is ever used. Settings.llm = None always.
  - Embedding model: BAAI/bge-small-en-v1.5 (33M params, ~130MB, fully offline).
  - Query returns RAW retrieved chunks + rich metadata so the LLM only reads
    what it needs — not the entire PDF. This is the token-efficiency contract.
"""

import sys
import os
import json
import argparse

# ── AGGRESSIVE CACHE REDIRECTION: Must happen BEFORE llama_index/torch imports ──
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))
LOCAL_CACHE = os.path.join(_project_root, ".cache")
os.makedirs(LOCAL_CACHE, exist_ok=True)

# Force everything to use our local project cache
os.environ["LLAMA_INDEX_CACHE_DIR"]   = LOCAL_CACHE
os.environ["TRANSFORMERS_CACHE"]      = LOCAL_CACHE
os.environ["HF_HOME"]                 = LOCAL_CACHE
os.environ["SENTENCE_TRANSFORMERS_HOME"] = LOCAL_CACHE

try:
    import fitz  # PyMuPDF
except ImportError:
    pass # Handled inside functions that need it

# ── Embedding model constant ──────────────────────────────────────────────────
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
DEFAULT_TOP_K    = 5           # sensible default: 5 chunks covers ~5 pages of context


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

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

def _configure_llama_settings():
    """
    Configure LlamaIndex global settings:
    - Use offline HuggingFace embedding model (no API key, no internet after first download)
    - Explicitly disable LLM so LlamaIndex NEVER calls OpenAI / Anthropic / etc.
    """
    try:
        from llama_index.core import Settings
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    except ImportError as e:
        raise ImportError(
            f"Required libraries missing. Run:\n"
            f"  pip install llama-index-core llama-index-embeddings-huggingface\n"
            f"Original error: {e}"
        )

    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME, cache_folder=LOCAL_CACHE)
    Settings.llm = None          # ← CRITICAL: disables all generative LLM calls
    Settings.num_output = 0      # extra guard: no output synthesis
    return Settings


def _load_kg_json(json_path: str) -> dict:
    """Load and validate the Knowledge Graph JSON produced by extract_hierarchical_pdf."""
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"Knowledge Graph JSON not found: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "nodes" not in data:
        raise ValueError(f"Invalid Knowledge Graph JSON (missing 'nodes' key): {json_path}")
    return data


def _kg_to_documents(data: dict):
    """
    Convert Knowledge Graph JSON nodes back to LlamaIndex Document objects.

    Each node carries its section metadata (section_id, section_title, page)
    so the retriever can return structured results without needing a generative LLM.
    """
    from llama_index.core.schema import Document

    docs = []
    for node in data.get("nodes", []):
        text = node.get("text", "").strip()
        if not text:
            continue  # skip empty pages (cover page, blank pages, etc.)

        # Merge node-level fields into metadata for retrieval
        meta = dict(node.get("metadata", {}))
        meta.setdefault("node_id",       node.get("node_id", ""))
        meta.setdefault("page",          node.get("page", None))
        meta.setdefault("section_id",    node.get("section_id", None))
        meta.setdefault("section_level", node.get("section_level", None))
        meta.setdefault("section_title", node.get("section_title", "Unmapped"))

        doc = Document(text=text, metadata=meta)
        docs.append(doc)

    return docs


# ─────────────────────────────────────────────────────────────────────────────
# Public API  (called by server.py MCP tools)
# ─────────────────────────────────────────────────────────────────────────────

def extract_hierarchical_pdf_to_json(pdf_path, output_json_path):
    """
    Stage 1 of the RAG pipeline:
    Builds a RAG Knowledge Graph structured by the PDF Table of Contents.

    Uses `pymupdf4llm` as the ultimate Miner to extract pristine 
    Markdown page chunks (preserving tables and strict layouts), and packages them 
    natively into `llama_index` Document abstractions. 
    It then maps these authentic nodes to PyMuPDF's TOC hierarchy and serializes 
    everything to a structured JSON file (metadata, sections, nodes).
    """
    documents_mock = []
    loader_name = "Unknown"

    # ── 1. Load Document Nodes (pymupdf4llm + LlamaIndex Document nodes) ─────
    try:
        import pymupdf4llm
        from llama_index.core.schema import Document

        print(f"pymupdf4llm {pymupdf4llm.__version__} detected. Extracting pristine markdown chunks.", file=sys.stderr)
        chunks = pymupdf4llm.to_markdown(
            pdf_path,
            page_chunks=True,
            table_strategy="lines_strict",
            show_progress=True
        )
        
        # Package pymupdf4llm chunks natively into LlamaIndex Document abstractions
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            doc_node = Document(
                text=chunk.get("text", ""),
                metadata=meta
            )
            documents_mock.append(doc_node)
            
        loader_name = "pymupdf4llm -> LlamaIndex Document API"

    except ImportError:
        return "Failed: 'pymupdf4llm' is not installed but is strictly required for Knowledge Graph parsing."
    except Exception as e_mu:
        return f"Failed to extract markdown chunks via pymupdf4llm: {e_mu}"

    if not documents_mock:
        return "Failed: No document chunks or text could be extracted."

    # ── 2. Read TOC via PyMuPDF for hierarchy ─────────────────────────────────
    try:
        import fitz
        doc = fitz.open(pdf_path)
    except ImportError:
        return "Failed: 'pymupdf' (fitz) is not installed."
    except Exception as e:
        return f"Failed to open PDF with PyMuPDF for TOC: {e}"

    toc = doc.get_toc()  # [[level, title, page_1indexed], ...]
    total_pages = len(doc)
    doc.close()

    # Build a page-number → section lookup: {1-indexed page: {level, title, section_id}}
    section_map = {}   # page_1idx -> section info
    sections = []

    for i, (lvl, title, start_page) in enumerate(toc):
        end_page = toc[i + 1][2] if i + 1 < len(toc) else total_pages + 1
        section_id = f"sec_{i:04d}"
        section_entry = {
            "section_id": section_id,
            "level": lvl,
            "title": title.strip(),
            "start_page": start_page,
            "end_page": end_page - 1,
            "node_ids": []
        }
        sections.append(section_entry)
        for p in range(start_page, end_page):
            section_map[p] = {"section_id": section_id, "level": lvl, "title": title.strip()}

    # ── 3. Build enriched LlamaIndex nodes ────────────────────────────────────
    nodes = []
    section_nodes_index = {s["section_id"]: s["node_ids"] for s in sections}

    for doc_node in documents_mock:
        meta = doc_node.metadata
        page_num = meta.get("page", None)
        
        # normalise to 1-indexed
        if isinstance(page_num, int) and page_num == 0:
            page_num = 1
            meta["page"] = 1

        node_id = f"node_p{page_num:04d}" if isinstance(page_num, int) else f"node_{len(nodes):04d}"
        
        # Fetch the TOC blueprint for this page
        section_info = section_map.get(page_num, {"section_id": None, "level": None, "title": "Unmapped"})
        
        # INJECT hierarchy natively into the LlamaIndex Document metadata
        meta["section_id"] = section_info["section_id"]
        meta["section_level"] = section_info["level"]
        meta["section_title"] = section_info["title"]
        
        doc_node.id_ = node_id

        node_entry = {
            "node_id": doc_node.id_,
            "page": page_num,
            "section_id": meta["section_id"],
            "section_level": meta["section_level"],
            "section_title": meta["section_title"],
            "text": doc_node.text.strip(),
            "metadata": doc_node.metadata,
            "embedding": None
        }
        nodes.append(node_entry)

        sid = section_info["section_id"]
        if sid and sid in section_nodes_index:
            section_nodes_index[sid].append(node_id)

    # ── 4. Assemble & persist knowledge graph JSON ────────────────────────────
    knowledge_graph = {
        "kg_metadata": {
            "source_pdf": pdf_path,
            "loader": loader_name,
            "total_nodes": len(nodes),
            "total_sections": len(sections),
            "has_toc": bool(toc),
            "note": "Embedding field is None. Populate with an embedding model for vector search."
        },
        "sections": sections,
        "nodes": nodes
    }

    final_output_path = get_versioned_path(output_json_path)
    os.makedirs(os.path.dirname(os.path.abspath(final_output_path)), exist_ok=True)
    with open(final_output_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_graph, f, indent=4, ensure_ascii=False)

    print(
        f"Success! LlamaIndex RAG Knowledge Graph saved: {final_output_path} "
        f"({len(nodes)} nodes, {len(sections)} sections)",
        file=sys.stderr
    )
    return final_output_path

def build_vector_index_from_json(json_path: str, persist_dir: str) -> str:
    """
    Stage 2 of the RAG pipeline:
      • Reads the Knowledge Graph JSON (output of extract_hierarchical_pdf_to_json)
      • Rebuilds LlamaIndex Document objects with full section metadata
      • Embeds every chunk with BAAI/bge-small-en-v1.5 (completely offline)
      • Persists the full VectorStoreIndex to disk → reusable across sessions

    Args:
        json_path   : Absolute path to the KG JSON file.
        persist_dir : Directory to persist the vector index (created if needed).

    Returns:
        Human-readable status string (success or error details).
    """
    # ── 1. Validate inputs ────────────────────────────────────────────────────
    try:
        data = _load_kg_json(json_path)
    except (FileNotFoundError, ValueError) as e:
        return f"Error: {e}"

    # ── 2. Configure LlamaIndex (no LLM, offline embed) ──────────────────────
    try:
        _configure_llama_settings()
    except ImportError as e:
        return str(e)

    # ── 3. Convert nodes → Documents ─────────────────────────────────────────
    try:
        from llama_index.core.schema import Document  # noqa — ensure import works
        docs = _kg_to_documents(data)
    except ImportError as e:
        return f"Failed to import LlamaIndex schema: {e}"

    if not docs:
        return (
            "Error: No non-empty nodes found in the Knowledge Graph JSON. "
            "Re-run Stage 1 (extract_hierarchical_pdf) to regenerate."
        )

    kg_meta   = data.get("kg_metadata", {})
    src_pdf   = kg_meta.get("source_pdf", json_path)
    n_sections = kg_meta.get("total_sections", "?")

    print(
        f"[vector_index] Building index: {len(docs)} chunks, "
        f"{n_sections} sections — source: {os.path.basename(src_pdf)}",
        file=sys.stderr,
    )

    # ── 4. Build & persist the VectorStoreIndex ───────────────────────────────
    try:
        from llama_index.core import VectorStoreIndex

        os.makedirs(persist_dir, exist_ok=True)

        # show_progress=True prints per-node progress to stderr (safe for MCP)
        index = VectorStoreIndex.from_documents(docs, show_progress=True)
        index.storage_context.persist(persist_dir=persist_dir)

    except Exception as e:
        return f"Failed to build or persist vector index: {e}"

    # Write a small manifest alongside the index so other tools can discover it
    manifest = {
        "source_json":  json_path,
        "source_pdf":   src_pdf,
        "embed_model":  EMBED_MODEL_NAME,
        "total_chunks": len(docs),
        "total_sections": n_sections,
        "persist_dir":  persist_dir,
    }
    try:
        with open(os.path.join(persist_dir, "_index_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    except Exception:
        pass  # manifest is informational only

    return (
        f"SUCCESS: Vector index built from {len(docs)} chunks and persisted to '{persist_dir}'.\n"
        f"Source JSON : {json_path}\n"
        f"Source PDF  : {src_pdf}\n"
        f"Embed model : {EMBED_MODEL_NAME}\n"
        f"Sections    : {n_sections}\n"
        f"Index size  : {len(docs)} docs\n"
        f"Ready for query_vector_index()"
    )


def query_vector_index(persist_dir: str, query_str: str, top_k: int = DEFAULT_TOP_K) -> str:
    """
    Stage 3 of the RAG pipeline — PURE RETRIEVAL, ZERO LLM TOKENS.
    Args:
        persist_dir : Path to the directory created by build_vector_index_from_json.
        query_str   : Technical query string.
        top_k       : Number of most-relevant chunks to return.
    Returns:
        Formatted string of retrieved chunks with section/page metadata and scores.
    """
    if not os.path.isdir(persist_dir):
        return (
            f"Error: Vector index directory not found: '{persist_dir}'.\n"
            f"Run build_vector_index first to create the index."
        )

    try:
        from llama_index.core import StorageContext, load_index_from_storage
        _configure_llama_settings()
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(storage_context)

        # Use a raw retriever — NOT a query engine — so NO LLM is invoked.
        # The retriever computes cosine similarity in embedding space and returns
        # the top-K raw document chunks directly.
        retriever = index.as_retriever(similarity_top_k=top_k)
        retrieved_nodes = retriever.retrieve(query_str)

    except Exception as e:
        return f"Failed to load or query vector index from '{persist_dir}': {e}"

    # ── 4. Format results ─────────────────────────────────────────────────────
    if not retrieved_nodes:
        return (
            f"No relevant context found for query: '{query_str}'\n"
            f"Try rephrasing with more specific technical terms."
        )

    lines = [
        f"=== RAG RETRIEVAL: '{query_str}' ===",
        f"Index     : {persist_dir}",
        f"Chunks    : {len(retrieved_nodes)} returned (top_k={top_k})",
        f"Embed model: {EMBED_MODEL_NAME}",
        f"LLM used  : NONE (pure vector retrieval — zero generative tokens)",
        "=" * 60,
        "",
    ]

    compliance_keywords = ["shall", "must", "required", "permitted", "illegal", "reserved", "forbidden"]

    for i, node in enumerate(retrieved_nodes, start=1):
        meta    = node.metadata or {}
        text    = node.text
        
        # ── Automated Compliance Detection ─────────────────────────────────────
        found_rules = [kw for kw in compliance_keywords if kw in text.lower()]
        rule_alert = f" [COMPLIANCE ALERT: {', '.join(found_rules).upper()}]" if found_rules else ""

        section = meta.get("section_title", "Unmapped Section")
        page    = meta.get("page", "?")
        sec_lvl = meta.get("section_level", "")
        score   = getattr(node, "score", 0.0) or 0.0
        node_id = meta.get("node_id", f"chunk_{i}")

        lines.append(
            f"--- CHUNK {i}/{len(retrieved_nodes)} "
            f"[Score: {score:.4f}] "
            f"[Page: {page}] "
            f"[{node_id}] ---"
        )
        lines.append(f"Section (L{sec_lvl}): {section}")
        lines.append(f"spec_ref: Section '{section}', Page {page}{rule_alert}")
        lines.append("")
        lines.append(text)
        lines.append("-" * 60)
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point  (run directly without MCP, zero token cost)
# ─────────────────────────────────────────────────────────────────────────────

def _cli_extract(args):
    print(f"[EXTRACT] Starting hierarchical PDF extraction: {args.pdf}", file=sys.stderr)
    result = extract_hierarchical_pdf_to_json(args.pdf, args.output)
    print(result)

def _cli_build(args):
    print("[BUILD] Starting vector index build...", file=sys.stderr)
    result = build_vector_index_from_json(args.json, args.persist)
    print(result)

def _cli_query(args):
    result = query_vector_index(args.persist, args.query, top_k=args.top_k)
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="vector_index.py",
        description=(
            "Offline LlamaIndex RAG pipeline for PDF specifications.\n"
            "No paid LLM is used at any step — pure embedding-based retrieval.\n\n"
            "Workflow:\n"
            "  1. python vector_index.py extract ...       → generates KG JSON\n"
            "  2. python vector_index.py build ...         → embeds & persists index\n"
            "  3. python vector_index.py query ...         → retrieves top-K chunks\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ── extract sub-command ───────────────────────────────────────────────────
    p_ext = sub.add_parser(
        "extract",
        help="Extract a hierarchical Knowledge Graph JSON from a PDF specification.",
    )
    p_ext.add_argument(
        "--pdf", required=True,
        metavar="PATH",
        help="Path to the source PDF specification.",
    )
    p_ext.add_argument(
        "--output", required=True,
        metavar="PATH",
        help="Path where the Knowledge Graph JSON should be saved.",
    )
    p_ext.set_defaults(func=_cli_extract)

    # ── build sub-command ─────────────────────────────────────────────────────
    p_build = sub.add_parser(
        "build",
        help="Build and persist the vector index from a Knowledge Graph JSON.",
    )
    p_build.add_argument(
        "--json", required=True,
        metavar="PATH",
        help="Path to the Knowledge Graph JSON file (output of extract_hierarchical_pdf).",
    )
    p_build.add_argument(
        "--persist", required=True,
        metavar="DIR",
        help="Directory to save the persisted vector index (created if needed).",
    )
    p_build.set_defaults(func=_cli_build)

    # ── query sub-command ─────────────────────────────────────────────────────
    p_query = sub.add_parser(
        "query",
        help="Query the persisted vector index and return top-K relevant chunks.",
    )
    p_query.add_argument(
        "--persist", required=True,
        metavar="DIR",
        help="Path to the persisted vector index directory.",
    )
    p_query.add_argument(
        "--query", required=True,
        metavar="TEXT",
        help='Technical query string (e.g., "TVALID TREADY handshake rules").',
    )
    p_query.add_argument(
        "--top-k", type=int, default=DEFAULT_TOP_K,
        metavar="N",
        help=f"Number of top chunks to return (default: {DEFAULT_TOP_K}).",
    )
    p_query.set_defaults(func=_cli_query)

    args = parser.parse_args()
    args.func(args)
