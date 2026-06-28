---
name: vector_index
description: Complete LlamaIndex-powered vector index pipeline for offline semantic search over PDF specifications. Provides a 3-stage protocol (Extract → Build → Query) that any other skill can call to retrieve spec context without token-costly raw PDF reads.
---

# LlamaIndex Vector Index Skill

This skill defines the **canonical pipeline** for building and querying a semantic vector database from any PDF specification. It is designed to be consumed by other skills (e.g., `uvc_planning`) as a zero-token, offline RAG backend.

> [!IMPORTANT]
> All three stages MUST be executed in order for a new PDF. If a `vector_db/` directory for the target PDF already exists, skip straight to **Stage 3 (Query)**.

---

## Overview: The 3-Stage Pipeline

```
[PDF File]
     │
     ▼ Stage 1 (extract_hierarchical_pdf)
[JSON Knowledge Graph]   ← TOC-mapped, page-level nodes in json/
     │
     ▼ Stage 2 (build_vector_index)
[Persisted Vector DB]    ← HuggingFace BAAI/bge-small-en-v1.5 embeddings in vector_db/
     │
     ▼ Stage 3 (query_vector_index)
[Retrieved Chunks]       ← Top-K semantic matches returned to the calling skill/agent
```

---

## Stage 1 — Extract Knowledge Graph (JSON)

**When to run:** Only once per PDF, or when the spec has been updated.

**Tool:** `extract_hierarchical_pdf`

**What it does:**
- Uses `pymupdf4llm` to extract pristine markdown chunks (per page, with table support)
- Packages chunks natively as **LlamaIndex `Document` objects**
- Maps each page-node to its TOC section hierarchy using PyMuPDF `get_toc()`
- Serializes to a structured JSON with three top-level keys:
  - `kg_metadata` — source path, loader, node/section counts
  - `sections` — TOC hierarchy with `section_id`, `level`, `title`, page range, `node_ids`
  - `nodes` — per-page entries: `node_id`, `page`, `section_id`, `section_title`, `text`, `metadata`, `embedding: None`

**Path Convention:**
```
d:\Verification\VERIFICATION_PLANNER\json\<spec_name>_kg.json
```

**Example invocation:**
```
extract_hierarchical_pdf(
    pdf_path   = "d:\\Verification\\VERIFICATION_PLANNER\\pdfs\\amba_axi_stream_spec.pdf",
    output_json_path = "d:\\Verification\\VERIFICATION_PLANNER\\json\\axi_stream_kg.json"
)
```

> **Do NOT** read or view the JSON output unless explicitly asked. It can be hundreds of KB.

---

## Stage 2 — Build Vector Index (Offline Embedding)

**When to run:** After Stage 1 completes, or when the knowledge graph JSON is updated.

**Tool:** `build_vector_index`

**What it does:**
- Reads the Knowledge Graph JSON from Stage 1
- Reconstructs LlamaIndex `Document` objects from the `nodes` array
- Embeds all chunks using **`BAAI/bge-small-en-v1.5`** (free, offline, HuggingFace model — no API key required)
- Persists the full vector database (index store, docstore, vector store) to disk

**Path Convention:**
```
d:\Verification\VERIFICATION_PLANNER\vector_db\<spec_name>\
```

**Example invocation:**
```
build_vector_index(
    json_path   = "d:\\Verification\\VERIFICATION_PLANNER\\json\\axi_stream_kg.json",
    persist_dir = "d:\\Verification\\VERIFICATION_PLANNER\\vector_db\\axi_stream"
)
```

> This step may take 30–120 seconds on first run as the HuggingFace model is downloaded and all chunks are embedded. Subsequent runs are instant (index loaded from disk).

---

## Stage 3 — Query Vector Index (Semantic RAG)

**When to run:** Any time a skill needs spec context. This replaces grep-based extraction and raw markdown reads.

**Tool:** `query_vector_index`

**What it does:**
- Loads the persisted vector database from disk (uses same `BAAI/bge-small-en-v1.5` model, no LLM needed)
- Performs a semantic similarity search (top-K=3 chunks by default)
- Returns structured results: chunk text, section title, page number, and similarity score

**Path Convention:**
```
persist_dir = "d:\Verification\VERIFICATION_PLANNER\vector_db\<spec_name>"
```

**Example invocation:**
```
query_vector_index(
    persist_dir = "d:\\Verification\\VERIFICATION_PLANNER\\vector_db\\axi_stream",
    query_str   = "TVALID and TREADY handshake rules when TKEEP is asserted"
)
```

**Returned format:**
```
--- RAG RETRIEVAL RESULTS FOR: '<query_str>' ---

## CHUNK 1 [Score: 0.872] - Section 2.3 Handshake Protocol (Page 14)
<Extracted markdown text from page 14, verbatim from the spec>

## CHUNK 2 [Score: 0.841] - Section 2.3 Handshake Protocol (Page 15)
<Extracted markdown text from page 15>

## CHUNK 3 [Score: 0.789] - Section 3.1 Data Transfer (Page 22)
<Extracted markdown text from page 22>
```

---

## Integration Contract for Other Skills

Any skill that needs to read a PDF specification **MUST** follow this contract:

### Pre-flight Check
Before querying, check if a `vector_db/<spec_name>/` directory already exists:
```
find_by_name(
    SearchDirectory = "d:\\Verification\\VERIFICATION_PLANNER\\vector_db",
    Pattern = "<spec_name>"
)
```

- **If found** → Skip to Stage 3 (Query directly)
- **If NOT found** → Run Stage 1 → Stage 2 → Stage 3

### Recommended Query Strategy: The Recursive Discovery Protocol
To ensure "Enterprise Grade" density (30+ test cases), you MUST perform a **3-Pass Sweep**:

| Pass | Target | Example Query String | Goal |
|---|---|---|---|
| **Pass 1** | **Scope Discovery** | `"Table of Contents chapters sections signals list Table 2-1 list of signals"` | Identify the "Technical Map" of the document. |
| **Pass 2** | **Signal Deep-Dive** | `"Handshake rules TVALID TREADY TDATA TLAST TID TDEST TUSER byte qualifiers"` | Extract specific constraints for every signal found in Pass 1. |
| **Pass 3** | **Compliance Sweep** | `"shall must required permitted illegal forbidden reserved violation stability reset timing"` | Capture the "Hard Rules" and "Conformance Boundaries". |

> [!CAUTION]
> **Density Contract**: If your combined retrieval results from these 3 passes do not identify at least 15 technical requirements, your search was too narrow. Perform a fallback search using the "Deep Spec Grep" method in the calling skill.

### Data Contract
Each query returns a string. The calling skill should:
1. Parse the `## CHUNK N` blocks
2. Use `Section` and `Page` metadata for `spec_ref` anchoring in YAML plans
3. **Requirement Extraction**: Actively look for modal verbs (`shall`, `must`) in the text and convert them into individual `test_requirements` entries.

---

## Directory Structure Reference

```
d:\Verification\VERIFICATION_PLANNER\
├── pdfs\                    ← Source PDF specifications
├── json\                    ← Stage 1 output: Knowledge Graph JSONs
│   └── <spec_name>_kg.json
├── vector_db\               ← Stage 2 output: Persisted LlamaIndex Vector DBs
│   └── <spec_name>\
│       ├── docstore.json
│       ├── index_store.json
│       └── vector_store.json
└── .agent\skills\vector_index\SKILL.md   ← This file
```

---

## Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `pymupdf4llm not installed` | Missing package | `pip install pymupdf4llm` |
| `llama-index-embeddings-huggingface not installed` | Missing package | `pip install llama-index-embeddings-huggingface` |
| `No nodes found in JSON` | Stage 1 failed silently | Re-run `extract_hierarchical_pdf` |
| `Failed to query index: No such file` | Stage 2 not run yet | Run `build_vector_index` first |
| Low retrieval scores (< 0.5) | Query too vague | Use more specific technical terminology |

---

## Technical Notes

- **Embedding model:** `BAAI/bge-small-en-v1.5` — 33M parameter English model, ~130MB download, cached after first use
- **No API keys required** — fully offline, no OpenAI/Anthropic dependencies
- **LLM is explicitly disabled** (`Settings.llm = None`) — this is a pure retrieval pipeline
- **Granularity:** One LlamaIndex node per PDF page, with full section metadata injected
- **Versioning:** The JSON output is auto-versioned (`_v1.json`, `_v2.json`) if the target path exists
