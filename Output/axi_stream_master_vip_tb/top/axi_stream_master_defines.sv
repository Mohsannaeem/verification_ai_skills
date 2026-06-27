`ifndef AXI_STREAM_MASTER_DEFINES_SV
`define AXI_STREAM_MASTER_DEFINES_SV

// Protocol Parameters (Macros for Global Visibility)
`define TDATA_WIDTH 32
`define TID_WIDTH   8
`define TDEST_WIDTH 4
`define TUSER_WIDTH 4

// AXI5 Feature Configuration
`define HAS_PARITY 1
`define HAS_WAKEUP 1

// General UVM configuration
`define CLK_PERIOD 10

`endif
