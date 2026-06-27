class axi_stream_master_seq_item extends uvm_sequence_item;

  // Randomized Members
  rand bit [`TDATA_WIDTH-1:0] tdata;
  rand bit [`TDATA_WIDTH/8-1:0]  tkeep;
  rand bit [`TDATA_WIDTH/8-1:0]  tstrb;
  rand bit        tlast;
  rand bit [`TID_WIDTH-1:0]  tid;
  rand bit [`TDEST_WIDTH-1:0]  tdest;
  rand bit [`TUSER_WIDTH-1:0]  tuser;
  
  // Handshake control
  rand int delay_cycles;

  // Negative Testing Knobs
  rand bit drop_valid_early;
  rand bit corrupt_parity;
  rand bit corrupt_tdata;
  rand int twakeup_early;
  rand int pkt_len;

  // Standard UVM macros
  `uvm_object_utils_begin(axi_stream_master_seq_item)
    `uvm_field_int(tdata, UVM_ALL_ON)
    `uvm_field_int(tkeep, UVM_ALL_ON)
    `uvm_field_int(tstrb, UVM_ALL_ON)
    `uvm_field_int(tlast, UVM_ALL_ON)
    `uvm_field_int(tid,   UVM_ALL_ON)
    `uvm_field_int(tdest, UVM_ALL_ON)
    `uvm_field_int(tuser, UVM_ALL_ON)
    `uvm_field_int(delay_cycles, UVM_ALL_ON)
    `uvm_field_int(drop_valid_early, UVM_ALL_ON)
    `uvm_field_int(corrupt_parity,   UVM_ALL_ON)
    `uvm_field_int(corrupt_tdata,    UVM_ALL_ON)
    `uvm_field_int(twakeup_early,    UVM_ALL_ON)
    `uvm_field_int(pkt_len,          UVM_ALL_ON)
  `uvm_object_utils_end

  // Constraints
  constraint c_delay { delay_cycles inside {[0:10]}; }
  constraint c_wakeup { twakeup_early inside {[0:5]}; }
  constraint c_pkt_len { pkt_len inside {[1:16]}; }
  constraint c_default_clean {
    soft drop_valid_early == 0;
    soft corrupt_parity   == 0;
    soft corrupt_tdata    == 0;
  }

  constraint c_valid_qualifiers {
    foreach(tkeep[i]) {
      (tkeep[i] == 0) -> (tstrb[i] == 0);
    }
  }

  function new(string name = "axi_stream_master_seq_item");
    super.new(name);
  endfunction

  // Deep Copy and Compare for Scoreboard Traceability
  function void do_copy(uvm_object rhs);
    axi_stream_master_seq_item rhs_;
    if(!$cast(rhs_, rhs)) `uvm_fatal("CAST", "Cast failed in do_copy")
    super.do_copy(rhs);
    tdata = rhs_.tdata;
    tkeep = rhs_.tkeep;
    tstrb = rhs_.tstrb;
    tlast = rhs_.tlast;
    tid   = rhs_.tid;
    tdest = rhs_.tdest;
    tuser = rhs_.tuser;
  endfunction

  function bit do_compare(uvm_object rhs, uvm_comparer comparer);
    axi_stream_master_seq_item rhs_;
    if(!$cast(rhs_, rhs)) return 0;
    return (super.do_compare(rhs, comparer) &&
            (tdata == rhs_.tdata) &&
            (tkeep == rhs_.tkeep) &&
            (tstrb == rhs_.tstrb) &&
            (tlast == rhs_.tlast) &&
            (tid   == rhs_.tid));
  endfunction

endclass : axi_stream_master_seq_item
