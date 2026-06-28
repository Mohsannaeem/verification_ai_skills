---
description: Comprehensive workflow for generating a verification plan from a specification using grep and structured data.
---

# Verification Planning Workflow

This workflow automates the process of extracting requirements from a Markdown specification and generating a structured verification plan, complete with UVM architecture diagrams and functional coverage goals.

## Steps

1. **Select Specification**
   - Identify the target Markdown file.

2. **Iterative Extraction** // turbo
   - **Grep & Context**: Find requirements, signals, and potential coverage points.
   - **Refine**: Use `sed` and back-and-forth context fetching.

3. **Define Architecture & Configurations**
   - **Configuration Phase**: Identify all **Protocol Configurations** (OoO, Burst types, Sidebands).
   - **Diagram Phase**: Create a **Mermaid diagram** of the UVM environment.
   - **Coverage Phase**: Identify **Functional Coverage Groups** and specific bins.
   - **Requirements Phase**: Define Test Requirements (Features).
   - **Test Case Phase**: Map Test Cases to Requirements (N:M).

4. **Generate YAML Plan**
   - Create `verification_plan.yaml` containing:
     - `uvm_environment_diagram`.
     - `configurations` (OoO, Burst types, etc.).
     - `test_requirements`.
     - `test_cases`.
     - `coverage_groups`.
     - `interface_signals`.
     - `directory_structure`.

5. **Convert to PDF** // turbo
   - Invoke `convert_plan_to_pdf` to generate the final report.
