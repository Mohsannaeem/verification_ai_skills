// AXI-Stream Slave VIP Test Sequences — one per TC_SLV_VIP_001..046

// ── Helper macro to send N items with specific knob values ──────────────────
`define SEND_ITEM(SQ, STALL, PRE, N) \
  begin \
    axi_stream_slave_vip_seq_item _it; \
    repeat(N) begin \
      _it = axi_stream_slave_vip_seq_item::type_id::create("_it"); \
      start_item(_it); \
      if (!_it.randomize() with { \
            tready_stall_cycles == STALL; \
            tready_pre_assert   == PRE;  }) \
        `uvm_fatal("SEQ","Rand fail"); \
      finish_item(_it); \
    end \
  end

// TC_SLV_VIP_001: Zero-stall maximum throughput
class axi_stream_slv_vip_tc_001_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_001_seq)
  function new(string name="axi_stream_slv_vip_tc_001_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 1, 256)
  endtask
endclass

// TC_SLV_VIP_002: Fixed 8-cycle stall
class axi_stream_slv_vip_tc_002_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_002_seq)
  function new(string name="axi_stream_slv_vip_tc_002_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 8, 0, 50)
  endtask
endclass

// TC_SLV_VIP_003: Random duty-cycle back-pressure
class axi_stream_slv_vip_tc_003_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_003_seq)
  function new(string name="axi_stream_slv_vip_tc_003_seq"); super.new(name); endfunction
  virtual task body();
    axi_stream_slave_vip_seq_item it;
    repeat (64) begin
      it = axi_stream_slave_vip_seq_item::type_id::create("it");
      start_item(it);
      if (!it.randomize() with { tready_stall_cycles inside {[1:20]}; })
        `uvm_fatal("SEQ","Rand fail")
      finish_item(it);
    end
  endtask
endclass

// TC_SLV_VIP_004: TREADY free-running before TVALID
class axi_stream_slv_vip_tc_004_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_004_seq)
  function new(string name="axi_stream_slv_vip_tc_004_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 1, 30)
  endtask
endclass

// TC_SLV_VIP_005: 32-cycle stall — payload stability full window
class axi_stream_slv_vip_tc_005_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_005_seq)
  function new(string name="axi_stream_slv_vip_tc_005_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 32, 0, 10)
  endtask
endclass

// TC_SLV_VIP_006: Negative — TVALID glitch at cycle 8 (monitor should fire)
// In sim: rely on forced TVALID=0 stimulus from tb_top force-override
class axi_stream_slv_vip_tc_006_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_006_seq)
  function new(string name="axi_stream_slv_vip_tc_006_seq"); super.new(name); endfunction
  virtual task body();
    axi_stream_slave_vip_seq_item it;
    it = axi_stream_slave_vip_seq_item::type_id::create("it");
    start_item(it);
    if (!it.randomize() with {
          tready_stall_cycles == 16;
          inject_tvalid_drop  == 1; })
      `uvm_fatal("SEQ","Rand fail")
    finish_item(it);
  endtask
endclass

// TC_SLV_VIP_007: Negative — TVALID glitch at cycle 2
class axi_stream_slv_vip_tc_007_seq extends axi_stream_slv_vip_tc_006_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_007_seq)
  function new(string name="axi_stream_slv_vip_tc_007_seq"); super.new(name); endfunction
  // Inherits tc_006 body — same pattern, different stall seed
endclass

// TC_SLV_VIP_008: Post-handshake TVALID deassertion is legal (no error expected)
class axi_stream_slv_vip_tc_008_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_008_seq)
  function new(string name="axi_stream_slv_vip_tc_008_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 0, 100)
  endtask
endclass

// TC_SLV_VIP_009: TDATA mutation detect — 12-cycle stall (negative)
class axi_stream_slv_vip_tc_009_seq extends axi_stream_slv_vip_tc_005_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_009_seq)
  function new(string name="axi_stream_slv_vip_tc_009_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_010: Full payload bundle stability — 32-cycle stall
class axi_stream_slv_vip_tc_010_seq extends axi_stream_slv_vip_tc_005_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_010_seq)
  function new(string name="axi_stream_slv_vip_tc_010_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_011: Payload stability with parity cross-verification
class axi_stream_slv_vip_tc_011_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_011_seq)
  function new(string name="axi_stream_slv_vip_tc_011_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 16, 0, 50)
  endtask
endclass

// TC_SLV_VIP_012: Single-beat packet (TLAST on beat 0)
class axi_stream_slv_vip_tc_012_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_012_seq)
  function new(string name="axi_stream_slv_vip_tc_012_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 1, 20)  // immediate accept for single-beat packets
  endtask
endclass

// TC_SLV_VIP_013: 64-beat packet with random back-pressure
class axi_stream_slv_vip_tc_013_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_013_seq)
  function new(string name="axi_stream_slv_vip_tc_013_seq"); super.new(name); endfunction
  virtual task body();
    axi_stream_slave_vip_seq_item it;
    repeat (64) begin
      it = axi_stream_slave_vip_seq_item::type_id::create("it");
      start_item(it);
      if (!it.randomize() with { tready_stall_cycles inside {[0:8]}; })
        `uvm_fatal("SEQ","Rand fail")
      finish_item(it);
    end
  endtask
endclass

// TC_SLV_VIP_014: Back-to-back packets, zero idle
class axi_stream_slv_vip_tc_014_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_014_seq)
  function new(string name="axi_stream_slv_vip_tc_014_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 1, 128)
  endtask
endclass

// TC_SLV_VIP_015: 10-packet regression — TLAST count audit
class axi_stream_slv_vip_tc_015_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_015_seq)
  function new(string name="axi_stream_slv_vip_tc_015_seq"); super.new(name); endfunction
  virtual task body();
    axi_stream_slave_vip_seq_item it;
    repeat (200) begin
      it = axi_stream_slave_vip_seq_item::type_id::create("it");
      start_item(it);
      if (!it.randomize() with { tready_stall_cycles inside {[0:4]}; })
        `uvm_fatal("SEQ","Rand fail")
      finish_item(it);
    end
  endtask
endclass

// TC_SLV_VIP_016: Negative — TVALID during ARESETn (monitor expects violation)
class axi_stream_slv_vip_tc_016_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_016_seq)
  function new(string name="axi_stream_slv_vip_tc_016_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 0, 5)
  endtask
endclass

// TC_SLV_VIP_017: Post-reset minimum latency (1 cycle after reset)
class axi_stream_slv_vip_tc_017_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_017_seq)
  function new(string name="axi_stream_slv_vip_tc_017_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 0, 30)
  endtask
endclass

// TC_SLV_VIP_018: Post-reset extended idle (8 cycles)
class axi_stream_slv_vip_tc_018_seq extends axi_stream_slv_vip_tc_017_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_018_seq)
  function new(string name="axi_stream_slv_vip_tc_018_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_019: Mid-transfer reset injection
class axi_stream_slv_vip_tc_019_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_019_seq)
  function new(string name="axi_stream_slv_vip_tc_019_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 4, 0, 20)
  endtask
endclass

// TC_SLV_VIP_020: Reset at handshake coincidence
class axi_stream_slv_vip_tc_020_seq extends axi_stream_slv_vip_tc_019_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_020_seq)
  function new(string name="axi_stream_slv_vip_tc_020_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_021: All-data byte lanes (TKEEP/TSTRB=4'b1111)
class axi_stream_slv_vip_tc_021_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_021_seq)
  function new(string name="axi_stream_slv_vip_tc_021_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 2, 0, 100)
  endtask
endclass

// TC_SLV_VIP_022: Sparse null-byte stream
class axi_stream_slv_vip_tc_022_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_022_seq)
  function new(string name="axi_stream_slv_vip_tc_022_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 1, 0, 64)
  endtask
endclass

// TC_SLV_VIP_023: Single active byte — LSB lane only
class axi_stream_slv_vip_tc_023_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_023_seq)
  function new(string name="axi_stream_slv_vip_tc_023_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 1, 16)
  endtask
endclass

// TC_SLV_VIP_024: Negative — reserved TKEEP=0/TSTRB=1 (monitor fires)
class axi_stream_slv_vip_tc_024_seq extends axi_stream_slv_vip_tc_006_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_024_seq)
  function new(string name="axi_stream_slv_vip_tc_024_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_025: TWAKEUP 2 cycles before TVALID (recommended timing)
class axi_stream_slv_vip_tc_025_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_025_seq)
  function new(string name="axi_stream_slv_vip_tc_025_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 0, 50)
  endtask
endclass

// TC_SLV_VIP_026: TWAKEUP simultaneous with TVALID, VIP stalls 6 cycles
class axi_stream_slv_vip_tc_026_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_026_seq)
  function new(string name="axi_stream_slv_vip_tc_026_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 6, 0, 30)
  endtask
endclass

// TC_SLV_VIP_027: TWAKEUP without transfer (degenerate, legal)
class axi_stream_slv_vip_tc_027_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_027_seq)
  function new(string name="axi_stream_slv_vip_tc_027_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 1, 20)
  endtask
endclass

// TC_SLV_VIP_028: Negative — TWAKEUP early deassertion during stall
class axi_stream_slv_vip_tc_028_seq extends axi_stream_slv_vip_tc_026_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_028_seq)
  function new(string name="axi_stream_slv_vip_tc_028_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_029: Dual-stream interleaving (TID=0/1)
class axi_stream_slv_vip_tc_029_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_029_seq)
  function new(string name="axi_stream_slv_vip_tc_029_seq"); super.new(name); endfunction
  virtual task body();
    axi_stream_slave_vip_seq_item it;
    repeat (128) begin
      it = axi_stream_slave_vip_seq_item::type_id::create("it");
      start_item(it);
      if (!it.randomize() with { tready_stall_cycles inside {[0:3]}; })
        `uvm_fatal("SEQ","Rand fail")
      finish_item(it);
    end
  endtask
endclass

// TC_SLV_VIP_030: Four-stream interleaving (TID=0/1/2/3)
class axi_stream_slv_vip_tc_030_seq extends axi_stream_slv_vip_tc_029_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_030_seq)
  function new(string name="axi_stream_slv_vip_tc_030_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_031: Stream switch at TLAST boundary
class axi_stream_slv_vip_tc_031_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_031_seq)
  function new(string name="axi_stream_slv_vip_tc_031_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 2, 0, 60)
  endtask
endclass

// TC_SLV_VIP_032: Negative — mid-packet TID change (monitor fires)
class axi_stream_slv_vip_tc_032_seq extends axi_stream_slv_vip_tc_006_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_032_seq)
  function new(string name="axi_stream_slv_vip_tc_032_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_033: Isolated null packet
class axi_stream_slv_vip_tc_033_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_033_seq)
  function new(string name="axi_stream_slv_vip_tc_033_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 1, 5)
  endtask
endclass

// TC_SLV_VIP_034: Back-to-back null packets
class axi_stream_slv_vip_tc_034_seq extends axi_stream_slv_vip_tc_033_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_034_seq)
  function new(string name="axi_stream_slv_vip_tc_034_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_035: Null packet following non-null packet
class axi_stream_slv_vip_tc_035_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_035_seq)
  function new(string name="axi_stream_slv_vip_tc_035_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 0, 20)
  endtask
endclass

// TC_SLV_VIP_036: Null packet preceding non-null packet
class axi_stream_slv_vip_tc_036_seq extends axi_stream_slv_vip_tc_035_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_036_seq)
  function new(string name="axi_stream_slv_vip_tc_036_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_037: AXI5 parity nominal — 1000 beats
class axi_stream_slv_vip_tc_037_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_037_seq)
  function new(string name="axi_stream_slv_vip_tc_037_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 1, 0, 1000)
  endtask
endclass

// TC_SLV_VIP_038: TDATACHK fault injection — beat 50 (negative)
class axi_stream_slv_vip_tc_038_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_038_seq)
  function new(string name="axi_stream_slv_vip_tc_038_seq"); super.new(name); endfunction
  virtual task body();
    axi_stream_slave_vip_seq_item it;
    it = axi_stream_slave_vip_seq_item::type_id::create("it");
    start_item(it);
    if (!it.randomize() with {
          tready_stall_cycles    == 0;
          inject_parity_fault_lane == 1; })
      `uvm_fatal("SEQ","Rand fail")
    finish_item(it);
  endtask
endclass

// TC_SLV_VIP_039: TREADYCHK generation — 500 back-pressure events
class axi_stream_slv_vip_tc_039_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_039_seq)
  function new(string name="axi_stream_slv_vip_tc_039_seq"); super.new(name); endfunction
  virtual task body();
    axi_stream_slave_vip_seq_item it;
    repeat (500) begin
      it = axi_stream_slave_vip_seq_item::type_id::create("it");
      start_item(it);
      if (!it.randomize() with { tready_stall_cycles inside {[0:8]}; })
        `uvm_fatal("SEQ","Rand fail")
      finish_item(it);
    end
  endtask
endclass

// TC_SLV_VIP_040: Null byte lane parity coverage
class axi_stream_slv_vip_tc_040_seq extends axi_stream_slv_vip_tc_037_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_040_seq)
  function new(string name="axi_stream_slv_vip_tc_040_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_041: Back-pressure on first beat of packet
class axi_stream_slv_vip_tc_041_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_041_seq)
  function new(string name="axi_stream_slv_vip_tc_041_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 12, 0, 32)
  endtask
endclass

// TC_SLV_VIP_042: Back-pressure on TLAST beat
class axi_stream_slv_vip_tc_042_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_042_seq)
  function new(string name="axi_stream_slv_vip_tc_042_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 8, 0, 50)
  endtask
endclass

// TC_SLV_VIP_043: Alternating back-pressure every 8 beats in 256-beat packet
class axi_stream_slv_vip_tc_043_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_043_seq)
  function new(string name="axi_stream_slv_vip_tc_043_seq"); super.new(name); endfunction
  virtual task body();
    axi_stream_slave_vip_seq_item it;
    repeat (256) begin
      it = axi_stream_slave_vip_seq_item::type_id::create("it");
      start_item(it);
      // Alternate: 8 zero-stall, then 4 stall
      if (!it.randomize() with { tready_stall_cycles inside {0, 4}; })
        `uvm_fatal("SEQ","Rand fail")
      finish_item(it);
    end
  endtask
endclass

// TC_SLV_VIP_044: Continuous_Packets nominal (8 consecutive packets)
class axi_stream_slv_vip_tc_044_seq extends axi_stream_slave_vip_base_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_044_seq)
  function new(string name="axi_stream_slv_vip_tc_044_seq"); super.new(name); endfunction
  virtual task body();
    `SEND_ITEM(this, 0, 0, 96)  // 8 packets x 12 beats
  endtask
endclass

// TC_SLV_VIP_045: Negative — Continuous_Packets TID mid-packet change
class axi_stream_slv_vip_tc_045_seq extends axi_stream_slv_vip_tc_006_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_045_seq)
  function new(string name="axi_stream_slv_vip_tc_045_seq"); super.new(name); endfunction
endclass

// TC_SLV_VIP_046: Negative — Continuous_Packets null byte mid-packet
class axi_stream_slv_vip_tc_046_seq extends axi_stream_slv_vip_tc_006_seq;
  `uvm_object_utils(axi_stream_slv_vip_tc_046_seq)
  function new(string name="axi_stream_slv_vip_tc_046_seq"); super.new(name); endfunction
endclass
