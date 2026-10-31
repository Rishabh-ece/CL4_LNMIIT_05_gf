// One 8-bit timer shared by entry timeout, UNLOCK and LOCKOUT.
// The FSM determines whether to load, decrement, or hold via next_tmr.
module shared_timer (
  input  wire       clk,
  input  wire       rst_n,
  input  wire [7:0] next_tmr,
  output reg  [7:0] tmr
);
  always @(posedge clk) begin
    if (!rst_n) begin
      tmr <= 8'd0;
    end else begin
      tmr <= next_tmr;
    end
  end
endmodule
