////////////////////////////////////////////////////////////////////////
// Module Name    : dummy_tb_top
// Description    : Dummy Top level blueprint
///////////////////////////////////////////////////////////////////////
module dummy_tb_top;
  import uvm_pkg::*;
  import dummy_test_pkg::*;

  bit ACLK;
  bit ARESETn;

  always #5 ACLK = ~ACLK;

  dummy_intf vif(ACLK, ARESETn);

  initial begin
    uvm_config_db#(virtual dummy_intf)::set(null, "*", "dummy_if", vif);
    run_test();
  end

  initial begin
    ACLK = 0;
    ARESETn = 0;
    #20 ARESETn = 1;
  end

endmodule
