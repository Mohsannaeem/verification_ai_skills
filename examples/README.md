# Examples

This folder contains everything you need to understand the end-to-end flow —
from a raw protocol spec to a structured verification plan — before running the
AI pipeline on your own design.

```
examples/
├── spec/
│   └── simple_axi_stream_spec.md      ← Demo input: the protocol document
└── plan/
    └── verif_plan_axi_stream_master_example.yaml  ← Demo output: what the AI generates
```

---

## How to Read This Example

### Step 1 — The Input: `spec/simple_axi_stream_spec.md`

This is a simplified AXI4-Stream specification written in plain Markdown.
It covers:

| Section | What it defines |
|---------|----------------|
| Signal list | Every interface signal with width and direction |
| Handshake rules | TVALID/TREADY protocol (Rules 3.1.1–3.1.3) |
| Packet framing | TLAST assertion rules (Rules 4.1.1–4.1.2) |
| Byte qualifiers | TKEEP/TSTRB dependency (Rules 4.2.3, 4.3.1) |
| Sideband stability | TID/TDEST must hold for the full packet (Rules 5.1.1, 5.2.1) |
| Reset behavior | TVALID deassert rules (Rules 6.1–6.3) |
| Continuous streaming | Back-to-back packet rules (Rule 7.1) |

In a real run you would point the pipeline at a **PDF** of the official AMBA
specification. The `pdf_to_markdown` and `vector_index` skills handle PDF
ingestion automatically. The Markdown spec here is provided so you can read it
in GitHub without a PDF viewer.

---

### Step 2 — The Output: `plan/verif_plan_axi_stream_master_example.yaml`

This YAML is what `uvc_planning` produces. Open it to see the full plan
schema. Key sections:

| YAML key | What it contains |
|----------|-----------------|
| `uvm_environment_diagram` | Mermaid diagram of the full UVM hierarchy |
| `test_requirements` | One entry per protocol rule, with spec_ref traceability |
| `test_cases` | Directed test scenarios, each mapped to ≥1 requirement |
| `coverage_groups` | Functional coverage groups, each mapped to ≥1 requirement |
| `interface_signals` | All signals with direction relative to the Master VIP role |
| `directory_structure` | Exact filenames the UVM generator will create |

**This example is a trimmed snapshot** showing 5 requirements and 12 test cases
so it stays readable. A full production run for AXI4-Stream generates
12 requirements and 48 test cases. See [results in the main README](../README.md#end-to-end-example-axi5-stream-master-vip).

---

## What Happens Next (After the Plan)

Once the YAML plan exists, the orchestrator drives the remaining stages:

```
verif_plan_...yaml
       │
       ▼  uvc_generator
   Output/axi_stream_master_vip_tb/    ← 17-file UVM testbench (synthesized SV)
       │
       ▼  eda_yaml_generator
   yamls/build.yaml + run.yaml         ← Simulator build/run manifests
       │
       ▼  uvc_orchestrator (regression)
   logs/regression.log                 ← 48/48 PASS
```

You do not run these steps manually. Just invoke the orchestrator:

```
Run the verification orchestrator for AXI-Stream where VIP role is Master
and DUT would be Slave.
```

---

## Traceability at a Glance

Every object in the plan links to every other:

```
Spec Section (spec_ref)
    │
    └──► Test Requirement (REQ_MST_XX)
              │
              ├──► Test Case(s)    (TC_MST_XXX)  → 1 UVM sequence + 1 UVM test
              └──► Coverage Group  (cg_*)         → 1 covergroup in monitor.sv
```

No orphaned requirements (requirement with no TC or no coverage).  
No floating test cases (TC with no requirement).  
This traceability is enforced by the `uvc_planning` skill and verified during
the post-synthesis gap audit in `uvc_generator`.

---

## Trying It Yourself

1. Put your protocol PDF into a `pdfs/` folder at the repo root.
2. Start a Claude Code session in this directory.
3. Invoke the orchestrator skill and name your protocol + VIP role.
4. The agent will ask one question (verification role) and then drive the full
   pipeline — spec extraction → planning → UVM synthesis → regression.
