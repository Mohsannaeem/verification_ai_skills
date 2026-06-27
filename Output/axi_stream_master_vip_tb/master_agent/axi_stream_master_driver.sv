class axi_stream_master_driver extends uvm_driver#(axi_stream_master_seq_item);
  `uvm_component_utils(axi_stream_master_driver)

  virtual axi_stream_master_if vif;
  axi_stream_master_agent_config cfg;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if(!uvm_config_db#(virtual axi_stream_master_if)::get(this, "", "vif", vif))
      `uvm_fatal("DRV_VIF", "Virtual interface not found in config_db")
    if(!uvm_config_db#(axi_stream_master_agent_config)::get(this, "", "cfg", cfg))
      `uvm_fatal("DRV_CFG", "Agent config not found in config_db")
  endfunction

  task run_phase(uvm_phase phase);
    reset_signals();
    wait(vif.ARESETn == 1);
    
    forever begin
      seq_item_port.get_next_item(req);
      drive_item(req);
      seq_item_port.item_done();
    end
  endtask

  task reset_signals();
    vif.cb_drv.TVALID  <= 0;
    vif.cb_drv.TWAKEUP <= 0;
  endtask

  int pkt_count = 0;

  task drive_item(axi_stream_master_seq_item item);
    pkt_count++;
    
    `uvm_info(get_type_name(), $sformatf("==================================================\n[DRV] DRIVING PACKET #%0d\n==================================================\n%s", pkt_count, item.sprint()), UVM_MEDIUM)

    // 1. Handle Wakeup if enabled (REQ_MST_08)
    if (cfg.has_wakeup || item.twakeup_early > 0) begin
      vif.cb_drv.TWAKEUP <= 1;
      repeat(item.twakeup_early) @(vif.cb_drv);
    end
    
    // Handshake delay
    repeat(item.delay_cycles) @(vif.cb_drv);

    // 2. Drive Payload and Qualifiers
    // TC_MST_014: Inject bit-flip in TDATA if corrupt_tdata is set
    if (item.corrupt_tdata) begin
      vif.cb_drv.TDATA <= item.tdata ^ (1 << $urandom_range(0, `TDATA_WIDTH-1));
      `uvm_warning("DRV_NEG", "Intentionally corrupting TDATA bit-flip (TC_MST_014)")
    end else begin
      vif.cb_drv.TDATA <= item.tdata;
    end
    
    vif.cb_drv.TKEEP  <= item.tkeep;
    vif.cb_drv.TSTRB  <= item.tstrb;
    vif.cb_drv.TLAST  <= item.tlast;
    vif.cb_drv.TID    <= item.tid;
    vif.cb_drv.TDEST  <= item.tdest;
    vif.cb_drv.TUSER  <= item.tuser;

    // 3. AXI5 Parity Calculation (Odd Parity per Byte)
    for (int i = 0; i < `TDATA_WIDTH/8; i++) begin
      logic parity = ~(^item.tdata[i*8 +: 8]);
      if (item.corrupt_parity && i == 0) parity = ~parity; // TC_MST_010: Flip TDATACHK[0]
      vif.cb_drv.TDATACHK[i] <= parity;
    end
    // TC_MST_011: Corrupt TLASTCHK at packet boundary (TLAST=1 + corrupt_parity=1)
    // Normal odd parity: ~(^TLAST). Error injection (even parity): ^TLAST.
    if (item.corrupt_parity && item.tlast)
      vif.cb_drv.TLASTCHK <= ^item.tlast;    // Even parity -> DUT should detect error
    else
      vif.cb_drv.TLASTCHK <= ~(^item.tlast); // Correct odd parity

    // 4. Handshake
    vif.cb_drv.TVALID <= 1;
    
    `uvm_info(get_type_name(), $sformatf("[DRV] Waiting for TREADY for Packet #%0d...", pkt_count), UVM_HIGH)

    do begin
      @(vif.cb_drv);
      // REQ_MST_01 violation: drop TVALID early if requested
      if (item.drop_valid_early && vif.cb_drv.TREADY === 0) begin
         `uvm_warning("DRV_NEG", "Intentionally dropping TVALID before TREADY (Negative Test TC_MST_003)")
         break;
      end
    end while (vif.cb_mon.TREADY !== 1);

    vif.cb_drv.TVALID <= 0;
    
    `uvm_info(get_type_name(), $sformatf("[DRV] Handshake Complete for Packet #%0d\n--------------------------------------------------", pkt_count), UVM_MEDIUM)
  endtask

endclass : axi_stream_master_driver
