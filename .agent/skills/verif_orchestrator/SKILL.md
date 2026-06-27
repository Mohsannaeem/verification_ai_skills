# Verification Orchestration & Improvement Protocol (The "Brain" Skill)

> [!IMPORTANT]
> This skill is the central nervous system of the verification agent. It MUST be invoked at the start of any complex session to determine the "State of the Union" and manage the end-to-end lifecycle.

## 0. Initialization: The Handshake
At the start of any new project or major phase, the Orchestrator **MUST** establish the context:
1.  **Ask for Protocol Name**: (e.g., AXI4, APB, I2C).
2.  **Ask for Project Role**: (e.g., Master VIP, Slave VIP, Full SoC TB).
3.  **Establish Root Context**: All subsequent work (Extraction, Planning, Synthesis) will be anchored to this `Protocol_Role` pair to ensure directory and naming consistency.

## 1. Skill Status & Requirement Matrix (The Audit)
The orchestrator tracks the health and readiness of all underlying skills:

| Skill | Status | Primary Requirement |
| :--- | :--- | :--- |
| **pdf_to_markdown** | [Ready/Missing] | Raw PDF available in `specs/`. |
| **vector_index** | [Ready/Missing] | JSON Knowledge Graph in `.agent/vector_db/`. |
| **verification_planning** | [Draft/Final] | High-density YAML plan in `verf_plan_reports/`. |
| **uvm_generator** | [Partial/Complete] | Blueprint YAML + Source Code in `Output/`. |
| **eda_yaml_generator** | [Sync/Stale] | `build.yaml` and `run.yaml` in VIP `yamls/` folder. |
| **verif_orchestrator** | [Monitoring] | This SKILL. |

## 1. System State Audit (The Sentinel Pass)
Before taking any action, the orchestrator MUST perform a multi-dimensional sweep to catalog the current progress:

1.  **Spec Extraction State**:
    - Search `.agent/vector_db/` for active indexes.
    - Check `verf_plan_reports/` for existing YAML plans.
2.  **Implementation State**:
    - List `Output/` to see which VIP components are synthesised.
    - Check `eda_buddy/run/` for active build/run manifests.
3.  **Validation State**:
    - Check `logs/` or `eda_buddy_logs/` for the latest simulation results.
    - Identify the failing testcases vs. total testcases from the plan.

## 2. Dynamic Skill Dispatcher (Decision Logic)
The Orchestrator decides the next "Best Move" based on the following hierarchy:

| Condition | Action / Skill to Invoke | Rationale |
| :--- | :--- | :--- |
| No Vector DB or stale spec | `vector_index` | Cannot plan without high-fidelity spec retrieval. |
| Vector DB exists, but no YAML plan | `verification_planning` | Must establish requirements before writing code. |
| YAML Plan version < Spec version | `verification_planning` | Plan is stale; needs "Iterative Discovery" pass. |
| YAML Plan exists, but `Output/` is empty | `uvm_generator` | Transition from blueprint to SystemVerilog. |
| SV Code exists, but misses YAML requirements | `uvm_generator` (Pass 2) | Incremental synthesis to close implementation gaps. |
| Code synthesized, but YAMLs out of sync | `eda_yaml_generator` | Synchronize build/run manifests with generated code. |
| Compilation / Simulation failures | `EDA Buddy Debug Flow` | Fix infrastructure or protocol handshake logic. |

## 3. The Gap & Improvement Lens (Self-Correction)
The Orchestrator is responsible for identifying "Low Fidelity" artifacts. For every completed task, it must ask:

### 3a. Planning Improvements:
- **Requirement Density**: Did the `verification_planning` skill hit the minimum threshold (10 REQs, 30 TCs)? If not, trigger **Pass 4 (Drill Down)**.
- **Traceability Gaps**: Are there requirements without mapped coverage groups?
- **Protocol Depth**: Did we cover negative scenarios (error injection) or only "Happy Path"?

### 3b. Implementation Improvements:
- **Synthesis Fidelity**: Do the generated SV files match the blueprint `code_snippets`?
- **Boilerplate Bloat**: Are we using macros effectively in `defines.sv` to simplify cross-component logic?
- **Logging Clarity**: Are `uvm_info` messages providing enough debug context for failures?

### 3c. Workflow Improvements:
- **Token Efficiency**: Are we reading too much? (e.g., viewing entire files when only a range is needed).
- **Tool Automation**: Could a manual step (like running a python script) be integrated into a skill?

## 3. Simulation & Execution Protocol
Since the `make` utility may be unavailable in some environments, the Orchestrator uses a direct extraction tool to run simulations:

### Technical Engine: `eda_buddy_executor.py`
Located at: `.agent/skills/verif_orchestrator/scripts/eda_buddy_executor.py`

**Usage Patterns**:
1.  **List Tests**: `python .agent/skills/verif_orchestrator/scripts/eda_buddy_executor.py --makefile eda_buddy/run/Makefile --list-tests`
2.  **Execute Build**: `python .agent/skills/verif_orchestrator/scripts/eda_buddy_executor.py --makefile eda_buddy/run/Makefile --run-target questa_build_axi_stream`
3.  **Execute Test**: `python .agent/skills/verif_orchestrator/scripts/eda_buddy_executor.py --makefile eda_buddy/run/Makefile --run-target questa_run_axi_stream_axi_stream_master_tc_mst_001_test`

## 4. Operational Loop (Prompt-Driven Execution)
The Orchestrator does not run blindly. It follows a **"Check → Prompt → Delegate"** loop:
1.  **Status Display**: Show the user the current status of all skill requirements (see Section 1).
2.  **User Prompt**: Ask the user: "The current state is [X]. Would you like to proceed with [Skill Y] or refine [Feature Z]?"
3.  **Sub-skill Prompts**: When a sub-skill (e.g., `uvm_generator`) is invoked, the Orchestrator ensures all secondary prompts (like "Review the generated code") are presented clearly and handled before transitioning to the next state.

## 5. Artifact: The Verification Roadmap
Every time the orchestrator is invoked for a major transition, it MUST generate/update a `verification_roadmap.md` in the artifacts directory. This document **MUST** use the following tabular format:

### Project Identity: [Protocol] [Role]

| Phase | Milestone | Status | Details / Path |
| :--- | :--- | :--- | :--- |
| **0. Spec** | PDF Extraction | [✅/❌] | `verf_plan_reports/spec_summary.md` |
| **1. Search**| Vector Index | [✅/❌] | `.agent/vector_db/` |
| **2. Plan** | Verification Plan| [✅/❌] | `verf_plan_reports/plan_vX.Y.yaml` |
| **3. Code** | UVM Environment | [0-100%] | `Output/` (Missing: TC_XXX, etc.) |
| **4. Sync** | EDA Buddy YAMLs | [✅/❌] | `yamls/build.yaml` |
| **5. Test** | Regressions | [Passing/Failing]| `logs/regression.log` |

### Next Steps & Gap Analysis
| Priority | Action | Skill | Target Artifact |
| :--- | :--- | :--- | :--- |
| P1 | Implement Missing Tests| `uvm_generator` | `sequences/` |
| P2 | Refresh Manifests | `eda_yaml_generator`| `yamls/` |
| P3 | Run Smoke Test | `CLI Execution` | `logs/` |
