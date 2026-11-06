// CL-4 reset synchronizer (CL4-SPEC-001 2.1, 4.2).
//
// rs1 samples rst_n, rs2 samples rs1, both on the rising edge of clk.
// Neither flop has a reset of its own, and there is no asynchronous reset.
// rs2 is the internal reset.
//
// RST_SYNC = 1 : internal_rst_n = rs2 (two-flop synchronizer).
// RST_SYNC = 0 : internal_rst_n = rst_n directly (allowed only when the
//                harness guarantees rst_n is synchronous to clk).
//                rs1/rs2 are then unused and removed by synthesis.

module reset_sync #(
  parameter integer RST_SYNC = 1
) (
  input  wire clk,
  input  wire rst_n,           // raw reset from the board, active low
  output wire internal_rst_n   // reset for the rest of the design, active low
);

  reg rs1;
  reg rs2;

  always @(posedge clk) begin
    rs1 <= rst_n;    // first flop samples the raw reset
    rs2 <= rs1;      // second flop samples the first
  end

  assign internal_rst_n = (RST_SYNC == 1) ? rs2 : rst_n;

endmodule
