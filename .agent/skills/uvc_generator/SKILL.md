---
name: uvc_generator
description: Automated UVM Verification Environment Synthesis. Transforms YAML engineering reports into structured SystemVerilog code by merging protocol specifications with boilerplate blueprints. Also auto-generates EDA Buddy build.yaml and run.yaml manifests.
---

# UVM Generation Protocol (Blueprint Synthesis)

> [!IMPORTANT]
> **Mandatory Operational Mandate**: This skill **MUST** be used for all modifications, updates, or initial generations of any UVM/SystemVerilog file. Manual ad-hoc edits are strictly prohibited.
> 
> **Self-Synchronizing Updates**: Whenever any instruction, pattern, or logic within this `SKILL.md` is updated, the Agent **MUST** immediately perform an incremental synthesis (Pass 2) on all existing generated files in `Output/` to bring them into alignment with the new standard.

> [!IMPORTANT]
> This skill is responsible for the transition from **Planning (YAML)** to **Implementation (SystemVerilog)**. It relies on the presence of a `dummy_uvm/` template directory and a valid YAML verification plan.

## 1. Input Validation & Configuration
- **Source Plan**: Identify the target YAML file (e.g., `verf_plan_reports/verif_plan_<protocol>_vX_Y.yaml`).
- **Template Source**: Ensure `dummy_uvm/` exists and contains the necessary `.sv` templates.
- **State Check (Token Optimization)**: 
    - Check if the `Output/` directory exists.
    - If it exists, list its contents to identify already-generated components.
    - **Read-Existing**: If a file already exists in `Output/`, read its current implementation *before* overwriting. This allows for "Incremental Synthesis" where you only update changed sections rather than regenerating the entire codebase.
- **Protocol Context**: Extract the `<protocol>` and `<role>` from the YAML metadata to drive naming conventions.

## 2. Agentic AI Synthesis Protocol
This skill utilizes the Agent's domain expertise in UVM and SystemVerilog to implement the environment. 

### Implementation Strategy:
1.  **Structural Reference**: Read the corresponding blueprint in `dummy_uvm/` (for new files) or the existing file in `Output/` (for updates).
2.  **Expert Implementation**:
    *   **Logic Synthesis**: Read the `code_snippets` and `test_requirements` from the YAML. Translate these into high-fidelity, synthesizable SystemVerilog.
    *   **Macro-Based Architecture**: Use preprocessor `` `define `` macros (not `parameter`) in the `<protocol>_<role>_defines.sv` file for all architectural settings (widths, IDs, feature toggles). This ensures global visibility across all classes without complex package-scoping or redundant inclusions, resolving "Undefined variable" errors in modular flows.
    *   **Configuration-Driven Logic**: Move all protocol feature flags into the `<protocol>_<role>_agent_config` class, initialized via the architectural macros. Components must reference these flags via their `cfg` handle for dynamic control.
    *   **Incremental Edit**: If editing an existing file, use `replace_file_content` to update only the modified logic or parameters, preserving stable boilerplate to save tokens.
    *   **Handshake Precision**: Implement exact signal-level handshaking (e.g., `VALID`/`READY` toggling, reset synchronization, and parity calculations).
    *   **Data Integrity**: Ensure the `scoreboard` and `monitor` correctly handle packet boundaries (`TLAST`) and byte qualifiers (`TKEEP`/`TSTRB`).
    *   **High-Density Diagnostic Logging**: Implement comprehensive UVM reporting in `drivers` and `sequences`.
        *   **Verbosity Compliance**: Use `UVM_MEDIUM` for packet headers and `UVM_HIGH/FULL` for detailed member dumps.
        *   **Multi-Line Formatting**: Use structured, multi-line `` `uvm_info `` messages instead of single-line strings for readability.
        *   **Flow Tracking**: Include local packet counters and clear boundary markers (e.g., `[START PACKET X]`, `[END PACKET X]`) to trace the lifecycle of each transaction.
        *   **Full Member Visibility**: Ensure all transaction properties (data, addr, control signals, parity) are printed during the handshake.
    *   **Protocol-Aware Boundary Synthesis**: 
        *   **Boundary Analysis**: The Agent MUST analyze the protocol specification (via the YAML plan) to identify the logical packet boundary (e.g., `TLAST` for AXI-S, `EOP` for streaming protocols, or `IDLE` states).
        *   **Ambiguity Resolution**: If the packet boundary is not explicitly mapped in the YAML, the Agent MUST ask the USER for clarification by referencing specific requirements or signal descriptions from the plan.
        *   **Cross-Component Synchronization**: The identified boundary logic MUST be consistently implemented across the `driver` (for burst generation), `monitor` (for aggregation), and `scoreboard` (for packet-level comparison).
        *   **Violation Detection**: The monitor and scoreboard MUST include assertion-like diagnostic logic to catch protocol violations (e.g., missing boundary signals, invalid control combinations, or handshake timeouts).
    *   **Protocol-Aware Tracker File**: Implement a dedicated tracker mechanism in the `monitor`.
    *   **Interface Skew Management**: Generated interfaces must NOT use explicit `default input #` or `output #` skews in clocking blocks. 
        *   **Standard**: Rely on simulator default edge-based sampling (e.g. `posedge clk`) to maintain high-fidelity timing relative to the RTL clock.

    *   **Negative Testing Architecture**: To support negative test cases (e.g., protocol violations), the Agent MUST:
        *   Add "violation knobs" (e.g., `rand bit drop_valid_early`) to `seq_item`.
        *   Implement conditional logic in the `driver` to trigger these violations when the knob is active.
        *   This ensures the Monitor is exercised against invalid protocol transitions without manual testbench hacking.
    *   **Burst & Stream Synthesis**: Sequences for streaming protocols MUST:
        *   Iterate beat-by-beat to support per-beat randomization (interleaving).
        *   Ensure `TLAST` (or equivalent) is only driven on the final beat of a logical transaction.
        *   Support "Null Termination" (TLAST=1 with minimal/no data) as a distinct scenario.

3.  **Recursive Test Synthesis (Strict Traceability)**:
    *   **Comprehensive Coverage**: The Agent MUST generate a dedicated `uvm_sequence` and a corresponding `uvm_test` for EVERY test case ID found in the YAML `test_cases` list.
    *   **YAML Merge Protocol**: When updating manifests (`build.yaml`, `run.yaml`), the Agent MUST:
        1.  Invoke the `eda_yaml_generator` skill using the `gen_eda_yamls.py` script.
        2.  **Review the Diff**: Perform a manual diff of the updated YAMLs.
        3.  **Conflict Resolution**: If the script overwrote a critical user customization (e.g. specialized DPI flags or custom group mappings), the Agent MUST restore the user's data and notify them of the change.
    *   **Constraint Extraction**: For each test case, the Agent MUST:
        1.  Identify all mapped `REQ_...` IDs.
        2.  Read the `test_requirements` to extract specific constraints (e.g., TDATA widths, TID ranges, delay cycles, or parity corruption).
        3.  Translate the `scenario` description into sequence logic (e.g., a "burst" requires multiple beats before `TLAST`, "interleaving" requires switching `TID` between beats).
    *   **Naming Convention**:
        *   Sequence: `<protocol>_<role>_<tc_id>_seq` (e.g., `axi_stream_master_tc_mst_001_seq`).
        *   Test: `<protocol>_<role>_<tc_id>_test` (e.g., `axi_stream_master_tc_mst_001_test`).
    *   **Handshake Consistency**: Ensure that negative test cases (e.g., dropping `TVALID`) are implemented via driver callbacks or sequence-item overrides if supported.

4.  **Consistency Check**: Ensure all class names, signal handles, and configuration objects are consistent across the entire generated file set.
5.  **File Generation/Update**: Use `write_to_file` for new files and `replace_file_content` for surgical updates to existing files.

## 3. Directory Structure & Serialization
- **Root Container**: The output must be written into a protocol-specific root folder within `Output/` (e.g., `Output/axi_stream_master_vip_tb/`), as defined in the YAML `directory_structure.root` property.
- **Token Efficiency**: Do not `view_file` the entire directory if only one component (e.g., `driver`) needs an update based on a YAML change.
- **Folder Nomenclature**: Create subdirectories within the root container following the `directory_structure.folders` property, ensuring consistent nomenclature.

## 4. MCP Tool Integration
- **Manual Synthesis**: Use standard file system tools (`list_dir`, `view_file`, `write_to_file`, `multi_replace_file_content`) to perform the synthesis.
- **Workflow**:
    1.  Scan `Output/` for existing files.
    2.  Identify delta between YAML requirements and existing SV files.
    3.  Generate or Update files strategically.

## 5. Implementation Roadmap (Post-Synthesis)
- **Compilation Check**: After synthesis, attempt to compile the generated SV code.
- **Traceability Verification**: Cross-reference generated `_test.sv` scenarios with the YAML requirements.

---

## 6. Post-Synthesis Gap Analysis (Mandatory Final Step)

> [!IMPORTANT]
> Run after EVERY synthesis pass. Fix all P1 gaps before reporting to USER.

**Inputs to read**: YAML plan · `sequences/*.sv` · `top/*_test.sv` · `seq_item.sv` · `driver.sv` · `monitor.sv`

**5-Pass Audit:**
1. **TC Coverage** — For each plan `test_cases[].id` confirm a `<protocol>_<tc_id>_seq` class with scenario-specific constraints exists. Classify: ✅ Present / ⚠️ Partial (stub body) / ❌ Missing.
2. **Fidelity** — For every ⚠️ Partial: verify transfer count, delay value, and signal constraints exactly match the plan `scenario`.
3. **seq_item** — Every plan stimulus knob has a `rand` field. `do_copy()`/`do_compare()` exist.
4. **Driver paths** — Every `HAS_*` flag has active (non-commented) drive logic. Every negative knob has an `if (item.<knob>)` block.
5. **Coverage orphans** — Every plan `coverage_groups` entry has a live `covergroup` in `monitor.sv`.

**Output inline report:**
```
| TC ID | Mapping | ✅/⚠️/❌ | Gap description |
| seq_item holes | driver holes | coverage orphans |
| P1: fix now | P2: fix or escalate | P3-P4: defer, ask USER |
```
