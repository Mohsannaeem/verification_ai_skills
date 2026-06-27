// AXI-Stream Slave VIP — Global Defines
// Verification Role: SLAVE (VIP is Receiver, drives TREADY)
// DUT Role:          MASTER (DUT drives TVALID/TDATA)
`ifndef AXI_STREAM_SLAVE_VIP_DEFINES_SV
`define AXI_STREAM_SLAVE_VIP_DEFINES_SV

`define TDATA_WIDTH          32
`define TID_WIDTH             8
`define TDEST_WIDTH           4
`define TUSER_WIDTH           4
`define HAS_PARITY            1
`define HAS_WAKEUP            1
`define CLK_PERIOD           10
`define TREADY_STALL_MAX     32
`define TVALID_WATCHDOG_MAX  100000
// Parity helper: odd parity of N-bit value = ^(~value) but for 1-bit: ~bit
// For TDATA bytes: parity of 8-bit = reduction XOR of 8 bits (even) flipped = ~^byte

`endif
