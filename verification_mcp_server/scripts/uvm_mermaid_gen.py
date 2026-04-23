import sys

def generate_mermaid(dut_role, protocol="AXI", has_config=True, has_scoreboard=True):
    """
    Generates a Mermaid TD diagram for a UVM environment.
    dut_role: The role of the VIP/Agent (Master or Slave).
              The DUT is always the OPPOSITE role.
    """
    vip_role  = dut_role.capitalize()
    # DUT is opposite of the VIP role
    dut_label = "DUT Slave Receiver" if vip_role == "Master" else "DUT Master Transmitter"
    p = protocol.lower()

    lines = []
    lines.append("graph TD")

    # Style classes
    lines.append("    classDef test_layer  fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#7b1fa2;")
    lines.append("    classDef test_obj    fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,stroke-dasharray: 5 5,color:#7b1fa2;")
    lines.append("    classDef env_layer   fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#1565c0;")
    lines.append("    classDef env_obj     fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,stroke-dasharray: 5 5,color:#1565c0;")
    lines.append("    classDef agent_layer fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#00695c;")
    lines.append("    classDef agent_obj   fill:#e0f2f1,stroke:#00695c,stroke-width:2px,stroke-dasharray: 5 5,color:#00695c;")
    lines.append("    classDef dut_layer   fill:#fff8e1,stroke:#f57f17,stroke-width:2px,color:#f57f17;")
    lines.append("")

    # ── Test Layer ──────────────────────────────────────────────────────────
    lines.append("    subgraph UVM_Test_Layer [uvm_test]")
    if has_config:
        lines.append(f"        Test_Cfg[{p}_test_config]:::test_obj")
    lines.append(f"        SeqItem[{p}_seq_item]:::test_obj")
    lines.append(f"        Seq[{p}_sequence]:::test_obj")

    # ── Env Layer ────────────────────────────────────────────────────────────
    lines.append("        subgraph Env_Layer [uvm_env]")
    if has_scoreboard:
        lines.append(f"            Scoreboard[{p}_scoreboard]:::env_layer")
    if has_config:
        lines.append(f"            Env_Cfg[{p}_env_config]:::env_obj")

    # ── Agent Layer ──────────────────────────────────────────────────────────
    lines.append(f"            subgraph Agent_Layer [{vip_role} Agent]")
    lines.append(f"                Sequencer[{p}_sequencer]:::agent_layer")
    if has_config:
        lines.append(f"                Agent_Cfg[{p}_agent_config]:::agent_obj")
    lines.append(f"                Driver[{p}_driver]:::agent_layer")
    lines.append(f"                Monitor[{p}_monitor]:::agent_layer")
    lines.append(f"                Callback[{p}_callback]:::agent_obj")
    lines.append("                Sequencer --> Driver")
    lines.append("                Callback --> Driver")
    if has_config:
        # Anchor agent_config inside agent subgraph
        lines.append("                Agent_Cfg --> Sequencer")
    lines.append("            end")   # Agent
    if has_config and has_scoreboard:
        # Anchor env_config inside env by connecting it to scoreboard 
        lines.append("            Env_Cfg --> Scoreboard")
    lines.append("        end")       # Env
    if has_config:
        # Keep test_config anchored to Seq inside Test subgraph
        lines.append("        Test_Cfg --> Seq")
    lines.append("        SeqItem --> Seq")
    lines.append("    end")           # Test
    lines.append("")

    # ── Cross-layer stimulus edge ────────────────────────────────────────────
    lines.append("    Seq --> Sequencer")

    # ── Hardware Top ─────────────────────────────────────────────────────────
    lines.append("    subgraph Top_Level [Hardware Top]")
    lines.append("        VIF[Virtual Interface]:::dut_layer")
    lines.append(f"        DUT[{dut_label}]:::dut_layer")
    lines.append("        VIF <--> DUT")
    lines.append("    end")
    lines.append("")

    # ── Interface connections ─────────────────────────────────────────────────
    lines.append("    Driver  --- VIF")
    lines.append("    Monitor --- VIF")
    if has_scoreboard:
        lines.append("    Monitor --> Scoreboard")

    # ── Class assignments ─────────────────────────────────────────────────────
    lines.append("    class UVM_Test_Layer test_layer;")
    lines.append("    class Env_Layer env_layer;")
    lines.append("    class Agent_Layer agent_layer;")
    lines.append("    class Top_Level dut_layer;")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            arg = sys.argv[1].lower()
            role     = "slave" if "slave" in arg else "master"
            protocol = "apb" if "apb" in arg else "axi"
            print(generate_mermaid(dut_role=role, protocol=protocol))
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(generate_mermaid("Master"))
