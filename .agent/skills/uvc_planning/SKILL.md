---
name: uvc_planning
description: Ultra-precise agentic protocol for generating enterprise-grade functional verification plans. Focuses on configuration-aware signal population and total spec-to-coverage traceability.
---

# Advanced Functional Verification Planning (Clean Slate Protocol)

> [!IMPORTANT]
> This skill requires continuous improvement. For every new project, re-read the technical specification from scratch to eliminate stale assumptions. Zero omission is the goal.

## 1. Interactive User-Intent & Context Reset
- **Baseline Reset**: Do not rely on previous summaries. Re-read the source for every task.
- **Mandatory Initialization**: Before planning, ASK the user ONLY for:
    1. **Topology**: Verification Role (Master or Slave)? 
        - *Definition*: The **Verification Role** is the role of the UVM VIP/Environment being developed. 
        - *DUT Rule*: The **DUT (Design Under Test)** is always the **OPPOSITE** of the Verification Role. (e.g., Verification Role: Master $\to$ DUT: Slave).
- **Autonomous Discovery**: Since the user will NOT provide versions or specific options, the agent MUST independently identify:
    - Supported Protocol Versions (e.g., AXI4, AXI5).
    - All functional configurations (Out-of-Order, Burst Types, Interleaving).
    - Optional sidebands and data integrity features.

## 2. Iterative Information Extraction (Vector RAG Protocol)

> [!IMPORTANT]
> The **primary** extraction method is the **LlamaIndex Vector Index pipeline** from the `vector_index` skill. Raw grep is the **fallback** only when a vector DB is unavailable. Read `.agent/skills/vector_index/SKILL.md` before proceeding.

### 2a. Pre-flight: Check / Build Vector Index
1. Check if a vector DB exists for the target spec:
   ```
   find_by_name(SearchDirectory="d:\\Verification\\VERIFICATION_PLANNER\\vector_db", Pattern="<spec_name>")
   ```
2. **If NOT found** — run the full 3-stage pipeline:
   - **Stage 1:** `extract_hierarchical_pdf` → `json/<spec_name>_kg.json`
   - **Stage 2:** `build_vector_index` → `vector_db/<spec_name>/`
3. **If found** — proceed directly to the **Recursive Discovery Protocol**.

### 2b. The Recursive Discovery Protocol (Mandatory for High Density)
3.  **The Density Contract**:
    *   Minimum **10 Technical Requirements**.
    *   Minimum **30 Test Cases**.
    *   Failure to meet these thresholds is a "Low Fidelity" failure. Perform a "Pass 4 (Drill Down)" if thresholds are not met.

4.  **Master Schema Protocol (MANDATORY & EXHAUSTIVE)**:
    To ensure the PDF tool renders a complete engineering blueprint, you **MUST** include:
    *   **EXHAUSTIVE ENUMERATION**: Do NOT use placeholders or comments like "(rest of cases maintained in memory)". Every one of the 30+ test cases **MUST** be physically written into the YAML file.
    *   **Architecture Diagram**: Use `uvm_environment_diagram` with Mermaid syntax.
    *   **Directory Structure**: Use `directory_structure` object.
    *   **Implementation Pseudo-Code**: Use `code_snippets` list.
    *   **Requirements**: Use `test_requirements` list.
    *   **Test Cases**: Use `test_cases` list.

1. **Pass 1: Scope Extraction**: Query the Table of Contents and Signal List. Identify every signal name and chapter title.
2. **Pass 2: Functional Triangulation**: Query each signal identified in Pass 1 for its unique timing, handshake, and payload constraints.
3. **Pass 3: Conformance Sweep**: Search for modal keywords (`shall`, `must`, `illegal`, `reserved`, `forbidden`). Every "Shall" statement found must map to at least one Test Requirement.

> [!CAUTION]
> **DENSITY CHECK**: If at the end of Pass 3 you have fewer than 10 Test Requirements, you MUST perform a **Pass 4** targeting optional protocol extensions (e.g., AXI5 sidebands, continuous streaming properties, power-up sequencing).

### 2c. Spec Anchoring
Every requirement MUST be anchored to a **Section/Page** from the RAG chunk metadata. Use the exact `spec_ref` provided in the retrieval results.

## 4. Total Traceability & Elaborative Modeling
- **Test Requirements Formulation**:
    - **Feature & Sub-Feature Grouping**: Actively divide Test Requirements based on the high-level `feature` and specific `sub_feature` they belong to (e.g. Feature: "Handshake", Sub-Feature: "TVALID Stability"). This allows for easy evaluation and mapping logic.
    - **Signal Relationship Analysis**: Actively scan for signals and strictly document their relationships and dependencies (e.g., how TKEEP state depends on TVALID, or TREADY's relation to TWAKEUP). Over-generate the number of test requirements to ensure every signal inter-dependency and corner boundary is individually covered.
    - **Technical Narrative**: Utilize rigorous engineering terminology (e.g., "deterministic latency," "conformance boundary," "orthogonality").
    - **Multi-paragraph "Verification Intent"**: 
        - **Paragraph 1**: Hardware logic details and the specific failure mode or race condition being prevented based on signal relationships.
        - **Paragraph 2**: Detailed verification strategy spanning Functional, Negative, and Performance-based checks.
    - **Fluency**: Ensure descriptions are written in a cohesive, technical prose style rather than fragmented notes.
- **Test Case Definition Strategy**:
    - **Quantity & Ratio Goals**: The goal is to generate at least **3 to 4 test cases per test requirement**. While not always possible, actively try to generate a high volume of test cases, maintaining high quality and orthogonality, to guarantee rigorous structural coverage.
    - **Directed but Randomizable**: All test cases must be designed to test a highly specific aspect of the protocol (directed intent) while still utilizing constrained randomization (e.g., stall durations, packet sizes, variable interleaving depth) to hit edge boundaries.
    - **Control the VIP, Observe the DUT**: Test cases must be strictly defined by controlling verification component behaviors (e.g., configuring sequences, driver delays, protocol fault injections via the VIP). 
    - **Standard DUT Compliance**: Do NOT write test scenarios that expect the DUT to adopt a custom or altered behavior to pass. The DUT must be assumed to strictly adhere to the specification; the verification environment must generate the necessary corner cases to interact with standard DUT logic.
    - **Role-Safe Signal Control (MANDATORY)**: 
        *   **Ownership Check**: Every test case MUST respect the direction of the protocol signals. If the Verification Role is **Master**, the VIP **CANNOT** "drive," "hold," or "toggle" Slave-owned signals (e.g., `TREADY`). 
        *   **Phrasing Requirement**: Test cases must be phrased as: "VIP drives [Role Signals], then **observes** or **waits for** [DUT Signals]." 
        *   **Physical Validity**: Any test case that claims to control a signal owned by the DUT is a "Fatal Fidelity" failure.
- **N:M:P Mapping & Traceability Constraints**: 
    - **Incremental Numeric IDs**: Test Requirement IDs and Test Case IDs MUST be purely incremental numeric sequences (e.g., `REQ_MST_01, REQ_MST_02`... and `TC_MST_001, TC_MST_002, TC_MST_003`...). Do NOT append alphabetic sub-indices (like `_A`, `_B`) to test cases just because they map to the same requirement. Maintain a strictly flat, incremental numbering scheme.
    - Test Case $\to$ Requirement.
    - Coverage Group $\to$ Requirement.
    - **No Orphaned Requirements**: Every requirement must have at least one test case AND one coverage point.

## 5. Interface Fidelity & Signal Population
- **Table Scanning**: Locate every signal table in the document.
- **Configuration Filtering**: If a signal is marked "Conditional" or "AXI5-only", populate it based on the detected configuration in Step 1.
- **Port Metadata Constraints**: Name, Dir, Width, and a rich functional description are mandatory. For the 'direction' field, YOU MUST specify ONLY the exact primitive string "Input" or "Output". Determine this direction relatively from the perspective of the chosen verification VIP Role (e.g. Master = Transmitter, Slave = Receiver). Do NOT include extra contextual text like "Output (to Slave)" inside the direction string.

## 6. Visual Architecture (Automated UVM Modeling)
- **Mandatory Tool Usage**: Use the `generate_uvm_mermaid` tool for all architecture diagrams.
- **Hierarchical Nesting**: The UVM Test component MUST encompass the UVM Environment. The Environment must encompass the Agent(s).
- **Structural Centricity**: 
    - No separate "Dynamic Object" subgraph/layer should be used. 
    - Transactions and Sequences should be shown as auxiliary objects connected to the static sequencer/driver chain.
- **Visual Standards**: Components (Blue) vs. Objects (Green/Dashed). The tool automatically enforces this containment hierarchy.
- **DUT Labeling**: The diagram must explicitly label the hardware component as "**DUT ([Opposite Role])**" based on the Verification Role selected in Step 1.

## 7. Standardized YAML Schema
```yaml
project: "Title"
version: "X.Y"
verification_role: "Master | Slave"
protocol_version: "e.g., AXI5-Stream"
uvm_environment_diagram: |
  graph TD
    ...
test_requirements:
  - id: "REQ_ID"
    feature: "High-Level Feature (e.g., Handshake)"
    sub_feature: "Specific Drill-down (e.g., TVALID Stability)"
    name: "Name"
    spec_ref: "Section X.Y, Page Z"
    description: |
      [Paragraph 1: Hardware Logic/Failure Mode/Target]
      [Paragraph 2: Verification Intent and Strategy (Functional/Negative/Perf)]
test_cases:
  - id: "TC_ID"
    scenario: "Detail..."
    mapping: ["REQ_ID"]
coverage_groups:
  - name: "cg_name"
    description: "..."
    mapping: ["REQ_ID"]
interface_signals:
  - name: "SIG"
    direction: "Dir"
    width: "W"
    description: "Configuration-aware description"
directory_structure:
  root: "<protocol_name>_<role>_vip_tb/"
  folders:
    - master_agent: "List EXACT filenames: e.g., <interface>_<role>_driver.sv, <interface>_<role>_monitor.sv, <interface>_<role>_agent_config.sv, <interface>_<role>_callback.sv"
    - env: "List EXACT filenames: e.g., <interface>_<role>_scoreboard.sv, <interface>_<role>_env_config.sv"
    - sequences: "List sequences matching the <interface>_<role> nomenclature: e.g., <interface>_<role>_base_sequence.sv, <interface>_<role>_seq_item.sv"
    - top: "List the simulation top level files: e.g., <interface>_<role>_tb_top.sv, <interface>_<role>_test.sv, <interface>_<role>_pkg.sv, <interface>_<role>_if.sv, <interface>_<role>_defines.sv"
code_snippets:
  - title: "Filename.sv (Architecture Blueprint)"
    code: |
      [Structured blueprint defining COMPONENT, MEMBERS, and LOGIC mapping to sub-prompt rules]
```

## 7a. Architecture Rule: defines.sv + Parameterized Interface

> [!IMPORTANT]
> **ALWAYS** plan for a `*_defines.sv` file. It is the **single source of truth** for all width and capability constants. Changing one macro value there propagates to every component at next elaboration.

### File responsibilities

| File | Role |
|---|---|
| `*_defines.sv` | All `` `define `` macros: `AXI_DATA_W`, `AXI_ID_W`, `AXI_HAS_PAR`, etc. — wrapped in an `` `ifndef `` guard. |
| `*_if.sv` | Parameterized interface. `` `include `` defines.sv at the top; parameter defaults reference the macros (e.g., `parameter int DATA_W = \`AXI_DATA_W`). |
| `*_pkg.sv` | Imports uvm_pkg, `` `include `` uvm_macros.svh, then immediately `` `include `` defines.sv before any class includes. All included classes see the macros. Default `typedef` aliases at the bottom. |
| `agent_config.sv` | Virtual handle MUST carry explicit `#(.DATA_W(\`AXI_DATA_W), ...)` binding — never the bare unparameterized form. |
| `*_tb_top.sv` | `` `include `` defines.sv at the top. Interface instance MUST carry explicit `#(.DATA_W(\`AXI_DATA_W), ...)` — never bare. |

### Width propagation rule
The explicit `#(.DATA_W(\`AXI_DATA_W))` binding in BOTH `agent_config.sv` (virtual handle type) and `*_tb_top.sv` (interface instantiation) is **mandatory**. Without it, the interface uses its own hardcoded default and the macro change does NOT propagate to signal widths.

Default `typedef` aliases appear at the bottom of the package for behavioral factory overrides:
```
axi_stream_mst_seq_item_t::type_id::set_type_override(my_item::type_id::get());
```

## 7b. UVM Structural Constraints
- **UVM Component Listing Rules**: Within the `directory_structure` property, YOU MUST explicitly list every UVM component required (driver, monitor, scoreboard, callback, configs for each component). **Placeholders like 'etc.' or '...' are forbidden.**
- **Sequential Mapping**: Every file listed in the `directory_structure` MUST have a corresponding entry in the `code_snippets` section.
- **Naming Standard**: Every component MUST be listed as an `.sv` file explicitly utilizing the naming schema: `<interface_name>_<role>_<component_type>.sv` (e.g., `axi_stream_master_driver.sv`, `axi_stream_master_scoreboard.sv`, `axi_stream_master_agent_config.sv`).

## 8. Professional PDF Reporting & Versioning
- **Directory Rule**: All generated artifacts MUST be stored in the root directory `verf_plan_reports/`. This directory should be created if it does not exist.
- **Versioning Rule**: All artifacts MUST be saved with versioned filenames within the output directory to prevent overwriting.
    - *YAML Path*: `verf_plan_reports/verif_plan_<protocol>_v<X_Y>.yaml`
    - *PDF Path*: `verf_plan_reports/<protocol>_verif_report_v<X_Y>.pdf`
- **Rendering**: Invoke `convert_plan_to_pdf`.
- **Sections**: Traceability, Negative Scenarios, Performance, Interface Fidelity, and Architecture.

## 9. Protocol-Specific Reference (Sub-Prompts)
- **Modular Expansion**: The agent **MUST** detect the target protocol and extract all respective sub-prompt cheat sheets for architecture mapping:
  - If AXI-Stream: Read `sub_prompts/axi_stream_cheat_sheet.md`
  - If AMBA AXI Memory Mapped (AXI3, AXI4, AXI5): Read `sub_prompts/axi_mm_cheat_sheet.md`
  - If AMBA APB (APB3, APB4, APB5): Read `sub_prompts/apb_cheat_sheet.md`
  - If AMBA AHB (AHB3, AHB4, AHB5): Read `sub_prompts/ahb_cheat_sheet.md`
- **Universal Code Generation**: Regardless of protocol, the agent **MUST** read and enforce the pseudo-code logic outlined in `sub_prompts/uvm_pseudo_code_generation.md`.
- **Exhaustive Mapping**: Ensure that all corner cases and negative scenarios listed in the sub-prompt are mapped to at least one test case and coverage group in the final YAML plan.

## 10. Output Quality & Engineering Tone
- **Technical Rigor**: All generated descriptions MUST be written in a formal engineering tone. Avoid colloquialisms or simplified explanations.
- **Well-Structured Narratives**: Requirements and Test Scenarios must be presented as logically structured paragraphs that explain the "What," "Why," and "How" of the verification task.
- **Fluency & Professionalism**: The final verification report should be fluent and professional, suitable for review by senior architects and design leads.
