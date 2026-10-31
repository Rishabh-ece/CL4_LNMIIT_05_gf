/*
 * CL4 - Four-button combination lock
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

  wire unlock;
  wire locked_out;
  wire [1:0] attempt_count;
  wire [2:0] state;

  // Four active-high buttons are connected to ui_in[3:0].
  combo_lock U_combo_lock (
    .clk(clk),
    .rst_n(rst_n),
    .btn(ui_in[3:0]),
    .unlock(unlock),
    .locked_out(locked_out),
    .attempt_count(attempt_count),
    .state(state)
  );

  // Output mapping: lock status, then RGB channels.
  // LOCK_STATUS = 0 means locked; LOCK_STATUS = 1 means unlocked.
  // Red is asserted while locked; green is asserted while unlocked.
  assign uo_out[0]   = unlock;
  assign uo_out[1]   = ~unlock;
  assign uo_out[2]   = unlock;
  assign uo_out[3]   = 1'b0;
  assign uo_out[7:4] = 4'b0000;

  // No bidirectional pins are used.
  assign uio_out = 8'b00000000;
  assign uio_oe  = 8'b00000000;

  // Keep unused interface/internal signals visible to lint tools.
  wire _unused = &{ena, uio_in, locked_out, attempt_count, state, 1'b0};

endmodule

`default_nettype wire
