// CL-4 entry FSM: combinational next values, registered state/outputs.
// Timer and failure registers reside in shared_timer / failure_counter.
module entry_fsm #(
  parameter integer MAX_ATTEMPTS = 3,
  parameter integer UNLOCK_CYCLES = 100,
  parameter integer LOCKOUT_CYCLES = 200,
  parameter integer INTERDIGIT_TIMEOUT_CYCLES = 250
) (
  input  wire       clk,
  input  wire       rst_n,
  input  wire       valid,
  input  wire       match,
  input  wire [1:0] fail,
  input  wire [7:0] tmr,
  output reg  [2:0] st,
  output reg        unlock,
  output reg        locked_out,
  output reg  [1:0] fail_n,
  output reg  [7:0] tmr_n
);
  // Encodings are externally visible through combo_lock.state.
  localparam [2:0] IDLE    = 3'b000;
  localparam [2:0] DIGIT2  = 3'b001;
  localparam [2:0] DIGIT3  = 3'b010;
  localparam [2:0] DIGIT4  = 3'b011;
  localparam [2:0] UNLOCK  = 3'b100;
  localparam [2:0] FAIL    = 3'b101;
  localparam [2:0] LOCKOUT = 3'b110;

  // Valid parameter ranges ensure all loads fit in 8 bits.
  localparam [7:0] INTERDIGIT_LOAD = INTERDIGIT_TIMEOUT_CYCLES[7:0] - 8'd1;
  localparam [7:0] UNLOCK_LOAD     = UNLOCK_CYCLES[7:0] - 8'd1;
  localparam [7:0] LOCKOUT_LOAD    = LOCKOUT_CYCLES[7:0] - 8'd1;
  localparam [1:0] MAX_FAIL       = MAX_ATTEMPTS[1:0];
  localparam [1:0] FAIL_THRESHOLD = MAX_FAIL - 2'd1;

  reg [2:0] st_n;

  always @(*) begin
    st_n   = st;
    fail_n = fail;
    tmr_n  = tmr;

    case (st)
      IDLE, DIGIT2, DIGIT3, DIGIT4: begin
        // Valid press has priority over inter-digit expiry in cycle N.
        if (valid) begin
          if (!match) begin
            st_n = FAIL;
          end else if (st == DIGIT4) begin
            st_n   = UNLOCK;
            tmr_n  = UNLOCK_LOAD;
            fail_n = 2'd0;
          end else begin
            st_n  = st + 3'd1;
            tmr_n = INTERDIGIT_LOAD;
          end
        end else if ((st != IDLE) && (INTERDIGIT_TIMEOUT_CYCLES != 0)) begin
          if (tmr == 8'd0) begin
            st_n = IDLE; // abandonment does not change fail
          end else begin
            tmr_n = tmr - 8'd1;
          end
        end
      end

      UNLOCK: begin
        // Presses are discarded here, including the final timed cycle.
        if (tmr == 8'd0) begin
          st_n = IDLE;
        end else begin
          tmr_n = tmr - 8'd1;
        end
      end

      FAIL: begin
        // FAIL lasts exactly one cycle, and only its exit increments fail.
        if (fail >= FAIL_THRESHOLD) begin
          st_n   = LOCKOUT;
          tmr_n  = LOCKOUT_LOAD;
          fail_n = MAX_FAIL;
        end else begin
          st_n   = IDLE;
          fail_n = fail + 2'd1;
        end
      end

      LOCKOUT: begin
        // No input affects the lockout timer or failure counter.
        if (tmr == 8'd0) begin
          st_n   = IDLE;
          fail_n = 2'd0;
        end else begin
          tmr_n = tmr - 8'd1;
        end
      end

      default: begin
        // Illegal 3'b111: return to IDLE, preserving fail and tmr.
        st_n = IDLE;
      end
    endcase
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      st         <= IDLE;
      unlock     <= 1'b0;
      locked_out <= 1'b0;
    end else begin
      st         <= st_n;
      // Direct flop outputs, derived from NEXT state, no cycle lag.
      unlock     <= (st_n == UNLOCK);
      locked_out <= (st_n == LOCKOUT);
    end
  end
endmodule
