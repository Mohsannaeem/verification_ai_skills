// AXI-Stream Slave VIP Interface
// Verification Role: SLAVE — VIP drives TREADY + TREADYCHK
// DUT Role:          MASTER — DUT drives all payload + check signals
`include "axi_stream_slave_vip_defines.sv"

interface axi_stream_slave_vip_if (input bit ACLK);

  // ── Reset (plain logic — tb_top drives it; not a port to avoid multi-driver) ──
  logic ARESETn;

  // ── DUT Master outputs (inputs to VIP) ──────────────────────────────────────
  logic                       TVALID;
  logic [`TDATA_WIDTH-1:0]    TDATA;
  logic [`TDATA_WIDTH/8-1:0]  TKEEP;
  logic [`TDATA_WIDTH/8-1:0]  TSTRB;
  logic                       TLAST;
  logic [`TID_WIDTH-1:0]      TID;
  logic [`TDEST_WIDTH-1:0]    TDEST;
  logic [`TUSER_WIDTH-1:0]    TUSER;
  logic                       TWAKEUP;
  // AXI5 check signals driven by DUT Master
  logic [`TDATA_WIDTH/8-1:0]  TDATACHK;
  logic                       TVALIDCHK;
  logic                       TLASTCHK;
  logic                       TWAKEUPCHK;

  // ── VIP Slave outputs (driven by VIP Slave agent) ───────────────────────────
  logic                       TREADY;
  logic                       TREADYCHK;   // AXI5: odd parity of TREADY

  // ── Driver clocking block — VIP drives TREADY/TREADYCHK, samples DUT inputs ─
  clocking cb_drv @(posedge ACLK);
    output TREADY, TREADYCHK;
    input  TVALID, TDATA, TKEEP, TSTRB, TLAST, TID, TDEST, TUSER, TWAKEUP;
    input  TDATACHK, TVALIDCHK, TLASTCHK, TWAKEUPCHK;
  endclocking

  // ── Monitor clocking block — pure observation of all signals ─────────────────
  clocking cb_mon @(posedge ACLK);
    input  ARESETn, TVALID, TREADY, TDATA, TKEEP, TSTRB, TLAST;
    input  TID, TDEST, TUSER, TWAKEUP;
    input  TDATACHK, TVALIDCHK, TLASTCHK, TWAKEUPCHK, TREADYCHK;
  endclocking

endinterface
