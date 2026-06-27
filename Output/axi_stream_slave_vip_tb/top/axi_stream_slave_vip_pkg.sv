// AXI-Stream Slave VIP Package — includes all classes in dependency order
`include "axi_stream_slave_vip_defines.sv"

package axi_stream_slave_vip_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // Sequence item
  `include "axi_stream_slave_vip_seq_item.sv"

  // Configuration objects
  `include "axi_stream_slave_vip_agent_config.sv"
  `include "axi_stream_slave_vip_env_config.sv"

  // Agent internals
  `include "axi_stream_slave_vip_sequencer.sv"
  `include "axi_stream_slave_vip_driver.sv"
  `include "axi_stream_slave_vip_monitor.sv"
  `include "axi_stream_slave_vip_agent.sv"

  // Environment internals
  `include "axi_stream_slave_vip_scoreboard.sv"
  `include "axi_stream_slave_vip_env.sv"

  // Sequences
  `include "axi_stream_slave_vip_base_seq.sv"
  `include "axi_stream_slave_vip_test_sequences.sv"

  // Tests
  `include "axi_stream_slave_vip_test.sv"

endpackage
