#!/usr/bin/env python3
import os
import re
import sys
import argparse
import subprocess
from datetime import datetime

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

        # Resolve Makefile variables
        var_pattern = re.compile(r'^(\w+)\s*=\s*(.*)$', re.MULTILINE)
        variables = dict(var_pattern.findall(self.content))
        if overrides:
            variables.update(overrides)

        def resolve_make_vars(cmd, vars_dict):
            # Resolve $(VAR)
            for k, v in vars_dict.items():
                cmd = cmd.replace(f"$({k})", v)
            return cmd

        final_script = resolve_make_vars(script, variables)
        
        # Translate Bash to PowerShell
        # 1. Remove @
        final_script = final_script.replace('@', '')
        
        # 2. Translate mkdir -p
        def translate_mkdir(m):
            path = m.group(1).strip()
            return f'if (!(Test-Path "{path}")) {{ New-Item -ItemType Directory -Path "{path}" -Force | Out-Null }}'
        final_script = re.sub(r'mkdir -p ([^\s;&|]+)', translate_mkdir, final_script)
        
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

def main():
    parser = argparse.ArgumentParser(description="Direct EDA Buddy Executor")
    parser.add_argument("--makefile", required=True)
    parser.add_argument("--list-tests", action="store_true")
    parser.add_argument("--simulator", default="questa")
    parser.add_argument("--run-target", help="Target name to execute")
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

if __name__ == "__main__":
    main()
