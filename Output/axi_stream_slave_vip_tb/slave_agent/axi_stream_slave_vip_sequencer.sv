// AXI-Stream Slave VIP Sequencer
class axi_stream_slave_vip_sequencer extends uvm_sequencer #(axi_stream_slave_vip_seq_item);
  `uvm_component_utils(axi_stream_slave_vip_sequencer)
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass
