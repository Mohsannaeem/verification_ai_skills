////////////////////////////////////////////////////////////////////////
// Module Name    : dummy_callback
// Description    : Dummy Callback blueprint
///////////////////////////////////////////////////////////////////////
class dummy_callback extends uvm_callback;
  `uvm_object_utils(dummy_callback)

  function new(string name="dummy_callback");
    super.new(name);
  endfunction

  virtual task pre_drive();
    // LOGIC_START
    // LOGIC_END
  endtask

  virtual task post_drive();
    // LOGIC_START
    // LOGIC_END
  endtask
endclass
