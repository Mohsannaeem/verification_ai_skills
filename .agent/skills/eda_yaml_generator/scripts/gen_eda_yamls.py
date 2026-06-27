#!/usr/bin/env python3
"""
gen_eda_yamls.py — Dynamic EDA Buddy YAML Generator

Scans a UVM output directory to produce build.yaml and run.yaml,
then registers the component in project_structure.yaml.
"""
import os, re, sys, yaml, argparse

DEFAULT_PROJECT_STRUCT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..",
                 "eda_buddy", "project_structure.yaml")
)

EXCLUDE_DIRS = {"yamls", "work", "logs", "coverage", ".git", "__pycache__"}

def normalize(p): return p.replace("\\", "/")
def rel(p, root): return normalize(os.path.relpath(p, root))

# ── Directory scanner ────────────────────────────────────────────────────────

def scan_uvm_directory(root):
    results = {
        'interfaces': [], 'packages': [], 'modules': [],
        'include_dirs': set(), 'test_classes': [],
        'top_module': '', 'all_files': [], 'included_files': set()
    }
    pkg_pat   = re.compile(r'\bpackage\s+(\w+);')
    iface_pat = re.compile(r'\binterface\s+(\w+)\b')
    mod_pat   = re.compile(r'\bmodule\s+(\w+)\b')
    test_pat  = re.compile(r'\bclass\s+(\w+)\s+extends\s+uvm_test\b')
    macro_pat = re.compile(r'`AXI_STREAM_TEST_[A-Z]+\((tc_mst_\d+)')
    inc_pat   = re.compile(r'^\s*`include\s+"([^"]+)"', re.MULTILINE)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            if not f.endswith(('.sv', '.svh')): continue
            full = os.path.join(dirpath, f)
            r    = rel(full, root)
            results['all_files'].append(r)
            try:
                content = open(full, errors='ignore').read()
                for m in inc_pat.finditer(content):
                    results['included_files'].add(m.group(1))
                for m in test_pat.finditer(content):
                    results['test_classes'].append(m.group(1))
                for m in macro_pat.finditer(content):
                    results['test_classes'].append(f"axi_stream_master_{m.group(1)}_test")
            except Exception:
                pass

    for r in results['all_files']:
        full = os.path.join(root, r)
        results['include_dirs'].add(rel(os.path.dirname(full), root))
        if os.path.basename(r) in results['included_files']:
            continue
        try:
            content = open(full, errors='ignore').read()
            if pkg_pat.search(content):
                results['packages'].append(r)
            elif iface_pat.search(content):
                results['interfaces'].append(r)
            elif mod_pat.search(content):
                results['modules'].append(r)
                m = mod_pat.search(content).group(1)
                if 'tb_top' in m or 'top' in m:
                    results['top_module'] = m
        except Exception:
            pass

    results['include_dirs']  = sorted(results['include_dirs'])
    results['interfaces']    = sorted(results['interfaces'])
    results['packages']      = sorted(results['packages'])
    results['modules']       = sorted(results['modules'])
    results['test_classes']  = sorted(set(results['test_classes']))
    if not results['top_module'] and results['modules']:
        results['top_module'] = os.path.splitext(os.path.basename(results['modules'][0]))[0]
    return results

# ── Deep merge ───────────────────────────────────────────────────────────────

def deep_merge(existing, discovered):
    if isinstance(existing, dict) and isinstance(discovered, dict):
        for k, v in discovered.items():
            existing[k] = deep_merge(existing[k], v) if k in existing else v
        return existing
    if isinstance(existing, list) and isinstance(discovered, list):
        return existing + [x for x in discovered if x not in existing]
    return discovered

# ── YAML builders ────────────────────────────────────────────────────────────

def generate_build_yaml(root, data, component, existing=None):
    abs_root = normalize(os.path.abspath(root))
    discovered = {
        "project": {
            "name": os.path.basename(root),
            "top_module": data['top_module'],
            "timescale": "1ns/1ps",
            "uvm_version": "1.2",
        },
        # root_dir is the TB source root (used for filelist paths).
        # work / build / run dirs are under project_structure.yaml paths.root/<component>/
        "paths": {"root_dir": abs_root},
        "compilation": {
            "include_dirs": data['include_dirs'],
            "defines": [f"{component.upper()}_INTERFACE_V1_0", "UVM_NO_DEPRECATED"],
            "sources": {
                "interfaces": data['interfaces'],
                "packages":   data['packages'],
                "modules":    data['modules'],
                "dut": []
            }
        },
        "tool_settings": {
            "vcs": {
                "compile_flags":  ["-sverilog", "-full64", "-debug_access+all", "-lca", "-kdb", "+v2k"],
                "elaborate_flags": ["-top ${project.top_module}"],
                "coverage_flags":  ["-cm line+cond+fsm+tgl+path"]
            },
            "questa": {
                "compile_flags":  ["-sv", "-mfcu", "-timescale", "1ns/1ps"],
                "elaborate_flags": ["vopt +acc ${project.top_module} -o db_opt"],
                "coverage_flags":  ["-coverage"]
            }
        },
        # Hooks run before/after compile+elaborate for this component only.
        "hooks": {"pre": "", "post": ""},
    }
    if existing:
        merged = deep_merge(existing, discovered)
        merged["compilation"]["include_dirs"] = data['include_dirs']
        merged["compilation"]["sources"]      = discovered["compilation"]["sources"]
        merged["paths"]["root_dir"]           = abs_root
        return merged
    return discovered

def generate_run_yaml(test_list, existing=None):
    entry_points = [{"name": t, "description": f"Test: {t}", "seed": "random", "user_args": []}
                    for t in test_list]
    discovered = {
        "runtime": {
            "common_args": [
                "+UVM_VERBOSITY=UVM_MEDIUM",
                "+UVM_MAX_QUIT_COUNT=10",
                # 100,000,000 ps = 100 µs (timescale 1ns/1ps → $time in ps)
                "+UVM_TIMEOUT=100000000",
            ],
            "tool_args": {
                "vcs":   ["-l simv.log"],
                "questa": ["-batch", "-do 'run -all; quit'"]
            },
            "debug": {"gui_mode": False, "dump_waves": True, "wave_format": "fsdb", "quiet_sim": False}
        },
        "test_config": {
            "active_test":  test_list[0] if test_list else "",
            "entry_points": entry_points
        },
        "groups": {
            "smoke_test": [test_list[0]] if test_list else [],
            "regression": test_list[1:] if len(test_list) > 1 else []
        },
        # Hooks run before/after each simulation for this component only.
        "hooks": {"pre": "", "post": ""},
    }
    if existing:
        merged = deep_merge(existing, discovered)
        existing_names = {ep['name'] for ep in merged["test_config"]["entry_points"]}
        for ep in entry_points:
            if ep['name'] not in existing_names:
                merged["test_config"]["entry_points"].append(ep)
        merged["groups"]["regression"] = sorted(
            set(merged["groups"].get("regression", []) + test_list))
        return merged
    return discovered

# ── project_structure.yaml registration ─────────────────────────────────────

def register_component(struct_path, comp, build_path, run_path):
    """Add or update the component entry in project_structure.yaml."""
    if not os.path.exists(struct_path):
        print(f"[WARN] project_structure.yaml not found at {struct_path} — skipping registration")
        return
    with open(struct_path) as f:
        data = yaml.safe_load(f) or {}

    components = data.get('components', [])
    names = [c['name'] for c in components]
    entry = {
        'name':        comp,
        'build_cfg':   normalize(os.path.abspath(build_path)),
        'runtime_cfg': normalize(os.path.abspath(run_path))
    }
    if comp in names:
        components[names.index(comp)] = entry
    else:
        components.append(entry)

    data['components'] = components
    with open(struct_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"[GEN] Registered '{comp}' in {struct_path}")

# ── Write helper ─────────────────────────────────────────────────────────────

def write_yaml(path, data, header):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(f"# {header}\n")
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"[GEN] Written: {path}")

# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Dynamic EDA YAML Generator")
    parser.add_argument("--output-dir",        required=True,  help="TB root directory to scan")
    parser.add_argument("--component",         required=False, help="Component name (defaults to dir basename)")
    parser.add_argument("--project-structure", default=DEFAULT_PROJECT_STRUCT,
                        help="Path to eda_buddy/project_structure.yaml")
    args = parser.parse_args()

    root = os.path.abspath(args.output_dir)
    if not os.path.isdir(root):
        print(f"[FATAL] Directory not found: {root}")
        sys.exit(1)

    comp      = args.component or os.path.basename(root).replace("_vip_tb", "")
    yamls_dir = os.path.join(root, "yamls")
    build_path = os.path.join(yamls_dir, f"{comp}_build.yaml")
    run_path   = os.path.join(yamls_dir, f"{comp}_run.yaml")

    ex_build = yaml.safe_load(open(build_path)) if os.path.exists(build_path) else None
    ex_run   = yaml.safe_load(open(run_path))   if os.path.exists(run_path)   else None

    print(f"[STATUS] Scanning: {root}")
    fs_data    = scan_uvm_directory(root)
    build_data = generate_build_yaml(root, fs_data, comp, ex_build)
    run_data   = generate_run_yaml(fs_data['test_classes'], ex_run)

    write_yaml(build_path, build_data, "EDA Buddy Build Manifest (Auto-Generated)")
    write_yaml(run_path,   run_data,   "EDA Buddy Runtime Config (Auto-Generated)")

    # Register this component in project_structure.yaml
    register_component(args.project_structure, comp, build_path, run_path)

    print("\n[DONE] Scan complete.")
    print(f"  Top module    : {fs_data['top_module']}")
    print(f"  Include dirs  : {', '.join(fs_data['include_dirs'])}")
    print(f"  Test classes  : {len(fs_data['test_classes'])}")
    print(f"  [!] Review    : {yamls_dir}")

if __name__ == "__main__":
    main()
