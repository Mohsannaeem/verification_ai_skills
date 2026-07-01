#!/usr/bin/env python3
import os
import re
import sys
import argparse
import subprocess

class EDABuddyExecutor:
    def __init__(self, makefile_path):
        self.makefile_path = makefile_path
        self.root_dir = os.path.dirname(os.path.dirname(makefile_path)) # up two levels from run/Makefile
        self.run_dir = os.path.dirname(makefile_path)
        self.content = ""
        if os.path.exists(makefile_path):
            with open(makefile_path, 'r') as f:
                self.content = f.read()

    def list_tests(self, simulator="questa"):
        """
        Parses the Makefile and returns a list of tests for the specified simulator.
        Targets: <sim>_run_<comp>_<test>:
        """
        pattern = re.compile(rf'^{simulator}_run_(\w+)_(\w+):', re.MULTILINE)
        tests = []
        for match in pattern.finditer(self.content):
            comp, tname = match.groups()
            tests.append({
                "target": match.group(0).rstrip(':'),
                "component": comp,
                "test_name": tname,
                "simulator": simulator
            })
        return tests

    def get_target_commands(self, target_name):
        """
        Extracts the shell commands for a specific target.
        Handles line continuations and variable substitutions.
        """
        lines = self.content.splitlines()
        commands = []
        found = False
        target_pat = re.compile(rf'^{re.escape(target_name)}\s*:')
        # print(f"[DEBUG] Searching for pattern: {target_pat.pattern}")
        for i, line in enumerate(lines):
            clean_line = line.strip()
            if clean_line.endswith(":"):
                # Debug print for targets near the start
                # if i < 500: print(f"[DEBUG] Found potential target: '{clean_line}'")
                pass
            if target_pat.match(clean_line):
                # Check if it's a group target (has dependencies but no commands)
                target_line = line.strip()
                if ":" in target_line:
                    deps = target_line.split(":")[1].strip().split()
                    if deps:
                        # Scan for actual commands
                        j = i + 1
                        has_cmds = False
                        while j < len(lines) and (lines[j].startswith('\t') or lines[j].strip() == ''):
                            if lines[j].startswith('\t'):
                                has_cmds = True
                            j += 1
                        
                        if not has_cmds:
                            print(f"[EXECUTOR] Group target detected. Following first dependency: {deps[0]}")
                            return self.get_target_commands(deps[0])

                # Collect subsequent lines starting with tabs
                j = i + 1
                while j < len(lines) and (lines[j].startswith('\t') or lines[j].strip() == ''):
                    cmd_line = lines[j].strip()
                    if cmd_line:
                        commands.append(cmd_line)
                    j += 1
                found = True
                break

        if not found:
            return None

        # Process commands (join continuations, handle make variables)
        full_script = " ".join(commands).replace('\\ ', ' ').replace('\\', '')

        return full_script

    def run_target(self, target_name, overrides=None):
        """
        Extracts and runs the command using PowerShell.
        """
        print(f"[EXECUTOR] Extracting commands for target: {target_name}")
        script = self.get_target_commands(target_name)
        if not script:
            print(f"[ERROR] Target {target_name} not found in Makefile.")
            return False

        # Resolve Makefile variables (handles both = and := assignments)
        var_pattern = re.compile(r'^([\w]+)\s*:?=\s*(.*)$', re.MULTILINE)
        variables = dict(var_pattern.findall(self.content))
        if overrides:
            variables.update(overrides)

        def resolve_make_vars(cmd, vars_dict):
            # Multi-pass resolution handles chained refs like $(ROOT)/sub where ROOT also from Makefile
            for _ in range(5):
                new_cmd = cmd
                for k, v in vars_dict.items():
                    new_cmd = new_cmd.replace(f"$({k})", v.strip())
                if new_cmd == cmd:
                    break
                cmd = new_cmd
            return cmd

        final_script = resolve_make_vars(script, variables)
        
        # Translate Bash to PowerShell
        # 1. Remove @
        final_script = final_script.replace('@', '')
        
        # 2. Translate mkdir -p (handles one or more space-separated paths)
        def translate_mkdir(m):
            paths = m.group(1).strip().split()
            cmds = [f'New-Item -ItemType Directory -Path "{p}" -Force | Out-Null' for p in paths]
            return '; '.join(cmds) + ';'
        final_script = re.sub(r'mkdir -p ((?:[^\s;&|\\]+\s*)+?)(?=\s*(?:&&|;|\|\||\||echo|vlib|vlog|vopt|vsim|$))', translate_mkdir, final_script)
        
        # 3. Translate tee (simplified)
        # 2>&1 | tee -a <file>  ->  *>&1 | Tee-Object -FilePath <file> -Append
        final_script = final_script.replace('2>&1 | tee -a', '*>&1 | Tee-Object -Append -FilePath')
        final_script = final_script.replace('2>&1 | tee', '*>&1 | Tee-Object -FilePath')
        
        # 4. Translate && to ;
        final_script = final_script.replace('&&', '; if ($?) {')
        # Close the if blocks at the end of the script for every &&
        if_count = final_script.count('if ($?) {')
        final_script += ' }' * if_count

        # 5. Handle shell variables like $$LOGFILE
        # In Makefile they are $$, in shell they are $
        final_script = final_script.replace('$$', '$')

        # 6. Inject exported Makefile variables as PowerShell env vars so filelists expand them
        export_pat = re.compile(r'^export\s+([\w]+)', re.MULTILINE)
        env_prefix_lines = []
        for m in export_pat.finditer(self.content):
            var = m.group(1)
            if var in variables:
                val = resolve_make_vars(variables[var], variables).strip()
                env_prefix_lines.append(f'$env:{var} = "{val}"')
        if env_prefix_lines:
            final_script = '; '.join(env_prefix_lines) + '; ' + final_script

        print(f"[EXECUTOR] Executing via PowerShell in {self.run_dir}...")

        # Execute in PowerShell
        try:
            p = subprocess.Popen(['powershell', '-Command', final_script],
                               cwd=self.run_dir,
                               stdout=sys.stdout,
                               stderr=sys.stderr)
            p.wait()
            return p.returncode == 0
        except Exception as e:
            print(f"[ERROR] Failed to execute: {e}")
            return False

def run_vsim_direct(work_dir, test_name, run_yaml_path, log_path=None):
    """
    Run a single vsim test directly from run.yaml config.
    Bypasses Makefile bash conditionals — works on Windows/PowerShell.
    Returns (passed: bool, log: str).
    """
    import yaml as _yaml
    with open(run_yaml_path) as f:
        run_cfg = _yaml.safe_load(f)

    rt = run_cfg.get('runtime', {})
    common_args = ' '.join(rt.get('common_args', []))

    if log_path is None:
        os.makedirs(os.path.join(os.path.dirname(work_dir), 'logs'), exist_ok=True)
        log_path = os.path.join(os.path.dirname(work_dir), 'logs', f'{test_name}.log')

    abs_work = os.path.abspath(work_dir)
    cmd = (
        f'vsim -batch -do "run -all; quit" '
        f'-lib "{abs_work}" db_opt '
        f'+UVM_TESTNAME={test_name} -sv_seed random '
        f'{common_args}'
    )

    print(f"[VSIM] {test_name}")
    try:
        result = subprocess.run(
            ['powershell', '-Command', cmd],
            cwd=os.path.dirname(work_dir),
            capture_output=True, text=True, timeout=300
        )
        combined = result.stdout + result.stderr
        with open(log_path, 'w') as lf:
            lf.write(combined)

        passed = ('UVM_ERROR :    0' in combined and
                  'UVM_FATAL :    0' in combined and
                  result.returncode == 0)
        return passed, combined
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"


def run_regression(work_dir, run_yaml_path, log_dir=None):
    """
    Run all entry_points from run.yaml (skips bare base_test class).
    Returns (passed, failed, results_list).
    """
    import yaml as _yaml
    with open(run_yaml_path) as f:
        run_cfg = _yaml.safe_load(f)

    entry_points = run_cfg.get('test_config', {}).get('entry_points', [])
    # Skip the abstract base test — it always fatal-errors by design
    entry_points = [ep for ep in entry_points
                    if not ep['name'].endswith('_base_test')]

    if not entry_points:
        print("[ERROR] No runnable entry_points found in run.yaml")
        return 0, 0, []

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    results = []
    passed = failed = 0
    total = len(entry_points)
    print(f"[REGRESSION] {total} tests queued")
    print("=" * 70)

    for idx, ep in enumerate(entry_points, 1):
        test_name  = ep['name']
        desc       = ep.get('description', '')
        log_path   = os.path.join(log_dir, f'{test_name}.log') if log_dir else None

        print(f"[{idx:3d}/{total}] {test_name}")
        ok, log = run_vsim_direct(work_dir, test_name, run_yaml_path, log_path)

        status = "PASS" if ok else "FAIL"
        results.append({'test': test_name, 'status': status, 'desc': desc})
        if ok:
            passed += 1
        else:
            failed += 1
            # Print last 15 lines of log on failure to help diagnose
            lines = log.strip().splitlines()
            for ln in lines[-15:]:
                print(f"       {ln}")
        print(f"       --> {status}")

    return passed, failed, results


def main():
    parser = argparse.ArgumentParser(description="Direct EDA Buddy Executor")
    parser.add_argument("--makefile", required=True)
    parser.add_argument("--list-tests",     action="store_true")
    parser.add_argument("--simulator",      default="questa")
    parser.add_argument("--run-target",     help="Makefile target to execute")
    parser.add_argument("--run-test",       help="Single test name — runs vsim directly via run.yaml")
    parser.add_argument("--run-regression", action="store_true",
                        help="Run all entry_points from run.yaml (skips base_test)")
    parser.add_argument("--work-dir",       help="QuestaSim work lib directory")
    parser.add_argument("--run-yaml",       help="Path to run.yaml")
    parser.add_argument("--log-dir",        help="Directory for per-test log files (--run-regression)")
    args = parser.parse_args()

    executor = EDABuddyExecutor(args.makefile)

    if args.list_tests:
        tests = executor.list_tests(args.simulator)
        print("\nAvailable Tests:")
        print("-" * 50)
        for t in tests:
            print(f"Target: {t['target']}")
            print(f"  Test: {t['test_name']} (Component: {t['component']})")
        print("-" * 50)

    if args.run_target:
        success = executor.run_target(args.run_target)
        sys.exit(0 if success else 1)

    if args.run_test:
        if not args.work_dir or not args.run_yaml:
            print("[ERROR] --run-test requires --work-dir and --run-yaml")
            sys.exit(1)
        passed, log = run_vsim_direct(args.work_dir, args.run_test, args.run_yaml)
        lines = log.strip().splitlines()
        for ln in lines[-40:]:
            print(ln)
        print(f"\n[RESULT] {args.run_test}: {'PASS' if passed else 'FAIL'}")
        sys.exit(0 if passed else 1)

    if args.run_regression:
        if not args.work_dir or not args.run_yaml:
            print("[ERROR] --run-regression requires --work-dir and --run-yaml")
            sys.exit(1)
        passed, failed, results = run_regression(
            args.work_dir, args.run_yaml, args.log_dir)
        total = passed + failed
        print("\n" + "=" * 70)
        print(f"[REGRESSION SUMMARY]  TOTAL={total}  PASS={passed}  FAIL={failed}")
        print("=" * 70)
        for r in results:
            icon = "PASS" if r['status'] == "PASS" else "FAIL"
            print(f"  [{icon}] {r['test']}")
        print("=" * 70)
        sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
