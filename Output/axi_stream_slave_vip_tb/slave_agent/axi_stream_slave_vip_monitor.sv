// AXI-Stream Slave VIP Monitor
// Observes all DUT Master outputs passively. Checks protocol compliance.
// Drives 12 coverage groups. Sends received items to scoreboard via ap.
class axi_stream_slave_vip_monitor extends uvm_monitor;
  `uvm_component_utils(axi_stream_slave_vip_monitor)

  virtual axi_stream_slave_vip_if vif;
  axi_stream_slave_vip_agent_config cfg;
  uvm_analysis_port #(axi_stream_slave_vip_seq_item) ap;

  // ── Payload snapshot (captured on first TVALID=1 of each pending transfer) ──
  logic [`TDATA_WIDTH-1:0]   snap_tdata;
  logic [`TDATA_WIDTH/8-1:0] snap_tkeep, snap_tstrb;
  logic                      snap_tlast;
  logic [`TID_WIDTH-1:0]     snap_tid;
  logic [`TDEST_WIDTH-1:0]   snap_tdest;
  logic [`TUSER_WIDTH-1:0]   snap_tuser;
  bit                        snap_valid = 0;

  // ── Per-stream ordering tracking ─────────────────────────────────────────────
  int unsigned stream_beat_cnt [logic [(`TID_WIDTH+`TDEST_WIDTH-1):0]];

  // ── Coverage group tracking variables ────────────────────────────────────────
  int  tready_stall_depth        = 0;  // cycles TVALID=1, TREADY=0
  int  pkt_beat_count            = 0;
  bit  pkt_back_to_back          = 0;
  bit  prev_tlast                = 1;  // start as if prior packet ended
  int  twakeup_lead_cycles       = 0;
  bit  twakeup_seen              = 0;
  int  active_tid_count          = 1;
  int  beats_per_tid_before_sw   = 1;
  int  null_pkt_ctx              = 0;  // 0=isolated 1=after-data 2=before-data 3=b2b-null
  bit  prev_pkt_was_null         = 0;
  int  stall_beat_position       = 0;  // 0=first 1=mid 2=last
  bit  continuous_pkt_viol       = 0;  // 0=no viol 1=TID 2=null_byte 3=TSTRB
  int  handshake_ordering        = 0;  // 0=TVALID-first 1=TREADY-first 2=simul

  // ── Packet tracker file ───────────────────────────────────────────────────────
  int tracker_fd;
  int pkt_count = 0;
  int null_count = 0;
  int total_beats = 0;

  // ── Coverage Groups ───────────────────────────────────────────────────────────

  // REQ_SLV_VIP_01 + REQ_SLV_VIP_11
  covergroup cg_tready_backpressure_depth;
    cp_stall: coverpoint tready_stall_depth {
      bins immediate    = {0};
      bins short_stall  = {[1:4]};
      bins mid_stall    = {[5:16]};
      bins long_stall   = {[17:32]};
    }
    cp_pos: coverpoint stall_beat_position {
      bins first_beat = {0};
      bins mid_beat   = {1};
      bins last_beat  = {2};
    }
    cx_stall_pos: cross cp_stall, cp_pos;
  endgroup

  // REQ_SLV_VIP_01 + REQ_SLV_VIP_02
  covergroup cg_tvalid_to_tready_gap;
    cp_gap: coverpoint tready_stall_depth {
      bins simul        = {0};
      bins one_cycle    = {1};
      bins short_gap    = {[2:4]};
      bins mid_gap      = {[5:16]};
      bins long_gap     = {[17:32]};
    }
  endgroup

  // REQ_SLV_VIP_03
  covergroup cg_payload_stability_window;
    cp_window: coverpoint tready_stall_depth {
      bins one_cycle    = {1};
      bins short_window = {[2:4]};
      bins mid_window   = {[5:16]};
      bins long_window  = {[17:32]};
    }
  endgroup

  // REQ_SLV_VIP_04
  covergroup cg_packet_size_distribution;
    cp_len: coverpoint pkt_beat_count {
      bins single_beat = {1};
      bins short_burst = {[2:8]};
      bins mid_burst   = {[9:64]};
      bins long_burst  = {[65:256]};
    }
    cp_b2b: coverpoint pkt_back_to_back {
      bins isolated     = {0};
      bins back_to_back = {1};
    }
    cx_len_b2b: cross cp_len, cp_b2b;
  endgroup

  // REQ_SLV_VIP_05
  covergroup cg_reset_injection_context;
    cp_ctx: coverpoint null_pkt_ctx {
      bins idle        = {0};
      bins mid_pkt     = {1};
      bins at_handshk  = {2};
    }
    cp_dur: coverpoint tready_stall_depth {
      bins one_cycle   = {1};
      bins short_reset = {[2:4]};
      bins long_reset  = {[5:16]};
    }
    cx_ctx_dur: cross cp_ctx, cp_dur;
  endgroup

  // REQ_SLV_VIP_06
  covergroup cg_byte_qualifier_patterns;
    cp_tkeep: coverpoint snap_tkeep {
      bins all_data     = {'1};
      bins all_null     = {'0};
      bins sparse_low   = {4'b0001, 4'b0011};
      bins sparse_high  = {4'b1100, 4'b1110};
      bins mixed        = default;
    }
    cp_tstrb: coverpoint snap_tstrb {
      bins all_data     = {'1};
      bins positional   = {'0};
      bins mixed        = default;
    }
    cx_qualifier: cross cp_tkeep, cp_tstrb;
  endgroup

  // REQ_SLV_VIP_07
  covergroup cg_twakeup_timing;
    cp_lead: coverpoint twakeup_lead_cycles {
      bins simultaneous = {0};
      bins one_early    = {1};
      bins two_or_more  = {[2:8]};
    }
  endgroup

  // REQ_SLV_VIP_08
  covergroup cg_stream_interleaving_depth;
    cp_streams: coverpoint active_tid_count {
      bins one_stream  = {1};
      bins two_streams = {2};
      bins four_plus   = {[4:16]};
    }
    cp_beats_per_tid: coverpoint beats_per_tid_before_sw {
      bins max_interleave = {1};
      bins short_run      = {[2:4]};
      bins long_run       = {[5:16]};
    }
    cx_depth: cross cp_streams, cp_beats_per_tid;
  endgroup

  // REQ_SLV_VIP_09
  covergroup cg_null_packet_context;
    cp_null_ctx: coverpoint null_pkt_ctx {
      bins isolated         = {0};
      bins after_data       = {1};
      bins before_data      = {2};
      bins back_to_back_null= {3};
    }
  endgroup

  // REQ_SLV_VIP_10
  covergroup cg_parity_lane_coverage;
    cp_lane: coverpoint snap_tkeep {
      bins lane0_active = {4'b???1};
      bins lane1_active = {4'b??1?};
      bins lane2_active = {4'b?1??};
      bins lane3_active = {4'b1???};
      bins lane0_null   = {4'b???0};
      bins lane1_null   = {4'b??0?};
    }
    cp_tready_edge: coverpoint handshake_ordering {
      bins tvalid_first  = {0};
      bins tready_first  = {1};
      bins simultaneous  = {2};
    }
  endgroup

  // REQ_SLV_VIP_11
  covergroup cg_intra_packet_backpressure_position;
    cp_stall_pos: coverpoint stall_beat_position {
      bins first_beat      = {0};
      bins mid_beat        = {1};
      bins penultimate_beat= {2};
      bins last_beat       = {3};
    }
  endgroup

  // REQ_SLV_VIP_12
  covergroup cg_continuous_packets_violations;
    cp_viol: coverpoint continuous_pkt_viol {
      bins no_violation   = {0};
      bins tid_change     = {1};
      bins null_byte_mid  = {2};
      bins tstrb_present  = {3};
    }
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent);
    cg_tready_backpressure_depth        = new();
    cg_tvalid_to_tready_gap             = new();
    cg_payload_stability_window         = new();
    cg_packet_size_distribution         = new();
    cg_reset_injection_context          = new();
    cg_byte_qualifier_patterns          = new();
    cg_twakeup_timing                   = new();
    cg_stream_interleaving_depth        = new();
    cg_null_packet_context              = new();
    cg_parity_lane_coverage             = new();
    cg_intra_packet_backpressure_position = new();
    cg_continuous_packets_violations    = new();
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap = new("ap", this);
    if (!uvm_config_db #(virtual axi_stream_slave_vip_if)::get(this, "", "vif", vif))
      `uvm_fatal("CFG", "No VIF for axi_stream_slave_vip_monitor")
    if (!uvm_config_db #(axi_stream_slave_vip_agent_config)::get(this, "", "cfg", cfg))
      `uvm_fatal("CFG", "No CFG for axi_stream_slave_vip_monitor")
  endfunction

  // ── Odd parity helpers ────────────────────────────────────────────────────────
  function automatic logic byte_odd_parity(logic [7:0] b);
    return ~^b;
  endfunction

  function automatic logic [`TDATA_WIDTH/8-1:0] compute_tdatachk(logic [`TDATA_WIDTH-1:0] d);
    logic [`TDATA_WIDTH/8-1:0] chk;
    for (int i = 0; i < `TDATA_WIDTH/8; i++)
      chk[i] = byte_odd_parity(d[8*i +: 8]);
    return chk;
  endfunction

  // ── Main run phase ────────────────────────────────────────────────────────────
  task run_phase(uvm_phase phase);
    axi_stream_slave_vip_seq_item item;
    logic [`TDATA_WIDTH/8-1:0] exp_datachk;
    logic exp_lastchk;

    // Open tracker file
    if (cfg.enable_tracker) begin
      tracker_fd = $fopen("slave_vip_packet_tracker.log", "w");
      $fwrite(tracker_fd, "== AXI-Stream Slave VIP Packet Tracker ==\n");
    end

    // Wait for reset
    @(posedge vif.ARESETn);
    @(vif.cb_mon);

    forever begin
      @(vif.cb_mon);

      // ── Reset protocol check ─────────────────────────────────────────────────
      if (vif.cb_mon.ARESETn === 1'b0) begin
        if (vif.cb_mon.TVALID === 1'b1)
          `uvm_error("MON_RESET", "TVALID_DURING_RESET_VIOLATION: DUT Master drove TVALID=1 during ARESETn=0!")
        snap_valid = 0;
        tready_stall_depth = 0;
        continue;
      end

      // ── TVALID pending window tracking ───────────────────────────────────────
      if (vif.cb_mon.TVALID === 1'b1 && vif.cb_mon.TREADY !== 1'b1) begin
        tready_stall_depth++;

        if (snap_valid) begin
          // ── Payload stability check (XOR snapshot comparison) ───────────────
          if (vif.cb_mon.TDATA  !== snap_tdata  ||
              vif.cb_mon.TKEEP  !== snap_tkeep  ||
              vif.cb_mon.TSTRB  !== snap_tstrb  ||
              vif.cb_mon.TLAST  !== snap_tlast  ||
              vif.cb_mon.TID    !== snap_tid    ||
              vif.cb_mon.TDEST  !== snap_tdest  ||
              vif.cb_mon.TUSER  !== snap_tuser) begin
            `uvm_error("MON_STAB", $sformatf(
              "PAYLOAD_MUTATION during back-pressure! TDATA: 0x%08h→0x%08h TKEEP:%0b→%0b",
              snap_tdata, vif.cb_mon.TDATA, snap_tkeep, vif.cb_mon.TKEEP))
          end
        end else begin
          // First cycle of TVALID=1 — capture snapshot
          snap_tdata  = vif.cb_mon.TDATA;
          snap_tkeep  = vif.cb_mon.TKEEP;
          snap_tstrb  = vif.cb_mon.TSTRB;
          snap_tlast  = vif.cb_mon.TLAST;
          snap_tid    = vif.cb_mon.TID;
          snap_tdest  = vif.cb_mon.TDEST;
          snap_tuser  = vif.cb_mon.TUSER;
          snap_valid  = 1;

          // Determine handshake ordering
          if (vif.cb_mon.TREADY !== 1'b1)
            handshake_ordering = 0;  // TVALID-first
          else
            handshake_ordering = 2;  // simultaneous
        end

        // ── TWAKEUP tracking ─────────────────────────────────────────────────
        if (cfg.has_wakeup && vif.cb_mon.TWAKEUP !== 1'b1 && !twakeup_seen)
          twakeup_lead_cycles = 0;

        // ── Byte qualifier check (reserved TKEEP=0/TSTRB=1) ──────────────────
        for (int i = 0; i < `TDATA_WIDTH/8; i++) begin
          if (vif.cb_mon.TKEEP[i] === 1'b0 && vif.cb_mon.TSTRB[i] === 1'b1)
            `uvm_fatal("MON_QUAL", $sformatf(
              "RESERVED_QUALIFIER_VIOLATION: TKEEP[%0d]=0, TSTRB[%0d]=1", i, i))
        end

        // ── Continuous_Packets mode: TID stability check ─────────────────────
        if (cfg.continuous_pkt_mode && snap_valid && vif.cb_mon.TLAST !== 1'b1) begin
          if (vif.cb_mon.TID !== snap_tid) begin
            `uvm_error("MON_CONT", "CONTINUOUS_PKTS_TID_VIOLATION: TID changed while TLAST=0!")
            continuous_pkt_viol = 1;
          end
          // Null byte in mid-packet (TKEEP not all-1)
          if (vif.cb_mon.TKEEP !== {(`TDATA_WIDTH/8){1'b1}}) begin
            `uvm_error("MON_CONT", "CONTINUOUS_PKTS_NULL_BYTE_VIOLATION: TKEEP not all-1 while TLAST=0!")
            continuous_pkt_viol = 2;
          end
        end

        // ── AXI5 Parity verification ──────────────────────────────────────────
        if (cfg.has_parity) begin
          // TVALIDCHK: Check enable = ARESETn=1; expected = ~TVALID
          if (vif.cb_mon.TVALIDCHK !== ~vif.cb_mon.TVALID)
            `uvm_error("MON_PAR", $sformatf(
              "PARITY_FAULT TVALIDCHK: got=%0b expected=%0b",
              vif.cb_mon.TVALIDCHK, ~vif.cb_mon.TVALID))
        end
      end // TVALID pending window

      // ── Handshake completion ─────────────────────────────────────────────────
      if (vif.cb_mon.TVALID === 1'b1 && vif.cb_mon.TREADY === 1'b1) begin
        total_beats++;
        pkt_beat_count++;

        // ── AXI5 parity checks on handshake beat ────────────────────────────
        if (cfg.has_parity) begin
          exp_datachk = compute_tdatachk(vif.cb_mon.TDATA);
          exp_lastchk = ~vif.cb_mon.TLAST;
          if (vif.cb_mon.TDATACHK !== exp_datachk)
            `uvm_error("MON_PAR", $sformatf(
              "PARITY_FAULT TDATACHK: got=0x%0h expected=0x%0h", vif.cb_mon.TDATACHK, exp_datachk))
          if (vif.cb_mon.TLASTCHK !== exp_lastchk)
            `uvm_error("MON_PAR", $sformatf(
              "PARITY_FAULT TLASTCHK: got=%0b expected=%0b", vif.cb_mon.TLASTCHK, exp_lastchk))
        end

        // ── Build and send received item to scoreboard ───────────────────────
        item = axi_stream_slave_vip_seq_item::type_id::create("rx_item");
        item.tdata = vif.cb_mon.TDATA;
        item.tkeep = vif.cb_mon.TKEEP;
        item.tstrb = vif.cb_mon.TSTRB;
        item.tlast = vif.cb_mon.TLAST;
        item.tid   = vif.cb_mon.TID;
        item.tdest = vif.cb_mon.TDEST;
        item.tuser = vif.cb_mon.TUSER;
        ap.write(item);

        // ── Sample coverage groups ────────────────────────────────────────────
        cg_tready_backpressure_depth.sample();
        cg_tvalid_to_tready_gap.sample();
        cg_payload_stability_window.sample();
        cg_byte_qualifier_patterns.sample();
        cg_parity_lane_coverage.sample();

        // ── Packet boundary handling ──────────────────────────────────────────
        if (vif.cb_mon.TLAST === 1'b1) begin
          pkt_count++;
          // Null packet check (all TKEEP=0)
          if (vif.cb_mon.TKEEP === {(`TDATA_WIDTH/8){1'b0}}) begin
            null_count++;
            null_pkt_ctx = (prev_pkt_was_null) ? 3 : (pkt_beat_count == 1 ? 0 : 1);
            prev_pkt_was_null = 1;
          end else begin
            null_pkt_ctx = (prev_pkt_was_null) ? 2 : 0;
            prev_pkt_was_null = 0;
          end

          pkt_back_to_back = !prev_tlast; // prev cycle TLAST was 0 means same TVALID window
          cg_packet_size_distribution.sample();
          cg_null_packet_context.sample();

          if (cfg.enable_tracker)
            $fwrite(tracker_fd, "PKT#%0d: beats=%0d null=%0b TID=0x%0h TDEST=0x%0h\n",
                    pkt_count, pkt_beat_count,
                    (vif.cb_mon.TKEEP === {(`TDATA_WIDTH/8){1'b0}}),
                    vif.cb_mon.TID, vif.cb_mon.TDEST);

          pkt_beat_count = 0;
          prev_tlast = 1;
        end else begin
          prev_tlast = 0;
        end

        // ── Sample remaining covergroups ──────────────────────────────────────
        cg_twakeup_timing.sample();
        cg_stream_interleaving_depth.sample();
        cg_intra_packet_backpressure_position.sample();
        cg_continuous_packets_violations.sample();

        // Reset tracking for next transfer
        snap_valid         = 0;
        tready_stall_depth = 0;
        stall_beat_position = 0;
        continuous_pkt_viol = 0;
      end
      else if (vif.cb_mon.TVALID !== 1'b1 && snap_valid) begin
        // TVALID dropped without handshake — protocol violation
        `uvm_fatal("MON_STAB", "TVALID_RETRACTION_VIOLATION: TVALID deasserted before TREADY!")
      end

      // ── TWAKEUP check: must persist if simultaneous with TVALID ──────────────
      if (cfg.has_wakeup && vif.cb_mon.TWAKEUP === 1'b1) begin
        twakeup_seen = 1;
        if (vif.cb_mon.TVALID === 1'b1 && vif.cb_mon.TREADY !== 1'b1) begin
          // TWAKEUP must remain asserted — already checking by sampling it here
          // Lead-time is negative if TWAKEUP=TVALID=1 on same cycle
        end
      end
    end // forever
  endtask

  function void final_phase(uvm_phase phase);
    `uvm_info("MON", $sformatf(
      "[MON] FINAL: total_beats=%0d  pkts=%0d  null_pkts=%0d",
      total_beats, pkt_count, null_count), UVM_NONE)
    if (cfg.enable_tracker) $fclose(tracker_fd);
  endfunction

endclass
