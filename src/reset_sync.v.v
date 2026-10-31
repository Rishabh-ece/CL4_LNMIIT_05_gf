// CL-4 optional two-flop reset synchronizer. No asynchronous resets.
module reset_sync #(
  parameter integer RST_SYNC = 1
) (
  input  wire clk,
  input  wire rst_n,
  output wire internal_rst_n
);
  generate
    if (RST_SYNC == 1) begin : g_sync
      // Intentionally no reset on either synchronizer flop.
      reg rst_s1;
      reg rst_s2;
      always @(posedge clk) begin
        rst_s1 <= rst_n;
        rst_s2 <= rst_s1;
      end
      assign internal_rst_n = rst_s2;
    end else begin : g_direct
      assign internal_rst_n = rst_n;
    end
  endgenerate
endmodule
