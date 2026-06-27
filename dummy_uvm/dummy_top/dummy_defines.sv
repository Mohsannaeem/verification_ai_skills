////////////////////////////////////////////////////////////////////////
// Module Name    : dummy_defines
// Description    : Dummy Defines blueprint with standardized parameters
///////////////////////////////////////////////////////////////////////
`ifndef DUMMY_DEFINES_SV
`define DUMMY_DEFINES_SV

// Standard Bus Widths
parameter DATA_WIDTH = 32;
parameter ADDR_WIDTH = 32;
parameter ID_WIDTH   = 8;
parameter USER_WIDTH = 4;

// Feature Toggles (AXI5, AHB5, etc.)
parameter HAS_PARITY = 0;
parameter HAS_WAKEUP = 0;

`endif
