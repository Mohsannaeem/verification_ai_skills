////////////////////////////////////////////////////////////////////////
// Module Name    : dummy_scoreboard
// Description    : Dummy Scoreboard blueprint
///////////////////////////////////////////////////////////////////////
class dummy_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(dummy_scoreboard)
  `uvm_analysis_imp_decl(_master)

  uvm_analysis_imp_master #(dummy_seq_item, dummy_scoreboard) master_export;

  function new(string name="dummy_scoreboard", uvm_component parent=null);
    super.new(name, parent);
    master_export = new("master_export", this);
  endfunction

  function void write_master(dummy_seq_item item);
    // LOGIC_START
    // LOGIC_END
  endfunction

  function void check_phase(uvm_phase phase);
    super.check_phase(phase);
    // Comparison logic
  endfunction
endclass
