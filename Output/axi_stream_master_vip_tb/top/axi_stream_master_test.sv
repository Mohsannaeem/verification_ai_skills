// AXI-Stream Master Test Suite
// Explicit unrolling to ensure total Factory registration reliability

class axi_stream_master_base_test extends uvm_test;
  `uvm_component_utils(axi_stream_master_base_test)

  axi_stream_master_env env;
  axi_stream_master_env_config cfg;

  function new(string name = "axi_stream_master_base_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = axi_stream_master_env::type_id::create("env", this);
    cfg = axi_stream_master_env_config::type_id::create("cfg");
    cfg.agent_cfg.is_active = UVM_ACTIVE;
    uvm_config_db#(axi_stream_master_env_config)::set(this, "*", "cfg", cfg);
  endfunction
endclass

// Explicit Test Case Implementations
`define AXI_STREAM_TEST_UNROLL(ID) \
class axi_stream_master_``ID``_test extends axi_stream_master_base_test; \
  `uvm_component_utils(axi_stream_master_``ID``_test) \
  function new(string name = `"axi_stream_master_``ID``_test`", uvm_component parent = null); super.new(name, parent); endfunction \
  task run_phase(uvm_phase phase); \
    axi_stream_master_``ID``_seq seq = axi_stream_master_``ID``_seq::type_id::create("seq"); \
    phase.raise_objection(this); \
    seq.start(env.agent.sqr); \
    phase.drop_objection(this); \
  endtask \
endclass

`AXI_STREAM_TEST_UNROLL(tc_mst_001)
`AXI_STREAM_TEST_UNROLL(tc_mst_002)
`AXI_STREAM_TEST_UNROLL(tc_mst_003)
`AXI_STREAM_TEST_UNROLL(tc_mst_004)
`AXI_STREAM_TEST_UNROLL(tc_mst_005)
`AXI_STREAM_TEST_UNROLL(tc_mst_006)
`AXI_STREAM_TEST_UNROLL(tc_mst_007)
`AXI_STREAM_TEST_UNROLL(tc_mst_008)
`AXI_STREAM_TEST_UNROLL(tc_mst_009)
`AXI_STREAM_TEST_UNROLL(tc_mst_010)
`AXI_STREAM_TEST_UNROLL(tc_mst_011)
`AXI_STREAM_TEST_UNROLL(tc_mst_012)
`AXI_STREAM_TEST_UNROLL(tc_mst_013)
`AXI_STREAM_TEST_UNROLL(tc_mst_014)
`AXI_STREAM_TEST_UNROLL(tc_mst_015)
`AXI_STREAM_TEST_UNROLL(tc_mst_016)
`AXI_STREAM_TEST_UNROLL(tc_mst_017)
`AXI_STREAM_TEST_UNROLL(tc_mst_018)
`AXI_STREAM_TEST_UNROLL(tc_mst_019)
`AXI_STREAM_TEST_UNROLL(tc_mst_020)
`AXI_STREAM_TEST_UNROLL(tc_mst_021)
`AXI_STREAM_TEST_UNROLL(tc_mst_022)
`AXI_STREAM_TEST_UNROLL(tc_mst_023)
`AXI_STREAM_TEST_UNROLL(tc_mst_024)
`AXI_STREAM_TEST_UNROLL(tc_mst_025)
`AXI_STREAM_TEST_UNROLL(tc_mst_026)
`AXI_STREAM_TEST_UNROLL(tc_mst_027)