// AXI-Stream Slave VIP Agent Configuration
class axi_stream_slave_vip_agent_config extends uvm_object;
  `uvm_object_utils(axi_stream_slave_vip_agent_config)

  virtual axi_stream_slave_vip_if vif;

  uvm_active_passive_enum is_active   = UVM_ACTIVE;
  bit has_parity                      = `HAS_PARITY;   // enable TREADYCHK + parity checks
  bit has_wakeup                      = `HAS_WAKEUP;   // enable TWAKEUP monitoring
  bit continuous_pkt_mode             = 0;             // Continuous_Packets constraint check
  bit enable_tracker                  = 1;             // write slave_packet_tracker.log
  int watchdog_cycles                 = `TVALID_WATCHDOG_MAX;

  function new(string name = "axi_stream_slave_vip_agent_config");
    super.new(name);
    if ($test$plusargs("ENABLE_TRACKER"))
      enable_tracker = 1;
    if ($test$plusargs("CONT_PKT_MODE"))
      continuous_pkt_mode = 1;
  endfunction

endclass
