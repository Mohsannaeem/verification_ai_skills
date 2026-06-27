// AXI-Stream Slave VIP Environment
class axi_stream_slave_vip_env extends uvm_env;
  `uvm_component_utils(axi_stream_slave_vip_env)

  axi_stream_slave_vip_agent      agent;
  axi_stream_slave_vip_scoreboard scb;
  axi_stream_slave_vip_env_config cfg;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db #(axi_stream_slave_vip_env_config)::get(this, "", "cfg", cfg)) begin
      cfg = axi_stream_slave_vip_env_config::type_id::create("cfg");
      `uvm_warning("CFG", "No env config found, using defaults")
    end

    uvm_config_db #(axi_stream_slave_vip_agent_config)::set(this, "agent", "cfg", cfg.agent_cfg);
    agent = axi_stream_slave_vip_agent::type_id::create("agent", this);

    if (cfg.enable_scoreboard)
      scb = axi_stream_slave_vip_scoreboard::type_id::create("scb", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    if (cfg.enable_scoreboard)
      agent.ap.connect(scb.slave_export);
  endfunction

endclass
