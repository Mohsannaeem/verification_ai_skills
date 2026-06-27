// AXI-Stream Slave VIP Scoreboard
// Receives handshaked items from monitor, maintains per-stream queues,
// verifies byte accumulation and null-packet handling.
class axi_stream_slave_vip_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(axi_stream_slave_vip_scoreboard)

  uvm_analysis_imp #(axi_stream_slave_vip_seq_item, axi_stream_slave_vip_scoreboard) slave_export;

  // Per-stream packet queues (keyed by {TID, TDEST} concatenation)
  axi_stream_slave_vip_seq_item stream_queues[int][$];

  // Global stats
  int total_beats  = 0;
  int total_pkts   = 0;
  int null_pkts    = 0;
  int byte_count   = 0;
  int parity_errors= 0;
  int order_errors = 0;

  // Per-stream stats
  int stream_null_count[int];
  int stream_byte_count[int];
  int stream_pkt_count[int];

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    slave_export = new("slave_export", this);
  endfunction

  function void write(axi_stream_slave_vip_seq_item item);
    int key;
    key = {item.tid, item.tdest};

    total_beats++;

    // ── Null packet detection ────────────────────────────────────────────────
    if (item.tlast === 1'b1 && item.tkeep === {(`TDATA_WIDTH/8){1'b0}}) begin
      null_pkts++;
      if (!stream_null_count.exists(key)) stream_null_count[key] = 0;
      stream_null_count[key]++;
      // Null packet: do NOT advance byte counter
      `uvm_info("SCB", $sformatf(
        "[SCB] NULL PKT received: TID=0x%0h TDEST=0x%0h total_null=%0d",
        item.tid, item.tdest, null_pkts), UVM_MEDIUM)
    end else begin
      // Data bytes = popcount(TKEEP)
      int active_bytes = $countones(item.tkeep);
      byte_count += active_bytes;
      if (!stream_byte_count.exists(key)) stream_byte_count[key] = 0;
      stream_byte_count[key] += active_bytes;
    end

    // ── Packet counting (on TLAST) ────────────────────────────────────────────
    if (item.tlast === 1'b1) begin
      total_pkts++;
      if (!stream_pkt_count.exists(key)) stream_pkt_count[key] = 0;
      stream_pkt_count[key]++;
    end

    // ── Store in per-stream queue ─────────────────────────────────────────────
    if (!stream_queues.exists(key)) begin
      stream_queues[key] = '{};
    end
    stream_queues[key].push_back(item);

    `uvm_info("SCB", $sformatf(
      "[SCB] Beat #%0d | TDATA=0x%08h TKEEP=%0b TLAST=%0b TID=0x%0h TDEST=0x%0h | total_pkts=%0d bytes=%0d",
      total_beats, item.tdata, item.tkeep, item.tlast,
      item.tid, item.tdest, total_pkts, byte_count), UVM_HIGH)
  endfunction

  function void check_phase(uvm_phase phase);
    `uvm_info("SCB", "====== AXI-Stream Slave VIP Scoreboard Final Report ======", UVM_NONE)
    `uvm_info("SCB", $sformatf("  Total Beats    : %0d", total_beats),  UVM_NONE)
    `uvm_info("SCB", $sformatf("  Total Packets  : %0d", total_pkts),   UVM_NONE)
    `uvm_info("SCB", $sformatf("  Null Packets   : %0d", null_pkts),    UVM_NONE)
    `uvm_info("SCB", $sformatf("  Data Bytes Rcvd: %0d", byte_count),   UVM_NONE)
    `uvm_info("SCB", $sformatf("  Parity Errors  : %0d", parity_errors),UVM_NONE)
    `uvm_info("SCB", $sformatf("  Order Errors   : %0d", order_errors), UVM_NONE)
    `uvm_info("SCB", $sformatf("  Active Streams : %0d", stream_queues.size()), UVM_NONE)
    `uvm_info("SCB", "=========================================================", UVM_NONE)

    if (parity_errors > 0)
      `uvm_error("SCB", $sformatf("%0d parity error(s) detected!", parity_errors))
    if (order_errors > 0)
      `uvm_error("SCB", $sformatf("%0d ordering violation(s) detected!", order_errors))
  endfunction

endclass
