class axi_stream_master_agent_config extends uvm_object;
  `uvm_object_utils(axi_stream_master_agent_config)

  uvm_active_passive_enum is_active = UVM_ACTIVE;
  bit has_functional_coverage = 1;
  bit has_scoreboard = 1;
  bit has_parity = 1;
  bit has_wakeup = 1;
  bit enable_tracker = 0;

  function new(string name = "axi_stream_master_agent_config");
    super.new(name);
    process_cli_args();
  endfunction

  function void process_cli_args();
    uvm_cmdline_processor clp = uvm_cmdline_processor::get_inst();
    string args[$];
    if (clp.get_arg_values("+ENABLE_TRACKER=", args) > 0) begin
      enable_tracker = args[0].atoi();
    end
  endfunction

endclass : axi_stream_master_agent_config
