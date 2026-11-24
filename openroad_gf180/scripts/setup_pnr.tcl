# Sourced by every P&R step after read_db: constraints, wire RC, layers, cells the tools must not use.
read_sdc constraints/$::env(TOP).sdc
set_wire_rc -signal -layer Metal2
set_wire_rc -clock -layer Metal4
set_routing_layers -signal Metal2-Metal5 -clock Metal2-Metal5
set_dont_use "*__sdff* $::env(SCL)__mux2_1 $::env(SCL)__oai33_2 $::env(SCL)__antenna $::env(SCL)__fill_* $::env(SCL)__fillcap_* $::env(SCL)__filltie $::env(SCL)__endcap"
