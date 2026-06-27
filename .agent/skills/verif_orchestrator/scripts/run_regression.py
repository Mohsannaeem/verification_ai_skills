#!/usr/bin/env python3
import os
import subprocess
import sys
from datetime import datetime

TESTS = [f"axi_stream_master_tc_mst_{i:03d}_test" for i in range(1, 28)]
BASE_CMD = (
    "vsim -c -batch -do 'run -all; quit' "
    "-lib D:/Verification/VERIFICATION_PLANNER/eda_buddy/run/logs/build/axi_stream/work db_opt "
    "+UVM_MAX_QUIT_COUNT=10 +UVM_TIMEOUT=15000000 -sv_seed random"
)

def run_test(test_name):
    print(f"[REGRESSION] Running {test_name}...")
    cmd = f"{BASE_CMD} +UVM_TESTNAME={test_name}"
    
    start_time = datetime.now()
    try:
        process = subprocess.Popen(['powershell', '-Command', cmd], 
                                   cwd="d:/Verification/VERIFICATION_PLANNER/eda_buddy/run",
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   text=True)
        stdout, stderr = process.communicate()
        duration = (datetime.now() - start_time).total_seconds()
        
        # Check for UVM_ERROR or UVM_FATAL in output
        passed = "UVM_ERROR :    0" in stdout and "UVM_FATAL :    0" in stdout
        if process.returncode != 0:
            passed = False
            
        return {
            "name": test_name,
            "status": "PASS" if passed else "FAIL",
            "duration": f"{duration:.1f}s",
            "log": stdout
        }
    except Exception as e:
        return {
            "name": test_name,
            "status": "ERROR",
            "duration": "0s",
            "log": str(e)
        }

def main():
    results = []
    print("=" * 60)
    print(f"STARTING REGRESSION AT {datetime.now()}")
    print("=" * 60)
    
    for t in TESTS:
        res = run_test(t)
        results.append(res)
        print(f"Result: {res['status']} ({res['duration']})")
        
    print("\n" + "=" * 60)
    print("REGRESSION SUMMARY")
    print("-" * 60)
    print(f"{'Test Case':<40} | {'Status':<10} | {'Time':<10}")
    print("-" * 60)
    passes = 0
    for r in results:
        print(f"{r['name']:<40} | {r['status']:<10} | {r['duration']:<10}")
        if r['status'] == "PASS":
            passes += 1
    print("-" * 60)
    print(f"FINAL SCORE: {passes}/{len(TESTS)} PASSED")
    print("=" * 60)

if __name__ == "__main__":
    main()
