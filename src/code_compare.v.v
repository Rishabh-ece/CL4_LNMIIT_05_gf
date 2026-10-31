// Compare the pressed digit with the code digit selected by FSM state.
module code_compare #(
  parameter [7:0] CODE_VALUE = 8'h9C
) (
  input  wire [2:0] state,
  input  wire [1:0] digit,
  output wire       match
);
  localparam [2:0] IDLE = 3'b000;
  localparam [2:0] DIGIT2 = 3'b001;
  localparam [2:0] DIGIT3 = 3'b010;
  localparam [2:0] DIGIT4 = 3'b011;

  reg [1:0] want;
  always @(*) begin
    want = 2'b00;
    case (state)
      IDLE:    want = CODE_VALUE[7:6];
      DIGIT2:  want = CODE_VALUE[5:4];
      DIGIT3:  want = CODE_VALUE[3:2];
      DIGIT4:  want = CODE_VALUE[1:0];
      default: want = 2'b00;
    endcase
  end
  assign match = (digit == want);
endmodule
