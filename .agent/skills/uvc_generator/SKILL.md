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
    *   **Define-Based Architecture with Parameterized Interface**: ALL structural constants MUST live in `*_defines.sv` as `` `define `` macros. The interface uses these macros as parameter defaults. The package includes the defines file before any class includes, making macros available to every included class. This is the **single source of truth** — change ONE macro value and every component (seq_item fields, driver helpers, interface instance, virtual handle type) picks it up at next elaboration.

        *   **`*_defines.sv`** — one `ifndef` guard, all width and capability constraints:
            ```systemverilog
            `ifndef <PROTOCOL>_<ROLE>_VIP_DEFINES
            `define <PROTOCOL>_<ROLE>_VIP_DEFINES

            `define <PROTOCOL>_DATA_W            32
            `define <PROTOCOL>_ADDR_W            32
            `define <PROTOCOL>_ID_W              8
            `define <PROTOCOL>_USER_W            4
            `define <PROTOCOL>_HAS_PAR           1
            `define <PROTOCOL>_HAS_WAKE          1
            `define CLK_PERIOD_PS         10
            `define <PROTOCOL>_WATCHDOG_MAX   100_000
            `define MAX_PACKET_BEATS      256
            `define <PROTOCOL>_STALL_MAX      100

            `endif
            ```

        *   **`*_if.sv`** — parameterized, with defaults driven by the macros (`` `include `` the defines file at the very top, before the interface declaration):
            ```systemverilog
            `include "<protocol>_<role>_vip_defines.sv"
            interface <protocol>_<role>_vip_if #(
              parameter int DATA_W   = `<PROTOCOL>_DATA_W,
              parameter int ADDR_W   = `<PROTOCOL>_ADDR_W,
              parameter int ID_W     = `<PROTOCOL>_ID_W,
              parameter int USER_W   = `<PROTOCOL>_USER_W,
              parameter bit HAS_PAR  = `<PROTOCOL>_HAS_PAR,
              parameter bit HAS_WAKE = `<PROTOCOL>_HAS_WAKE
            )(input logic ACLK, input logic ARESETn);
              logic [DATA_W-1:0]     DATA;
              logic [ADDR_W-1:0]     ADDR;
              logic [ID_W-1:0]       ID;
              logic [USER_W-1:0]     USER;
            endinterface
            ```

        *   **`*_pkg.sv`** — includes defines FIRST so all class files see the macros; class files use backtick macros for widths:
            ```systemverilog
            package <protocol>_<role>_vip_pkg;
              import uvm_pkg::*; `include "uvm_macros.svh"

              // ── Width/capability constants (macro-scoped from defines.sv) ───
              `include "<protocol>_<role>_vip_defines.sv"

              // ── VIP class files (use `<PROTOCOL>_DATA_W etc. from above) ──────────
              `include "<protocol>_<role>_vip_seq_item.sv"
              `include "<protocol>_<role>_vip_agent_config.sv"
              // ... all other includes ...

              // ── Default typedefs (behavioral factory override aliases) ──────
              typedef <protocol>_<role>_vip_seq_item  <protocol>_<role>_seq_item_t;
              typedef <protocol>_<role>_vip_agent     <protocol>_<role>_agent_t;
              typedef <protocol>_<role>_vip_env       <protocol>_<role>_env_t;
            endpackage
            ```

        *   **Class files use backtick macros** (they are in scope because the package included defines.sv before them):
            ```systemverilog
            // <protocol>_<role>_vip_seq_item.sv
            rand logic [`<PROTOCOL>_DATA_W-1:0]  data[$]; // Queue-based payload
            rand logic [`<PROTOCOL>_ADDR_W-1:0]  addr;
            rand logic [`<PROTOCOL>_ID_W-1:0]    id;
            rand logic [`<PROTOCOL>_USER_W-1:0]  user;
            ```

        *   **`agent_config.sv`** — virtual handle MUST explicitly bind every interface parameter to its macro. Since agent_config is compiled inside the package body, the defines macros are already in scope:
            ```systemverilog
            class <protocol>_<role>_vip_agent_config extends uvm_object;
              `uvm_object_utils(<protocol>_<role>_vip_agent_config)
              virtual <protocol>_<role>_vip_if #(
                .DATA_W  (`<PROTOCOL>_DATA_W),
                .ADDR_W  (`<PROTOCOL>_ADDR_W),
                .ID_W    (`<PROTOCOL>_ID_W),
                .USER_W  (`<PROTOCOL>_USER_W),
                .HAS_PAR (`<PROTOCOL>_HAS_PAR),
                .HAS_WAKE(`<PROTOCOL>_HAS_WAKE)
              ) vif;
              uvm_active_passive_enum is_active        = UVM_ACTIVE;
              bit  has_parity          = `<PROTOCOL>_HAS_PAR;
              bit  has_twakeup         = `<PROTOCOL>_HAS_WAKE;
              bit  enable_tracker      = 0;
              bit  continuous_pkt_mode = 0;
              int  watchdog_cycles     = `<PROTOCOL>_WATCHDOG_MAX;
              int  max_packet_beats    = `MAX_PACKET_BEATS;
            endclass
            ```

        *   **`*_tb_top.sv`** — `` `include `` defines at the top; interface instance MUST explicitly bind every parameter to its macro so width changes propagate:
            ```systemverilog
            `timescale 1ns/1ps
            `include "<protocol>_<role>_vip_defines.sv"
            import <protocol>_<role>_vip_pkg::*;
            import uvm_pkg::*; `include "uvm_macros.svh"

            module <protocol>_<role>_vip_tb_top;
              // ...
              <protocol>_<role>_vip_if #(
                .DATA_W  (`<PROTOCOL>_DATA_W),
                .ADDR_W  (`<PROTOCOL>_ADDR_W),
                .ID_W    (`<PROTOCOL>_ID_W),
                .USER_W  (`<PROTOCOL>_USER_W),
                .HAS_PAR (`<PROTOCOL>_HAS_PAR),
                .HAS_WAKE(`<PROTOCOL>_HAS_WAKE)
              ) dut_if (.ACLK(ACLK), .ARESETn(ARESETn));
              // ...
            endmodule
            ```

        > [!IMPORTANT]
        > The explicit `#(.DATA_W(`<PROTOCOL>_DATA_W) ...)` binding in BOTH `agent_config.sv` (virtual handle) and `*_tb_top.sv` (interface instance) is **mandatory**. Without it, changing the macro value does NOT propagate to the interface — the interface would use its own hardcoded default instead. Bare `virtual <protocol>_<role>_vip_if vif;` or `<protocol>_<role>_vip_if dut_if(...)` without the `#(...)` parameter list is **forbidden**.

    *   **Configuration-Driven Logic**: Agent config carries ONLY runtime knobs (active/passive, enable_tracker, watchdog, stall limits). It MUST NOT contain signal-width fields — those are structural and live in the defines macros / interface parameters:
            ```systemverilog
            // ← NO data_width, id_width integer fields — those are interface parameters
            // ← Use `<PROTOCOL>_HAS_PAR macro (not a field) as the default for has_parity
            ```
    *   **Incremental Edit**: If editing an existing file, use `replace_file_content` to update only the modified logic or parameters, preserving stable boilerplate to save tokens.
    *   **Handshake Precision**: Implement exact signal-level handshaking (e.g., `VALID`/`READY` toggling, reset synchronization, and parity calculations).
    *   **Data Integrity**: Ensure the `scoreboard` and `monitor` correctly handle packet boundaries (`TLAST`) and byte qualifiers (`TKEEP`/`TSTRB`).
    *   **High-Density Diagnostic Logging**: Implement comprehensive UVM reporting in `drivers` and `sequences`.
        *   **Verbosity Compliance**: Adhere strictly to the logging levels defined in the [coding_guideline](sub_skills/coding_guideline/SKILL.md) sub-skill (e.g., `UVM_MEDIUM` for standard transaction tracking and packet headers, and `UVM_HIGH`/`UVM_FULL` for cycle-by-cycle or member-level dumps during debugging).
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
    *   **Burst & Stream Synthesis**: Sequences for streaming and burst protocols MUST:
        *   **Queue-Based Payload**: Represent payloads using a data queue in the `seq_item` (e.g., `rand logic [`<PROTOCOL>_DATA_W-1:0] data[$]`).
        *   **Sequence-Driven Population**: The sequence MUST populate the data queue based on the resolved packet length and related packet parameters (such as `burst_mode`, `burst_length`, and `packet_length`).
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
        *   Sequence: `<protocol>_<role>_<tc_id>_seq` (e.g., `<protocol>_<role>_tc_mst_001_seq`).
        *   Test: `<protocol>_<role>_<tc_id>_test` (e.g., `<protocol>_<role>_tc_mst_001_test`).
    *   **Handshake Consistency**: Ensure that negative test cases (e.g., dropping `TVALID`) are implemented via driver callbacks or sequence-item overrides if supported.

4.  **Consistency Check**: Ensure all class names, signal handles, and configuration objects are consistent across the entire generated file set.
5.  **File Generation/Update**: Use `write_to_file` for new files and `replace_file_content` for surgical updates to existing files.

## 3. Directory Structure & Serialization
- **Root Container**: The output must be written into a protocol-specific root folder within `Output/` (e.g., `Output/<protocol>_<role>_vip_tb/`), as defined in the YAML `directory_structure.root` property.
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

---

## 7. Interface Port Correctness Rules (Mandatory)

Apply these rules to every `*_if.sv` file generated or modified by this skill.

### 7.1 Clock port type — always `logic`, never `bit`
```systemverilog
// WRONG — 2-state type; X/Z map silently to 0
interface foo_if(input bit ACLK);

// CORRECT — 4-state type; propagates X/Z faithfully
interface foo_if(input logic ACLK);
```
- All clock and enable signals that arrive from outside the interface **must** use `logic`.
- `bit` is only acceptable for internal state variables that are never driven from the DUT or TB top.

### 7.2 Reset — always a port, never an internal signal
```systemverilog
// WRONG — ARESETn as an internal logic; tb_top must directly assign interface members
interface foo_if(input logic ACLK);
  logic ARESETn;          // requires tb_top to do: vif.ARESETn = reset; (multi-driver risk)

// CORRECT — ARESETn as a proper input port
interface foo_if(input logic ACLK, input logic ARESETn);
```
- Active-low reset (`ARESETn`) **must** be an `input logic` port on every interface.
- After changing the interface port signature, update every instantiation site (tb_top, any wrapper) to pass the signal as a named port connection.

### 7.3 Clocking block membership
- Clocking blocks must list `ARESETn` as `input` in the monitor clocking block only (it is never driven by the driver).
- No clocking block should list `ARESETn` as `output`.

### 7.4 After interface changes — mandatory follow-on
When any interface port list changes, this skill **must**:
1. Update the interface instantiation in the corresponding `*_tb_top.sv` to use the new port signature.
2. Update any parent system testbench/TB tops (e.g., `<protocol>_fifo_tb_top.sv`) if they instantiate the modified interface.
3. Verify that no `always_comb` or `assign` in any tb_top drives an interface signal that is now a proper port — remove those workarounds.
