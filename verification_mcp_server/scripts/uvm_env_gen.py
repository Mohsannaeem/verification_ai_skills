import os
import yaml
import re

def translate_to_sv(text, prefix, signals):
    """Expert translation of pseudo-code to SystemVerilog."""
    lines = text.split('\n')
    sv_lines = []
    
    sig_names = [s['name'] for s in signals]
    reset_sig = next((s for s in sig_names if s.lower() == 'aresetn' or s.lower().endswith('_n')), 'ARESETn')
    is_active_low = reset_sig.lower().endswith('n')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.startswith('-'): line = line[1:].strip()
        
        # 1. Handshake patterns
        if "Wait for" in line and "TREADY" in line:
            sv_lines.append(f"    while(!vif.{prefix}_if.TREADY) @(posedge vif.{prefix}_if.ACLK);")
        elif "Wait for" in line and "ARESET" in line:
            if is_active_low:
                sv_lines.append(f"    wait(vif.{prefix}_if.{reset_sig} == 1); // Wait for reset deassertion")
            else:
                sv_lines.append(f"    wait(vif.{prefix}_if.{reset_sig} == 0); // Wait for reset deassertion")
        elif "Wait for" in line and "ACLK" in line:
            match = re.search(r"(\d+)", line)
            count = match.group(1) if match else "1"
            sv_lines.append(f"    repeat({count}) @(posedge vif.{prefix}_if.ACLK);")
        
        # 2. Driving patterns
        elif "Drive" in line:
            found_sigs = [s for s in sig_names if s in line]
            if found_sigs:
                for s in found_sigs:
                    sv_lines.append(f"    vif.{prefix}_if.{s} <= req.{s};")
            else:
                sv_lines.append(f"    // TODO: Implement expert Drive logic for: {line}")
        
        # 3. UVM Handshake
        elif "Get item" in line:
            sv_lines.append(f"    seq_item_port.get_next_item(req);")
        elif "Signal item_done" in line:
            sv_lines.append(f"    seq_item_port.item_done();")
            
        # 4. Parity
        elif "Calculated Odd Parity" in line:
            sv_lines.append(f"    vif.{prefix}_if.TDATACHK = ~(^req.tdata); // Odd parity calculation")
            
        # 5. Throughput/Burst logic
        elif "Burst of" in line:
            match = re.search(r"(\d+)", line)
            count = match.group(1) if match else "10"
            sv_lines.append(f"    repeat({count}) begin")
            sv_lines.append(f"        // Sequence execution logic")
            sv_lines.append(f"    end")
            
        # Fallback
        else:
            sv_lines.append(f"    // {line}")
            
    return "\n".join(sv_lines)

def generate_uvm_env(yaml_path, template_dir, output_dir):
    if not os.path.exists(yaml_path):
        return f"Error: YAML file not found at {yaml_path}"
    if not os.path.exists(template_dir):
        return f"Error: Template directory not found at {template_dir}"

    with open(yaml_path, 'r') as f:
        plan = yaml.safe_load(f)

    protocol_raw = plan.get('protocol_version', 'protocol')
    protocol = protocol_raw.lower().replace('-', '_')
    role = plan.get('verification_role', 'role').lower()
    prefix = f"{protocol}_{role}"
    
    templates = {}
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.sv') or file == 'Makefile':
                templates[file] = os.path.join(root, file)

    os.makedirs(output_dir, exist_ok=True)
    results = []

    # 1. Generate Interface
    signals = plan.get('interface_signals', [])
    if signals:
        if_content = f"interface {prefix}_if(input bit ACLK, input bit ARESETn);\n"
        for sig in signals:
            width = sig.get('width', '1')
            if_content += f"  logic [{width}-1:0] {sig['name']};\n"
        if_content += "endinterface\n"
        if_path = os.path.join(output_dir, f"{prefix}_if.sv")
        with open(if_path, 'w') as f:
            f.write(if_content)
        results.append(f"Generated Interface: {if_path}")

    # 2. Generate Makefile
    if 'Makefile' in templates:
        with open(templates['Makefile'], 'r') as f:
            mk_content = f.read()
        mk_content = mk_content.replace('dummy_', f'{prefix}_')
        mk_content = mk_content.replace('DUMMY_UVM', '.')
        mk_content = mk_content.replace('tb_cuboid_prcr', f'{prefix}_tb_top')
        mk_path = os.path.join(output_dir, 'Makefile')
        with open(mk_path, 'w') as f:
            f.write(mk_content)
        results.append(f"Generated Makefile: {mk_path}")

    dir_struct = plan.get('directory_structure', {})
    folders = dir_struct.get('folders', [])
    code_snippets = {s['title'].split(' ')[0]: s['code'] for s in plan.get('code_snippets', [])}

    for folder_obj in folders:
        for folder_name, file_list_str in folder_obj.items():
            folder_path = os.path.join(output_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            files_to_gen = [f.strip() for f in file_list_str.split(',')]
            
            for target_file in files_to_gen:
                template_file = None
                if 'driver' in target_file: template_file = 'dummy_driver.sv'
                elif 'monitor' in target_file: template_file = 'dummy_monitor.sv'
                elif 'sequencer' in target_file: template_file = 'dummy_sequencer.sv'
                elif 'agent_config' in target_file: template_file = 'dummy_agent_config.sv'
                elif 'env_config' in target_file: template_file = 'dummy_env_config.sv'
                elif 'env.sv' in target_file: template_file = 'dummy_env.sv'
                elif 'seq_item' in target_file: template_file = 'dummy_seq_item.sv'
                elif 'base_seq' in target_file: template_file = 'dummy_base_sequence.sv'
                elif 'burst_seq' in target_file: template_file = 'dummy_base_sequence.sv' # fallback
                elif 'test.sv' in target_file: template_file = 'dummy_base_test.sv'
                elif 'tb_top' in target_file: template_file = 'dummy_tb_top.sv'
                elif 'scoreboard' in target_file: template_file = 'dummy_scoreboard.sv'
                elif 'callback' in target_file: template_file = 'dummy_callback.sv'
                elif 'defines' in target_file: template_file = 'dummy_defines.sv'
                elif '_pkg.sv' in target_file: 
                    if 'env' in target_file: template_file = 'dummy_env_pkg.sv'
                    elif 'seq' in target_file: template_file = 'dummy_seq_pkg.sv'
                    elif 'test' in target_file: template_file = 'dummy_test_pkg.sv'
                elif 'agent' in target_file: template_file = 'dummy_agent.sv'

                if not template_file or template_file not in templates:
                    template_file = 'dummy_agent.sv' if 'agent' in target_file else None
                
                if template_file in templates:
                    with open(templates[template_file], 'r') as f:
                        content = f.read()
                    
                    content = content.replace('dummy_', f'{prefix}_')
                    content = content.replace('DUMMY_', f'{prefix.upper()}_')
                    
                    if target_file in code_snippets:
                        snippet = code_snippets[target_file]
                        if 'METHODS & LOGIC:' in snippet:
                            logic = snippet.split('METHODS & LOGIC:')[1].strip()
                            logic_sv = translate_to_sv(logic, prefix, signals)
                            
                            # Replace logic blocks
                            if 'task run_phase' in content:
                                content = re.sub(r'(task run_phase\(uvm_phase phase\);.*?super\.run_phase\(phase\);)(.*?)(endtask)', 
                                               r'\1\n' + logic_sv + r'\n  \3', content, flags=re.DOTALL)
                            elif 'task body' in content:
                                content = re.sub(r'(task body\(.*?\);)(.*?)(endtask)', 
                                               r'\1\n' + logic_sv + r'\n  \3', content, flags=re.DOTALL)
                            elif 'function void write_master' in content:
                                content = re.sub(r'(function void write_master\(.*?\);)(.*?)(endfunction)', 
                                               r'\1\n' + logic_sv + r'\n  \3', content, flags=re.DOTALL)
                            elif '// LOGIC_START' in content:
                                content = re.sub(r'// LOGIC_START.*?// LOGIC_END', f'// LOGIC_START\n{logic_sv}\n    // LOGIC_END', content, flags=re.DOTALL)

                    if template_file == 'dummy_seq_item.sv':
                        members_sv = ""
                        for sig in signals:
                            if sig['name'] not in ['ACLK', 'ARESETn']:
                                members_sv += f"  rand bit [{sig['width']}-1:0] {sig['name']};\n"
                        content = re.sub(r'(-- Interface, port, fields)', r'\1\n' + members_sv, content)

                    target_path = os.path.join(folder_path, target_file)
                    with open(target_path, 'w') as f:
                        f.write(content)
                    results.append(f"Synthesized: {target_path}")
                else:
                    results.append(f"Warning: No template for {target_file}")

    return "\n".join(results)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: uvm_env_gen.py <yaml_path> <template_dir> <output_dir>")
    else:
        print(generate_uvm_env(sys.argv[1], sys.argv[2], sys.argv[3]))
