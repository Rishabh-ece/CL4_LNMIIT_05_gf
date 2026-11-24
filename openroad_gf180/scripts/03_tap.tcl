read_liberty $::env(LIB_TT)
read_db out/02_floorplan.odb
tapcell -distance 20 -tapcell_master $::env(SCL)__filltie -endcap_master $::env(SCL)__endcap
write_db out/03_tap.odb
