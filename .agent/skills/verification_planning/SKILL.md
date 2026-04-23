---
name: verification_planning
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

## 2. Iterative Information Extraction (The Data Loop)
- **Deep Grep**: Search for "shall", "must", "illegal", "reserved","Transfer","Packet","Interleaving","Outstanding","Parity" and "Data Streams" "Aligned" "Unaligned" "Handshaking" "Wake Up" "ID" "Flow control" "Packing" "Unpacking" "Qualifiers" "Boundaries" "Clock" "Reset" "User Signaling" "Continuous packets" and "error".
- **Refinement**: Use context windows (-C 50) to capture the "Why" behind a requirement.
- **Spec Anchoring**: Every requirement MUST be anchored to a Section/Page/Paragraph.

## 3. Configuration & High-Value Feature Matrix
Systematically list and describe all supported configurations found in the spec using the following strict format:
- **Formatting Rule**: The configuration `name` should be concise, meaningful, and consist of Delimiter-separated words (e.g. `OoO_Transactions`, `Interleaving_Variable_Depth`).
- **Impact Description**: The `impact` field MUST NOT just describe the feature itself. Instead, strictly describe its **impact on terms of functionality, performance, and other verification constraints** (e.g. impact on scoreboard modeling, bandwidth limits, memory allocation). 
- **Core Areas to cover**:
    - **Out-of-Order & Burst Types**: Impact of tracking multi-beat transfers and reordering on the UVM architecture.
    - **Handshaking & Protocol Scenarios**: Impact on pipeline stalling, throughput, and negative stimulus injection routing.
    - **Data Integrity**: Impact of parity or ECC on error injection handlers.

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
configurations:
  - feature: "Out-of-Order"
    name: "OoO_Transaction_Depth_Config"
    impact: "Functionality impact involves expanding scoreboard reorder buffers. Performance impact allows for saturated bandwidth despite varied slave latency."
  - feature: "Burst Type"
    name: "Fixed_Incr_Wrap_Bursts"
    impact: "Functional impact requires address-calculation checking logic. Performance impacts alignment logic penalties on wrapped boundaries."
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
    - top: "List the simulation top level files"
```

## 7b. UVM Structural Constraints
- **UVM Component Listing Rules**: Within the `directory_structure` property, YOU MUST explicitly list every UVM component required (driver, monitor, scoreboard, callback, configs for each component).
- **Naming Standard**: Every component MUST be listed as an `.sv` file explicitly utilizing the naming schema: `<interface_name>_<role>_<component_type>.sv` (e.g., `axi_stream_master_driver.sv`, `axi_stream_master_scoreboard.sv`, `axi_stream_master_agent_config.sv`). Do not produce generic abstract descriptions; list the specific files.

## 8. Professional PDF Reporting & Versioning
- **Directory Rule**: All generated artifacts MUST be stored in the root directory `verf_plan_reports/`. This directory should be created if it does not exist.
- **Versioning Rule**: All artifacts MUST be saved with versioned filenames within the output directory to prevent overwriting.
    - *YAML Path*: `verf_plan_reports/verif_plan_<protocol>_v<X_Y>.yaml`
    - *PDF Path*: `verf_plan_reports/<protocol>_verif_report_v<X_Y>.pdf`
- **Rendering**: Invoke `convert_plan_to_pdf`.
- **Sections**: Configurations, Traceability, Negative Scenarios, Performance, Interface Fidelity, and Architecture.

## 9. Protocol-Specific Reference (Sub-Prompts)
- **Modular Expansion**: The agent **MUST** detect the target protocol and extract all respective sub-prompt cheat sheets for architecture mapping:
  - If AXI-Stream: Read `sub_prompts/axi_stream_cheat_sheet.md`
  - If AMBA AXI Memory Mapped (AXI3, AXI4, AXI5): Read `sub_prompts/axi_mm_cheat_sheet.md`
  - If AMBA APB (APB3, APB4, APB5): Read `sub_prompts/apb_cheat_sheet.md`
  - If AMBA AHB (AHB3, AHB4, AHB5): Read `sub_prompts/ahb_cheat_sheet.md`
- **Exhaustive Mapping**: Ensure that all corner cases and negative scenarios listed in the sub-prompt are mapped to at least one test case and coverage group in the final YAML plan.

## 10. Output Quality & Engineering Tone
- **Technical Rigor**: All generated descriptions MUST be written in a formal engineering tone. Avoid colloquialisms or simplified explanations.
- **Well-Structured Narratives**: Requirements and Test Scenarios must be presented as logically structured paragraphs that explain the "What," "Why," and "How" of the verification task.
- **Fluency & Professionalism**: The final verification report should be fluent and professional, suitable for review by senior architects and design leads.
