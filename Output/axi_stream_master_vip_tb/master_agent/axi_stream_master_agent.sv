class axi_stream_master_agent extends uvm_agent;
  `uvm_component_utils(axi_stream_master_agent)

  axi_stream_master_driver    drv;
  axi_stream_master_monitor   mon;
  axi_stream_master_sequencer sqr;
  axi_stream_master_agent_config cfg;

  uvm_analysis_port#(axi_stream_master_seq_item) ap;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    
    if(!uvm_config_db#(axi_stream_master_agent_config)::get(this, "", "cfg", cfg))
      `uvm_fatal("AGT_CFG", "Agent config not found")

    mon = axi_stream_master_monitor::type_id::create("mon", this);
    
    if(cfg.is_active == UVM_ACTIVE) begin
      drv = axi_stream_master_driver::type_id::create("drv", this);
      sqr = axi_stream_master_sequencer::type_id::create("sqr", this);
    end
  endfunction

  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    ap = mon.ap;
    if(cfg.is_active == UVM_ACTIVE) begin
      drv.seq_item_port.connect(sqr.seq_item_export);
    end
  endfunction

endclass : axi_stream_master_agent
