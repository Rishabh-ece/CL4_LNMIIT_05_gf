// CL-4 top-level integration: seven-state lock controller.
// All child modules use one clock and synchronous active-low internal reset.
module combo_lock #(
  parameter integer DEBOUNCE_CYCLES = 24,
  parameter integer MAX_ATTEMPTS = 3,
  parameter integer UNLOCK_CYCLES = 100,
  parameter integer LOCKOUT_CYCLES = 200,
  parameter integer INTERDIGIT_TIMEOUT_CYCLES = 250,
  parameter [7:0] CODE_VALUE = 8'h9C,
  parameter integer RST_SYNC = 1
) (
  input  wire       clk,
  input  wire       rst_n,
  input  wire [3:0] btn,
  output wire       unlock,
  output wire       locked_out,
  output wire [1:0] attempt_count,
  output wire [2:0] state
);
  wire internal_rst_n;
  wire [3:0] press;
  wire valid;
  wire [1:0] digit;
  wire match;
  wire [2:0] st;
  wire [1:0] fail;
  wire [1:0] fail_n;
  wire [7:0] tmr;
  wire [7:0] tmr_n;

  reset_sync #(
    .RST_SYNC(RST_SYNC)
  ) U_reset_sync (
    .clk(clk),
    .rst_n(rst_n),
    .internal_rst_n(internal_rst_n)
  );

  genvar i;
  generate
    for (i = 0; i < 4; i = i + 1) begin : g_buttons
      button_debounce #(
        .DEBOUNCE_CYCLES(DEBOUNCE_CYCLES)
      ) U_button_debounce (
        .clk(clk),
        .rst_n(internal_rst_n),
        .btn(btn[i]),
        .press(press[i])
      );
    end
  endgenerate

  press_qualify U_press_qualify (
    .press(press),
    .valid(valid),
    .digit(digit)
  );

  code_compare #(
    .CODE_VALUE(CODE_VALUE)
  ) U_code_compare (
    .state(st),
    .digit(digit),
    .match(match)
  );

  entry_fsm #(
    .MAX_ATTEMPTS(MAX_ATTEMPTS),
    .UNLOCK_CYCLES(UNLOCK_CYCLES),
    .LOCKOUT_CYCLES(LOCKOUT_CYCLES),
    .INTERDIGIT_TIMEOUT_CYCLES(INTERDIGIT_TIMEOUT_CYCLES)
  ) U_entry_fsm (
    .clk(clk),
    .rst_n(internal_rst_n),
    .valid(valid),
    .match(match),
    .fail(fail),
    .tmr(tmr),
    .st(st),
    .unlock(unlock),
    .locked_out(locked_out),
    .fail_n(fail_n),
    .tmr_n(tmr_n)
  );

  shared_timer U_shared_timer (
    .clk(clk),
    .rst_n(internal_rst_n),
    .next_tmr(tmr_n),
    .tmr(tmr)
  );

  failure_counter U_failure_counter (
    .clk(clk),
    .rst_n(internal_rst_n),
    .next_fail(fail_n),
    .fail(fail)
  );

  assign state = st;
  assign attempt_count = fail;

  // Invalid configurations are rejected at elaboration/simulation.
  generate
    if ((DEBOUNCE_CYCLES < 1) || (DEBOUNCE_CYCLES > 32) ||
        (MAX_ATTEMPTS < 1) || (MAX_ATTEMPTS > 3) ||
        (UNLOCK_CYCLES < 1) || (UNLOCK_CYCLES > 255) ||
        (LOCKOUT_CYCLES < 1) || (LOCKOUT_CYCLES > 255) ||
        (INTERDIGIT_TIMEOUT_CYCLES < 0) ||
        (INTERDIGIT_TIMEOUT_CYCLES > 255) ||
        ((RST_SYNC != 0) && (RST_SYNC != 1))) begin : g_invalid_parameters
      initial $error("CL-4: parameter value out of range");
    end
  endgenerate
endmodule
