import yaml
import sys
import json
import os

class FinalEnterpriseGrader:
    def __init__(self, target_path, golden_path):
        self.target_path = target_path
        self.golden_path = golden_path
        self.scores = {}
        self.logs = []
        self.target_data = None
        self.golden_data = None

    def load_plans(self):
        try:
            with open(self.target_path, 'r') as f:
                self.target_data = yaml.safe_load(f)
            with open(self.golden_path, 'r') as f:
                self.golden_data = yaml.safe_load(f)
            return True
        except: return False

    def grade_enterprise_readiness(self):
        """Checks for high-value modules. No Neg/Perf = Immediate Failure."""
        modules = ['negative_scenarios', 'performance_metrics', 'coverage_groups']
        score = 0
        for mod in modules:
            if mod in self.target_data and len(self.target_data[mod]) >= 3:
                score += 33.3
            else:
                self.logs.append(f"[CRITICAL] Missing/Thin Enterprise Module: {mod}")
        
        self.scores['enterprise_modules'] = round(min(100, score), 2)

    def grade_golden_mapping(self):
        """Checks for ID and naming symmetry."""
        g_ids = [r.get('id') for r in self.golden_data.get('test_requirements', [])]
        t_ids = [r.get('id') for r in self.target_data.get('test_requirements', [])]
        
        matches = sum(1 for gid in g_ids if gid in t_ids)
        self.scores['golden_mapping'] = round((matches / len(g_ids)) * 100, 2)

    def grade_technical_density(self):
        """Grades based on word-count and signal precision."""
        reqs = self.target_data.get('test_requirements', [])
        signals = self.target_data.get('interface_signals', [])
        
        # Word count density (Target 50 words)
        avg_words = sum(len(r.get('description', '').split()) for r in reqs) / len(reqs) if reqs else 0
        density_score = min(100, (avg_words / 50) * 100)
        
        # Signal precision (Check for parameter usage)
        has_params = any("WIDTH" in str(s.get('width', '')) for s in signals)
        signal_score = 100 if has_params else 20
        
        self.scores['technical_density'] = round((density_score + signal_score) / 2, 2)
        if density_score < 40:
            self.logs.append(f"[FAIL] Shallow Requirement Content ({avg_words:.1f} words/req).")

    def get_results(self):
        self.grade_enterprise_readiness()
        self.grade_golden_mapping()
        self.grade_technical_density()
        
        total = sum(self.scores.values()) / len(self.scores)
        return {"total_score": round(total, 2), "breakdown": self.scores, "logs": self.logs}

if __name__ == "__main__":
    t_p = sys.argv[1]
    g_p = "d:/Verification/VERIFICATION_PLANNER/.agent/skills/uvc_planning/grading/golden_data/golden_axi_stream_plan.yaml"
    
    grader = FinalEnterpriseGrader(t_p, g_p)
    if grader.load_plans():
        print(json.dumps(grader.get_results(), indent=2))
    else: print("Error loading")
