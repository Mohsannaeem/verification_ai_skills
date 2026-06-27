interface axi_stream_master_if (input bit ACLK, input bit ARESETn);
  import uvm_pkg::*;
  `include "uvm_macros.svh"
  `include "axi_stream_master_defines.sv"

  // Handshake Signals
  logic TVALID;
  logic TREADY;

  // Payload & Qualifiers
  logic [`TDATA_WIDTH-1:0] TDATA; 
  logic [`TDATA_WIDTH/8-1:0]  TSTRB;
  logic [`TDATA_WIDTH/8-1:0]  TKEEP;
  logic        TLAST;

  // Routing & Metadata
  logic [`TID_WIDTH-1:0]  TID;
  logic [`TDEST_WIDTH-1:0]  TDEST;
  logic [`TUSER_WIDTH-1:0]  TUSER;

  // AXI5 Specific
  logic        TWAKEUP;
  logic [`TDATA_WIDTH/8-1:0]  TDATACHK;
  logic        TLASTCHK;

  // Clocking Block for Driver
  clocking cb_drv @(posedge ACLK);
    output TVALID, TDATA, TSTRB, TKEEP, TLAST, TID, TDEST, TUSER, TWAKEUP, TDATACHK, TLASTCHK;
    input  TREADY;
  endclocking

  // Clocking Block for Monitor
  clocking cb_mon @(posedge ACLK);
    input TVALID, TREADY, TDATA, TSTRB, TKEEP, TLAST, TID, TDEST, TUSER, TWAKEUP, TDATACHK, TLASTCHK;
  endclocking

  modport master_drv (clocking cb_drv, input ACLK, ARESETn);
  modport master_mon (clocking cb_mon, input ACLK, ARESETn);

endinterface : axi_stream_master_if
