////////////////////////////////////////////////////////////////////////
// Module Name    : dummy_monitor
// Description    : Dummy Monitor blueprint
///////////////////////////////////////////////////////////////////////
class dummy_monitor extends uvm_monitor;
  `uvm_component_utils(dummy_monitor)

  virtual interface dummy_intf dummy_if;
  uvm_analysis_port #(dummy_seq_item) ap;

  function new(string name="dummy_monitor", uvm_component parent=null);
    super.new(name, parent);
    ap = new("ap", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if(!uvm_config_db#(virtual dummy_intf)::get(this, "", "dummy_if", dummy_if))
      `uvm_fatal("NOVIF", {"virtual interface must be set for: ", get_full_name(), ".dummy_if"});
  endfunction

  task run_phase(uvm_phase phase);
    super.run_phase(phase);
    // LOGIC_START
    // LOGIC_END
  endtask
endclass
