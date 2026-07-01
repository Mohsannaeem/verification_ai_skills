---
name: coding_guideline
description: UVM SystemVerilog coding guidelines, focusing on strict UVM verbosity levels and logging standards.
---

# UVM Coding Guidelines

This sub-skill establishes the coding rules and guidelines to be adhered to during UVM verification code generation, modification, and review.

## 1. UVM Verbosity Standards

Report verbosity must be strictly controlled to prevent log bloat while providing complete diagnostic tracing during debug. SystemVerilog code generators and developers MUST map logging messages to the following verbosity levels:

| Level | Value | Usage Recommendation / Target Scenario |
| :--- | :--- | :--- |
| **`UVM_NONE`** | `0` | **Unconditional messages.** Keep reserved for fatal errors, major test configuration banners, or mandatory compliance/sign-off logs. These cannot be disabled. |
| **`UVM_LOW`** | `100` | **High-level simulation flow.** Major milestones, `uvm_test` starts, phase changes, and major DUT reset events. |
| **`UVM_MEDIUM`** | `200` | **Default logging.** standard testbench tracking (e.g., transactions entering a scoreboard, basic monitor activity). |
| **`UVM_HIGH`** | `300` | **Moderate debugging.** Detailed bus transactions or internal component state changes that are only needed when investigating failures. |
| **`UVM_FULL`** | `400` | **Deep debugging.** Cycle-by-cycle signal toggles, internal FIFO/queue pushes/pops, or intricate protocol tracing. |
| **`UVM_DEBUG`** | `500` | **UVM Library debug.** Intended exclusively for debugging the UVM package base classes. *Avoid using this for user-level verification code.* |

### Logging Constraints & Rules

1. **Enum Enforcement**: Always use the UVM symbolic enum constants (`UVM_NONE`, `UVM_LOW`, etc.) instead of raw integers.
2. **Diagnostic Quality**: Check-points, handshakes, and packet state logs must verify correct parameter bounds and display clear trace markers.
