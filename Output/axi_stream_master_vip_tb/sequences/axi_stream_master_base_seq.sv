class axi_stream_master_base_seq extends uvm_sequence#(axi_stream_master_seq_item);
	`uvm_object_utils(axi_stream_master_base_seq)

	function new(string name = "axi_stream_master_base_seq");
		super.new(name);
	endfunction : new

	task body ();
		axi_stream_master_seq_item req;
		req = axi_stream_master_seq_item::type_id::create("req");
		start_item(req);
		if(!req.randomize()) `uvm_error("SEQ", "Randomization failed")
		finish_item(req);
	endtask : body

endclass : axi_stream_master_base_seq
