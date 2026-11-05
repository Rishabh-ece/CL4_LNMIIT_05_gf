
module reset_sync (
    input wire clk,
    input wire rst_n,
    output wire internal_rst_n
);

    reg rst_sync1;
    reg rst_sync2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rst_sync1 <= 1'b0;
            rst_sync2 <= 1'b0;
        end
        else begin
            rst_sync1 <= 1'b1;
            rst_sync2 <= rst_sync1;
        end
    end

    wire internal_rst_n = rst_sync2;

endmodule
