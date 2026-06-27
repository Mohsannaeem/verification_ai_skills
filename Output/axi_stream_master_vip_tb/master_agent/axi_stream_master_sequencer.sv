class axi_stream_master_sequencer extends uvm_sequencer#(axi_stream_master_seq_item);
  `uvm_component_utils(axi_stream_master_sequencer)

  function new(string name = "axi_stream_master_sequencer", uvm_component parent=null);
    super.new(name, parent);
  endfunction

endclass : axi_stream_master_sequencer
