import subprocess
import json
import os
import sys

# Configuration
MIN_PASS_SCORE = 85.0
LATEST_PLAN = "d:/Verification/VERIFICATION_PLANNER/verf_plan_reports/verif_plan_axi4_stream_v5_0.yaml"
GRADING_ENGINE = "d:/Verification/VERIFICATION_PLANNER/.agent/skills/uvc_planning/grading/grading_engine.py"

def run_grading_test():
    print(f"--- Verification Planning Skill Grading Suite ---")
    print(f"Target Plan: {LATEST_PLAN}\n")

    if not os.path.exists(LATEST_PLAN):
        print(f"[ERROR] Target plan not found at {LATEST_PLAN}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, GRADING_ENGINE, LATEST_PLAN],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"[ERROR] Grading engine failed: {result.stderr}")
            return False

        report = json.loads(result.stdout)
        score = report.get('total_score', 0)
        
        print(f"FINAL SCORE: {score}%")
        print(f"Breakdown: {json.dumps(report.get('breakdown'), indent=2)}")
        
        if report.get('logs'):
            print("\nAdvisory Logs:")
            for log in report['logs']:
                print(f"  {log}")

        if score >= MIN_PASS_SCORE:
            print(f"\n[PASS] Skill performance exceeds threshold ({MIN_PASS_SCORE}%).")
            return True
        else:
            print(f"\n[FAIL] Skill performance below quality threshold ({MIN_PASS_SCORE}%).")
            return False

    except Exception as e:
        print(f"[ERROR] Unexpected test failure: {e}")
        return False

if __name__ == "__main__":
    success = run_grading_test()
    sys.exit(0 if success else 1)
