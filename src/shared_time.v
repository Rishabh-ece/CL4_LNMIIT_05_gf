// One 8-bit timer shared by entry timeout, UNLOCK and LOCKOUT.
// The FSM determines whether to load, decrement, or hold via next_tmr.
module shared_time (
  input  wire       clk,
  input  wire       rst_n,
  input  wire [11:0] next_tmr,
  output reg  [11:0] tmr
);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tmr <= 12'd0;
    end else begin
      tmr <= next_tmr;
    end
  end
endmodule
