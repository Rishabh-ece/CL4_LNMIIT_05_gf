// Complete-code comparison. Meaningful only when the FSM is in DIGIT4 and
// valid=1: 'prefix' holds digits 1-3, 'digit' is the live fourth digit.
module code_compare #(
  parameter [7:0] CODE_VALUE = 8'h9C
) (
  input  wire [7:2] prefix,   // stored digits 1..3
  input  wire [1:0] digit,    // digit from press_qualify (this cycle)
  output wire       match
);
  wire [7:0] complete_code = {prefix, digit};
  assign match = (complete_code == CODE_VALUE);
endmodule
