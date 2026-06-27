// AXI-Stream Slave VIP Base Sequence
// Sends randomized TREADY control items to the driver
class axi_stream_slave_vip_base_seq extends uvm_sequence #(axi_stream_slave_vip_seq_item);
  `uvm_object_utils(axi_stream_slave_vip_base_seq)

  int num_items = 20;

  function new(string name = "axi_stream_slave_vip_base_seq");
    super.new(name);
  endfunction

  virtual task body();
    axi_stream_slave_vip_seq_item item;
    repeat (num_items) begin
      item = axi_stream_slave_vip_seq_item::type_id::create("item");
      start_item(item);
      if (!item.randomize())
        `uvm_fatal("SEQ", "Randomization failed in base_seq")
      finish_item(item);
    end
  endtask

endclass

// ── Macro to define a named test sequence with specific constraint overrides ──
`define DEF_SLV_VIP_SEQ(NAME, BODY) \
  class axi_stream_slv_vip_``NAME``_seq extends axi_stream_slave_vip_base_seq; \
    `uvm_object_utils(axi_stream_slv_vip_``NAME``_seq) \
    function new(string name = `"axi_stream_slv_vip_``NAME``_seq`"); super.new(name); endfunction \
    virtual task body(); \
      axi_stream_slave_vip_seq_item item; \
      BODY \
    endtask \
  endclass
