# verification_ai_skills

> **From PDF to Passing Simulation — Entirely AI-Driven.**

This repository is the realization of a simple but ambitious idea: what if an AI agent could read a protocol specification and autonomously produce a complete, simulation-ready UVM verification environment — including the verification plan, the SystemVerilog testbench, the EDA manifests, and a passing regression? Not as a code skeleton, but as real, synthesized engineering work.

This project answers that question with a production-grade agent skill system built on top of Claude Code's `.agent/` framework. It has been validated end-to-end on the AMBA AXI5-Stream protocol, where the agent autonomously generated 48 directed test cases, synthesized a 17-file UVM testbench, and drove a regression to **48/48 PASS** — with zero human-written SystemVerilog.

---

## The Problem This Solves

Writing a UVM Verification IP (VIP) is expensive. A senior verification engineer typically spends weeks going through the following lifecycle for every new interface:

1. Read the protocol specification PDF (often 100–400 pages).
2. Manually extract signal tables, handshake rules, and conformance constraints.
3. Author a verification plan document, mapping requirements to test cases and coverage goals.
4. Write the UVM environment — driver, monitor, scoreboard, sequences, agent, env, tests.
5. Author EDA build/run manifests for the simulator.
6. Debug compilation and simulation failures, often caused by subtle timing issues.
7. Iterate until regression passes.

This is repetitive, expensive, and error-prone. The skill system in this repository automates every single one of these steps.

---

## Architecture: A Pipeline of Specialist Skills

The system is organized as a directed pipeline of seven skills, each responsible for one stage of the verification lifecycle. They are coordinated by a central orchestrator skill that acts as the "brain" — auditing the current project state and dispatching the right sub-skill for the next step.

```
PDF Specification
       │
       ▼
 ┌─────────────────────┐
 │   pdf_to_markdown   │  ← Stage 0: Token-free PDF extraction to Markdown
 └─────────────────────┘
       │
       ▼
 ┌─────────────────────┐
 │    vector_index     │  ← Stage 1: Build offline semantic search index (RAG)
 └─────────────────────┘
       │
       ▼
 ┌─────────────────────┐
 │    uvc_planning     │  ← Stage 2: Generate Verification Plan YAML + PDF report
 └─────────────────────┘
       │
       ▼
 ┌─────────────────────┐
 │    uvc_generator    │  ← Stage 3: Synthesize UVM SystemVerilog testbench
 └─────────────────────┘
       │
       ▼
 ┌─────────────────────┐
 │  eda_yaml_generator │  ← Stage 4: Generate EDA Buddy build/run manifests
 └─────────────────────┘
       │
       ▼
 ┌─────────────────────┐
 │   uvc_orchestrator  │  ← Runs regression, debugs failures, closes gaps
 └─────────────────────┘
```

All stages are coordinated by **`uvc_orchestrator`** — the meta-skill that audits the project state and decides what to do next.

---

## Skill Breakdown

### `uvc_orchestrator` — The Brain

*Located at `.agent/skills/uvc_orchestrator/`*

This is the entry point for every verification session. Before touching any file, it performs a **System State Audit**: it scans for existing vector databases, YAML plans, synthesized source files, and simulation logs, then builds a "State of the Union" dashboard. Based on what it finds, it dispatches the appropriate sub-skill.

The orchestrator follows a strict **"Check → Prompt → Delegate"** loop. It never runs blindly. At each transition, it surfaces a **Verification Roadmap** showing exactly where the project stands across all six lifecycle phases (Spec → Search → Plan → Code → Sync → Test), and what the next best move is.

It also owns the regression execution layer. Since `make` is not always available across environments, it ships with `eda_buddy_executor.py` — a Python script that parses EDA Buddy Makefiles and directly invokes `vsim` for build and run targets without requiring a shell `make` installation.

**The Decision Matrix:**

| Current State | Action |
|---|---|
| No vector DB or spec not indexed | Run `vector_index` pipeline first |
| Vector DB found, no YAML plan | Invoke `uvc_planning` |
| YAML plan stale vs. spec version | Re-run `uvc_planning` (Iterative Discovery pass) |
| Plan complete, `Output/` empty | Invoke `uvc_generator` |
| SV code exists but missing TCs | Re-run `uvc_generator` (Pass 2 Incremental) |
| Code synthesized, YAMLs out of sync | Run `eda_yaml_generator` |
| Compilation or simulation failures | Enter EDA debug loop |

---

### `pdf_to_markdown` — Token-Free PDF Extraction

*Located at `.agent/skills/pdf_to_markdown/`*

Reading a 300-page PDF directly into the LLM context is prohibitively expensive and slow. This skill solves the problem by pushing all extraction work to the **MCP server** — a Python process running `pymupdf4llm` that reads the PDF and writes results directly to a Markdown file, *without sending the raw content back to the model*.

Two modes are supported:

- **Keyword Extraction**: The agent specifies a list of terms (e.g., `TVALID, TREADY, TLAST`). The MCP tool searches the PDF and writes contextual excerpts to `markdown/<output>.md`.
- **Full Conversion**: The entire PDF is converted to a clean Markdown file using `pymupdf4llm.to_markdown()` with configurable options for headers, images, table detection strategy, and page separators.

The tool is intentionally *write-only* from the model's perspective. Files are versioned automatically (`_v1.md`, `_v2.md`) to prevent overwrites.

---

### `vector_index` — Offline Semantic Search (RAG Backend)

*Located at `.agent/skills/vector_index/`*

Once the PDF is extracted, this skill builds a persistent semantic vector database over the specification content — enabling any downstream skill to retrieve *exactly the right spec sections* for a given query, without loading the entire document.

The pipeline has three stages:

**Stage 1 — Knowledge Graph Extraction**
`extract_hierarchical_pdf` runs `pymupdf4llm` over the source PDF and packages each page as a **LlamaIndex Document node**, enriched with TOC section metadata (section title, level, page range). The output is a structured JSON knowledge graph at `json/<spec_name>_kg.json`.

**Stage 2 — Vector Index Build**
`build_vector_index` reads the JSON, reconstructs the LlamaIndex Document objects, and embeds all nodes using **`BAAI/bge-small-en-v1.5`** — a 33M-parameter English model that runs fully offline with no API key. The persisted index lands at `vector_db/<spec_name>/`.

**Stage 3 — Semantic Query**
`query_vector_index` loads the persisted index and runs a similarity search (top-K=3 by default), returning structured results with chunk text, section title, page number, and similarity score.

**The Recursive Discovery Protocol**

The planning skill is instructed to run a mandatory 3-pass sweep over the vector index:

| Pass | Intent | Example Query |
|---|---|---|
| Pass 1: Scope | Find all signals and chapter titles | `"Table of Contents, signal list, Table 2-1"` |
| Pass 2: Deep Dive | Extract timing and handshake rules per signal | `"TVALID TREADY handshake TKEEP TLAST byte qualifier"` |
| Pass 3: Compliance | Find all "shall/must/illegal" statements | `"shall must required illegal forbidden reserved"` |

This 3-pass sweep is what drives the **"high-density" planning** guarantee: ≥10 requirements and ≥30 test cases.

---

### `uvc_planning` — Verification Plan Generation

*Located at `.agent/skills/uvc_planning/`*

This is the intellectual core of the pipeline. After the vector index is built, `uvc_planning` synthesizes a complete, enterprise-grade **verification plan** from the retrieved spec chunks.

**What makes this non-trivial:**

The skill is not simply asking the model to "summarize requirements." It enforces a rigorous **density contract** and a **full traceability model**:

- Every requirement must be anchored to a specific `spec_ref` (section/page) from the RAG retrieval.
- Every requirement maps to ≥1 test case **and** ≥1 functional coverage group. No orphaned requirements.
- Every test case maps back to ≥1 requirement. No floating test cases.
- The signal direction table is **role-aware**: if the Verification Role is Master, then signals the VIP drives are Output; signals it observes are Input. The DUT always plays the opposite role.
- A **Mermaid architecture diagram** is auto-generated using the `generate_uvm_mermaid` MCP tool, showing the full UVM containment hierarchy (Test → Env → Agent → Driver/Monitor/Scoreboard).

The output is a structured YAML file (`verif_plan_<protocol>_v<X_Y>.yaml`) and a professional PDF report rendered via `convert_plan_to_pdf`. See [`examples/plan/`](examples/plan/) for an annotated sample plan you can read right now.

**Protocol-Specific Cheat Sheets**

The skill auto-detects the target protocol and loads the matching cheat sheet from `sub_prompts/`:

| Protocol | Cheat Sheet |
|---|---|
| AXI-Stream | `axi_stream_cheat_sheet.md` |
| AXI Memory Mapped (AXI3/4/5) | `axi_mm_cheat_sheet.md` |
| APB (APB3/4/5) | `apb_cheat_sheet.md` |
| AHB (AHB3/4/5) | `ahb_cheat_sheet.md` |

The UVM pseudo-code generation rules (`sub_prompts/uvm_pseudo_code_generation.md`) are also always loaded to enforce consistent driver/monitor/scoreboard patterns.

**Built-in Grading Engine**

The `grading/` directory contains `grading_engine.py` and `skill_test_suite.py` — a self-evaluation framework that scores a generated YAML plan against a golden reference (`golden_data/golden_axi_stream_plan.yaml`) across multiple dimensions: requirement density, traceability completeness, signal population fidelity, and coverage group coverage ratio.

---

### `uvc_generator` — UVM Testbench Synthesis

*Located at `.agent/skills/uvc_generator/`*

This skill performs the most technically demanding step in the pipeline: translating a structured YAML verification plan into real, simulation-ready **SystemVerilog UVM code**.

It is not a template expander. It is a **synthesis engine** that uses the agent's deep UVM/SystemVerilog domain knowledge to:

1. Read the YAML `directory_structure` to know what files to create.
2. Use the `code_snippets` blueprints in the YAML as architectural guidance.
3. Read the `test_requirements` to understand what each component must implement.
4. Synthesize each component from scratch, correctly implementing all handshake logic, parity computations, clocking block skew management, coverage groups, and violation injection knobs.

**Key synthesis rules enforced:**

- **Clocking Block Discipline**: No explicit `#1step` input/output skews — relies on simulator default edge-based sampling to avoid race conditions with the DUT.
- **Macro-Based Architecture**: All width parameters and feature flags live in `_defines.sv` as `\`define` macros for global visibility without complex package scoping.
- **Violation Knobs**: Every negative test case is implemented via `rand bit` fields on the sequence item (e.g., `drop_valid_early`, `inject_invalid_tstrb_tkeep`, `parity_inject_error`). The driver checks these flags and applies the violation conditionally.
- **High-Density Logging**: Packet boundary markers (`[PKT#N START]`, `[PKT#N END]`), per-beat dumps, and watchdog counters are included in all drivers.
- **Post-Synthesis Gap Audit**: After every synthesis pass, the skill runs a mandatory 5-pass audit checking TC coverage, fidelity of constraints, seq_item completeness, driver branch coverage, and coverage group orphans.

The skill generates **one `uvm_sequence` and one `uvm_test` per test case ID in the YAML**, maintaining strict 1:1 mapping between the plan and the implementation.

---

### `eda_yaml_generator` — EDA Buddy Manifest Generation

*Located at `.agent/skills/eda_yaml_generator/`*

After the SV code is synthesized, build and run manifests need to be created for the EDA simulation toolchain. This skill automates that step using `gen_eda_yamls.py`.

The script:
1. Walks the TB output directory and classifies `.sv/.svh` files by content (packages, interfaces, modules).
2. Discovers all `uvm_test` subclasses and test macros to populate `run.yaml` entry points.
3. Deep-merges results into any existing YAMLs — user-customized flags (DPI settings, special sim args) are preserved through the merge.
4. Registers the component in `eda_buddy/project_structure.yaml`.

The outputs land in `<tb_root>/yamls/`:
- `<component>_build.yaml` — include dirs, source file list, compile and elaborate flags.
- `<component>_run.yaml` — test entry points, UVM plusargs, regression groups.

A critical detail: `+UVM_TIMEOUT` is always set to `100000000` (100 µs in picoseconds, for a 1ns/1ps timescale). This is because `$time` in QuestaSim with 1ns/1ps timescale returns values in picoseconds, and common mistakes of setting the timeout in nanoseconds cause test timeouts at the 1 µs mark instead of 100 µs.

---

## The MCP Server

All PDF extraction, vector indexing, and diagram generation tools are implemented as **Model Context Protocol (MCP) tools** served by a local Python process.

**Server:** `verification_mcp_server/server.py`

To configure the MCP server in Anti-Gravity (Claude Code agent runner), add to `.gemini/antigravity/mcp_config.json`:

```json
{
  "mcpServers": {
    "pdf-custom-tools": {
      "command": "python",
      "args": [
        "d:/Verification/VERIFICATION_PLANNER/verification_mcp_server/server.py"
      ]
    }
  }
}
```

The MCP server exposes the following tools:

| Tool | Description |
|---|---|
| `extract_pdf_context_to_md` | Keyword-targeted extraction from PDF to Markdown |
| `convert_pdf_to_md` | Full PDF-to-Markdown conversion (pymupdf4llm) |
| `extract_hierarchical_pdf` | Build TOC-mapped JSON Knowledge Graph from PDF |
| `build_vector_index` | Embed all KG nodes and persist the vector DB |
| `query_vector_index` | Semantic similarity search over the persisted index |
| `generate_uvm_mermaid` | Generate UVM architecture Mermaid diagrams |
| `convert_plan_to_pdf` | Render a YAML verification plan to a PDF report |

---

## Repository Structure

```
verification_ai_skills/
│
├── .agent/
│   ├── skills/
│   │   ├── uvc_orchestrator/          ← Meta-skill: audit, dispatch, regress
│   │   │   └── scripts/
│   │   │       ├── eda_buddy_executor.py
│   │   │       └── run_regression.py
│   │   ├── pdf_to_markdown/           ← Token-free PDF extraction
│   │   ├── vector_index/              ← 3-stage LlamaIndex RAG pipeline
│   │   ├── uvc_planning/              ← Verification plan synthesis
│   │   │   ├── grading/               ← Self-evaluation engine
│   │   │   └── sub_prompts/           ← Protocol cheat sheets (AXI-S, AXI-MM, APB, AHB)
│   │   ├── uvc_generator/             ← UVM SV testbench synthesis
│   │   └── eda_yaml_generator/        ← EDA Buddy YAML manifest generation
│   │       └── scripts/
│   │           └── gen_eda_yamls.py
│   └── workflows/
│       └── uvc_verif_planning.md      ← End-to-end workflow definition
│
├── verification_mcp_server/           ← Python MCP server
│   ├── server.py
│   └── scripts/
│       ├── pdf_to_markdown.py
│       ├── plan_to_pdf.py
│       ├── uvm_mermaid_gen.py
│       └── vector_index.py
│
├── examples/                          ← Demo spec + sample plan (start here)
│   ├── README.md                      ← Step-by-step walkthrough of the example
│   ├── spec/simple_axi_stream_spec.md ← Demo input: readable protocol specification
│   └── plan/verif_plan_axi_stream_master_example.yaml  ← Demo output: sample plan
├── dummy_uvm/                         ← UVM component templates (blueprint source)
├── Output/                            ← Generated UVM testbenches land here (gitignored)
├── verf_plan_reports/                 ← Generated YAML plans and PDF reports (gitignored)
├── vector_db/                         ← Persisted LlamaIndex vector databases
├── json/                              ← Knowledge Graph JSON files
├── markdown/                          ← Extracted Markdown files
└── eda_buddy/                         ← EDA simulation toolchain manifests
```

---

## End-to-End Example: AXI5-Stream Master VIP

To illustrate the system in action, here is what the orchestrator produced for **AXI5-Stream, Verification Role: Master** (VIP drives the bus, DUT is the Slave).

### The Ask

```
Run the verification orchestrator for AXI-Stream where VIP role is Master 
and DUT would be Slave.
```

### What the Agent Did (Autonomously)

**Stage 1 — Spec Ingestion**
The agent built a vector index over the AMBA AXI5-Stream specification, embedding the content of every page using `BAAI/bge-small-en-v1.5`.

**Stage 2 — Verification Planning**
Running the Recursive Discovery Protocol (3 passes over the vector index), the agent extracted:
- **12 functional requirements** (REQ_MST_01 through REQ_MST_12) covering TVALID stability, TREADY pre-assertion, TLAST framing, null-termination, byte qualifiers (TKEEP/TSTRB), TID stream interleaving, continuous streaming, reset behavior, TWAKEUP wake-up timing, and AXI5 parity signals.
- **48 directed test cases** (TC_MST_001 through TC_MST_048), at an average of 4 TCs per requirement.
- **12 functional coverage groups** spanning every requirement dimension.
- **16 interface signals** with correct direction relative to the Master VIP role (TVALID/TDATA/TKEEP/TSTRB/TLAST/TID/TDEST/TUSER/TWAKEUP/TVALIDCHK/TDATACHK/TLASTCHK/TWAKEUPCHK as Output; TREADY/TREADYCHK as Input).

The agent also generated the full PDF verification report from the YAML plan.

**Stage 3 — UVM Synthesis**
The agent synthesized a 17-file UVM testbench:

| File | Purpose |
|---|---|
| `axi_stream_master_vip_defines.sv` | Global macros (TDATA_WIDTH=32, HAS_PARITY, HAS_TWAKEUP) |
| `axi_stream_master_vip_if.sv` | Interface with `cb_drv` and `cb_mon` clocking blocks |
| `axi_stream_master_vip_seq_item.sv` | Randomized packet item with 5 constraint blocks + violation knobs |
| `axi_stream_master_vip_driver.sv` | Master driver with beat-level TVALID/parity management |
| `axi_stream_master_vip_monitor.sv` | Protocol checker + 12 functional covergroups |
| `axi_stream_master_vip_scoreboard.sv` | TID/TDEST stability + TSTRB/TKEEP reserved-combo checker |
| `axi_stream_master_vip_callback.sv` | Pre/post-transmit callback hooks |
| `axi_stream_master_vip_sequencer.sv` | Standard UVM sequencer |
| `axi_stream_master_vip_agent.sv` | Agent wiring driver + monitor + sequencer |
| `axi_stream_master_vip_agent_config.sv` | Config object (VIF, feature flags, watchdog cycles) |
| `axi_stream_master_vip_env_config.sv` | Environment-level config |
| `axi_stream_master_vip_env.sv` | Env connecting agent to scoreboard |
| `axi_stream_master_vip_base_sequence.sv` | Sequence helpers (send_packet, send_null_term_packet, send_violation_packet) |
| `axi_stream_master_vip_test_sequences.sv` | 48 individual test sequence classes |
| `axi_stream_master_vip_test.sv` | Base test + 48 test classes (via `DEFINE_MST_TEST` macro) |
| `axi_stream_master_vip_tb_top.sv` | Simulation top with clock, reset, passive DUT stub |
| `axi_stream_master_vip_pkg.sv` | Package including all files in dependency order |

**Stage 4 — EDA Manifest Generation**
`build.yaml` and `run.yaml` were generated with all 48 test entry points registered, grouped into a `smoke_test` group (9 tests) and a `regression` group (37 tests).

**Stage 5 — Simulation & Debug**

The agent compiled and ran the regression against QuestaSim 2021.1, then autonomously diagnosed and fixed four issues before arriving at a passing run:

1. **Clocking Block Output Skew Bug**: The original driver deasserted `TVALID` one clock *after* the handshake cycle (with an extra `@(vif.cb_drv)` between the while-exit and the deassert). This created a one-cycle window where the monitor saw `TVALID=1` and `TREADY=0` after the handshake was already complete, triggering false `TVALID_STABILITY_VIOLATION` fatals. The fix: deassert `TVALID` *immediately* at the same clock edge where the while exits, before the next `@(vif.cb_drv)`. With QuestaSim's clocking block `#1step` output skew, the deassert takes effect at posedge + 1ps — making it visible to the monitor at the next posedge with no false stall window.

2. **Virtual Interface in Covergroup**: A coverpoint referencing `vif.cb_mon.TDATA[1:0]` inside a class-scope `covergroup` triggered a QuestaSim parse error (hierarchical references to virtual interface signals are not allowed inside class-scope covergroup bodies). Removed the offending coverpoint and cross.

3. **Null-Termination Constraint Conflict**: The seq_item's `c_tkeep_nonzero` constraint — `tkeep != '0` — conflicted with `send_null_term_packet`'s inline constraint `tkeep == '0`. Fixed by relaxing the class constraint to `(tkeep != '0) || (tstrb == '0)`, which correctly allows null-termination (TKEEP=0 only when TSTRB is also 0) while still preventing accidental zero-byte packets in normal tests.

4. **TC_048 Timeout**: The "full parity regression" test sent 200 random packets with `packet_length` unconstrained (up to 256 beats), producing ~512 µs of simulation time against a 100 µs budget. Fixed by constraining `packet_length <= 8` and reducing to 15 packets.

### Final Regression Results

```
PASS: axi_stream_master_vip_tc_mst_001_test   [TVALID Stability — single beat]
PASS: axi_stream_master_vip_tc_mst_002_test   [TVALID Stability — 64-beat extended stall]
...
PASS: axi_stream_master_vip_tc_mst_048_test   [AXI5 Parity — full regression]

=====================================================
  AXI-Stream Master VIP Regression
  PASS: 48 / 48    FAIL: 0 / 48
  Tool: QuestaSim 2021.1
=====================================================
```

---

## Installation & Setup

### Prerequisites

```bash
pip install pymupdf4llm llama-index-embeddings-huggingface reportlab pyyaml
```

QuestaSim (or any IEEE 1800 SystemVerilog simulator) is required for simulation.

### Configure the MCP Server

Add to your Anti-Gravity / Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "pdf-custom-tools": {
      "command": "python",
      "args": [
        "d:/Verification/VERIFICATION_PLANNER/verification_mcp_server/server.py"
      ]
    }
  }
}
```

### Running a Verification Session

Simply tell the orchestrator what you want:

```
Run the verification orchestrator for <protocol> where VIP role is <Master|Slave> 
and DUT would be <Slave|Master>.
```

The orchestrator will audit the current state, display the Verification Roadmap, and drive the pipeline forward — asking for confirmation at major transitions.

---

## Supported Protocols

The skill system ships with protocol cheat sheets for the full AMBA family:

| Protocol | Versions | Cheat Sheet |
|---|---|---|
| AXI-Stream | AXI4-Stream, AXI5-Stream | `uvc_planning/sub_prompts/axi_stream_cheat_sheet.md` |
| AXI Memory Mapped | AXI3, AXI4, AXI5 | `uvc_planning/sub_prompts/axi_mm_cheat_sheet.md` |
| APB | APB3, APB4, APB5 | `uvc_planning/sub_prompts/apb_cheat_sheet.md` |
| AHB | AHB3, AHB4, AHB5 | `uvc_planning/sub_prompts/ahb_cheat_sheet.md` |

Any protocol can be added by authoring a new cheat sheet and registering it in `uvc_planning`'s SKILL.md.

---

## Extending the System

**Adding a new protocol**
1. Create `uvc_planning/sub_prompts/<protocol>_cheat_sheet.md` with signal tables, handshake rules, and common corner cases.
2. Register the protocol name in `uvc_planning/SKILL.md` Section 9.

**Adding a new MCP tool**
1. Implement the tool function in `verification_mcp_server/scripts/`.
2. Register it with `@mcp.tool()` in `verification_mcp_server/server.py`.

**Extending the EDA YAML schema**
Modify `eda_yaml_generator/scripts/gen_eda_yamls.py` to add new fields. The deep-merge strategy ensures existing user customizations survive re-generation.

---

## Key Engineering Lessons

Working on this system uncovered several non-obvious insights about QuestaSim and UVM that are worth documenting:

**1. Never pass `uvm_pkg.sv` to `vlog` in QuestaSim.**
QuestaSim 2021.1 ships with UVM 1.1d as a built-in library (`mtiUvm`). Explicitly compiling `uvm_pkg.sv` causes a DPI GCC runtime error at load time. Use `-L mtiUvm` instead, or simply import `uvm_pkg::*` and let QuestaSim resolve the built-in automatically.

**2. `UVM_TIMEOUT` is in picoseconds when your timescale is 1ns/1ps.**
The `+UVM_TIMEOUT` plusarg sets a timeout in simulation time units, which for a `1ns/1ps` timescale means picoseconds. A value of `5000000` is only 5 µs — far too short for most regressions. The correct value for a 100 µs budget is `100000000`.

**3. Clocking block output skew creates a subtle 1-cycle timing window.**
When a driver writes to `vif.cb_drv.TVALID <= 0` at posedge P using a QuestaSim clocking block with `#1step` output skew, the change does not propagate until posedge P + 1ps. A monitor sampling at posedge P+1 - 1ps will still see the *old* value (1) from the previous clock edge. Any driver that does `@(vif.cb_drv); TVALID <= 0` after a handshake — rather than deassert-immediately-then-advance — will create a phantom stall cycle that the monitor cannot distinguish from a real one.

**4. Virtual interface hierarchical references are illegal inside class-scope covergroups.**
`covergroup cg_name; coverpoint vif.cb_mon.SIGNAL; endgroup` compiles fine in some tools but fails in QuestaSim 2021.1 with a cascading parse error. Move any VIF-dependent sampling to a task that manually samples signals into class member variables, then cover the class members.

---

*Built with Claude Code · Agent SDK · QuestaSim 2021.1 · LlamaIndex · BAAI/bge-small-en-v1.5*
