// AXI-Stream Slave VIP Environment Configuration
class axi_stream_slave_vip_env_config extends uvm_object;
  `uvm_object_utils(axi_stream_slave_vip_env_config)

  axi_stream_slave_vip_agent_config agent_cfg;
  bit enable_scoreboard = 1;
  bit enable_coverage   = 1;

  function new(string name = "axi_stream_slave_vip_env_config");
    super.new(name);
    agent_cfg = axi_stream_slave_vip_agent_config::type_id::create("agent_cfg");
  endfunction

endclass
