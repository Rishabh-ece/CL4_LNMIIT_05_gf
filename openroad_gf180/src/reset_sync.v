module reset_sync #(
    parameter integer RST_SYNC = 1
) (
    input  wire clk,
    input  wire rst_n,
    output wire internal_rst_n
);

    reg rs1;
    reg rs2;

    always @(posedge clk or negedge rst_n) begin

        if (!rst_n) begin
            rs1 <= 1'b0;
            rs2 <= 1'b0;
        end

        else begin
            rs1 <= 1'b1;
            rs2 <= rs1;
        end

    end

    assign internal_rst_n = (RST_SYNC == 1) ? rs2 : rst_n;

endmodule
