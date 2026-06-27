# UVM Pseudo-Code Generation Guidelines (Sub-Prompt)

## 0. Objective
This sub-prompt provides the rules for generating **Architectural Blueprints** in pseudo-code format. These snippets are NOT direct SystemVerilog code, but structured descriptions of members, methods, and connectivity that the "UVM Agent" will use to write the final HDL source.

## 1. Output Format: The "Architecture Blueprint"
All items in the `code_snippets` array MUST follow this structured text format instead of direct code writing:

```text
COMPONENT: <ComponentName>
EXTENDS: <BaseUvmClass>
CONFIG_REF: <ConfigObjectName> (Source: ConfigDB)
MEMBERS:
  - [Type] [Name] ([Properties: rand, static, etc.])
METHODS & LOGIC:
  - build_phase: [Logical steps for object creation and config retrieval]
  - connect_phase: [Explicit port/export connection mapping]
  - run_phase / body: [Textual description of the core algorithm or handshake]
```

## 2. Structural Requirements by Component

### A. Global Defines (`_defines.sv`)
- **BLUEPRINT**: List all `parameter` names and their intended mappings to spec-defined widths (Reference: `defines.sv` logic).

### B. Sequence Item (`_seq_item.sv`)
- **MEMBERS**: Explicitly list every signal from the `interface_signals` table.
- **CONSTRAINTS**: Describe the mathematical bounds (e.g., "delay must be between 0 and 15 cycles").

### C. Configuration Objects (`_config.sv`)
- **MEMBERS**:
  - `virtual interface` handle.
  - `is_active` (UVM_ACTIVE/PASSIVE).
  - Protocol specific knobs (e.g., `enable_parity`, `depth_limit`).

### D. Driver & Monitor
- **MEMBERS**: Reference the Local Virtual Interface handle and Configuration Object.
- **LOGIC**: 
  - **Driver**: Describe the "Request-Response" loop with the Sequencer and the physical pin-toggling logic.
  - **Monitor**: Describe the "Observation" loop, valid-sampling triggers, and analysis port broadcasting.

### E. Agent (`_agent.sv`)
- **MEMBERS**: Instances of Driver, Sequencer, and Monitor.
- **CONNECTIVITY**: Explicitly describe the port-to-export connection for the transaction flow.

### F. Scoreboard (`_scoreboard.sv`)
- **MEMBERS**: Analysis exports for Monitor connection, Reference Model (Queue/Assoc Array), Comparison Logic.
- **LOGIC**: Describe the `write` function behavior (sampling) and the `check_phase` logic (comparison against reference).

### G. Base & Virtual Sequences (`_seq.sv`)
- **MEMBERS**: Sequence item handle, randomization constraints.
- **LOGIC**: Describe the `body()` task lifecycle: `start_item`, `finish_item`, and response handling.

## 3. Formatting & Policy
- **TOTAL ENUMERATION**: Every file listed in the `directory_structure` MUST have a corresponding `code_snippets` entry.
- **NO DIRECT SV CODE**: DO NOT write actual SystemVerilog syntax (no `class`, `function new`, `endclass`).
- **STRICT NAMING**: Ensure all identifiers follow the `<interface>_<role>_<type>` convention.
- **TRACEABILITY**: Ensure every member in the blueprint corresponds to a feature or signal defined earlier in the YAML plan.
