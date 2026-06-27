// AXI-Stream Slave VIP Driver
// Drives TREADY back-pressure patterns and TREADYCHK (AXI5 odd parity on TREADY).
class axi_stream_slave_vip_driver extends uvm_driver #(axi_stream_slave_vip_seq_item);
  `uvm_component_utils(axi_stream_slave_vip_driver)

  virtual axi_stream_slave_vip_if vif;
  axi_stream_slave_vip_agent_config cfg;

  int beat_num = 0;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db #(virtual axi_stream_slave_vip_if)::get(this, "", "vif", vif))
      `uvm_fatal("CFG", "No VIF for axi_stream_slave_vip_driver")
    if (!uvm_config_db #(axi_stream_slave_vip_agent_config)::get(this, "", "cfg", cfg))
      `uvm_fatal("CFG", "No CFG for axi_stream_slave_vip_driver")
  endfunction

  // ── Compute odd parity for TREADY (1-bit signal → parity = ~TREADY) ─────────
  function automatic logic compute_treadychk(logic tready_val);
    return ~tready_val;
  endfunction

  // ── Drive TREADYCHK every cycle while ARESETn=1 ──────────────────────────────
  task drive_treadychk_continuous();
    fork
      forever begin
        @(vif.cb_drv);
        if (vif.ARESETn === 1'b1)
          vif.cb_drv.TREADYCHK <= compute_treadychk(vif.TREADY);
        else
          vif.cb_drv.TREADYCHK <= 1'b0;
      end
    join_none
  endtask

  // ── Reset handling: hold TREADY=0 during reset ───────────────────────────────
  task wait_for_reset_done();
    vif.cb_drv.TREADY    <= 1'b0;
    vif.cb_drv.TREADYCHK <= 1'b0;
    @(posedge vif.ARESETn);
    @(vif.cb_drv);
  endtask

  // ── Main run phase ────────────────────────────────────────────────────────────
  task run_phase(uvm_phase phase);
    axi_stream_slave_vip_seq_item req;

    // Initial deassert
    vif.cb_drv.TREADY    <= 1'b0;
    vif.cb_drv.TREADYCHK <= 1'b0;

    // Wait for reset
    wait_for_reset_done();

    // Start continuous TREADYCHK generation
    if (cfg.has_parity)
      drive_treadychk_continuous();

    forever begin
      seq_item_port.get_next_item(req);
      drive_tready(req);
      seq_item_port.item_done();
    end
  endtask

  // ── TREADY driving logic ──────────────────────────────────────────────────────
  task drive_tready(axi_stream_slave_vip_seq_item req);
    int watchdog_cnt;

    // --- Pre-assertion mode: assert TREADY before TVALID arrives ---
    if (req.tready_pre_assert) begin
      `uvm_info("DRV", $sformatf("[DRV] PRE-ASSERT mode: TREADY=1 before TVALID"), UVM_MEDIUM)
      vif.cb_drv.TREADY <= 1'b1;
      // Wait for handshake (TVALID=1 while TREADY=1)
      watchdog_cnt = 0;
      while (vif.cb_mon.TVALID !== 1'b1 || vif.cb_mon.TREADY !== 1'b1) begin
        @(vif.cb_drv);
        watchdog_cnt++;
        if (watchdog_cnt > cfg.watchdog_cycles)
          `uvm_fatal("DRV", "[DRV] WATCHDOG: No handshake for too long (pre-assert mode)")
      end
      @(vif.cb_drv);
      vif.cb_drv.TREADY <= 1'b0;
      return;
    end

    // --- Standard mode: wait for TVALID, then apply stall, then accept ---
    // Wait for DUT Master to assert TVALID
    `uvm_info("DRV", "[DRV] Waiting for TVALID from DUT Master...", UVM_HIGH)
    watchdog_cnt = 0;
    while (vif.cb_mon.TVALID !== 1'b1) begin
      @(vif.cb_drv);
      watchdog_cnt++;
      if (watchdog_cnt > cfg.watchdog_cycles)
        `uvm_fatal("DRV", "[DRV] WATCHDOG: TVALID never asserted by DUT Master")
    end

    // Apply stall (back-pressure)
    if (req.tready_stall_cycles > 0) begin
      `uvm_info("DRV", $sformatf("[DRV] Back-pressure: TREADY=0 for %0d cycles",
                                  req.tready_stall_cycles), UVM_MEDIUM)
      vif.cb_drv.TREADY <= 1'b0;
      repeat (req.tready_stall_cycles) @(vif.cb_drv);
    end

    // Assert TREADY to accept the transfer
    `uvm_info("DRV", $sformatf(
      "[DRV] Asserting TREADY (beat #%0d) | TDATA=0x%08h TLAST=%0b TID=%0h",
      beat_num+1, vif.cb_mon.TDATA, vif.cb_mon.TLAST, vif.cb_mon.TID), UVM_MEDIUM)
    vif.cb_drv.TREADY <= 1'b1;
    @(vif.cb_drv);  // handshake cycle
    vif.cb_drv.TREADY <= 1'b0;
    beat_num++;

    `uvm_info("DRV", $sformatf("[DRV] Beat #%0d handshake complete", beat_num), UVM_HIGH)
  endtask

endclass
