---
name: eda_yaml_generator
description: Generates build.yaml and run.yaml for a UVM TB directory, then registers the component in project_structure.yaml.
---

# EDA YAML Generator

Scans a UVM output directory, produces `build.yaml` + `run.yaml`, and registers the component in `eda_buddy/project_structure.yaml`.

> **Golden File Rule**: Existing YAMLs are deep-merged — user-added tool flags and sim args are preserved.  
> **User Review**: Always ask the user to review generated YAMLs before running simulation.

## Path Convention

| Field | Location |
|---|---|
| `build.yaml paths.root_dir` | TB source root — used only for filelist source paths |
| work / build / run dirs | `project_structure.yaml paths.root/<component>/` — owned by EDA Buddy |
| `+UVM_TIMEOUT` | `100000000` ps = 100 µs (timescale 1ns/1ps — `$time` is in ps, not ns) |

## Usage

```bash
python .agent/skills/eda_yaml_generator/scripts/gen_eda_yamls.py \
    --output-dir     <abs_path_to_tb_root>           \
    --component      <name>                           \
    --project-structure eda_buddy/project_structure.yaml
```

Outputs written to `<output-dir>/yamls/`:
- `<component>_build.yaml` — include dirs, source files, tool compile/elab flags
- `<component>_run.yaml`   — test entry points, UVM args, regression groups
- Component entry added/updated in `project_structure.yaml`

After generation, regenerate the Makefile:
```bash
python eda_buddy/eda_buddy.py --gen-makefile
```

## What the script does

1. Walks `<output-dir>` (skips `yamls/`, `work/`, `logs/`) and classifies `.sv/.svh` files as packages / interfaces / modules via content regex.
2. Discovers test classes via `class X extends uvm_test` and `` `AXI_STREAM_TEST_* `` macros.
3. Deep-merges into existing YAMLs — source lists refresh, tool flags survive.
4. Registers the component in `project_structure.yaml` (adds if new, updates if present).

## Validation rules

- Every `uvm_test` subclass found in the directory must appear in `run.yaml test_config.entry_points`.
- All filelist paths must resolve to existing files (`root_dir` + relative path).
- `build.yaml` must not contain `work_dir`, `log_dir`, or `cov_dir` — those are EDA Buddy's responsibility.
