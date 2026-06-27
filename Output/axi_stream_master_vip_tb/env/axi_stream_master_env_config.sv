class axi_stream_master_env_config extends uvm_object;
  `uvm_object_utils(axi_stream_master_env_config)

  axi_stream_master_agent_config agent_cfg;

  function new(string name = "axi_stream_master_env_config");
    super.new(name);
    agent_cfg = axi_stream_master_agent_config::type_id::create("agent_cfg");
  endfunction

endclass : axi_stream_master_env_config
