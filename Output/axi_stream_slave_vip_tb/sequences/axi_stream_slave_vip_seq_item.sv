// AXI-Stream Slave VIP Sequence Item
// Carries both: (a) TREADY stimulus knobs from Driver, and
//               (b) received payload fields populated by Monitor
class axi_stream_slave_vip_seq_item extends uvm_sequence_item;
  `uvm_object_utils(axi_stream_slave_vip_seq_item)

  // ── TREADY stimulus knobs (used by Driver) ──────────────────────────────────
  rand int unsigned tready_stall_cycles;    // 0 = no stall (immediate accept)
  rand bit          tready_pre_assert;      // assert TREADY before TVALID arrives
  rand int unsigned tready_duty_high_pct;   // duty cycle % high (10–90)
  rand int unsigned stall_at_beat;          // intra-packet beat to apply stall

  // ── Negative/fault injection knobs ──────────────────────────────────────────
  rand bit          inject_tvalid_drop;     // force monitor violation (negative TC)
  rand int unsigned inject_parity_fault_lane; // 0=none; 1-4 = inject fault on that lane

  // ── Received payload fields (populated by Monitor at handshake) ─────────────
  logic [`TDATA_WIDTH-1:0]   tdata;
  logic [`TDATA_WIDTH/8-1:0] tkeep;
  logic [`TDATA_WIDTH/8-1:0] tstrb;
  logic                      tlast;
  logic [`TID_WIDTH-1:0]     tid;
  logic [`TDEST_WIDTH-1:0]   tdest;
  logic [`TUSER_WIDTH-1:0]   tuser;

  // ── Constraints ──────────────────────────────────────────────────────────────
  constraint c_stall   { tready_stall_cycles inside {[0:`TREADY_STALL_MAX]}; }
  constraint c_duty    { tready_duty_high_pct inside {[10:90]}; }
  constraint c_no_fault { inject_parity_fault_lane == 0; }  // off by default
  constraint c_no_drop  { inject_tvalid_drop == 0; }        // off by default

  function new(string name = "axi_stream_slave_vip_seq_item");
    super.new(name);
  endfunction

  virtual function void do_copy(uvm_object rhs);
    axi_stream_slave_vip_seq_item rhs_;
    super.do_copy(rhs);
    if (!$cast(rhs_, rhs)) return;
    tready_stall_cycles    = rhs_.tready_stall_cycles;
    tready_pre_assert      = rhs_.tready_pre_assert;
    tready_duty_high_pct   = rhs_.tready_duty_high_pct;
    stall_at_beat          = rhs_.stall_at_beat;
    inject_tvalid_drop     = rhs_.inject_tvalid_drop;
    inject_parity_fault_lane = rhs_.inject_parity_fault_lane;
    tdata = rhs_.tdata; tkeep = rhs_.tkeep; tstrb = rhs_.tstrb;
    tlast = rhs_.tlast; tid   = rhs_.tid;   tdest = rhs_.tdest;
    tuser = rhs_.tuser;
  endfunction

  virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
    axi_stream_slave_vip_seq_item rhs_;
    if (!$cast(rhs_, rhs)) return 0;
    return (tdata === rhs_.tdata && tkeep === rhs_.tkeep && tstrb === rhs_.tstrb &&
            tlast === rhs_.tlast && tid   === rhs_.tid   && tdest === rhs_.tdest &&
            tuser === rhs_.tuser);
  endfunction

  virtual function string convert2string();
    return $sformatf(
      "[SlvVIP_Item] TDATA=0x%08h TKEEP=%0b TSTRB=%0b TLAST=%0b TID=0x%02h TDEST=0x%0h | STALL=%0d PRE=%0b",
      tdata, tkeep, tstrb, tlast, tid, tdest,
      tready_stall_cycles, tready_pre_assert);
  endfunction

endclass
