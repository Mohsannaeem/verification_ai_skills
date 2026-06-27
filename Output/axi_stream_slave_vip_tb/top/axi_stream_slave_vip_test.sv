// AXI-Stream Slave VIP Tests — base test + 46 concrete tests
class axi_stream_slave_vip_base_test extends uvm_test;
  `uvm_component_utils(axi_stream_slave_vip_base_test)

  axi_stream_slave_vip_env         env;
  axi_stream_slave_vip_env_config  cfg;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    virtual axi_stream_slave_vip_if vif;
    super.build_phase(phase);

    cfg = axi_stream_slave_vip_env_config::type_id::create("cfg");

    if (!uvm_config_db #(virtual axi_stream_slave_vip_if)::get(this, "", "vif", vif))
      `uvm_fatal("CFG", "No VIF in test build_phase")

    cfg.agent_cfg.vif = vif;
    uvm_config_db #(axi_stream_slave_vip_env_config)::set(this, "env", "cfg", cfg);
    env = axi_stream_slave_vip_env::type_id::create("env", this);
  endfunction

  function void end_of_elaboration_phase(uvm_phase phase);
    `uvm_info("TEST", $sformatf("[TEST] %s elaborated OK", get_type_name()), UVM_NONE)
    uvm_top.print_topology();
  endfunction

  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    // Derived classes start their sequence here
    phase.drop_objection(this);
  endtask

endclass

// ── Macro: define a concrete test class ────────────────────────────────────
`define DEF_SLV_VIP_TEST(ID, SEQ_CLASS) \
class axi_stream_slv_vip_tc_``ID``_test extends axi_stream_slave_vip_base_test; \
  `uvm_component_utils(axi_stream_slv_vip_tc_``ID``_test) \
  function new(string name, uvm_component parent); super.new(name, parent); endfunction \
  task run_phase(uvm_phase phase); \
    SEQ_CLASS seq; \
    phase.raise_objection(this); \
    seq = SEQ_CLASS::type_id::create("seq"); \
    seq.start(env.agent.sqr); \
    phase.drop_objection(this); \
  endtask \
endclass

`DEF_SLV_VIP_TEST(001, axi_stream_slv_vip_tc_001_seq)
`DEF_SLV_VIP_TEST(002, axi_stream_slv_vip_tc_002_seq)
`DEF_SLV_VIP_TEST(003, axi_stream_slv_vip_tc_003_seq)
`DEF_SLV_VIP_TEST(004, axi_stream_slv_vip_tc_004_seq)
`DEF_SLV_VIP_TEST(005, axi_stream_slv_vip_tc_005_seq)
`DEF_SLV_VIP_TEST(006, axi_stream_slv_vip_tc_006_seq)
`DEF_SLV_VIP_TEST(007, axi_stream_slv_vip_tc_007_seq)
`DEF_SLV_VIP_TEST(008, axi_stream_slv_vip_tc_008_seq)
`DEF_SLV_VIP_TEST(009, axi_stream_slv_vip_tc_009_seq)
`DEF_SLV_VIP_TEST(010, axi_stream_slv_vip_tc_010_seq)
`DEF_SLV_VIP_TEST(011, axi_stream_slv_vip_tc_011_seq)
`DEF_SLV_VIP_TEST(012, axi_stream_slv_vip_tc_012_seq)
`DEF_SLV_VIP_TEST(013, axi_stream_slv_vip_tc_013_seq)
`DEF_SLV_VIP_TEST(014, axi_stream_slv_vip_tc_014_seq)
`DEF_SLV_VIP_TEST(015, axi_stream_slv_vip_tc_015_seq)
`DEF_SLV_VIP_TEST(016, axi_stream_slv_vip_tc_016_seq)
`DEF_SLV_VIP_TEST(017, axi_stream_slv_vip_tc_017_seq)
`DEF_SLV_VIP_TEST(018, axi_stream_slv_vip_tc_018_seq)
`DEF_SLV_VIP_TEST(019, axi_stream_slv_vip_tc_019_seq)
`DEF_SLV_VIP_TEST(020, axi_stream_slv_vip_tc_020_seq)
`DEF_SLV_VIP_TEST(021, axi_stream_slv_vip_tc_021_seq)
`DEF_SLV_VIP_TEST(022, axi_stream_slv_vip_tc_022_seq)
`DEF_SLV_VIP_TEST(023, axi_stream_slv_vip_tc_023_seq)
`DEF_SLV_VIP_TEST(024, axi_stream_slv_vip_tc_024_seq)
`DEF_SLV_VIP_TEST(025, axi_stream_slv_vip_tc_025_seq)
`DEF_SLV_VIP_TEST(026, axi_stream_slv_vip_tc_026_seq)
`DEF_SLV_VIP_TEST(027, axi_stream_slv_vip_tc_027_seq)
`DEF_SLV_VIP_TEST(028, axi_stream_slv_vip_tc_028_seq)
`DEF_SLV_VIP_TEST(029, axi_stream_slv_vip_tc_029_seq)
`DEF_SLV_VIP_TEST(030, axi_stream_slv_vip_tc_030_seq)
`DEF_SLV_VIP_TEST(031, axi_stream_slv_vip_tc_031_seq)
`DEF_SLV_VIP_TEST(032, axi_stream_slv_vip_tc_032_seq)
`DEF_SLV_VIP_TEST(033, axi_stream_slv_vip_tc_033_seq)
`DEF_SLV_VIP_TEST(034, axi_stream_slv_vip_tc_034_seq)
`DEF_SLV_VIP_TEST(035, axi_stream_slv_vip_tc_035_seq)
`DEF_SLV_VIP_TEST(036, axi_stream_slv_vip_tc_036_seq)
`DEF_SLV_VIP_TEST(037, axi_stream_slv_vip_tc_037_seq)
`DEF_SLV_VIP_TEST(038, axi_stream_slv_vip_tc_038_seq)
`DEF_SLV_VIP_TEST(039, axi_stream_slv_vip_tc_039_seq)
`DEF_SLV_VIP_TEST(040, axi_stream_slv_vip_tc_040_seq)
`DEF_SLV_VIP_TEST(041, axi_stream_slv_vip_tc_041_seq)
`DEF_SLV_VIP_TEST(042, axi_stream_slv_vip_tc_042_seq)
`DEF_SLV_VIP_TEST(043, axi_stream_slv_vip_tc_043_seq)
`DEF_SLV_VIP_TEST(044, axi_stream_slv_vip_tc_044_seq)
`DEF_SLV_VIP_TEST(045, axi_stream_slv_vip_tc_045_seq)
`DEF_SLV_VIP_TEST(046, axi_stream_slv_vip_tc_046_seq)
