// Accept only cycles containing exactly one debounced press.
module press_qualify (
  input  wire [3:0] press,
  output wire       valid,
  output wire [1:0] digit
);
  assign valid = (press == 4'b0001) ||
                 (press == 4'b0010) ||
                 (press == 4'b0100) ||
                 (press == 4'b1000);

  // Meaningful only when valid=1 (CL4-SPEC-001 Section 4.2).
  assign digit = {press[3] | press[2], press[3] | press[1]};
endmodule
