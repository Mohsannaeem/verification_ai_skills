# verification_ai_skills

> **From PDF Spec to Passing Simulation — Fully AI-Driven.**

An agent skill system that reads a protocol specification PDF and autonomously produces a complete, simulation-ready UVM verification environment — verification plan, SystemVerilog testbench, EDA manifests, and a passing regression.

Validated on AMBA AXI5-Stream: **48/48 tests passing**, zero human-written SystemVerilog.

---

## What It Does

```
Your Protocol Spec PDF
        │
        ▼  pdf_to_markdown  →  vector_index
   Semantic knowledge base (offline, no API key)
        │
        ▼  uvc_planning
   Verification Plan YAML  +  PDF Report
   (12 requirements · 48 test cases · coverage groups)
        │
        ▼  uvc_generator
   Complete UVM Testbench (17 SystemVerilog files)
        │
        ▼  eda_yaml_generator
   build.yaml + run.yaml (QuestaSim / VCS / Xcelium)
        │
        ▼  uvc_orchestrator
   Regression: 48/48 PASS
```

---

## Prerequisites

Install these before anything else.

### 1. Claude Code

Claude Code is the AI agent runtime that executes all skills.

```bash
npm install -g @anthropic/claude-code
```

Or download the desktop app from [claude.ai/code](https://claude.ai/code).  
Sign in with your Anthropic account. A Claude Pro or API subscription is required.

### 2. Python 3.10+

```bash
python --version   # must be 3.10 or higher
```

Download from [python.org](https://www.python.org/downloads/) if needed.

### 3. Python dependencies

```bash
pip install pymupdf4llm llama-index-embeddings-huggingface reportlab pyyaml
```

| Package | Used for |
|---------|----------|
| `pymupdf4llm` | PDF extraction to Markdown |
| `llama-index-embeddings-huggingface` | Offline vector embeddings (BAAI/bge-small-en-v1.5) |
| `reportlab` | PDF report generation |
| `pyyaml` | YAML plan parsing |

> The embedding model (`BAAI/bge-small-en-v1.5`, ~130 MB) downloads automatically on first use and caches locally. No API key required — fully offline.

### 4. SystemVerilog Simulator (for running the testbench)

Any of:
- **QuestaSim** 2021.1+ (tested)
- **VCS**
- **Xcelium**

> The planning and code generation steps work without a simulator. You only need one to compile and run the generated testbench.

---

## Installation

### Step 1 — Clone the repository

```bash
git clone --recurse-submodules https://github.com/Mohsannaeem/verification_ai_skills.git
cd verification_ai_skills
```

> `--recurse-submodules` clones `eda_buddy` and `dummy_uvm` alongside the main repo. If you forgot it, run `git submodule update --init` afterwards.

### Step 2 — Configure the MCP server

The MCP server runs as a local Python process. Claude Code connects to it to get PDF extraction and vector search tools.

**Find your Claude Code config file:**

| Platform | Location |
|----------|----------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

**Add this block** (replace the path with your actual clone location):

```json
{
  "mcpServers": {
    "verification-ai": {
      "command": "python",
      "args": [
        "/absolute/path/to/verification_ai_skills/verification_mcp_server/server.py"
      ]
    }
  }
}
```

**Windows example:**
```json
{
  "mcpServers": {
    "verification-ai": {
      "command": "python",
      "args": [
        "D:/projects/verification_ai_skills/verification_mcp_server/server.py"
      ]
    }
  }
}
```

**macOS / Linux example:**
```json
{
  "mcpServers": {
    "verification-ai": {
      "command": "python",
      "args": [
        "/home/user/projects/verification_ai_skills/verification_mcp_server/server.py"
      ]
    }
  }
}
```

> Restart Claude Code after editing the config file.

### Step 3 — Verify the MCP server is connected

Open Claude Code and type:

```
/mcp
```

You should see `verification-ai` listed as a connected server with tools like `extract_hierarchical_pdf`, `build_vector_index`, `query_vector_index`, etc.

---

## Quick Start

### Running your first verification session

1. Place your protocol specification PDF anywhere accessible.
2. Open Claude Code in the `verification_ai_skills` directory.
3. Type:

```
Run the verification orchestrator for AXI-Stream where VIP role is Master 
and DUT would be Slave.
```

Replace `AXI-Stream` with your protocol and `Master`/`Slave` with your VIP role. The orchestrator will ask one clarifying question (verification role) and then drive the full pipeline automatically.

### What you will see

The orchestrator displays a live **Verification Roadmap** at each stage:

```
Phase       Milestone              Status   Path
──────────  ─────────────────────  ───────  ─────────────────────────────
0. Spec     PDF Extraction         ✅       markdown/axi_stream_spec.md
1. Search   Vector Index           ✅       vector_db/axi_stream/
2. Plan     Verification Plan      ✅       verf_plan_reports/verif_plan_*.yaml
3. Code     UVM Environment        ✅       Output/axi_stream_master_vip_tb/
4. Sync     EDA Buddy YAMLs        ✅       Output/axi_stream_master_vip_tb/yamls/
5. Test     Regression             ✅       run/axi_stream_master_vip/
```

---

## Skills Reference

| Skill | What it does | When it runs |
|-------|-------------|--------------|
| `uvc_orchestrator` | Audits project state, dispatches other skills, runs regression | Always — the entry point |
| `pdf_to_markdown` | Converts protocol PDF to structured Markdown | First run, new spec |
| `vector_index` | Builds offline semantic search index (RAG) over the spec | First run, spec updated |
| `uvc_planning` | Generates verification plan YAML + PDF report | After vector index |
| `uvc_generator` | Synthesizes UVM SystemVerilog testbench | After planning |
| `eda_yaml_generator` | Generates EDA build/run YAML manifests | After code generation |

---

## Supported Protocols

| Protocol | Versions | Notes |
|----------|----------|-------|
| AXI-Stream | AXI4-Stream, AXI5-Stream | Master VIP: **48/48 PASS** (validated) |
| AXI Memory Mapped | AXI3, AXI4, AXI5 | Cheat sheet included |
| APB | APB3, APB4, APB5 | Cheat sheet included |
| AHB | AHB3, AHB4, AHB5 | Cheat sheet included |

---

## Generated Output Locations

After a full run everything lands in well-defined paths:

```
verification_ai_skills/
├── markdown/                   ← extracted spec Markdown
├── json/                       ← knowledge graph JSON
├── vector_db/                  ← persisted vector index (reused on next run)
├── verf_plan_reports/          ← verification plan YAML + PDF report
└── Output/
    └── <protocol>_<role>_vip_tb/
        ├── top/                ← defines, interface, package, tb_top, tests
        ├── master_agent/       ← driver, monitor, sequencer, agent, config
        ├── env/                ← scoreboard, env, env_config
        ├── sequences/          ← seq_item, base_sequence, test_sequences
        └── yamls/              ← build.yaml, run.yaml for the simulator
```

---

## Running the Simulation Manually

If you want to compile and run without the orchestrator:

### QuestaSim

```bash
cd Output/axi_stream_master_vip_tb/

# Build (compile + elaborate)
make -f ../../sim/Makefile questa_build_axi_stream_master_vip

# Run a single test
make -f ../../sim/Makefile \
  questa_run_axi_stream_master_vip_axi_stream_master_vip_tc_mst_001_test

# Run with waveforms
make -f ../../sim/Makefile \
  questa_run_axi_stream_master_vip_axi_stream_master_vip_tc_mst_001_test WAVES=1
```

Or use the standalone Makefile inside `Output/`:

```bash
cd Output/sim/
make questa_build_axi_stream_master_vip
make questa_run_axi_stream_master_vip_axi_stream_master_vip_tc_mst_001_test
```

### QuestaSim — Important notes

- **Do not** compile `uvm_pkg.sv` — QuestaSim 2021.1+ ships UVM 1.1d built-in.
- `+UVM_TIMEOUT` is set to `100000000` (100 µs in picoseconds for `1ns/1ps` timescale).

---

## Repository Structure

```
verification_ai_skills/
│
├── .agent/
│   ├── skills/
│   │   ├── uvc_orchestrator/       ← master orchestrator (start here)
│   │   ├── pdf_to_markdown/        ← PDF extraction
│   │   ├── vector_index/           ← offline RAG pipeline
│   │   ├── uvc_planning/           ← verification plan synthesis
│   │   │   └── sub_prompts/        ← protocol cheat sheets (AXI-S, AXI-MM, APB, AHB)
│   │   ├── uvc_generator/          ← UVM SV synthesis
│   │   └── eda_yaml_generator/     ← EDA Buddy YAML manifests
│   └── workflows/
│       └── uvc_verif_planning.md   ← end-to-end workflow definition
│
├── verification_mcp_server/        ← Python MCP server (PDF, RAG, diagram tools)
│   ├── server.py
│   └── scripts/
│
├── examples/
│   ├── spec/simple_axi_stream_spec.md          ← demo protocol spec
│   ├── plan/verif_plan_axi_stream_master_example.yaml  ← demo output plan
│   └── README.md                               ← step-by-step example walkthrough
│
├── Output/                         ← generated UVM testbenches land here
├── eda_buddy/                      ← EDA simulation toolchain (submodule)
└── dummy_uvm/                      ← UVM component templates (submodule)
```

---

## Troubleshooting

**MCP server not showing in `/mcp`**
- Confirm the path in `claude_desktop_config.json` is absolute, not relative.
- Confirm Python 3.10+ is on your `PATH`: `python --version`.
- Restart Claude Code completely after editing the config.

**`pymupdf4llm not found` during PDF extraction**
```bash
pip install pymupdf4llm
```

**`llama-index-embeddings-huggingface not found`**
```bash
pip install llama-index-embeddings-huggingface
```

**Embedding model download is slow**
The `BAAI/bge-small-en-v1.5` model (~130 MB) downloads from HuggingFace on first use and caches at `~/.cache/huggingface/`. Subsequent runs are instant.

**QuestaSim compile error: DPI GCC runtime**
You are likely passing `uvm_pkg.sv` to `vlog`. Remove it — use QuestaSim's built-in UVM instead.

**Tests timing out at ~5 µs**
`+UVM_TIMEOUT` is set in picoseconds for a `1ns/1ps` timescale. `5000000` = 5 µs. Use `100000000` for 100 µs.

---

## Example: AXI5-Stream Master VIP (Full Run)

See [examples/README.md](examples/README.md) for the complete annotated walkthrough:
- [examples/spec/simple_axi_stream_spec.md](examples/spec/simple_axi_stream_spec.md) — the demo spec input
- [examples/plan/verif_plan_axi_stream_master_example.yaml](examples/plan/verif_plan_axi_stream_master_example.yaml) — the generated plan output

**Result:** 48 directed test cases, 17-file UVM testbench, **48/48 PASS** on QuestaSim 2021.1.

---

*Built with Claude Code · Python · LlamaIndex · BAAI/bge-small-en-v1.5 · QuestaSim 2021.1*
