`timescale 1ps/1fs
module axi_stream_master_tb_top;
  import uvm_pkg::*;
  import axi_stream_master_pkg::*;

  // Global Clock and Reset
  bit ACLK;
  bit ARESETn;

  // Clock Generation
  always #5 ACLK = ~ACLK;

  // Interface Instantiation
  axi_stream_master_if vif(ACLK, ARESETn);

  initial begin
    // Virtual Interface Registration
    uvm_config_db#(virtual axi_stream_master_if)::set(null, "*", "vif", vif);
    
    // Start UVM Test
    run_test();
  end

  // Reset Control
  initial begin
    ARESETn = 0;
    #25 ARESETn = 1;
  end
  /*###########################################################
  DUT Instantiation: Started Don't edit below this section
  #############################################################*/
  axis_data_fifo_v2_0_0_top #(
    .C_FAMILY("zynq"),
    .C_AXIS_TDATA_WIDTH(32),
    .C_AXIS_TID_WIDTH(8),
    .C_AXIS_TDEST_WIDTH(4),
    .C_AXIS_TUSER_WIDTH(4),
    .C_AXIS_SIGNAL_SET('B00000000000000000000000000000011),
    .C_FIFO_DEPTH(512),
    .C_FIFO_MODE(1),
    .C_IS_ACLK_ASYNC(0),
    .C_SYNCHRONIZER_STAGE(3),
    .C_ACLKEN_CONV_MODE(0),
    .C_ECC_MODE(0),
    .C_FIFO_MEMORY_TYPE("auto"),
    .C_USE_ADV_FEATURES(825241648),
    .C_PROG_EMPTY_THRESH(5),
    .C_PROG_FULL_THRESH(11)
  ) inst (
    .s_axis_aresetn(ARESETn),
    .s_axis_aclk(ACLK),
    .s_axis_aclken(1'H1),
    .s_axis_tvalid(vif.TVALID),
    .s_axis_tready(vif.TREADY),
    .s_axis_tdata(vif.TDATA),
    .s_axis_tstrb(vif.TSTRB),
    .s_axis_tkeep(vif.TKEEP),
    .s_axis_tlast(vif.TLAST),
    .s_axis_tid(vif.TID),
    .s_axis_tdest(vif.TDEST),
    .s_axis_tuser(vif.TUSER),
    .m_axis_aclk(1'H0),
    .m_axis_aclken(1'H1),
    .m_axis_tvalid(),
    .m_axis_tready(1'h0),
    .m_axis_tdata(),
    .m_axis_tstrb(),
    .m_axis_tkeep(),
    .m_axis_tlast(),
    .m_axis_tid(),
    .m_axis_tdest(),
    .m_axis_tuser(),
    .axis_wr_data_count(),
    .axis_rd_data_count(),
    .almost_empty(),
    .prog_empty(),
    .almost_full(),
    .prog_full(),
    .sbiterr(),
    .dbiterr(),
    .injectsbiterr(1'H0),
    .injectdbiterr(1'H0)
  );
  /*###########################################################
   DUT Instantiation: Ended Don't edit above section
  #############################################################*/
endmodule


