
/*
 * CL4 - Four-button, four-digit combination lock
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_CL4_LNMIIT (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

  wire       unlock;
  wire       locked_out;
  wire [1:0] attempt_count;
  wire [2:0] state;

  // Four active-high combination buttons.
  combo_lock U_combo_lock (
    .clk(clk),
    .rst_n(rst_n),
    .btn(ui_in[3:0]),
    .unlock(unlock),
    .locked_out(locked_out),
    .attempt_count(attempt_count),
    .state(state)
  );

  // Outputs match info.yaml pin mapping.
  assign uo_out[0] = unlock;
  assign uo_out[1] = locked_out;
  assign uo_out[2] = attempt_count[0];
  assign uo_out[3] = attempt_count[1];
  assign uo_out[4] = state[0];  // RGB Red
  assign uo_out[5] = state[1];  // RGB Green
  assign uo_out[6] = state[2];  // RGB Blue
  assign uo_out[7] = 1'b0;

  // All bidirectional pins are unused.
  assign uio_out = 8'b0000_0000;
  assign uio_oe  = 8'b0000_0000;

  // Suppress unused-input warnings.
  wire _unused = &{ena, ui_in[7:4], uio_in, 1'b0};

endmodule

`default_nettype wire
