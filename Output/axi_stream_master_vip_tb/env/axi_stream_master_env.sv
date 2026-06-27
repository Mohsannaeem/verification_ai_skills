class axi_stream_master_env extends uvm_env;
  `uvm_component_utils(axi_stream_master_env)

  axi_stream_master_agent      agent;
  axi_stream_master_scoreboard scb;
  axi_stream_master_env_config cfg;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    
    if(!uvm_config_db#(axi_stream_master_env_config)::get(this, "", "cfg", cfg))
      `uvm_fatal("ENV_CFG", "Environment config not found")

    agent = axi_stream_master_agent::type_id::create("agent", this);
    scb   = axi_stream_master_scoreboard::type_id::create("scb", this);
    
    // Pass agent config from env config
    uvm_config_db#(axi_stream_master_agent_config)::set(this, "agent*", "cfg", cfg.agent_cfg);
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    agent.ap.connect(scb.master_export);
  endfunction

endclass : axi_stream_master_env
