class axi_stream_master_monitor extends uvm_monitor;
  `uvm_component_utils(axi_stream_master_monitor)

  virtual axi_stream_master_if vif;
  axi_stream_master_agent_config cfg;
  uvm_analysis_port#(axi_stream_master_seq_item) ap;

  // -------------------------------------------------------------------------
  // Functional Coverage Groups (REQ_MST_ALL)
  // -------------------------------------------------------------------------
  covergroup cg_handshake;
    cp_valid: coverpoint vif.cb_mon.TVALID;
    cp_ready: coverpoint vif.cb_mon.TREADY;
    cp_handshake: cross cp_valid, cp_ready {
      bins transfer = binsof(cp_valid) intersect {1} && binsof(cp_ready) intersect {1};
      bins wait_state = binsof(cp_valid) intersect {1} && binsof(cp_ready) intersect {0};
    }
  endgroup

  covergroup cg_qualifiers;
    cp_tkeep: coverpoint vif.cb_mon.TKEEP {
      bins all_ones = { '1 };
      bins partial  = { [1:14] };
      bins all_zeros = { 0 };
    }
    cp_tstrb: coverpoint vif.cb_mon.TSTRB;
    cp_tlast: coverpoint vif.cb_mon.TLAST;
    cp_null_packet: cross cp_tkeep, cp_tlast {
      bins null_tlast = binsof(cp_tkeep) intersect {0} && binsof(cp_tlast) intersect {1};
    }
  endgroup

  covergroup cg_packet_boundary;
    cp_tlast: coverpoint vif.cb_mon.TLAST;
    cp_tid:   coverpoint vif.cb_mon.TID {
      bins ids[] = { [0:3] };
      bins max_val = { 255 };
    }
    cp_tdest: coverpoint vif.cb_mon.TDEST {
      bins dests[] = { [0:3] };
    }
  endgroup

  covergroup cg_parity;
    cp_tdatchk: coverpoint vif.cb_mon.TDATACHK;
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap = new("ap", this);
    cg_handshake = new();
    cg_qualifiers = new();
    cg_packet_boundary = new();
    cg_parity = new();
  endfunction

  int tracker_fd;
  bit enable_tracker = 0;
  axi_stream_master_seq_item packet_buffer[$];

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if(!uvm_config_db#(virtual axi_stream_master_if)::get(this, "", "vif", vif))
      `uvm_fatal("MON_VIF", "Virtual interface not found in config_db")
    if(!uvm_config_db#(axi_stream_master_agent_config)::get(this, "", "cfg", cfg))
      `uvm_fatal("MON_CFG", "Agent config not found")
    
    enable_tracker = cfg.enable_tracker;
    if(enable_tracker) begin
      tracker_fd = $fopen("packet_tracker.log", "w");
      if(tracker_fd == 0) `uvm_error("MON", "Failed to open packet_tracker.log for writing")
      else `uvm_info("MON", "Packet Tracker ENABLED via Config. Writing to packet_tracker.log", UVM_LOW)
    end
  endfunction

  function void sample_coverage();
    cg_handshake.sample();
    cg_qualifiers.sample();
    cg_packet_boundary.sample();
    if (cfg.has_parity) cg_parity.sample();
  endfunction

  task run_phase(uvm_phase phase);
    axi_stream_master_seq_item item;
    int beat_count = 0;
    int pkt_count =0;
    // Protocol Check Variables
    logic [`TDATA_WIDTH-1:0] prev_tdata;
    logic [`TDATA_WIDTH/8-1:0] prev_tkeep, prev_tstrb;
    logic                    prev_tlast;
    logic [`TID_WIDTH-1:0]   prev_tid;
    logic [`TDEST_WIDTH-1:0] prev_tdest;
    logic [`TUSER_WIDTH-1:0] prev_tuser;

    forever begin
      @(vif.cb_mon);
      
      // REQ_MST_01: TVALID Stability & Data Lock
      if (vif.cb_mon.TVALID === 1 && vif.cb_mon.TREADY === 0) begin
         if (pkt_count > 0) begin
           if (vif.cb_mon.TDATA !== prev_tdata || vif.cb_mon.TKEEP !== prev_tkeep || 
               vif.cb_mon.TSTRB !== prev_tstrb || vif.cb_mon.TLAST !== prev_tlast ||
               vif.cb_mon.TID !== prev_tid     || vif.cb_mon.TDEST !== prev_tdest) begin
             `uvm_error("STABILITY_ERR", "Protocol Violation: Data changed while TVALID=1 and TREADY=0 (REQ_MST_01)")
           end
         end
      end

      if(vif.cb_mon.TVALID === 1 && vif.cb_mon.TREADY === 1) begin
        pkt_count++;
        beat_count++;
        item = axi_stream_master_seq_item::type_id::create("item");
        
        // Sampling
        item.tdata = vif.cb_mon.TDATA;
        item.tkeep = vif.cb_mon.TKEEP;
        item.tstrb = vif.cb_mon.TSTRB;
        item.tlast = vif.cb_mon.TLAST;
        item.tid   = vif.cb_mon.TID;
        item.tdest = vif.cb_mon.TDEST;
        item.tuser = vif.cb_mon.TUSER;

        // Save for stability check
        prev_tdata = item.tdata;
        prev_tkeep = item.tkeep;
        prev_tstrb = item.tstrb;
        prev_tlast = item.tlast;
        prev_tid   = item.tid;
        prev_tdest = item.tdest;

        `uvm_info(get_type_name(), $sformatf("SAMPLED BEAT #%0d", pkt_count), UVM_MEDIUM)

        // Tracker Logic
        if(enable_tracker && tracker_fd != 0) begin
          packet_buffer.push_back(item);
          if(item.tlast) begin
            $fdisplay(tracker_fd, "PACKET_START: Time=%0t", $time);
            packet_buffer.delete();
            beat_count = 0;
          end
        end

        // AXI5 Parity Verification
        if (cfg.has_parity) begin
          for (int i = 0; i < `TDATA_WIDTH/8; i++) begin
            if(vif.cb_mon.TDATACHK[i] !== ~(^item.tdata[i*8 +: 8])) begin
              `uvm_error("PARITY_ERR", $sformatf("Parity mismatch byte %0d", i))
            end
          end
        end

        ap.write(item);
        sample_coverage();
      end else begin
        cg_handshake.sample();
      end
    end
  endtask

  function void final_phase(uvm_phase phase);
    if(enable_tracker && tracker_fd != 0) $fclose(tracker_fd);
  endfunction

endclass : axi_stream_master_monitor
