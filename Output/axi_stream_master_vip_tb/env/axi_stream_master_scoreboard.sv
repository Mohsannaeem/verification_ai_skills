class axi_stream_master_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(axi_stream_master_scoreboard)
  `uvm_analysis_imp_decl(_master)

  uvm_analysis_imp_master #(axi_stream_master_seq_item, axi_stream_master_scoreboard) master_export;

  // Internal storage for reference model
  axi_stream_master_seq_item exp_queue[$];

  function new(string name, uvm_component parent);
    super.new(name, parent);
    master_export = new("master_export", this);
  endfunction

  int pkt_count = 0;

  function void write_master(axi_stream_master_seq_item item);
    pkt_count++;
    `uvm_info(get_type_name(), $sformatf("==================================================\n[SCB] RECEIVED PACKET #%0d\n==================================================\n%s\n--------------------------------------------------", pkt_count, item.sprint()), UVM_MEDIUM)
    exp_queue.push_back(item);
  endfunction

  function void check_phase(uvm_phase phase);
    super.check_phase(phase);
    if(exp_queue.size() > 0) begin
       `uvm_info("SCB_FINAL", $sformatf("%0d transactions remained in expectation queue", exp_queue.size()), UVM_LOW)
    end
  endfunction

endclass : axi_stream_master_scoreboard
