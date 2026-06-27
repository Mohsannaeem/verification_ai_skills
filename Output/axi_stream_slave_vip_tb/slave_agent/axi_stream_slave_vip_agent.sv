// AXI-Stream Slave VIP Agent
class axi_stream_slave_vip_agent extends uvm_agent;
  `uvm_component_utils(axi_stream_slave_vip_agent)

  axi_stream_slave_vip_driver     drv;
  axi_stream_slave_vip_monitor    mon;
  axi_stream_slave_vip_sequencer  sqr;
  axi_stream_slave_vip_agent_config cfg;

  uvm_analysis_port #(axi_stream_slave_vip_seq_item) ap;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db #(axi_stream_slave_vip_agent_config)::get(this, "", "cfg", cfg)) begin
      cfg = axi_stream_slave_vip_agent_config::type_id::create("cfg");
      `uvm_warning("CFG", "No agent config found, using defaults")
    end
    uvm_config_db #(axi_stream_slave_vip_agent_config)::set(this, "*", "cfg", cfg);
    uvm_config_db #(virtual axi_stream_slave_vip_if)::set(this, "*", "vif", cfg.vif);

    if (cfg.is_active == UVM_ACTIVE) begin
      drv = axi_stream_slave_vip_driver::type_id::create("drv", this);
      sqr = axi_stream_slave_vip_sequencer::type_id::create("sqr", this);
    end
    mon = axi_stream_slave_vip_monitor::type_id::create("mon", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    if (cfg.is_active == UVM_ACTIVE)
      drv.seq_item_port.connect(sqr.seq_item_export);
    ap = mon.ap;
  endfunction

endclass
