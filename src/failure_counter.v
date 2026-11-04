// Consecutive wrong-digit counter. Updated only as directed by FSM.
module failure_counter (
  input  wire       clk,
  input  wire       rst_n,
  input  wire [1:0] next_fail,
  output reg  [1:0] fail
);
  always @(posedge clk) begin
    if (!rst_n) begin
      fail <= 2'd0;
    end else begin
      fail <= next_fail;
    end
  end
endmodule
